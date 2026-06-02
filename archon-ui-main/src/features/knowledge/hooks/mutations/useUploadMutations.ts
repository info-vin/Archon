import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useToast } from "@/features/shared/hooks/useToast";
import { createOptimisticEntity, createOptimisticId } from "@/features/shared/utils/optimistic";
import { progressKeys } from "../../../progress/hooks/useProgressQueries";
import type { ActiveOperation, ActiveOperationsResponse } from "../../../progress/types";
import { knowledgeService } from "../../services";
import type { KnowledgeItem, KnowledgeItemsResponse, UploadMetadata } from "../../types";
import {
  addOptimisticOperation,
  rollbackKnowledgeSummaries,
  updateKnowledgeSummariesOptimistically,
} from "../../utils/knowledgeOptimistic";
import { knowledgeKeys } from "../knowledgeKeys";

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
