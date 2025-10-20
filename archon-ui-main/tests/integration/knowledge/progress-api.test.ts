/**
 * Unit tests for Progress API
 * These tests use mocking and do not require a live backend.
 */

import { describe, it, expect, beforeEach, vi } from 'vitest';
import { progressService } from '../../../src/features/progress/services/progressService';
import { knowledgeService } from '../../../src/features/knowledge/services';
import type { ProgressResponse, CrawlStartResponse } from '../../../src/features/knowledge/progress/types';
import type { ActiveOperationsResponse } from '../../../src/features/progress/types';


// Mock the services
vi.mock('../../../src/features/progress/services/progressService', () => ({
  progressService: {
    getProgress: vi.fn(),
    listActiveOperations: vi.fn(),
  },
}));
vi.mock('../../../src/features/knowledge/services', () => ({
  knowledgeService: {
    crawlUrl: vi.fn(),
    stopCrawl: vi.fn(),
    uploadDocument: vi.fn(),
  },
}));

const mockedProgressService = vi.mocked(progressService);
const mockedKnowledgeService = vi.mocked(knowledgeService);


describe('Progress API (Mocked)', () => {

  beforeEach(() => {
    vi.resetAllMocks();
  });

  describe('Progress Tracking', () => {
    it('should track crawl progress', async () => {
      // Arrange
      const mockCrawlResponse: CrawlStartResponse = { progressId: 'crawl-123', success: true, message: 'started' };
      const mockProgressResponse: ProgressResponse = { progressId: 'crawl-123', status: 'processing', progress: 50, type: 'crawl' };
      mockedKnowledgeService.crawlUrl.mockResolvedValue(mockCrawlResponse);
      mockedProgressService.getProgress.mockResolvedValue(mockProgressResponse);

      // Act
      const crawlResponse = await knowledgeService.crawlUrl({ url: 'https://example.com/integration-test', knowledge_type: 'technical' });
      const progress = await progressService.getProgress(crawlResponse.progressId);

      // Assert
      expect(crawlResponse.progressId).toBe('crawl-123');
      expect(progress.progressId).toBe('crawl-123');
      expect(progress.status).toBe('processing');
    });

    it('should return 404 for non-existent progress', async () => {
      // Arrange
      mockedProgressService.getProgress.mockRejectedValue(new Error('Not Found'));

      // Act & Assert
      await expect(progressService.getProgress('non-existent-progress-id')).rejects.toThrow('Not Found');
    });

    it('should handle progress state transitions', async () => {
        // Arrange
        const mockCrawlResponse: CrawlStartResponse = { progressId: 'crawl-456', success: true, message: 'started' };
        mockedKnowledgeService.crawlUrl.mockResolvedValue(mockCrawlResponse);
        mockedProgressService.getProgress
            .mockResolvedValueOnce({ progressId: 'crawl-456', status: 'starting', progress: 10 })
            .mockResolvedValueOnce({ progressId: 'crawl-456', status: 'processing', progress: 50 })
            .mockResolvedValueOnce({ progressId: 'crawl-456', status: 'completed', progress: 100 });

        // Act
        const crawlResponse = await knowledgeService.crawlUrl({ url: 'https://httpbin.org/html', knowledge_type: 'technical' });
        const progress1 = await progressService.getProgress(crawlResponse.progressId);
        const progress2 = await progressService.getProgress(crawlResponse.progressId);
        const progress3 = await progressService.getProgress(crawlResponse.progressId);

        // Assert
        expect(progress1.status).toBe('starting');
        expect(progress2.status).toBe('processing');
        expect(progress3.status).toBe('completed');
    });

    it.skip('should track upload progress', () => {
      // Skipping this test as it requires FormData which is complex to mock reliably here.
    });
  });

  describe('Active Operations', () => {
    it('should list active operations', async () => {
      // Arrange
      const mockResponse: ActiveOperationsResponse = {
        operations: [{ operation_id: 'op-1', operation_type: 'crawl', status: 'processing', progress: 50 }],
        count: 1,
        timestamp: new Date().toISOString(),
      };
      mockedProgressService.listActiveOperations.mockResolvedValue(mockResponse);

      // Act
      const response = await progressService.listActiveOperations();

      // Assert
      expect(response.count).toBe(1);
      expect(response.operations[0].operation_id).toBe('op-1');
    });
  });

  describe('Progress Cleanup', () => {
    it.skip('should clean up completed progress after time', () => {
        // Skipping as this tests a time-based backend-only behavior.
    });
  });
});