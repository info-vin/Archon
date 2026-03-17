import { ContentSource } from '../VictoryFeedList';

export interface RAGRef {
  content: string;
  metadata: {
    source: string;
    [key: string]: any;
  };
}

export interface ContextData {
  logs: any[];
  rag_refs: RAGRef[];
  context_summary: string;
}

export interface ContentWorkbenchProps {
  activeSource: ContentSource | null;
  contextData: ContextData | null;
  isLoadingContext: boolean;
  onDraft: (topic: string, config?: any) => void;
  onGenerateImage: (title: string) => void;
  onPublish: (post: any) => void;
  onSave: () => void;
  isDrafting: boolean;
  isGeneratingImage: boolean;
  title: string;
  content: string;
  onTitleChange: (value: string) => void;
  onContentChange: (value: string) => void;
  usedPrompt?: string;
  feedback?: string; // GAP-023: Instructions from Charlie
  aiScore?: number; // AI Quality Metric
}
