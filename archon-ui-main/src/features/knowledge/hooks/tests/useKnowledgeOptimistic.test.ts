import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import React from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { knowledgeKeys, useCrawlUrl, useKnowledgeSummaries } from "../useKnowledgeQueries";

// Mock the services
vi.mock("../../services", () => ({
  knowledgeService: {
    getKnowledgeSummaries: vi.fn().mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      per_page: 100,
    }),
    crawlUrl: vi.fn().mockReturnValue(new Promise(() => {})), // Pending promise to keep it in "optimistic" state?
    // Actually crawlUrl mutation returns immediately? No, it awaits the result.
    // The mutation runs, onMutate happens, then mutationFn runs.
    // If mutationFn resolves, onSuccess happens.
    // We want to test the state *during* the mutation (or after onMutate).
    // But useMutation doesn't support "pause" easily in tests unless we mock mutationFn to hang.
  },
}));

// Mock the toast hook
vi.mock("@/features/shared/hooks/useToast", () => ({
  useToast: () => ({
    showToast: vi.fn(),
  }),
}));

// Mock smart polling
vi.mock("@/features/shared/hooks", () => ({
  useSmartPolling: () => ({
    refetchInterval: false,
    isPaused: false,
  }),
}));

// Mock active operations
vi.mock("../../progress/hooks", () => ({
  useActiveOperations: () => ({
    data: { operations: [], count: 0 },
  }),
}));

describe("Optimistic Updates Across Filters", () => {
  let queryClient: QueryClient;
  let wrapper: ({ children }: { children: React.ReactNode }) => React.ReactElement;

  beforeEach(async () => {
    vi.clearAllMocks();
    const { knowledgeService } = await import("../../services");

    // Setup mutation to hang so we can observe optimistic state
    // Or just resolve it but check "optimistic" store?
    // If it resolves, onSuccess updates ID and schedules removal.
    // We want to test that it IS visible in a new query.
    vi.mocked(knowledgeService.crawlUrl).mockImplementation(async () => {
      // Simulate delay
      await new Promise(resolve => setTimeout(resolve, 100));
      return {
        success: true,
        progressId: "progress-123",
        message: "Crawling started",
      };
    });

    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });

    wrapper = ({ children }: { children: React.ReactNode }) =>
      React.createElement(QueryClientProvider, { client: queryClient }, children);
  });

  it("should show optimistic item in a new filter view", async () => {
    // 1. Render useCrawlUrl
    const { result: mutationResult } = renderHook(() => useCrawlUrl(), { wrapper });

    // 2. Start mutation
    const crawlPromise = mutationResult.current.mutateAsync({
      url: "https://technical.example.com",
      knowledge_type: "technical",
      tags: ["tag1"],
    });

    // 3. Render useKnowledgeSummaries with "technical" filter
    // Note: The optimistic update happens in onMutate, which is synchronous-ish (await cancelQueries).
    // We need to wait for onMutate to finish.

    await waitFor(() => {
        expect(queryClient.getQueryData(knowledgeKeys.optimistic())).toHaveLength(1);
    });

    // Now verify it appears in a filtered view
    const { result: summaryResult } = renderHook(
      () => useKnowledgeSummaries({ knowledge_type: "technical" }),
      { wrapper }
    );

    // Should contain the optimistic item
    await waitFor(() => {
      expect(summaryResult.current.data?.items).toHaveLength(1);
      expect(summaryResult.current.data?.items[0].url).toBe("https://technical.example.com");
      expect(summaryResult.current.data?.items[0].status).toBe("processing");
    });

    // 4. Verify it does NOT appear in a non-matching filter view
    const { result: businessResult } = renderHook(
      () => useKnowledgeSummaries({ knowledge_type: "business" }),
      { wrapper }
    );

    await waitFor(() => {
      expect(businessResult.current.data?.items).toHaveLength(0);
    });

    // 5. Verify search filter
    const { result: searchResult } = renderHook(
      () => useKnowledgeSummaries({ search: "technical" }),
      { wrapper }
    );
     await waitFor(() => {
      expect(searchResult.current.data?.items).toHaveLength(1);
    });

    // Wait for mutation to finish
    await crawlPromise;
  });
});
