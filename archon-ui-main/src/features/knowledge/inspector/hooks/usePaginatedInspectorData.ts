/**
 * Paginated Inspector Data Hook
 * Implements progressive loading for documents and code examples
 */

import { useCallback, useEffect, useMemo, useState } from "react";
import { useKnowledgeChunks, useKnowledgeCodeExamples } from "../../hooks";
import type { CodeExample, DocumentChunk } from "../../types";

const PAGE_SIZE = 20;

export interface UsePaginatedInspectorDataProps {
  sourceId: string;
  searchQuery: string;
  enabled?: boolean;
}

export interface PaginatedData<T> {
  items: T[];
  isLoading: boolean;
  hasMore: boolean;
  total: number;
  loadMore: () => void;
  reset: () => void;
}

export interface UsePaginatedInspectorDataResult {
  documents: PaginatedData<DocumentChunk>;
  codeExamples: PaginatedData<CodeExample>;
}

export function usePaginatedInspectorData({
  sourceId,
  searchQuery,
  enabled = true,
}: UsePaginatedInspectorDataProps): UsePaginatedInspectorDataResult {
  // Pagination state for documents
  const [docsOffset, setDocsOffset] = useState(0);
  const [allDocs, setAllDocs] = useState<DocumentChunk[]>([]);

  // Pagination state for code examples
  const [codeOffset, setCodeOffset] = useState(0);
  const [allCode, setAllCode] = useState<CodeExample[]>([]);

  // Fetch documents with pagination
  const {
    data: docsResponse,
    isLoading: docsLoading,
    isFetching: docsFetching,
  } = useKnowledgeChunks(sourceId, {
    limit: PAGE_SIZE,
    offset: docsOffset,
    enabled,
  });

  // Fetch code examples with pagination
  const {
    data: codeResponse,
    isLoading: codeLoading,
    isFetching: codeFetching,
  } = useKnowledgeCodeExamples(sourceId, {
    limit: PAGE_SIZE,
    offset: codeOffset,
    enabled,
  });

  // Update accumulated documents when new data arrives
  useEffect(() => {
    if (!docsResponse?.chunks) return;

    if (docsOffset === 0) {
      // First page - replace all
      setAllDocs(docsResponse.chunks);
    } else {
      // Append new chunks, deduplicating by id
      setAllDocs((prev) => {
        const existingIds = new Set(prev.map((d) => d.id));
        const newChunks = docsResponse.chunks.filter((chunk) => !existingIds.has(chunk.id));
        return [...prev, ...newChunks];
      });
    }
  }, [docsResponse, docsOffset]);

  // Update accumulated code examples when new data arrives
  useEffect(() => {
    if (!codeResponse?.code_examples) return;

    if (codeOffset === 0) {
      // First page - replace all
      setAllCode(codeResponse.code_examples);
    } else {
      // Append new examples, deduplicating by id
      setAllCode((prev) => {
        const existingIds = new Set(prev.map((c) => c.id));
        const newExamples = codeResponse.code_examples.filter((example) => !existingIds.has(example.id));
        return [...prev, ...newExamples];
      });
    }
  }, [codeResponse, codeOffset]);

  // Pre-calculate document search strings to avoid O(N) string allocations during active search
  const searchableDocs = useMemo(() => {
    return allDocs.map((doc) => ({
      doc,
      searchStr: `${doc.content || ""} ${doc.metadata?.title || ""} ${doc.metadata?.section || ""} ${doc.url || ""}`.toLowerCase(),
    }));
  }, [allDocs]);

  // Pre-calculate code search strings to avoid O(N) string allocations during active search
  const searchableCode = useMemo(() => {
    return allCode.map((code) => ({
      code,
      searchStr: `${code.content || ""} ${code.summary || ""} ${code.metadata?.language || ""}`.toLowerCase(),
    }));
  }, [allCode]);

  // Filter documents based on search
  const filteredDocuments = useMemo(() => {
    if (!searchQuery) return allDocs;

    const query = searchQuery.toLowerCase();
    return searchableDocs
      .filter(({ searchStr }) => searchStr.includes(query))
      .map(({ doc }) => doc);
  }, [searchableDocs, allDocs, searchQuery]);

  // Filter code examples based on search
  const filteredCode = useMemo(() => {
    if (!searchQuery) return allCode;

    const query = searchQuery.toLowerCase();
    return searchableCode
      .filter(({ searchStr }) => searchStr.includes(query))
      .map(({ code }) => code);
  }, [searchableCode, allCode, searchQuery]);

  // Load more documents
  const loadMoreDocs = useCallback(() => {
    if (docsResponse?.has_more && !docsFetching) {
      setDocsOffset((prev) => prev + PAGE_SIZE);
    }
  }, [docsResponse?.has_more, docsFetching]);

  // Load more code examples
  const loadMoreCode = useCallback(() => {
    if (codeResponse?.has_more && !codeFetching) {
      setCodeOffset((prev) => prev + PAGE_SIZE);
    }
  }, [codeResponse?.has_more, codeFetching]);

  // Reset documents pagination
  const resetDocs = useCallback(() => {
    setDocsOffset(0);
    setAllDocs([]);
  }, []);

  // Reset code pagination
  const resetCode = useCallback(() => {
    setCodeOffset(0);
    setAllCode([]);
  }, []);

  // Reset when source changes or becomes enabled
  useEffect(() => {
    resetDocs();
    resetCode();
  }, [sourceId, enabled, resetDocs, resetCode]);

  return {
    documents: {
      items: filteredDocuments,
      isLoading: docsLoading,
      hasMore: docsResponse?.has_more || false,
      total: docsResponse?.total || 0,
      loadMore: loadMoreDocs,
      reset: resetDocs,
    },
    codeExamples: {
      items: filteredCode,
      isLoading: codeLoading,
      hasMore: codeResponse?.has_more || false,
      total: codeResponse?.total || 0,
      loadMore: loadMoreCode,
      reset: resetCode,
    },
  };
}
