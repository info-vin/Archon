import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useToast } from "@/features/shared/hooks/useToast";
import { createOptimisticEntity, createOptimisticId } from "@/features/shared/utils/optimistic";
import { progressKeys } from "../../progress/hooks/useProgressQueries";
import type { ActiveOperation, ActiveOperationsResponse } from "../../progress/types";
import { knowledgeService } from "../services";
import type {
  CrawlRequest,
  KnowledgeItem,
  KnowledgeItemsResponse,
  UploadMetadata,
} from "../types";
import { getProviderErrorMessage } from "../utils/providerErrorHandler";
import {
  addOptimisticOperation,
  rollbackKnowledgeSummaries,
  updateKnowledgeSummariesOptimistically,
} from "../utils/knowledgeOptimistic";
import { knowledgeKeys } from "./knowledgeKeys";

/**
 * Crawl URL mutation with optimistic updates
 * Returns the progressId that can be used to track crawl progress
 */
export function useCrawlUrl() {
  const queryClient = useQueryClient();
  const { showToast } = useToast();

  return useMutation<
    { progressId: string; message: string },
    Error,
    CrawlRequest,
    {
      previousSummaries?: Array<[readonly unknown[], KnowledgeItemsResponse | undefined]>;
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
      const previousSummaries = queryClient.getQueriesData<KnowledgeItemsResponse>({
        queryKey: knowledgeKeys.summariesPrefix(),
      });
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

      // Update all summaries caches with optimistic data
      updateKnowledgeSummariesOptimistically(queryClient, optimisticItem as KnowledgeItem);

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
      addOptimisticOperation(queryClient, optimisticOperation);

      // Return context for rollback and replacement
      return { previousSummaries, previousOperations, tempProgressId, tempItemId: tempProgressId };
    },
    onSuccess: (response, _variables, context) => {
      // Replace temporary IDs with real ones from the server
      if (context) {
        // Update summaries cache with real progress ID
        queryClient.setQueriesData<KnowledgeItemsResponse>({ queryKey: knowledgeKeys.summariesPrefix() }, (old) => {
          if (!old) return old;
          return {
            ...old,
            items: old.items.map((item) => {
              if (item.source_id === context.tempProgressId) {
                return {
                  ...item,
                  source_id: response.progressId,
                };
              }
              return item;
            }),
          };
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
      }

      // Invalidate to get fresh data
      queryClient.invalidateQueries({ queryKey: progressKeys.active() });

      showToast(`Crawl started: ${response.message}`, "success");

      // Return the response so caller can access progressId
      return response;
    },
    onError: (error, _variables, context) => {
      // Rollback optimistic updates on error
      if (context?.previousSummaries) {
        rollbackKnowledgeSummaries(queryClient, context.previousSummaries);
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
      previousSummaries?: Array<[readonly unknown[], KnowledgeItemsResponse | undefined]>;
      previousOperations?: ActiveOperationsResponse;
      tempProgressId: string;
    }
  >({
    mutationFn: ({ file, metadata }: { file: File; metadata: UploadMetadata }) =>
      knowledgeService.uploadDocument(file, metadata),
    onMutate: async ({ file, metadata }) => {
      // Cancel any outgoing refetches to prevent race conditions
      await queryClient.cancelQueries({ queryKey: knowledgeKeys.summariesPrefix() });
      await queryClient.cancelQueries({ queryKey: progressKeys.active() });

      // Snapshot the previous values for rollback
      const previousSummaries = queryClient.getQueriesData<KnowledgeItemsResponse>({
        queryKey: knowledgeKeys.summariesPrefix(),
      });
      const previousOperations = queryClient.getQueryData<ActiveOperationsResponse>(progressKeys.active());

      const tempProgressId = createOptimisticId();
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
        },
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      } as Omit<KnowledgeItem, "id">);

      // Update all summaries caches with optimistic data
      updateKnowledgeSummariesOptimistically(queryClient, optimisticItem as KnowledgeItem);

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
      addOptimisticOperation(queryClient, optimisticOperation);

      return { previousSummaries, previousOperations, tempProgressId, tempItemId: tempProgressId };
    },
    onSuccess: (response, _variables, context) => {
      // Replace temporary IDs with real ones from the server
      if (context && response?.progressId) {
        // Update summaries cache with real progress ID
        queryClient.setQueriesData<KnowledgeItemsResponse>({ queryKey: knowledgeKeys.summariesPrefix() }, (old) => {
          if (!old) return old;
          return {
            ...old,
            items: old.items.map((item) => {
              if (item.source_id === context.tempProgressId) {
                return {
                  ...item,
                  source_id: response.progressId,
                };
              }
              return item;
            }),
          };
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
      }

      // Only invalidate progress to start tracking the new operation
      // The lists/summaries will refresh automatically via polling when operations are active
      queryClient.invalidateQueries({ queryKey: progressKeys.active() });

      // Don't show success here - upload is just starting in background
      // Success/failure will be shown via progress polling
    },
    onError: (error, _variables, context) => {
      // Rollback optimistic updates on error
      if (context?.previousSummaries) {
        rollbackKnowledgeSummaries(queryClient, context.previousSummaries);
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
    onError: (error) => {
      // If it's a 404, the item might have already been deleted
      const is404Error =
        (error as any)?.statusCode === 404 ||
        (error instanceof Error && (error.message.includes("404") || error.message.includes("not found")));

      if (is404Error) {
        return;
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
