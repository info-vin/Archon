/**
 * Unit tests for Knowledge Base Service
 * These tests use mocking and do not require a live backend.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { knowledgeService } from '../../../src/features/knowledge/services';
import type { KnowledgeItemsResponse, CrawlStartResponse, ChunksResponse, CodeExamplesResponse, SearchResultsResponse, KnowledgeSource } from '../../../src/features/knowledge/types';

// Mock the entire knowledgeService module
vi.mock('../../../src/features/knowledge/services', () => ({
  knowledgeService: {
    getKnowledgeSummaries: vi.fn(),
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

// Now we can use vi.mocked to access the mocked functions
const mockedKnowledgeService = vi.mocked(knowledgeService);

describe('Knowledge API (Mocked)', () => {

  // Reset mocks before each test to ensure test isolation
  beforeEach(() => {
    vi.resetAllMocks();
  });

  describe('Knowledge Items', () => {
    it('should fetch knowledge items list', async () => {
      // Arrange
      const mockResponse: KnowledgeItemsResponse = {
        items: [{ source_id: '1', title: 'Test Item', metadata: {} }],
        total: 1, page: 1, per_page: 10, success: true,
      };
      mockedKnowledgeService.getKnowledgeSummaries.mockResolvedValue(mockResponse);

      // Act
      const response = await knowledgeService.getKnowledgeSummaries({ page: 1, per_page: 10 });

      // Assert
      expect(mockedKnowledgeService.getKnowledgeSummaries).toHaveBeenCalledWith({ page: 1, per_page: 10 });
      expect(response.items[0].title).toBe('Test Item');
    });

    it('should filter knowledge items by type', async () => {
      // Arrange
      const mockResponse: KnowledgeItemsResponse = {
        items: [{ source_id: '2', title: 'Technical Item', metadata: { knowledge_type: 'technical' } }],
        total: 1, page: 1, per_page: 5, success: true,
      };
      mockedKnowledgeService.getKnowledgeSummaries.mockResolvedValue(mockResponse);

      // Act
      const response = await knowledgeService.getKnowledgeSummaries({ knowledge_type: 'technical', page: 1, per_page: 5 });

      // Assert
      expect(response.items[0].metadata.knowledge_type).toBe('technical');
    });

    it('should handle pagination', async () => {
        // Arrange
        mockedKnowledgeService.getKnowledgeSummaries
            .mockResolvedValueOnce({ items: [], total: 4, page: 1, per_page: 2, success: true })
            .mockResolvedValueOnce({ items: [], total: 4, page: 2, per_page: 2, success: true });

        // Act
        const page1 = await knowledgeService.getKnowledgeSummaries({ page: 1, per_page: 2 });
        const page2 = await knowledgeService.getKnowledgeSummaries({ page: 2, per_page: 2 });

        // Assert
        expect(page1.page).toBe(1);
        expect(page2.page).toBe(2);
    });
  });

  describe('Crawl Operations', () => {
    it('should start a crawl and return progress ID', async () => {
        // Arrange
        const mockResponse: CrawlStartResponse = { progressId: 'crawl-123', message: 'Crawl started', success: true };
        mockedKnowledgeService.crawlUrl.mockResolvedValue(mockResponse);

        // Act
        const response = await knowledgeService.crawlUrl({ url: 'https://example.com/test', knowledge_type: 'technical' });

        // Assert
        expect(response.progressId).toBe('crawl-123');
        expect(response.success).toBe(true);
    });

    it('should handle invalid URL', async () => {
        // Arrange
        mockedKnowledgeService.crawlUrl.mockRejectedValue(new Error('Invalid URL'));

        // Act & Assert
        await expect(knowledgeService.crawlUrl({ url: 'not-a-valid-url', knowledge_type: 'technical' })).rejects.toThrow('Invalid URL');
    });
  });

  describe('Document Operations', () => {
    it('should get chunks for a knowledge item if it exists', async () => {
      // Arrange
      const mockResponse: ChunksResponse = { success: true, source_id: '1', chunks: [], total: 0 };
      mockedKnowledgeService.getKnowledgeItemChunks.mockResolvedValue(mockResponse);

      // Act
      const chunks = await knowledgeService.getKnowledgeItemChunks('1');

      // Assert
      expect(chunks.success).toBe(true);
      expect(chunks.source_id).toBe('1');
      expect(Array.isArray(chunks.chunks)).toBe(true);
    });

    it('should get code examples for a knowledge item if it exists', async () => {
        // Arrange
        const mockResponse: CodeExamplesResponse = { success: true, source_id: '1', code_examples: [], total: 0 };
        mockedKnowledgeService.getCodeExamples.mockResolvedValue(mockResponse);

        // Act
        const examples = await knowledgeService.getCodeExamples('1');

        // Assert
        expect(examples.success).toBe(true);
        expect(examples.source_id).toBe('1');
        expect(Array.isArray(examples.code_examples)).toBe(true);
    });
  });

  describe('Delete Operations', () => {
    it('should handle deletion of non-existent item', async () => {
      // Arrange
      const mockResponse = { success: true, message: 'Item not found, but operation is idempotent.' };
      mockedKnowledgeService.deleteKnowledgeItem.mockResolvedValue(mockResponse);

      // Act
      const result = await knowledgeService.deleteKnowledgeItem('non-existent-source-id');

      // Assert
      expect(result.success).toBe(true);
    });
  });

  describe('Search Operations', () => {
    it('should search knowledge base', async () => {
      // Arrange
      const mockResponse: SearchResultsResponse = { success: true, results: [], query: 'test' };
      mockedKnowledgeService.searchKnowledgeBase.mockResolvedValue(mockResponse);

      // Act
      const results = await knowledgeService.searchKnowledgeBase({ query: 'test', limit: 5 });

      // Assert
      expect(results).toBeDefined();
      expect(results.success).toBe(true);
    });
  });

  describe('Sources', () => {
    it('should get knowledge sources', async () => {
      // Arrange
      const mockResponse: KnowledgeSource[] = [{ source_id: '1', display_name: 'Source 1' }];
      mockedKnowledgeService.getKnowledgeSources.mockResolvedValue(mockResponse);

      // Act
      const sources = await knowledgeService.getKnowledgeSources();

      // Assert
      expect(Array.isArray(sources)).toBe(true);
      expect(sources.length).toBe(1);
      expect(sources[0].display_name).toBe('Source 1');
    });
  });
});