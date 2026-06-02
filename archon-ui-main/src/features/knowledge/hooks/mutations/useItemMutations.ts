import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useToast } from "@/features/shared/hooks/useToast";
import { knowledgeService } from "../../services";
import type { KnowledgeItem, KnowledgeItemsResponse } from "../../types";
import { knowledgeKeys } from "../knowledgeKeys";

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
