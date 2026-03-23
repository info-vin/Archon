import { describe, it, expect } from "vitest";
import { matchKnowledgeFilter } from "../knowledgeOptimistic";
import type { KnowledgeItem, KnowledgeItemsFilter } from "../../types";

describe("knowledgeOptimistic - matchKnowledgeFilter", () => {
  const mockItem: KnowledgeItem = {
    id: "1",
    source_id: "src-1",
    title: "Test Item",
    url: "https://example.com/test",
    source_type: "url",
    knowledge_type: "technical",
    status: "completed",
    document_count: 5,
    code_examples_count: 2,
    metadata: {
      description: "A technical test item",
      tags: ["react", "typescript"],
    },
    created_at: new Date().toISOString(),
    updated_at: new Date().toISOString(),
  };

  it("should match when no filter is provided", () => {
    expect(matchKnowledgeFilter(mockItem)).toBe(true);
  });

  it("should match when knowledge_type matches", () => {
    const filter: KnowledgeItemsFilter = { knowledge_type: "technical" };
    expect(matchKnowledgeFilter(mockItem, filter)).toBe(true);
  });

  it("should not match when knowledge_type differs", () => {
    const filter: KnowledgeItemsFilter = { knowledge_type: "business" };
    expect(matchKnowledgeFilter(mockItem, filter)).toBe(false);
  });

  it("should match when all tags are present", () => {
    const filter: KnowledgeItemsFilter = { tags: ["react"] };
    expect(matchKnowledgeFilter(mockItem, filter)).toBe(true);
    
    const filter2: KnowledgeItemsFilter = { tags: ["react", "typescript"] };
    expect(matchKnowledgeFilter(mockItem, filter2)).toBe(true);
  });

  it("should not match when some tags are missing", () => {
    const filter: KnowledgeItemsFilter = { tags: ["react", "missing"] };
    expect(matchKnowledgeFilter(mockItem, filter)).toBe(false);
  });

  it("should match when search query matches title", () => {
    const filter: KnowledgeItemsFilter = { search: "test" };
    expect(matchKnowledgeFilter(mockItem, filter)).toBe(true);
  });

  it("should match when search query matches URL", () => {
    const filter: KnowledgeItemsFilter = { search: "example" };
    expect(matchKnowledgeFilter(mockItem, filter)).toBe(true);
  });

  it("should match when search query matches description", () => {
    const filter: KnowledgeItemsFilter = { search: "technical" };
    expect(matchKnowledgeFilter(mockItem, filter)).toBe(true);
  });

  it("should not match when search query matches nothing", () => {
    const filter: KnowledgeItemsFilter = { search: "nomatch" };
    expect(matchKnowledgeFilter(mockItem, filter)).toBe(false);
  });
});
