import React from 'react';
import ReactMarkdown from 'react-markdown';
import { motion, AnimatePresence } from 'framer-motion';
import { FileTextIcon, XIcon } from '../../../../components/Icons';

export interface NexusSpecPanelProps {
    isOpen: boolean;
    onClose: () => void;
    specContent?: string;
}

export const NexusSpecPanel: React.FC<NexusSpecPanelProps> = ({ isOpen, onClose, specContent }) => {
    return (
        <AnimatePresence>
            {isOpen && (
                <>
                    {/* Backdrop */}
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        onClick={onClose}
                        className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-[70]"
                    />
                    {/* Panel */}
                    <motion.aside
                        initial={{ x: '100%' }}
                        animate={{ x: 0 }}
                        exit={{ x: '100%' }}
                        transition={{ type: 'spring', damping: 25, stiffness: 200 }}
                        className="fixed inset-y-0 right-0 w-full max-w-xl bg-white dark:bg-slate-900 shadow-2xl z-[80] overflow-hidden flex flex-col"
                    >
                        <div className="p-6 border-b border-gray-100 dark:border-slate-800 flex justify-between items-center bg-amber-50/30 dark:bg-amber-900/10">
                            <div className="flex items-center gap-3">
                                <div className="p-2 bg-amber-500 rounded-lg text-white">
                                    <FileTextIcon className="w-5 h-5" />
                                </div>
                                <h2 className="text-lg font-black text-gray-900 dark:text-white uppercase tracking-tight">Nexus Metrics Spec</h2>
                            </div>
                            <button onClick={onClose} className="p-2 hover:bg-gray-200/50 dark:hover:bg-slate-800 rounded-full transition-colors text-gray-400" aria-label="Close Nexus Metrics Spec">
                                <XIcon className="w-6 h-6" />
                            </button>
                        </div>
                        <div className="flex-1 overflow-y-auto p-8 prose prose-slate dark:prose-invert max-w-none prose-headings:font-black prose-h1:text-2xl prose-h2:text-xl prose-h3:text-lg">
                            <ReactMarkdown>{specContent}</ReactMarkdown>
                        </div>
                        <div className="p-6 border-t border-gray-100 dark:border-slate-800 bg-gray-50/50 dark:bg-slate-950/50 flex justify-end">
                            <button
                                onClick={onClose}
                                className="px-6 py-2 bg-gray-900 dark:bg-white text-white dark:text-gray-900 rounded-xl font-bold text-sm hover:scale-105 transition-transform"
                            >
                                Close Spec
                            </button>
                        </div>
                    </motion.aside>
                </>
            )}
        </AnimatePresence>
    );
};
