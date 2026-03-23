import type { KnowledgeItemsFilter } from "../types";

/**
 * Query keys factory for better organization and type safety in the Knowledge Base feature.
 * Physically isolated to prevent circular dependencies between Queries and Mutations.
 */
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
