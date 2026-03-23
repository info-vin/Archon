/**
 * Knowledge Base Query Hooks
 * Following TanStack Query best practices with query key factories
 */

import { useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { useSmartPolling } from "@/features/shared/hooks";
import { useActiveOperations } from "../../progress/hooks";
import type { ActiveOperation } from "../../progress/types";
import { DISABLED_QUERY_KEY, STALE_TIMES } from "../../shared/config/queryPatterns";
import { knowledgeService } from "../services";
import type {
  KnowledgeItem,
  KnowledgeItemsFilter,
  KnowledgeItemsResponse,
} from "../types";
import { knowledgeKeys } from "./knowledgeKeys";

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
 * Knowledge Summaries Hook with Active Operations Tracking
 * Fetches lightweight summaries and tracks active crawl operations
 * Only polls when there are active operations that we started
 */
export function useKnowledgeSummaries(filter?: KnowledgeItemsFilter) {
  // Track active crawl IDs locally - only set when we start a crawl/refresh
  const [activeCrawlIds, setActiveCrawlIds] = useState<string[]>([]);

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

  // When operations complete, remove them from tracking
  // Trust smart polling to handle eventual consistency - no manual invalidation needed
  // Active operations are already tracked and polling handles updates when operations complete

  return {
    ...summaryQuery,
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
