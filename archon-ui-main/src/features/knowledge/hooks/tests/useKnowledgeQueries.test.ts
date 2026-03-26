import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { renderHook, waitFor } from "@testing-library/react";
import React from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import type { KnowledgeItemsResponse } from "../../types";
import { knowledgeKeys, useCrawlUrl, useUploadDocument } from "..";

// Mock the services
vi.mock("../../services", () => ({
  knowledgeService: {
    getKnowledgeItem: vi.fn(),
    deleteKnowledgeItem: vi.fn(),
    updateKnowledgeItem: vi.fn(),
    crawlUrl: vi.fn(),
    refreshKnowledgeItem: vi.fn(),
    uploadDocument: vi.fn(),
    stopCrawl: vi.fn(),
    getKnowledgeItemChunks: vi.fn(),
    getCodeExamples: vi.fn(),
    searchKnowledgeBase: vi.fn(),
    getKnowledgeSources: vi.fn(),
  },
}));

// Mock progress keys since they're used in mutations
vi.mock("@/features/progress/hooks/useProgressQueries", () => ({
  progressKeys: {
    all: ["progress"],
    active: () => ["progress", "active"],
    detail: (id: string) => ["progress", "detail", id],
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
    refetchInterval: 30000,
    isPaused: false,
  }),
}));

describe("useKnowledgeQueries - Optimistic Updates", () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    vi.clearAllMocks();
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });
  });

  const Wrapper = ({ children }: { children: React.ReactNode }) =>
    React.createElement(QueryClientProvider, { client: queryClient }, children);

  describe("useCrawlUrl - Cache Injection", () => {
    it("should inject optimistic item into all matching summaries caches", async () => {
      // 1. Setup initial caches with different filters
      const technicalFilter = { knowledge_type: "technical" as const };
      const businessFilter = { knowledge_type: "business" as const };

      const initialTechData: KnowledgeItemsResponse = { items: [], total: 0, page: 1, per_page: 20 };
      const initialBizData: KnowledgeItemsResponse = { items: [], total: 0, page: 1, per_page: 20 };

      // We must set data to ensures the keys are in the cache
      queryClient.setQueryData(knowledgeKeys.summaries(technicalFilter), initialTechData);
      queryClient.setQueryData(knowledgeKeys.summaries(businessFilter), initialBizData);

      const { knowledgeService } = await import("../../services");
      vi.mocked(knowledgeService.crawlUrl).mockResolvedValue({
        success: true,
        progressId: "real-id",
        message: "Started",
      });

      const { result } = renderHook(() => useCrawlUrl(), { wrapper: Wrapper });

      // 2. Trigger mutation for a TECHNICAL crawl
      // We don't await yet because we want to check the cache state BEFORE success
      const mutationPromise = result.current.mutateAsync({
        url: "https://archon.ai",
        knowledge_type: "technical",
      });

      // 3. Check TECHNICAL cache (should have optimistic item)
      await waitFor(() => {
        const techCache = queryClient.getQueryData<KnowledgeItemsResponse>(knowledgeKeys.summaries(technicalFilter));
        expect(techCache?.items).toHaveLength(1);
        expect(techCache?.items[0].status).toBe("processing");
      });

      // 4. Check BUSINESS cache (should remain empty because type doesn't match)
      const bizCache = queryClient.getQueryData<KnowledgeItemsResponse>(knowledgeKeys.summaries(businessFilter));
      expect(bizCache?.items).toHaveLength(0);

      await mutationPromise;

      // 5. Check Success state - ID should be updated to real-id
      await waitFor(() => {
        const updatedTechCache = queryClient.getQueryData<KnowledgeItemsResponse>(
          knowledgeKeys.summaries(technicalFilter),
        );
        expect(updatedTechCache?.items[0].source_id).toBe("real-id");
      });
    });

    it("should rollback all summaries caches on error", async () => {
      const filter = { knowledge_type: "technical" as const };
      const initialData: KnowledgeItemsResponse = { items: [], total: 0, page: 1, per_page: 20 };
      queryClient.setQueryData(knowledgeKeys.summaries(filter), initialData);

      const { knowledgeService } = await import("../../services");
      vi.mocked(knowledgeService.crawlUrl).mockRejectedValue(new Error("Crawl failed"));

      const { result } = renderHook(() => useCrawlUrl(), { wrapper: Wrapper });

      try {
        await result.current.mutateAsync({ url: "https://fail.com", knowledge_type: "technical" });
      } catch (_e) {
        // Expected
      }

      // Cache should be rolled back to initial empty state
      const cache = queryClient.getQueryData<KnowledgeItemsResponse>(knowledgeKeys.summaries(filter));
      expect(cache?.items).toHaveLength(0);
    });
  });

  describe("useUploadDocument - Cache Injection", () => {
    it("should inject optimistic item for document upload", async () => {
      const filter = { knowledge_type: "business" as const };
      queryClient.setQueryData(knowledgeKeys.summaries(filter), { items: [], total: 0, page: 1, per_page: 20 });

      const { knowledgeService } = await import("../../services");
      vi.mocked(knowledgeService.uploadDocument).mockResolvedValue({
        success: true,
        progressId: "upload-123",
        message: "Started",
        filename: "manual.pdf",
      });

      const { result } = renderHook(() => useUploadDocument(), { wrapper: Wrapper });

      const file = new File(["test"], "manual.pdf", { type: "application/pdf" });
      await result.current.mutateAsync({
        file,
        metadata: { knowledge_type: "business" },
      });

      const cache = queryClient.getQueryData<KnowledgeItemsResponse>(knowledgeKeys.summaries(filter));
      expect(cache?.items).toHaveLength(1);
      expect(cache?.items[0].title).toBe("manual.pdf");
      expect(cache?.items[0].source_type).toBe("file");
    });
  });
});
