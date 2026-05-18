import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { api } from '../services/api';
import { BlogPost } from '../types';
import DiffViewer from '../components/DiffViewer';
import { SmartImagePicker } from '../features/marketing/components/SmartImagePicker';
// Icons
import { ArrowLeftIcon, SaveIcon, ImageIcon, CheckIcon, Wand2Icon, AlertTriangleIcon } from 'lucide-react';

const BlogEditor: React.FC = () => {
    const { id } = useParams<{ id: string }>();
    const navigate = useNavigate();
    const isNew = !id || id === 'new';
    
    const [post, setPost] = useState<Partial<BlogPost>>({
        title: '',
        excerpt: '',
        content: '',
        imageUrl: ''
    });
    const [loading, setLoading] = useState(!isNew);
    const [saving, setSaving] = useState(false);
    const [showImagePicker, setShowImagePicker] = useState<'cover' | 'markdown' | null>(null);

    // AI Context / Diff View
    const [showDiff, setShowDiff] = useState(false);
    const [suggestedContent, setSuggestedContent] = useState('');
    
    useEffect(() => {
        if (!isNew && id) {
            fetchPost(id);
        }
    }, [id, isNew]);

    const fetchPost = async (postId: string) => {
        try {
            const data = await api.getBlogPost(postId);
            setPost(data);
        } catch (e: any) {
            alert('Failed to load post: ' + e.message);
            navigate('/admin');
        } finally {
            setLoading(false);
        }
    };

    const handleSave = async () => {
        setSaving(true);
        try {
            if (isNew) {
                const newPost = await api.createBlogPost(post as any);
                alert('Post created!');
                navigate(`/admin/editor/${newPost.id}`);
            } else {
                await api.updateBlogPost(id!, post);
                alert('Post saved!');
            }
        } catch (e: any) {
            alert('Failed to save post: ' + e.message);
        } finally {
            setSaving(false);
        }
    };

    const handleImagePicked = (url: string) => {
        if (showImagePicker === 'cover') {
            setPost({ ...post, imageUrl: url });
        } else if (showImagePicker === 'markdown') {
            const imgName = url.split('/').pop() || 'image';
            const imgMarkdown = `\n![${imgName}](${url})\n`;
            setPost(prev => ({ ...prev, content: (prev.content || '') + imgMarkdown }));
        }
        setShowImagePicker(null);
    };

    if (loading) return <div className="p-8 text-center text-gray-500 animate-pulse">Loading Editor...</div>;

    return (
        <div className="max-w-6xl mx-auto p-4 md:p-8 font-sans font-inter relative">
            {showImagePicker && (
                <SmartImagePicker 
                    onSelect={handleImagePicked}
                    onClose={() => setShowImagePicker(null)}
                />
            )}
            
            {/* Header */}
            <header className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8 pb-4 border-b border-gray-200">
                <div className="flex items-center gap-4 border-b border-transparent">
                    <button 
                        onClick={() => navigate('/admin')}
                        className="p-2 hover:bg-gray-100 rounded-full transition-colors text-gray-500 hover:text-gray-900"
                        aria-label="Back to Admin"
                    >
                        <ArrowLeftIcon className="w-6 h-6" />
                    </button>
                    <div>
                        <h1 className="text-3xl font-bold text-gray-900 dark:text-white flex items-center gap-3">
                            {isNew ? 'Create New Post' : 'Edit Post'}
                        </h1>
                        <p className="text-sm text-gray-500 font-medium">
                            {isNew ? 'Draft mode' : `ID: ${id}`}
                        </p>
                    </div>
                </div>
                <div className="flex items-center gap-3">
                    {post.review_notes && (
                        <div className="hidden md:flex items-center gap-2 px-3 py-1.5 bg-amber-50 text-amber-600 rounded-lg text-xs font-bold mr-4">
                            <AlertTriangleIcon className="w-4 h-4" />
                            AI Review Notes Pending
                        </div>
                    )}
                    <button
                        onClick={() => setShowDiff(!showDiff)}
                        className={`flex items-center justify-center gap-2 px-4 py-2 rounded-xl text-sm font-bold transition-colors ${
                            showDiff ? 'bg-indigo-600 text-white shadow-md' : 'bg-indigo-50 text-indigo-600 hover:bg-indigo-100'
                        }`}
                    >
                        <Wand2Icon className="w-4 h-4" />
                        {showDiff ? 'Hide Diff Viewer' : 'AI Review / Diff Viewer'}
                    </button>
                    <button 
                        onClick={handleSave}
                        disabled={saving}
                        className="flex items-center justify-center gap-2 px-6 py-2 bg-gray-900 hover:bg-gray-800 text-white rounded-xl text-sm font-bold transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-md shadow-gray-200"
                    >
                        <SaveIcon className="w-4 h-4" />
                        {saving ? 'Saving...' : 'Save Post'}
                    </button>
                </div>
            </header>

            <div className={`grid gap-8 ${showDiff ? 'grid-cols-1 lg:grid-cols-2' : 'grid-cols-1 max-w-4xl mx-auto'}`}>
                {/* Editor Column */}
                <div className="space-y-6">
                    <div>
                        <label className="block text-xs font-black uppercase tracking-widest text-gray-500 mb-2">Post Title</label>
                        <input 
                            type="text" 
                            value={post.title}
                            onChange={(e) => setPost({...post, title: e.target.value})}
                            className="w-full text-2xl font-bold bg-white border border-gray-200 rounded-2xl px-4 py-3 focus:outline-none focus:ring-4 focus:ring-indigo-500/10 focus:border-indigo-500 transition-all placeholder:text-gray-300"
                            placeholder="A Captivating Title..."
                        />
                    </div>

                    <div>
                         <label className="block text-xs font-black uppercase tracking-widest text-gray-500 mb-2">Excerpt</label>
                         <textarea 
                            value={post.excerpt}
                            onChange={(e) => setPost({...post, excerpt: e.target.value})}
                            className="w-full text-sm bg-white border border-gray-200 rounded-xl px-4 py-3 focus:outline-none focus:ring-4 focus:ring-indigo-500/10 focus:border-indigo-500 transition-all placeholder:text-gray-300 resize-none h-24"
                            placeholder="Brief summary for cards and SEO..."
                        />
                    </div>

                    <div>
                        <div className="flex items-center justify-between mb-2">
                            <label className="text-xs font-black uppercase tracking-widest text-gray-500">Cover Image</label>
                            <div className="flex gap-2">
                                <button 
                                    onClick={() => setShowImagePicker('cover')}
                                    data-testid="smart-asset-search-btn"
                                    className="cursor-pointer flex items-center gap-1.5 text-xs font-bold text-indigo-600 hover:text-indigo-700 transition-colors"
                                >
                                    <ImageIcon className="w-4 h-4" /> Smart Asset Search
                                </button>
                            </div>
                        </div>
                        {post.imageUrl ? (
                            <div className="relative group rounded-2xl overflow-hidden border border-gray-200 bg-gray-50 aspect-video flex items-center justify-center">
                                <img src={post.imageUrl} alt="Cover" data-testid="cover-image" className="w-full h-full object-cover" />
                                <div className="absolute inset-0 bg-black/50 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                                     <button 
                                        onClick={() => setShowImagePicker('cover')}
                                        className="cursor-pointer flex items-center gap-2 px-4 py-2 bg-white rounded-lg text-sm font-bold text-gray-900 shadow-xl hover:scale-105 transition-transform"
                                     >
                                         <ImageIcon className="w-4 h-4" />
                                         Change Cover
                                     </button>
                                </div>
                            </div>
                        ) : (
                            <div className="rounded-2xl border-2 border-dashed border-gray-200 bg-gray-50 aspect-video flex flex-col items-center justify-center text-gray-400">
                                <ImageIcon className="w-12 h-12 mb-2 opacity-50" />
                                <p className="text-sm font-medium">No cover image selected</p>
                            </div>
                        )}
                    </div>

                    <div className="flex-1 min-w-0 flex flex-col">
                        <div className="flex items-center justify-between mb-2">
                            <label className="text-xs font-black uppercase tracking-widest text-gray-500">Main Content (Markdown)</label>
                            <button 
                                onClick={() => setShowImagePicker('markdown')}
                                className="cursor-pointer flex items-center gap-1.5 text-xs font-bold text-indigo-600 hover:text-indigo-700 transition-colors bg-indigo-50 px-3 py-1.5 rounded-lg"
                            >
                                 <ImageIcon className="w-4 h-4" /> Smart Insert
                            </button>
                        </div>
                        <textarea 
                            value={showDiff && suggestedContent ? suggestedContent : post.content}
                            onChange={(e) => {
                                if (showDiff && suggestedContent) {
                                    setSuggestedContent(e.target.value);
                                } else {
                                    setPost({...post, content: e.target.value});
                                }
                            }}
                            className="w-full flex-1 min-w-0 min-h-[500px] text-sm font-mono bg-white border border-gray-200 rounded-2xl px-4 py-4 focus:outline-none focus:ring-4 focus:ring-indigo-500/10 focus:border-indigo-500 transition-all placeholder:text-gray-300 shadow-inner block"
                            placeholder="# Write your magnificent content here...\n\nMarkdown is fully supported!"
                        />
                    </div>
                </div>

                {/* Diff Viewer Column */}
                {showDiff && (
                    <div className="h-full flex flex-col min-w-0 animate-in slide-in-from-right-8 opacity-0 fade-in duration-500 fill-mode-forwards max-w-full">
                         <div className="flex justify-between items-end mb-2">
                             <div>
                                <h3 className="text-lg font-black text-gray-900 tracking-tight flex items-center gap-2">
                                     <Wand2Icon className="w-5 h-5 text-indigo-600" />
                                     AI Content Analysis
                                </h3>
                                <p className="text-xs font-bold text-gray-500 uppercase tracking-widest mt-1">Reviewing changes side-by-side</p>
                             </div>
                             
                             <button
                                onClick={() => {
                                    if (suggestedContent) {
                                        setPost({...post, content: suggestedContent});
                                        setSuggestedContent('');
                                        setShowDiff(false);
                                        alert("AI Suggestions Accepted!");
                                    } else {
                                        // Mock generating AI suggestions
                                        setSuggestedContent((post.content || '') + "\n\n> *AI Added Paragraph for SEO value and depth.*");
                                    }
                                }}
                                className="flex items-center gap-2 px-4 py-2 bg-green-50 hover:bg-green-100 text-green-700 rounded-xl text-xs font-black uppercase tracking-widest transition-colors border border-green-200"
                             >
                                 <CheckIcon className="w-4 h-4" />
                                 {suggestedContent ? 'Accept Suggestions' : 'Auto-Suggest'}
                             </button>
                         </div>

                         {post.review_notes && (
                             <div className="mb-4 p-4 bg-amber-50 rounded-xl border border-amber-200 text-sm font-medium text-amber-900 shadow-sm break-words whitespace-pre-wrap">
                                 <strong className="text-amber-700 block mb-1">Editor AI Notes:</strong>
                                 {post.review_notes}
                             </div>
                         )}

                         <div className="flex-1 min-w-0 bg-white border border-gray-200 rounded-2xl overflow-hidden shadow-sm flex flex-col min-h-[500px]">
                            <DiffViewer 
                                oldCode={post.content || ''} 
                                newCode={suggestedContent || post.content || ''} 
                                splitView={false}
                            />
                         </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default BlogEditor;
