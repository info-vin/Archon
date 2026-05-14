/**
 * Inspector Data Hook
 * Encapsulates data fetching and filtering logic for the inspector
 */

import { useMemo } from "react";
import { useKnowledgeChunks, useKnowledgeCodeExamples } from "../../hooks";
import type { CodeExample, DocumentChunk } from "../../types";

export interface UseInspectorDataProps {
  sourceId: string;
  searchQuery: string;
}

export interface UseInspectorDataResult {
  documents: {
    data: DocumentChunk[];
    filtered: DocumentChunk[];
    isLoading: boolean;
  };
  codeExamples: {
    data: CodeExample[];
    filtered: CodeExample[];
    isLoading: boolean;
  };
}

export function useInspectorData({ sourceId, searchQuery }: UseInspectorDataProps): UseInspectorDataResult {
  // Fetch documents and code examples with pagination (load first batch for initial display)
  const { data: documentsResponse, isLoading: docsLoading } = useKnowledgeChunks(sourceId, { limit: 100 });
  const { data: codeResponse, isLoading: codeLoading } = useKnowledgeCodeExamples(sourceId, { limit: 100 });

  const documentChunks = useMemo(() => documentsResponse?.chunks || [], [documentsResponse?.chunks]);
  const codeList = useMemo(() => codeResponse?.code_examples || [], [codeResponse?.code_examples]);

  // Pre-calculate document search strings to avoid O(N) string allocations during active search
  const searchableDocuments = useMemo(() => {
    return documentChunks.map(
      (doc) => `${doc.content || ""} ${doc.title || ""} ${doc.metadata?.title || ""} ${doc.metadata?.section || ""}`.toLowerCase()
    );
  }, [documentChunks]);

  // Pre-calculate code search strings to avoid O(N) string allocations during active search
  const searchableCode = useMemo(() => {
    return codeList.map(
      (code) => `${code.content || ""} ${code.summary || ""} ${code.language || ""} ${code.file_path || ""} ${code.title || ""}`.toLowerCase()
    );
  }, [codeList]);

  // Filter documents based on search
  const filteredDocuments = useMemo(() => {
    if (!searchQuery) return documentChunks;

    const query = searchQuery.toLowerCase();
    return documentChunks.filter((_, index) => searchableDocuments[index].includes(query));
  }, [searchableDocuments, documentChunks, searchQuery]);

  // Filter code examples based on search
  const filteredCode = useMemo(() => {
    if (!searchQuery) return codeList;

    const query = searchQuery.toLowerCase();
    return codeList.filter((_, index) => searchableCode[index].includes(query));
  }, [searchableCode, codeList, searchQuery]);

  return {
    documents: {
      data: documentChunks,
      filtered: filteredDocuments,
      isLoading: docsLoading,
    },
    codeExamples: {
      data: codeList,
      filtered: filteredCode,
      isLoading: codeLoading,
    },
  };
}
