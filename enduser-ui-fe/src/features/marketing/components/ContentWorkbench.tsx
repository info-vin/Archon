import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  EyeIcon, 
  FileEditIcon,
  SparklesIcon
} from '@/components/Icons';

import {
  ContentWorkbenchProps,
  useWorkbenchLogic,
  WorkbenchHeader,
  SourceContextPane,
  CharlieFeedbackBanner,
  EditorBody,
  AICommandCenter
} from './workbench';

export const ContentWorkbench: React.FC<ContentWorkbenchProps> = ({
  activeSource,
  contextData,
  isLoadingContext,
  onDraft,
  onGenerateImage,
  onPublish,
  onSave,
  isDrafting,
  isGeneratingImage,
  title,
  content,
  onTitleChange,
  onContentChange,
  usedPrompt,
  feedback,
  aiScore
}) => {
  const [isContextOpen, setIsContextOpen] = useState(true);
  const [promptCenterOpen, setPromptCenterOpen] = useState(false);
  const navigate = useNavigate();

  const {
    promptTab,
    setPromptTab,
    config,
    setConfig,
    toggleItem,
    getTempPromptPreview,
    getPreviewImage
  } = useWorkbenchLogic({
    activeSource,
    usedPrompt,
    content
  });

  const handleDraftExecute = () => {
    if (activeSource) {
      onDraft(activeSource.title, {
        ...config,
        enable_web_research: config.enableWebSearch
      });
      // Keep panel open to show feedback if needed, or close based on UX
    }
  };

  const handleSave = () => {
    onSave();
  };

  if (!activeSource) {
    return (
      <div className="h-full flex items-center justify-center bg-slate-50 dark:bg-slate-950 text-slate-400">
        <div className="text-center font-sans">
          <EyeIcon className="w-12 h-12 mx-auto mb-4 opacity-20" />
          <p>Select a signal from the Victory Feed to start creating.</p>
        </div>
      </div>
    );
  }

  const previewUrl = getPreviewImage();

  return (
    <div className="h-full flex flex-col bg-white dark:bg-slate-900 font-sans relative overflow-hidden">
      {/* Header */}
      <WorkbenchHeader
        activeSource={activeSource}
        title={title}
        content={content}
        onSave={handleSave}
        onPublish={onPublish}
      />

      {/* Visual Feedback Banner (Charlie's Instructions) */}
      <CharlieFeedbackBanner
        feedback={feedback}
        aiScore={aiScore}
        activeSource={activeSource}
      />

      {/* Main Layout Area: Split View */}
      <div className="flex-1 flex overflow-hidden relative">
        
        {/* Left Pane: Source Context (Collapsible) */}
        <SourceContextPane
          isContextOpen={isContextOpen}
          isLoadingContext={isLoadingContext}
          contextData={contextData}
          onToggleContext={() => setIsContextOpen(!isContextOpen)}
        />

        {/* Right Pane: Editor战場 */}
        <div className="flex-1 flex flex-col relative bg-white dark:bg-slate-900 overflow-y-auto custom-scrollbar">
          
          <EditorBody
            activeSource={activeSource}
            previewUrl={previewUrl}
            isGeneratingImage={isGeneratingImage}
            title={title}
            content={content}
            onGenerateImage={onGenerateImage}
            onTitleChange={onTitleChange}
            onContentChange={onContentChange}
          />

          {/* Floating Action Buttons */}
          <div className="fixed bottom-8 right-8 flex flex-col gap-4 z-50">
            {/* Pro Editor Access */}
            <button 
              onClick={() => navigate(`/brand/editor/${activeSource.id}`)}
              className="w-16 h-16 bg-white dark:bg-slate-800 border-2 border-indigo-100 dark:border-slate-700 hover:border-indigo-500 text-indigo-600 rounded-2xl shadow-xl flex items-center justify-center transition-all hover:scale-110 active:scale-95 group"
              title="Open Pro Editor"
            >
              <FileEditIcon className="w-7 h-7 group-hover:rotate-12 transition-transform" />
            </button>
            
            {/* AI Command Center Trigger */}
            <button 
              onClick={() => setPromptCenterOpen(true)}
              className="w-16 h-16 bg-indigo-600 hover:bg-indigo-700 text-white rounded-2xl shadow-2xl flex items-center justify-center transition-all hover:scale-110 active:scale-95 group relative"
            >
              <SparklesIcon className="w-8 h-8 group-hover:rotate-12 transition-transform" />
              <div className="absolute -top-2 -right-2 w-5 h-5 bg-red-500 rounded-full border-2 border-white flex items-center justify-center text-[10px] font-black">!</div>
            </button>
          </div>

          {/* UNIFIED PROMPT CENTER (Drawer/Overlay) */}
          <AICommandCenter
            promptCenterOpen={promptCenterOpen}
            setPromptCenterOpen={setPromptCenterOpen}
            promptTab={promptTab}
            setPromptTab={setPromptTab}
            config={config}
            setConfig={setConfig}
            toggleItem={toggleItem}
            usedPrompt={usedPrompt}
            getTempPromptPreview={getTempPromptPreview}
            handleDraftExecute={handleDraftExecute}
            isDrafting={isDrafting}
          />
        </div>
      </div>
    </div>
  );
};
