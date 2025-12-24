/**
 * Manual test to verify knowledge API integration
 * Run with: npx tsx tests/manual/test-knowledge-api.ts
 */

// Set up test environment
process.env.NODE_ENV = 'test';
process.env.ARCHON_SERVER_PORT = '8181';

import { knowledgeService } from '../../src/features/knowledge/services/knowledgeService';
import { progressService } from '../../src/features/knowledge/progress/services/progressService';

// Ensure fetch in Node environments lacking global fetch
if (typeof fetch === "undefined") {
  // Use dynamic import for ESM compatibility
  const { fetch: nodeFetch } = await import('node-fetch');
  // @ts-expect-error: assign global
  globalThis.fetch = nodeFetch as typeof fetch;
}

async function testKnowledgeAPI(): Promise<void> {
  try {
    // Test 1: Get knowledge items
    const items = await knowledgeService.getKnowledgeSummaries({
      page: 1,
      per_page: 5,
    });
    if (items.items.length > 0) {
      // First item
    }

    // Test 2: Filter by type
    await knowledgeService.getKnowledgeSummaries({
      knowledge_type: 'technical',
      page: 1,
      per_page: 3,
    });

    // Test 3: Get chunks if item exists
    if (items.items.length > 0) {
      const sourceId = items.items[0].source_id;
      await knowledgeService.getKnowledgeItemChunks(sourceId);

      // Test 4: Get code examples
      await knowledgeService.getCodeExamples(sourceId);
    }

    // Test 5: Search
    try {
      await knowledgeService.searchKnowledgeBase({
        query: 'API',
        limit: 3,
      });
    } catch {
      // Search endpoint might not be implemented yet
    }

    // Test 6: Start a test crawl (but immediately stop it)
    try {
      const crawlResponse = await knowledgeService.crawlUrl({
        url: 'https://example.com/test-integration',
        knowledge_type: 'technical',
        max_depth: 1,
      });
      
      // Get progress
      await progressService.getProgress(crawlResponse.progressId);
      
      // Stop the crawl
      await knowledgeService.stopCrawl(crawlResponse.progressId);
    } catch {
      // Crawl test failed
    }
    
  } catch {
    process.exit(1);
  }
}

// Run the test
testKnowledgeAPI();