import React from 'react';
import { X } from 'lucide-react';
import { Button } from '../../ui/primitives';

interface KnowledgePreviewModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  url: string;
}

export const KnowledgePreviewModal: React.FC<KnowledgePreviewModalProps> = ({
  isOpen,
  onClose,
  title,
  url
}) => {
  if (!isOpen) return null;

  const isPdf = url.toLowerCase().endsWith('.pdf');
  // Support common office formats via Google Viewer
  const isOffice = /\.(docx|doc|pptx|ppt|xlsx|xls)$/i.test(url);

  return (
    <div className="fixed inset-0 z-[100] flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
      <div 
        className="bg-white dark:bg-gray-900 w-full max-w-5xl h-[90vh] rounded-xl shadow-2xl flex flex-col overflow-hidden border border-white/10"
        role="dialog"
        aria-modal="true"
        aria-label={`Preview: ${title}`}
      >
        {/* Header */}
        <div className="px-6 py-4 border-b border-gray-200 dark:border-gray-800 flex justify-between items-center bg-gray-50/50 dark:bg-gray-800/50">
          <h3 className="text-lg font-bold text-gray-900 dark:text-white truncate pr-4">
            {title}
          </h3>
          <Button variant="ghost" size="sm" onClick={onClose} className="rounded-full hover:bg-red-500/10 hover:text-red-500">
            <X className="w-5 h-5" />
          </Button>
        </div>

        {/* Content */}
        <div className="flex-1 bg-gray-100 dark:bg-black/20 p-0 relative">
          {isPdf ? (
            <iframe
              src={`${url}#toolbar=0`}
              className="w-full h-full bg-white"
              title={title}
            />
          ) : isOffice ? (
            <iframe
              src={`https://docs.google.com/gview?url=${encodeURIComponent(url)}&embedded=true`}
              className="w-full h-full bg-white"
              title={title}
            />
          ) : (
            <div className="flex flex-col items-center justify-center h-full text-gray-500 p-8">
              <p className="mb-4 text-center text-lg">Preview not available for this format.</p>
              <a 
                href={url} 
                target="_blank" 
                rel="noopener noreferrer"
                download
                className="px-6 py-3 bg-cyan-500 text-white rounded-md hover:bg-cyan-600 transition-colors font-medium"
              >
                Download to View
              </a>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-6 py-3 border-t border-gray-200 dark:border-gray-800 flex justify-end gap-3 bg-gray-50/50 dark:bg-gray-800/50">
          <Button variant="outline" onClick={onClose}>
            Close
          </Button>
          <a 
            href={url} 
            download
            className="inline-flex items-center justify-center px-4 py-2 bg-cyan-500 hover:bg-cyan-600 text-white rounded-md text-sm font-medium transition-colors"
          >
            Download Original
          </a>
        </div>
      </div>
    </div>
  );
};
