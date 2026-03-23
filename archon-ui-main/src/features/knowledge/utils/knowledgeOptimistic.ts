import type { QueryClient } from "@tanstack/react-query";
import type { ActiveOperation, ActiveOperationsResponse } from "../../progress/types";
import { progressKeys } from "../../progress/hooks/useProgressQueries";
import type { KnowledgeItem, KnowledgeItemsFilter, KnowledgeItemsResponse } from "../types";
import { knowledgeKeys } from "../hooks/knowledgeKeys";

/**
 * Helper to determine if a knowledge item matches a given filter.
 * Used for client-side optimistic filtering.
 */
export function matchKnowledgeFilter(item: KnowledgeItem, filter?: KnowledgeItemsFilter): boolean {
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

/**
 * Updates all knowledge summary caches with an optimistic item.
 */
export function updateKnowledgeSummariesOptimistically(
  queryClient: QueryClient,
  optimisticItem: KnowledgeItem
) {
  const queryEntries = queryClient.getQueriesData<KnowledgeItemsResponse>({
    queryKey: knowledgeKeys.summariesPrefix(),
  });

  queryEntries.forEach(([qk, old]) => {
    const filter = qk[qk.length - 1] as KnowledgeItemsFilter | undefined;
    
    if (!matchKnowledgeFilter(optimisticItem, filter)) return;

    const updatedData: KnowledgeItemsResponse = !old
      ? { items: [optimisticItem], total: 1, page: 1, per_page: 100 }
      : { ...old, items: [optimisticItem, ...old.items], total: (old.total ?? old.items.length) + 1 };

    queryClient.setQueryData(qk, updatedData);
  });
}

/**
 * Adds an optimistic operation to the active operations cache.
 */
export function addOptimisticOperation(
  queryClient: QueryClient,
  operation: ActiveOperation
) {
  queryClient.setQueryData<ActiveOperationsResponse>(progressKeys.active(), (old) => {
    if (!old) {
      return {
        operations: [operation],
        count: 1,
        timestamp: new Date().toISOString(),
      };
    }
    return {
      ...old,
      operations: [operation, ...old.operations],
      count: old.count + 1,
    };
  });
}

/**
 * Rollback all knowledge summary queries to previous state.
 */
export function rollbackKnowledgeSummaries(
  queryClient: QueryClient,
  previousSummaries: Array<[readonly unknown[], KnowledgeItemsResponse | undefined]>
) {
  for (const [queryKey, data] of previousSummaries) {
    queryClient.setQueryData(queryKey, data);
  }
}
