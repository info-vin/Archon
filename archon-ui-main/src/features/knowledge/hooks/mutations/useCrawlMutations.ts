import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useToast } from "@/features/shared/hooks/useToast";
import { createOptimisticEntity, createOptimisticId } from "@/features/shared/utils/optimistic";
import { progressKeys } from "../../../progress/hooks/useProgressQueries";
import type { ActiveOperation, ActiveOperationsResponse } from "../../../progress/types";
import { knowledgeService } from "../../services";
import type {
  CrawlRequest,
  KnowledgeItem,
  KnowledgeItemsResponse,
} from "../../types";
import { getProviderErrorMessage } from "../../utils/providerErrorHandler";
import {
  addOptimisticOperation,
  rollbackKnowledgeSummaries,
  updateKnowledgeSummariesOptimistically,
} from "../../utils/knowledgeOptimistic";
import { knowledgeKeys } from "../knowledgeKeys";

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
