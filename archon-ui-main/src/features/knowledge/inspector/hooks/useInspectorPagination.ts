/**
 * Inspector Pagination Hook
 * Handles pagination for the Knowledge Inspector with "Load More" functionality
 */

import { useInfiniteQuery } from "@tanstack/react-query";
import { useMemo } from "react";
import { STALE_TIMES } from "@/features/shared/config/queryPatterns";
import { knowledgeKeys } from "../../hooks";
import { knowledgeService } from "../../services";
import type { ChunksResponse, CodeExample, CodeExamplesResponse, DocumentChunk } from "../../types";

export interface UseInspectorPaginationProps {
  sourceId: string;
  viewMode: "documents" | "code";
  searchQuery: string;
}

export interface UseInspectorPaginationResult {
  items: (DocumentChunk | CodeExample)[];
  isLoading: boolean;
  hasNextPage: boolean;
  fetchNextPage: (options?: any) => Promise<any>;
  isFetchingNextPage: boolean;
  totalCount: number;
  loadedCount: number;
}

export function useInspectorPagination({
  sourceId,
  viewMode,
  searchQuery,
}: UseInspectorPaginationProps): UseInspectorPaginationResult {
  const PAGE_SIZE = 100;

  // Use infinite query for the current view mode
  const { data, isLoading, hasNextPage, fetchNextPage, isFetchingNextPage } = useInfiniteQuery<
    ChunksResponse | CodeExamplesResponse,
    Error
  >({
    queryKey: [
      ...knowledgeKeys.detail(sourceId),
      viewMode === "documents" ? "chunks-infinite" : "code-examples-infinite",
    ],
    queryFn: ({ pageParam }: { pageParam: unknown }) => {
      const page = Number(pageParam) || 0;
      const service =
        viewMode === "documents" ? knowledgeService.getKnowledgeItemChunks : knowledgeService.getCodeExamples;

      return service(sourceId, {
        limit: PAGE_SIZE,
        offset: page * PAGE_SIZE,
      });
    },
    getNextPageParam: (lastPage, allPages) => {
      const hasMore = (lastPage as ChunksResponse | CodeExamplesResponse)?.has_more;
      return hasMore ? allPages.length : undefined;
    },
    enabled: !!sourceId,
    staleTime: STALE_TIMES.normal,
    initialPageParam: 0,
  });

  // PERFORMANCE: Separate data extraction/precalculation from search filtering
  // This prevents recalculating the search strings on every keystroke
  const processedData = useMemo(() => {
    type Page = ChunksResponse | CodeExamplesResponse;
    if (!data || !data.pages) {
      return { allItems: [], searchableItems: [], totalCount: 0, loadedCount: 0 };
    }

    // Flatten all pages - data has 'pages' property from useInfiniteQuery
    const pages = data.pages as Page[];
    const allItems = pages.flatMap((page): (DocumentChunk | CodeExample)[] =>
      "chunks" in page ? (page.chunks ?? []) : "code_examples" in page ? (page.code_examples ?? []) : [],
    );

    // Get total from first page (fallback to loadedCount)
    const first = pages[0];
    const totalCount = first && "total" in first && typeof first.total === "number" ? first.total : allItems.length;
    const loadedCount = allItems.length;

    // Precalculate .toLowerCase() searchable string to prevent O(N*M) redundant string allocations during filter
    const searchableItems = allItems.map((item) => {
      let searchStr = "";
      if (viewMode === "documents") {
        const doc = item as DocumentChunk;
        searchStr = `${doc.content || ""} ${doc.title || ""} ${doc.metadata?.title || ""} ${doc.metadata?.section || ""}`.toLowerCase();
      } else {
        const code = item as CodeExample;
        searchStr = `${code.content || ""} ${code.summary || ""} ${code.language || ""} ${code.file_path || ""} ${code.title || ""}`.toLowerCase();
      }
      return { item, searchStr };
    });

    return { allItems, searchableItems, totalCount, loadedCount };
  }, [data, viewMode]);

  // Apply search filtering
  const { items, totalCount, loadedCount } = useMemo(() => {
    const { allItems, searchableItems, totalCount, loadedCount } = processedData;

    if (!searchQuery) {
      return { items: allItems, totalCount, loadedCount };
    }

    const query = searchQuery.toLowerCase();
    const filteredItems = searchableItems
      .filter(({ searchStr }) => searchStr.includes(query))
      .map(({ item }) => item);

    return { items: filteredItems, totalCount, loadedCount };
  }, [processedData, searchQuery]);

  return {
    items,
    isLoading,
    hasNextPage: !!hasNextPage,
    fetchNextPage,
    isFetchingNextPage,
    totalCount,
    loadedCount,
  };
}
