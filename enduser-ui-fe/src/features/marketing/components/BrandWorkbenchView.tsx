import React from 'react';
import { ContentSource } from './VictoryFeedList';
import { ContentWorkbench } from './ContentWorkbench';
import { 
    LayoutIcon, XIcon, RefreshCwIcon
} from '../../../components/Icons';

interface BrandWorkbenchViewProps {
    sources: ContentSource[];
    activeSource: ContentSource | null;
    contextData: any;
    isLoadingSources: boolean;
    isLoadingContext: boolean;
    isDrafting: boolean;
    isSidebarOpen: boolean;
    setIsSidebarOpen: (val: boolean) => void;
    workbenchTitle: string;
    setWorkbenchTitle: (val: string) => void;
    workbenchContent: string;
    setWorkbenchContent: (val: string) => void;
    handleSelectSource: (source: ContentSource) => void;
    handleMagicDraft: (topic: string, config?: any) => void;
    handleSaveWorkbench: () => void;
    handlePublishWorkbench: (data: { title: string, content: string }) => void;
    handleGenerateImage: (style: string) => void;
    isGeneratingLogo: boolean;
}

export const BrandWorkbenchView: React.FC<BrandWorkbenchViewProps> = ({
    sources, activeSource, contextData, 
    isLoadingSources, isLoadingContext, isDrafting,
    isSidebarOpen, setIsSidebarOpen,
    workbenchTitle, setWorkbenchTitle, workbenchContent, setWorkbenchContent,
    handleSelectSource, handleMagicDraft, handleSaveWorkbench, handlePublishWorkbench,
    handleGenerateImage, isGeneratingLogo
}) => {
    return (
        <div className="flex h-full relative font-sans">
            {/* Workbench Side Nav */}
            <aside className={`${isSidebarOpen ? 'w-80' : 'w-0'} bg-white border-r transition-all duration-300 flex flex-col shrink-0 relative overflow-hidden`}>
                <div className="p-6 border-b shrink-0 flex justify-between items-center bg-slate-50/50">
                    <h2 className="font-bold text-slate-800 flex items-center gap-2">
                        <LayoutIcon className="w-4 h-4 text-indigo-600" />
                        Sources
                    </h2>
                    {isLoadingSources && <RefreshCwIcon className="w-4 h-4 animate-spin text-indigo-400" />}
                </div>
                <div className="flex-1 overflow-y-auto p-4 space-y-2">
                    {sources.map(source => (
                        <div 
                            key={`${source.type}-${source.id}`}
                            onClick={() => handleSelectSource(source)}
                            className={`p-4 rounded-xl border cursor-pointer transition-all ${
                                activeSource?.id === source.id ? 'bg-indigo-50 border-indigo-200 shadow-sm ring-1 ring-indigo-100' : 'bg-white border-slate-100 hover:border-indigo-100'
                            }`}
                        >
                            <div className="flex justify-between items-start mb-1">
                                <span className={`text-[9px] font-black px-1.5 py-0.5 rounded uppercase tracking-tighter ${
                                    source.type === 'lead' ? 'bg-emerald-100 text-emerald-700' : 
                                    source.type === 'blog' ? 'bg-blue-100 text-blue-700' : 'bg-amber-100 text-amber-700'
                                }`}>
                                    {source.type}
                                </span>
                                {source.score && <span className="text-[9px] font-bold text-indigo-600">AI {source.score}%</span>}
                            </div>
                            <h4 className="font-bold text-slate-800 text-sm line-clamp-1">{source.title}</h4>
                            <p className="text-[10px] text-slate-400 mt-1 line-clamp-2 leading-relaxed">{source.summary}</p>
                        </div>
                    ))}
                </div>
            </aside>

            {/* Main Workbench Area */}
            <section className="flex-1 flex flex-col bg-white overflow-hidden">
                <ContentWorkbench 
                    activeSource={activeSource}
                    contextData={contextData}
                    isDrafting={isDrafting}
                    isLoadingContext={isLoadingContext}
                    onDraft={handleMagicDraft}
                    onGenerateImage={handleGenerateImage}
                    onSave={handleSaveWorkbench}
                    onPublish={handlePublishWorkbench}
                    title={workbenchTitle}
                    content={workbenchContent}
                    onTitleChange={setWorkbenchTitle}
                    onContentChange={setWorkbenchContent}
                    isGeneratingImage={isGeneratingLogo}
                />
            </section>

            {/* Sidebar Toggle */}
            <button 
                onClick={() => setIsSidebarOpen(!isSidebarOpen)}
                className="absolute left-0 bottom-10 z-30 bg-indigo-600 text-white p-2 rounded-r-lg shadow-lg hover:bg-indigo-700 transition-all transform hover:scale-110 active:scale-95"
            >
                {isSidebarOpen ? <XIcon className="w-4 h-4" /> : <LayoutIcon className="w-4 h-4" />}
            </button>
        </div>
    );
};
