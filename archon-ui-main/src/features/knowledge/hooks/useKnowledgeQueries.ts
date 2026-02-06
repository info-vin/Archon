/**
 * Knowledge Base Query Hooks
 * Following TanStack Query best practices with query key factories
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useMemo, useState } from "react";
import { useSmartPolling } from "@/features/shared/hooks";
import { useToast } from "@/features/shared/hooks/useToast";
import { createOptimisticEntity, createOptimisticId } from "@/features/shared/utils/optimistic";
import { useKnowledgeOptimistic } from "../context";
import { useActiveOperations } from "../../progress/hooks";
import { progressKeys } from "../../progress/hooks/useProgressQueries";
import type { ActiveOperation, ActiveOperationsResponse } from "../../progress/types";
import { DISABLED_QUERY_KEY, STALE_TIMES } from "../../shared/config/queryPatterns";
import { knowledgeService } from "../services";
import type {
  CrawlRequest,
  CrawlStartResponse,
  KnowledgeItem,
  KnowledgeItemsFilter,
  KnowledgeItemsResponse,
  UploadMetadata,
} from "../types";
import { getProviderErrorMessage } from "../utils/providerErrorHandler";

// Query keys factory for better organization and type safety
export const knowledgeKeys = {
  all: ["knowledge"] as const,
  lists: () => [...knowledgeKeys.all, "list"] as const,
  detail: (id: string) => [...knowledgeKeys.all, "detail", id] as const,
  // Include domain + pagination to avoid cache collisions
  chunks: (id: string, opts?: { domain?: string; limit?: number; offset?: number }) =>
    [
      ...knowledgeKeys.all,
      id,
      "chunks",
      { domain: opts?.domain ?? "all", limit: opts?.limit, offset: opts?.offset },
    ] as const,
  // Include pagination in the key
  codeExamples: (id: string, opts?: { limit?: number; offset?: number }) =>
    [...knowledgeKeys.all, id, "code-examples", { limit: opts?.limit, offset: opts?.offset }] as const,
  // Prefix helper for targeting all summaries queries
  summariesPrefix: () => [...knowledgeKeys.all, "summaries"] as const,
  summaries: (filter?: KnowledgeItemsFilter) => [...knowledgeKeys.all, "summaries", filter] as const,
  sources: () => [...knowledgeKeys.all, "sources"] as const,
  search: (query: string) => [...knowledgeKeys.all, "search", query] as const,
};

/**
 * Fetch a specific knowledge item
 */
export function useKnowledgeItem(sourceId: string | null) {
  return useQuery<KnowledgeItem>({
    queryKey: sourceId ? knowledgeKeys.detail(sourceId) : DISABLED_QUERY_KEY,
    queryFn: () => (sourceId ? knowledgeService.getKnowledgeItem(sourceId) : Promise.reject("No source ID")),
    enabled: !!sourceId,
    staleTime: STALE_TIMES.normal,
  });
}

/**
 * Fetch document chunks for a knowledge item
 */
export function useKnowledgeItemChunks(
  sourceId: string | null,
  opts?: { domain?: string; limit?: number; offset?: number },
) {
  // See PRPs/local/frontend-state-management-refactor.md Phase 4: Configure Request Deduplication
  return useQuery({
    queryKey: sourceId ? knowledgeKeys.chunks(sourceId, opts) : DISABLED_QUERY_KEY,
    queryFn: () =>
      sourceId
        ? knowledgeService.getKnowledgeItemChunks(sourceId, {
            domainFilter: opts?.domain,
            limit: opts?.limit,
            offset: opts?.offset,
          })
        : Promise.reject("No source ID"),
    enabled: !!sourceId,
    staleTime: STALE_TIMES.normal,
  });
}

/**
 * Fetch code examples for a knowledge item
 */
export function useCodeExamples(sourceId: string | null) {
  return useQuery({
    queryKey: sourceId ? knowledgeKeys.codeExamples(sourceId) : DISABLED_QUERY_KEY,
    queryFn: () => (sourceId ? knowledgeService.getCodeExamples(sourceId) : Promise.reject("No source ID")),
    enabled: !!sourceId,
    staleTime: STALE_TIMES.normal,
  });
}

/**
 * Crawl URL mutation with optimistic updates
 * Returns the progressId that can be used to track crawl progress
 */
export function useCrawlUrl() {
  const queryClient = useQueryClient();
  const { showToast } = useToast();
  const { addOptimisticCreate, removeOptimisticCreate } = useKnowledgeOptimistic();

  return useMutation<
    CrawlStartResponse,
    Error,
    CrawlRequest,
    {
      previousOperations?: ActiveOperationsResponse;
      tempProgressId: string;
      optimisticItem: KnowledgeItem;
    }
  >({
    mutationFn: (request: CrawlRequest) => knowledgeService.crawlUrl(request),
    onMutate: async (request) => {
      // Cancel any outgoing refetches to prevent race conditions
      await queryClient.cancelQueries({ queryKey: progressKeys.active() });

      // Snapshot the previous values for rollback
      const previousOperations = queryClient.getQueryData<ActiveOperationsResponse>(progressKeys.active());

      // Generate temporary progress ID and optimistic entity
      const tempProgressId = createOptimisticId();
      const optimisticItem = createOptimisticEntity<KnowledgeItem>({
        title: (() => {
          try {
            return new URL(request.url).hostname || "New crawl";
          } catch {
            return "New crawl";
          }
        })(),
        url: request.url,
        source_id: tempProgressId,
        source_type: "url",
        knowledge_type: request.knowledge_type || "technical",
        status: "processing",
        document_count: 0,
        code_examples_count: 0,
        metadata: {
          knowledge_type: request.knowledge_type || "technical",
          tags: request.tags || [],
          source_type: "url",
          status: "processing",
          description: `Crawling ${request.url}`,
        },
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      } as Omit<KnowledgeItem, "id">);

      // Add to global optimistic context (fixes invisible updates issue)
      addOptimisticCreate(optimisticItem);

      // Create optimistic progress operation
      const optimisticOperation: ActiveOperation = {
        operation_id: tempProgressId,
        operation_type: "crawl",
        status: "starting",
        progress: 0,
        message: `Initializing crawl for ${request.url}`,
        started_at: new Date().toISOString(),
        progressId: tempProgressId,
        type: "crawl",
        url: request.url,
        source_id: tempProgressId,
      };

      // Add optimistic operation to active operations
      queryClient.setQueryData<ActiveOperationsResponse>(progressKeys.active(), (old) => {
        if (!old) {
          return {
            operations: [optimisticOperation],
            count: 1,
            timestamp: new Date().toISOString(),
          };
        }
        return {
          ...old,
          operations: [optimisticOperation, ...old.operations],
          count: old.count + 1,
        };
      });

      // Return context for rollback and replacement
      return { previousOperations, tempProgressId, optimisticItem };
    },
    onSuccess: async (response, _variables, context) => {
      // Replace temporary IDs with real ones from the server
      if (context) {
        // Update progress operation with real progress ID
        queryClient.setQueryData<ActiveOperationsResponse>(progressKeys.active(), (old) => {
          if (!old) return old;
          return {
            ...old,
            operations: old.operations.map((op) => {
              if (op.operation_id === context.tempProgressId) {
                return {
                  ...op,
                  operation_id: response.progressId,
                  progressId: response.progressId,
                  source_id: response.progressId,
                  message: response.message || op.message,
                };
              }
              return op;
            }),
          };
        });

        // Update the optimistic item in context to use real ID
        // This ensures deduplication works when server returns the item
        removeOptimisticCreate(context.tempProgressId);
        addOptimisticCreate({
          ...context.optimisticItem,
          source_id: response.progressId,
        });
      }

      // Invalidate to get fresh data
      await queryClient.invalidateQueries({ queryKey: progressKeys.active() });
      await queryClient.invalidateQueries({ queryKey: knowledgeKeys.summariesPrefix() });

      showToast(`Crawl started: ${response.message}`, "success");

      return response;
    },
    onError: (error, _variables, context) => {
      // Rollback optimistic updates on error
      if (context) {
        removeOptimisticCreate(context.tempProgressId);
      }
      if (context?.previousOperations) {
        queryClient.setQueryData(progressKeys.active(), context.previousOperations);
      }

      const errorMessage = getProviderErrorMessage(error) || "Failed to start crawl";
      showToast(errorMessage, "error");
    },
  });
}

/**
 * Upload document mutation with optimistic updates
 */
export function useUploadDocument() {
  const queryClient = useQueryClient();
  const { showToast } = useToast();
  const { addOptimisticCreate, removeOptimisticCreate } = useKnowledgeOptimistic();

  return useMutation<
    { progressId: string; message: string },
    Error,
    { file: File; metadata: UploadMetadata },
    {
      previousOperations?: ActiveOperationsResponse;
      tempProgressId: string;
      optimisticItem: KnowledgeItem;
    }
  >({
    mutationFn: ({ file, metadata }: { file: File; metadata: UploadMetadata }) =>
      knowledgeService.uploadDocument(file, metadata),
    onMutate: async ({ file, metadata }) => {
      // Cancel any outgoing refetches to prevent race conditions
      await queryClient.cancelQueries({ queryKey: progressKeys.active() });

      // Snapshot the previous values for rollback
      const previousOperations = queryClient.getQueryData<ActiveOperationsResponse>(progressKeys.active());

      const tempProgressId = createOptimisticId();

      // Create optimistic knowledge item for the upload
      const optimisticItem = createOptimisticEntity<KnowledgeItem>({
        title: file.name,
        url: `file://${file.name}`,
        source_id: tempProgressId,
        source_type: "file",
        knowledge_type: metadata.knowledge_type || "technical",
        status: "processing",
        document_count: 0,
        code_examples_count: 0,
        metadata: {
          knowledge_type: metadata.knowledge_type || "technical",
          tags: metadata.tags || [],
          source_type: "file",
          status: "processing",
          description: `Uploading ${file.name}`,
          file_name: file.name,
        },
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      } as Omit<KnowledgeItem, "id">);

      // Add to global optimistic context
      addOptimisticCreate(optimisticItem);

      // Create optimistic progress operation for upload
      const optimisticOperation: ActiveOperation = {
        operation_id: tempProgressId,
        operation_type: "upload",
        status: "starting",
        progress: 0,
        message: `Uploading ${file.name}`,
        started_at: new Date().toISOString(),
        progressId: tempProgressId,
        type: "upload",
        url: `file://${file.name}`,
        source_id: tempProgressId,
      };

      // Add optimistic operation to active operations
      queryClient.setQueryData<ActiveOperationsResponse>(progressKeys.active(), (old) => {
        if (!old) {
          return {
            operations: [optimisticOperation],
            count: 1,
            timestamp: new Date().toISOString(),
          };
        }
        return {
          ...old,
          operations: [optimisticOperation, ...old.operations],
          count: old.count + 1,
        };
      });

      return { previousOperations, tempProgressId, optimisticItem };
    },
    onSuccess: async (response, _variables, context) => {
      // Replace temporary IDs with real ones from the server
      if (context && response?.progressId) {
        // Update progress operation with real progress ID
        queryClient.setQueryData<ActiveOperationsResponse>(progressKeys.active(), (old) => {
          if (!old) return old;
          return {
            ...old,
            operations: old.operations.map((op) => {
              if (op.operation_id === context.tempProgressId) {
                return {
                  ...op,
                  operation_id: response.progressId,
                  progressId: response.progressId,
                  source_id: response.progressId,
                  message: response.message || op.message,
                };
              }
              return op;
            }),
          };
        });

        // Update the optimistic item in context to use real ID
        removeOptimisticCreate(context.tempProgressId);
        addOptimisticCreate({
          ...context.optimisticItem,
          source_id: response.progressId,
        });
      }

      // Only invalidate progress to start tracking the new operation
      await queryClient.invalidateQueries({ queryKey: progressKeys.active() });
      await queryClient.invalidateQueries({ queryKey: knowledgeKeys.summariesPrefix() });
    },
    onError: (error, _variables, context) => {
      // Rollback optimistic updates on error
      if (context) {
        removeOptimisticCreate(context.tempProgressId);
      }
      if (context?.previousOperations) {
        queryClient.setQueryData(progressKeys.active(), context.previousOperations);
      }

      // Display the actual error message from backend
      const message = error instanceof Error ? error.message : "Failed to upload document";
      showToast(message, "error");
    },
  });
}

/**
 * Stop crawl mutation
 */
export function useStopCrawl() {
  const { showToast } = useToast();

  return useMutation({
    mutationFn: (progressId: string) => knowledgeService.stopCrawl(progressId),
    onSuccess: (_data, progressId) => {
      showToast(`Stop requested (${progressId}). Operation will end shortly.`, "info");
    },
    onError: (error, progressId) => {
      // If it's a 404, the operation might have already completed or been cancelled
      // See PRPs/local/frontend-state-management-refactor.md Phase 4: Configure Request Deduplication
      const is404Error =
        (error as any)?.statusCode === 404 ||
        (error instanceof Error && (error.message.includes("404") || error.message.includes("not found")));

      if (is404Error) {
        // Don't show error for 404s - the operation is likely already gone
        return;
      }

      const errorMessage = error instanceof Error ? error.message : "Unknown error";
      showToast(`Failed to stop crawl (${progressId}): ${errorMessage}`, "error");
    },
  });
}

/**
 * Delete knowledge item mutation
 */
export function useDeleteKnowledgeItem() {
  const queryClient = useQueryClient();
  const { showToast } = useToast();
  const { addOptimisticDelete, removeOptimisticDelete } = useKnowledgeOptimistic();

  return useMutation({
    mutationFn: (sourceId: string) => knowledgeService.deleteKnowledgeItem(sourceId),
    onMutate: async (sourceId) => {
      // Add to global optimistic context
      addOptimisticDelete(sourceId);
      return { sourceId };
    },
    onError: (error, sourceId) => {
      // Roll back
      removeOptimisticDelete(sourceId);

      const errorMessage = error instanceof Error ? error.message : "Failed to delete item";
      showToast(errorMessage, "error");
    },
    onSuccess: async (data, _sourceId) => {
      showToast(data.message || "Item deleted successfully", "success");

      // Invalidate summaries to reconcile with server
      await queryClient.invalidateQueries({ queryKey: knowledgeKeys.summariesPrefix() });
      await queryClient.invalidateQueries({ queryKey: knowledgeKeys.all });

      // Cleanup is handled by useKnowledgeSummaries when it detects item is gone
    },
  });
}

/**
 * Update knowledge item mutation
 */
export function useUpdateKnowledgeItem() {
  const queryClient = useQueryClient();
  const { showToast } = useToast();
  const { addOptimisticUpdate, removeOptimisticUpdate } = useKnowledgeOptimistic();

  return useMutation({
    mutationFn: ({ sourceId, updates }: { sourceId: string; updates: Partial<KnowledgeItem> & { tags?: string[] } }) =>
      knowledgeService.updateKnowledgeItem(sourceId, updates),
    onMutate: async ({ sourceId, updates }) => {
      // Add to global optimistic context
      const updateData: Partial<KnowledgeItem> = {};

      // Map updates to KnowledgeItem structure
      if ("title" in updates && typeof updates.title === "string") updateData.title = updates.title;
      if ("knowledge_type" in updates && typeof updates.knowledge_type === "string") updateData.knowledge_type = updates.knowledge_type as "technical" | "business";

      // Handle tags updates by constructing metadata
      if ("tags" in updates && Array.isArray(updates.tags)) {
        // Try to find current metadata to preserve other fields
        let currentMetadata: any = {};

        // Check detail cache
        const detailItem = queryClient.getQueryData<KnowledgeItem>(knowledgeKeys.detail(sourceId));
        if (detailItem?.metadata) {
           currentMetadata = detailItem.metadata;
        } else {
           // Check summaries cache
           const summaries = queryClient.getQueriesData<KnowledgeItemsResponse>({ queryKey: knowledgeKeys.summariesPrefix() });
           for (const [_, data] of summaries) {
             const found = data?.items.find((i) => i.source_id === sourceId);
             if (found?.metadata) {
               currentMetadata = found.metadata;
               break;
             }
           }
        }

        updateData.metadata = {
          ...currentMetadata,
          tags: updates.tags,
        };
      }

      addOptimisticUpdate(sourceId, updateData);

      // Optimistically update the detail item
      await queryClient.cancelQueries({ queryKey: knowledgeKeys.detail(sourceId) });
      const previousItem = queryClient.getQueryData<KnowledgeItem>(knowledgeKeys.detail(sourceId));

      if (previousItem) {
        const updatedItem = { ...previousItem, ...updateData };
        // Ensure metadata is merged correctly if updateData has it
        if (updateData.metadata) {
          updatedItem.metadata = updateData.metadata; // We constructed full metadata in updateData
        }
        queryClient.setQueryData<KnowledgeItem>(knowledgeKeys.detail(sourceId), updatedItem);
      }

      return { sourceId, previousItem };
    },
    onError: (error, variables, context) => {
      // Rollback context
      removeOptimisticUpdate(variables.sourceId);

      // Rollback detail
      if (context?.previousItem) {
        queryClient.setQueryData(knowledgeKeys.detail(variables.sourceId), context.previousItem);
      }

      const errorMessage = error instanceof Error ? error.message : "Failed to update item";
      showToast(errorMessage, "error");
    },
    onSuccess: async (_data, { sourceId }) => {
      showToast("Item updated successfully", "success");

      // Invalidate all related queries
      await queryClient.invalidateQueries({ queryKey: knowledgeKeys.detail(sourceId) });
      await queryClient.invalidateQueries({ queryKey: knowledgeKeys.summariesPrefix() });

      // Cleanup
      removeOptimisticUpdate(sourceId);
    },
  });
}

/**
 * Refresh knowledge item mutation
 */
export function useRefreshKnowledgeItem() {
  const queryClient = useQueryClient();
  const { showToast } = useToast();

  return useMutation({
    mutationFn: (sourceId: string) => knowledgeService.refreshKnowledgeItem(sourceId),
    onSuccess: (data, sourceId) => {
      showToast("Refresh started", "success");

      // Remove the item from cache as it's being refreshed
      queryClient.removeQueries({ queryKey: knowledgeKeys.detail(sourceId) });

      // Invalidate summaries immediately - backend is consistent after refresh initiation
      queryClient.invalidateQueries({ queryKey: knowledgeKeys.summariesPrefix() });

      return data;
    },
    onError: (error) => {
      const errorMessage = error instanceof Error ? error.message : "Failed to refresh item";
      showToast(errorMessage, "error");
    },
  });
}

/**
 * Knowledge Summaries Hook with Active Operations Tracking
 * Fetches lightweight summaries and tracks active crawl operations
 * Only polls when there are active operations that we started
 */
export function useKnowledgeSummaries(filter?: KnowledgeItemsFilter) {
  // Track active crawl IDs locally - only set when we start a crawl/refresh
  const [activeCrawlIds, setActiveCrawlIds] = useState<string[]>([]);

  // Consume optimistic context
  const {
    optimisticCreates,
    optimisticUpdates,
    optimisticDeletes,
    removeOptimisticCreate,
    removeOptimisticDelete
  } = useKnowledgeOptimistic();

  // ALWAYS poll for active operations to catch pre-existing ones
  // This ensures we discover operations that were started before page load
  const { data: activeOperationsData } = useActiveOperations(true);

  // Check if we have any active operations (either tracked or discovered)
  const hasActiveOperations = (activeOperationsData?.operations?.length || 0) > 0;

  // Convert to the format expected by components
  const activeOperations: ActiveOperation[] = useMemo(() => {
    if (!activeOperationsData?.operations) return [];

    // Include ALL active operations (not just tracked ones) to catch pre-existing operations
    // This ensures operations started before page load are still shown
    return activeOperationsData.operations.map((op) => ({
      ...op,
      progressId: op.operation_id,
      type: op.operation_type,
    }));
  }, [activeOperationsData]);

  // Fetch summaries with smart polling when there are active operations
  const { refetchInterval } = useSmartPolling(hasActiveOperations ? STALE_TIMES.frequent : STALE_TIMES.normal);

  const summaryQuery = useQuery<KnowledgeItemsResponse>({
    queryKey: knowledgeKeys.summaries(filter),
    queryFn: () => knowledgeService.getKnowledgeSummaries(filter),
    refetchInterval: hasActiveOperations ? refetchInterval : false, // Poll when ANY operations are active
    refetchOnWindowFocus: true,
    staleTime: STALE_TIMES.normal, // Consider data stale after 30 seconds
  });

  // Cleanup optimistic creates that are now in the server response
  useEffect(() => {
    if (!summaryQuery.data?.items) return;

    // Find optimistic creates that match server items by ID
    const serverIds = new Set(summaryQuery.data.items.map(i => i.source_id));

    optimisticCreates.forEach(item => {
      if (serverIds.has(item.source_id)) {
        removeOptimisticCreate(item.source_id);
      }
    });

    // Also cleanup optimistic deletes if they are gone from server
    optimisticDeletes.forEach(id => {
      if (!serverIds.has(id)) {
        removeOptimisticDelete(id);
      }
    });

  }, [summaryQuery.data, optimisticCreates, optimisticDeletes, removeOptimisticCreate, removeOptimisticDelete]);

  // Merge optimistic data with server data
  const mergedData = useMemo(() => {
    const serverItems = summaryQuery.data?.items || [];
    const serverTotal = summaryQuery.data?.total || 0;

    // 1. Filter optimistic creates based on current filter
    const visibleOptimisticCreates = optimisticCreates.filter(item => {
      // Filter by knowledge_type
      if (filter?.knowledge_type && item.knowledge_type !== filter.knowledge_type) return false;

      // Filter by tags
      if (filter?.tags && filter.tags.length > 0) {
         const itemTags = item.metadata?.tags || [];
         if (!filter.tags.every(tag => itemTags.includes(tag))) return false;
      }

      // Filter by source_type
      if (filter?.source_type && item.source_type !== filter.source_type) return false;

      // Filter by search query
      if (filter?.search) {
        const searchLower = filter.search.toLowerCase();
        const titleMatch = item.title.toLowerCase().includes(searchLower);
        const urlMatch = item.url.toLowerCase().includes(searchLower);
        if (!titleMatch && !urlMatch) return false;
      }

      // Exclude if pending deletion
      if (optimisticDeletes.has(item.source_id)) return false;

      // Deduplicate: If server already has it (should be handled by useEffect, but for render safety)
      if (serverItems.some(si => si.source_id === item.source_id)) return false;

      return true;
    });

    // 2. Filter deletes from server items
    let processedServerItems = serverItems.filter(item => !optimisticDeletes.has(item.source_id));

    // 3. Apply updates to server items
    processedServerItems = processedServerItems.map(item => {
      if (optimisticUpdates[item.source_id]) {
        return { ...item, ...optimisticUpdates[item.source_id] };
      }
      return item;
    });

    // 4. Apply updates to optimistic creates
    const processedOptimisticCreates = visibleOptimisticCreates.map(item => {
       if (optimisticUpdates[item.source_id]) {
         return { ...item, ...optimisticUpdates[item.source_id] };
       }
       return item;
    });

    // 5. Combine: Optimistic creates first
    // Only show optimistic creates if we are on page 1 (or no page specified)
    const showOptimistic = !filter?.page || filter.page === 1;

    const finalItems = showOptimistic
      ? [...processedOptimisticCreates, ...processedServerItems]
      : processedServerItems;

    return {
      ...(summaryQuery.data || { page: 1, per_page: 100, total: 0 }),
      items: finalItems,
      total: serverTotal + (showOptimistic ? processedOptimisticCreates.length : 0)
    } as KnowledgeItemsResponse;

  }, [summaryQuery.data, optimisticCreates, optimisticUpdates, optimisticDeletes, filter]);

  // When operations complete, remove them from tracking
  // Trust smart polling to handle eventual consistency - no manual invalidation needed
  // Active operations are already tracked and polling handles updates when operations complete

  return {
    ...summaryQuery,
    data: mergedData, // Use the merged data
    activeCrawlIds,
    setActiveCrawlIds, // Export this so components can add IDs when starting operations
    activeOperations,
  };
}

/**
 * Fetch document chunks with pagination
 */
export function useKnowledgeChunks(
  sourceId: string | null,
  options?: { limit?: number; offset?: number; enabled?: boolean },
) {
  return useQuery({
    queryKey: sourceId
      ? knowledgeKeys.chunks(sourceId, { limit: options?.limit, offset: options?.offset })
      : DISABLED_QUERY_KEY,
    queryFn: () =>
      sourceId
        ? knowledgeService.getKnowledgeItemChunks(sourceId, {
            limit: options?.limit,
            offset: options?.offset,
          })
        : Promise.reject("No source ID"),
    enabled: options?.enabled !== false && !!sourceId,
    staleTime: STALE_TIMES.normal,
  });
}

/**
 * Fetch code examples with pagination
 */
export function useKnowledgeCodeExamples(
  sourceId: string | null,
  options?: { limit?: number; offset?: number; enabled?: boolean },
) {
  return useQuery({
    queryKey: sourceId
      ? knowledgeKeys.codeExamples(sourceId, { limit: options?.limit, offset: options?.offset })
      : DISABLED_QUERY_KEY,
    queryFn: () =>
      sourceId
        ? knowledgeService.getCodeExamples(sourceId, {
            limit: options?.limit,
            offset: options?.offset,
          })
        : Promise.reject("No source ID"),
    enabled: options?.enabled !== false && !!sourceId,
    staleTime: STALE_TIMES.normal,
  });
}
