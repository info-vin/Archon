/**
 * Knowledge Base Query Hooks
 * Following TanStack Query best practices with query key factories
 */

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useMemo, useState } from "react";
import { useSmartPolling } from "@/features/shared/hooks";
import { useToast } from "@/features/shared/hooks/useToast";
import { createOptimisticEntity, createOptimisticId } from "@/features/shared/utils/optimistic";
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
  optimistic: () => [...knowledgeKeys.all, "optimistic"] as const,
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

// Helper to filter optimistic items based on KnowledgeItemsFilter
function matchKnowledgeFilter(item: KnowledgeItem, filter?: KnowledgeItemsFilter): boolean {
  if (!filter) return true;

  // Filter by type
  if (filter.knowledge_type && item.knowledge_type !== filter.knowledge_type) {
    return false;
  }

  // Filter by tags
  if (filter.tags && filter.tags.length > 0) {
    const itemTags = item.metadata?.tags || [];
    const hasAllTags = filter.tags.every((t) => itemTags.includes(t));
    if (!hasAllTags) return false;
  }

  // Filter by search query (simple fuzzy match)
  if (filter.search) {
    const query = filter.search.toLowerCase();
    const title = item.title?.toLowerCase() || "";
    const url = item.url?.toLowerCase() || "";
    const description = item.metadata?.description?.toLowerCase() || "";

    if (!title.includes(query) && !url.includes(query) && !description.includes(query)) {
      return false;
    }
  }

  return true;
}

// Hook to access the optimistic items store
function useOptimisticKnowledgeItems() {
  const { data } = useQuery<KnowledgeItem[]>({
    queryKey: knowledgeKeys.optimistic(),
    queryFn: () => [], // Client-only query
    staleTime: Infinity,
    gcTime: Infinity,
    enabled: false, // Don't fetch
    initialData: [],
  });
  return data || [];
}

/**
 * Crawl URL mutation with optimistic updates
 * Returns the progressId that can be used to track crawl progress
 */
export function useCrawlUrl() {
  const queryClient = useQueryClient();
  const { showToast } = useToast();

  return useMutation<
    CrawlStartResponse,
    Error,
    CrawlRequest,
    {
      previousOperations?: ActiveOperationsResponse;
      tempProgressId: string;
      tempItemId: string;
    }
  >({
    mutationFn: (request: CrawlRequest) => knowledgeService.crawlUrl(request),
    onMutate: async (request) => {
      // Cancel any outgoing refetches to prevent race conditions
      await queryClient.cancelQueries({ queryKey: knowledgeKeys.summariesPrefix() });
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

      // Add to optimistic store (centralized optimistic updates)
      queryClient.setQueryData<KnowledgeItem[]>(knowledgeKeys.optimistic(), (old) => {
        return [optimisticItem, ...(old || [])];
      });

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
      return { previousOperations, tempProgressId, tempItemId: tempProgressId };
    },
    onSuccess: (response, _variables, context) => {
      // Replace temporary IDs with real ones from the server
      if (context) {
        // Update optimistic store with real ID to prevent duplication during transition
        queryClient.setQueryData<KnowledgeItem[]>(knowledgeKeys.optimistic(), (old) => {
          if (!old) return [];
          return old.map((item) =>
            item.source_id === context.tempProgressId ? { ...item, source_id: response.progressId } : item,
          );
        });

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

        // Schedule removal of the optimistic item after a delay
        // This ensures the item stays visible (deduplicated) until the server response is guaranteed to have it
        setTimeout(() => {
          queryClient.setQueryData<KnowledgeItem[]>(knowledgeKeys.optimistic(), (old) => {
            return (old || []).filter((item) => item.source_id !== response.progressId);
          });
        }, 5000);
      }

      // Invalidate to get fresh data
      queryClient.invalidateQueries({ queryKey: progressKeys.active() });
      queryClient.invalidateQueries({ queryKey: knowledgeKeys.summariesPrefix() });

      showToast(`Crawl started: ${response.message}`, "success");

      // Return the response so caller can access progressId
      return response;
    },
    onError: (error, _variables, context) => {
      // Rollback optimistic updates on error
      if (context?.tempItemId) {
        // Remove from optimistic store
        queryClient.setQueryData<KnowledgeItem[]>(knowledgeKeys.optimistic(), (old) => {
          return (old || []).filter((item) => item.source_id !== context.tempItemId);
        });
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

  return useMutation<
    { progressId: string; message: string },
    Error,
    { file: File; metadata: UploadMetadata },
    {
      previousOperations?: ActiveOperationsResponse;
      tempProgressId: string;
      tempItemId: string;
    }
  >({
    mutationFn: ({ file, metadata }: { file: File; metadata: UploadMetadata }) =>
      knowledgeService.uploadDocument(file, metadata),
    onMutate: async ({ file, metadata }) => {
      // Cancel any outgoing refetches to prevent race conditions
      await queryClient.cancelQueries({ queryKey: knowledgeKeys.summariesPrefix() });
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

      // Add to optimistic store
      queryClient.setQueryData<KnowledgeItem[]>(knowledgeKeys.optimistic(), (old) => {
        return [optimisticItem, ...(old || [])];
      });

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

      return { previousOperations, tempProgressId, tempItemId: tempProgressId };
    },
    onSuccess: (response, _variables, context) => {
      // Replace temporary IDs with real ones from the server
      if (context && response?.progressId) {
        // Update optimistic store with real ID
        queryClient.setQueryData<KnowledgeItem[]>(knowledgeKeys.optimistic(), (old) => {
          if (!old) return [];
          return old.map((item) =>
            item.source_id === context.tempProgressId ? { ...item, source_id: response.progressId } : item,
          );
        });

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

        // Schedule removal
        setTimeout(() => {
          queryClient.setQueryData<KnowledgeItem[]>(knowledgeKeys.optimistic(), (old) => {
            return (old || []).filter((item) => item.source_id !== response.progressId);
          });
        }, 5000);
      }

      // Only invalidate progress to start tracking the new operation
      queryClient.invalidateQueries({ queryKey: progressKeys.active() });
      queryClient.invalidateQueries({ queryKey: knowledgeKeys.summariesPrefix() });

      // Don't show success here - upload is just starting in background
      // Success/failure will be shown via progress polling
    },
    onError: (error, _variables, context) => {
      // Rollback optimistic updates on error
      if (context?.tempItemId) {
        // Remove from optimistic store
        queryClient.setQueryData<KnowledgeItem[]>(knowledgeKeys.optimistic(), (old) => {
          return (old || []).filter((item) => item.source_id !== context.tempItemId);
        });
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

  return useMutation({
    mutationFn: (sourceId: string) => knowledgeService.deleteKnowledgeItem(sourceId),
    onMutate: async (sourceId) => {
      // Cancel summary queries (all filters)
      await queryClient.cancelQueries({ queryKey: knowledgeKeys.summariesPrefix() });

      // Snapshot all summary caches (for all filters)
      const summariesPrefix = knowledgeKeys.summariesPrefix();
      const previousEntries = queryClient.getQueriesData<KnowledgeItemsResponse>({
        queryKey: summariesPrefix,
      });

      // Optimistically remove the item from each cached summary
      for (const [queryKey, data] of previousEntries) {
        if (!data) continue;
        const nextItems = data.items.filter((item) => item.source_id !== sourceId);
        const removed = data.items.length - nextItems.length;
        queryClient.setQueryData<KnowledgeItemsResponse>(queryKey, {
          ...data,
          items: nextItems,
          total: Math.max(0, (data.total ?? data.items.length) - removed),
        });
      }

      return { previousEntries };
    },
    onError: (error, _sourceId, context) => {
      // Roll back all summaries
      for (const [queryKey, data] of context?.previousEntries ?? []) {
        queryClient.setQueryData(queryKey, data);
      }

      const errorMessage = error instanceof Error ? error.message : "Failed to delete item";
      showToast(errorMessage, "error");
    },
    onSuccess: (data) => {
      showToast(data.message || "Item deleted successfully", "success");

      // Invalidate summaries to reconcile with server
      queryClient.invalidateQueries({ queryKey: knowledgeKeys.summariesPrefix() });
      // Also invalidate detail views
      queryClient.invalidateQueries({ queryKey: knowledgeKeys.all });
    },
  });
}

/**
 * Update knowledge item mutation
 */
export function useUpdateKnowledgeItem() {
  const queryClient = useQueryClient();
  const { showToast } = useToast();

  return useMutation({
    mutationFn: ({ sourceId, updates }: { sourceId: string; updates: Partial<KnowledgeItem> & { tags?: string[] } }) =>
      knowledgeService.updateKnowledgeItem(sourceId, updates),
    onMutate: async ({ sourceId, updates }) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: knowledgeKeys.detail(sourceId) });
      await queryClient.cancelQueries({ queryKey: knowledgeKeys.summariesPrefix() });

      // Snapshot the previous values
      const previousItem = queryClient.getQueryData<KnowledgeItem>(knowledgeKeys.detail(sourceId));
      const previousSummaries = queryClient.getQueriesData({ queryKey: knowledgeKeys.summariesPrefix() });

      // Optimistically update the detail item
      if (previousItem) {
        const updatedItem = { ...previousItem };

        // Initialize metadata if missing
        const currentMetadata = updatedItem.metadata || {};

        // Handle title updates
        if ("title" in updates && typeof updates.title === "string") {
          updatedItem.title = updates.title;
        }

        // Handle tags updates - update in metadata only
        if ("tags" in updates && Array.isArray(updates.tags)) {
          const newTags = updates.tags as string[];
          updatedItem.metadata = {
            ...currentMetadata,
            tags: newTags,
          };
        }

        // Handle knowledge_type updates
        if ("knowledge_type" in updates && typeof updates.knowledge_type === "string") {
          const newType = updates.knowledge_type as "technical" | "business";
          updatedItem.knowledge_type = newType;
          // Also update in metadata for consistency
          updatedItem.metadata = {
            ...updatedItem.metadata,
            knowledge_type: newType,
          };
        }

        queryClient.setQueryData<KnowledgeItem>(knowledgeKeys.detail(sourceId), updatedItem);
      }

      // Optimistically update summaries cache
      queryClient.setQueriesData<KnowledgeItemsResponse>({ queryKey: knowledgeKeys.summariesPrefix() }, (old) => {
        if (!old?.items) return old;

        return {
          ...old,
          items: old.items.map((item) => {
            if (item.source_id === sourceId) {
              const updatedItem = { ...item };

              // Initialize metadata if missing
              const currentMetadata = updatedItem.metadata || {};

              // Update title if provided
              if ("title" in updates && typeof updates.title === "string") {
                updatedItem.title = updates.title;
              }

              // Update tags if provided - update in metadata only
              if ("tags" in updates && Array.isArray(updates.tags)) {
                const newTags = updates.tags as string[];
                updatedItem.metadata = {
                  ...currentMetadata,
                  tags: newTags,
                };
              }

              // Update knowledge_type if provided
              if ("knowledge_type" in updates && typeof updates.knowledge_type === "string") {
                const newType = updates.knowledge_type as "technical" | "business";
                updatedItem.knowledge_type = newType;
                // Also update in metadata for consistency
                updatedItem.metadata = {
                  ...updatedItem.metadata,
                  knowledge_type: newType,
                };
              }

              return updatedItem;
            }
            return item;
          }),
        };
      });

      return { previousItem, previousSummaries };
    },
    onError: (error, variables, context) => {
      // Rollback on error
      if (context?.previousItem) {
        queryClient.setQueryData(knowledgeKeys.detail(variables.sourceId), context.previousItem);
      }
      if (context?.previousSummaries) {
        // Rollback all summary queries
        for (const [queryKey, data] of context.previousSummaries) {
          queryClient.setQueryData(queryKey, data);
        }
      }

      const errorMessage = error instanceof Error ? error.message : "Failed to update item";
      showToast(errorMessage, "error");
    },
    onSuccess: (_data, { sourceId }) => {
      showToast("Item updated successfully", "success");

      // Invalidate all related queries
      queryClient.invalidateQueries({ queryKey: knowledgeKeys.detail(sourceId) });
      queryClient.invalidateQueries({ queryKey: knowledgeKeys.summariesPrefix() });
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

  // Access the centralized optimistic store
  const optimisticItems = useOptimisticKnowledgeItems();

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

  // Merge optimistic items with server data
  const mergedData = useMemo(() => {
    const serverData = summaryQuery.data || { items: [], total: 0, page: 1, per_page: 100 };

    // 1. Filter optimistic items based on the current filter
    const matchingOptimistic = optimisticItems.filter((item) => matchKnowledgeFilter(item, filter));

    if (matchingOptimistic.length === 0) return serverData;

    // 2. Remove optimistic items that are already present in the server response (deduplication)
    // We check by source_id. Real items have persistent IDs. Optimistic items have temp IDs.
    // However, in onSuccess we update optimistic items to have real IDs.
    // So if the server has processed the item, we will find a collision and prefer the server version (or we could just dedupe).
    const serverIds = new Set(serverData.items.map((i) => i.source_id));
    const uniqueOptimistic = matchingOptimistic.filter((item) => !serverIds.has(item.source_id));

    if (uniqueOptimistic.length === 0) return serverData;

    return {
      ...serverData,
      items: [...uniqueOptimistic, ...serverData.items],
      total: (serverData.total || 0) + uniqueOptimistic.length,
    };
  }, [summaryQuery.data, optimisticItems, filter]);

  // When operations complete, remove them from tracking
  // Trust smart polling to handle eventual consistency - no manual invalidation needed
  // Active operations are already tracked and polling handles updates when operations complete

  return {
    ...summaryQuery,
    data: mergedData, // Return merged data
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
