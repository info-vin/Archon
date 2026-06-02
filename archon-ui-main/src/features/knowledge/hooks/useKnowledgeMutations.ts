/**
 * Facade for knowledge mutations
 * This file re-exports all mutations to maintain backward compatibility
 * with existing imports while keeping the implementation modular.
 */
export { useCrawlUrl, useStopCrawl } from "./mutations/useCrawlMutations";
export { useUploadDocument } from "./mutations/useUploadMutations";
export {
  useDeleteKnowledgeItem,
  useUpdateKnowledgeItem,
  useRefreshKnowledgeItem,
} from "./mutations/useItemMutations";
