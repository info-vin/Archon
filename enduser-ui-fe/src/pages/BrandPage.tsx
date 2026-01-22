import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { BlogPost } from '../types';
import { useAuth } from '../hooks/useAuth';
import { PermissionGuard } from '../features/auth/components/PermissionGuard';
import { 
    PlusIcon, 
    PaletteIcon, 
    LayoutIcon, 
    TrendingUpIcon, 
    DownloadIcon,
    RefreshCwIcon,
    CheckCircleIcon,
    FileEditIcon,
    EyeIcon
} from '../components/Icons';

const BrandPage: React.FC = () => {
    const { user } = useAuth();
    const [posts, setPosts] = useState<BlogPost[]>([]);
    const [marketStats, setMarketStats] = useState<any>(null);
    const [logoSvg, setLogoSvg] = useState<string | null>(null);
    const [isGenerating, setIsLogoGenerating] = useState(false);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        loadData();
    }, []);

    const loadData = async () => {
        setLoading(true);
        try {
            const [postsData, stats] = await Promise.all([
                api.getBlogPosts(),
                api.getMarketStats()
            ]);
            setPosts(postsData);
            setMarketStats(stats);
        } catch (err) {
            console.error("Failed to load brand data:", err);
        } finally {
            setLoading(false);
        }
    };

    const handleGenerateLogo = async () => {
        setIsLogoGenerating(true);
        try {
            const result = await api.generateLogo("eciton");
            setLogoSvg(result.svg_content);
        } catch (err) {
            alert("Failed to generate logo");
        } finally {
            setIsLogoGenerating(false);
        }
    };

    const updatePostStatus = async (id: string, newStatus: any) => {
        try {
            await api.updateBlogPostStatus(id, newStatus);
            setPosts(prev => prev.map(p => p.id === id ? { ...p, status: newStatus } : p));
        } catch (err) {
            alert("Status update failed");
        }
    };

    const downloadLogo = () => {
        if (!logoSvg) return;
        const blob = new Blob([logoSvg], { type: 'image/svg+xml' });
        const url = URL.createObjectURL(blob);
        const link = document.createElement('a');
        link.href = url;
        link.download = 'logo-eciton.svg';
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
    };

    const KanbanColumn = ({ status, title, icon: Icon, colorClass }: any) => (
        <div className="flex-1 min-w-[300px] bg-gray-50/50 rounded-xl p-4 flex flex-col gap-4">
            <div className={`flex items-center justify-between border-b pb-2 ${colorClass}`}>
                <h3 className="font-bold flex items-center gap-2">
                    <Icon className="w-5 h-5" />
                    {title}
                </h3>
                <span className="bg-white px-2 py-0.5 rounded-full text-xs shadow-sm font-bold">
                    {posts.filter(p => p.status === status).length}
                </span>
            </div>
            <div className="space-y-3 overflow-y-auto max-h-[500px] pr-1">
                {posts.filter(p => p.status === status).map(post => (
                    <div key={post.id} className="bg-white p-4 rounded-lg shadow-sm border border-gray-100 hover:shadow-md transition-all group">
                        <h4 className="font-semibold text-gray-800 line-clamp-2">{post.title}</h4>
                        <p className="text-xs text-gray-500 mt-2 italic">By {post.authorName}</p>
                        <div className="mt-4 flex justify-between items-center opacity-0 group-hover:opacity-100 transition-opacity">
                            <div className="flex gap-1">
                                {status !== 'draft' && (
                                    <button onClick={() => updatePostStatus(post.id, 'draft')} className="p-1 hover:bg-gray-100 rounded text-gray-400" title="Move to Draft">
                                        <FileEditIcon className="w-4 h-4" />
                                    </button>
                                )}
                                {status !== 'review' && (
                                    <button onClick={() => updatePostStatus(post.id, 'review')} className="p-1 hover:bg-amber-50 rounded text-amber-500" title="Move to Review">
                                        <EyeIcon className="w-4 h-4" />
                                    </button>
                                )}
                                {status !== 'published' && (
                                    <button onClick={() => updatePostStatus(post.id, 'published')} className="p-1 hover:bg-green-50 rounded text-green-600" title="Publish Now">
                                        <CheckCircleIcon className="w-4 h-4" />
                                    </button>
                                )}
                            </div>
                            <span className="text-[10px] uppercase font-bold text-gray-300">#{post.id.slice(0,4)}</span>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );

    return (
        <PermissionGuard permission="leads:view:all" userRole={user?.role} fallback={<div className="p-12 text-center text-gray-500">Access Denied: Brand Hub is for Marketing roles only.</div>}>
            <div className="p-6 max-w-7xl mx-auto space-y-8">
                <header className="flex justify-between items-start">
                    <div>
                        <h1 className="text-3xl font-bold text-gray-800 flex items-center gap-3">
                            <PaletteIcon className="w-8 h-8 text-indigo-600" />
                            Brand Hub
                        </h1>
                        <p className="text-gray-500 mt-2">Manage brand identity, content planning, and market trends.</p>
                    </div>
                    <button onClick={loadData} className="p-2 hover:bg-gray-100 rounded-full transition-colors" title="Refresh data">
                        <RefreshCwIcon className={`w-5 h-5 ${loading ? 'animate-spin' : ''}`} />
                    </button>
                </header>

                <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    {/* Brand Identity Section */}
                    <div className="lg:col-span-2 bg-white p-6 rounded-2xl shadow-sm border border-gray-100 space-y-6">
                        <div className="flex justify-between items-center">
                            <h2 className="text-xl font-bold text-gray-800 flex items-center gap-2">
                                <LayoutIcon className="w-5 h-5 text-indigo-500" />
                                Visual Identity
                            </h2>
                            <button 
                                onClick={handleGenerateLogo}
                                disabled={isGenerating}
                                className="bg-indigo-600 text-white px-4 py-2 rounded-lg text-sm font-bold hover:bg-indigo-700 disabled:opacity-50 transition-all flex items-center gap-2 shadow-lg shadow-indigo-200"
                            >
                                {isGenerating ? <RefreshCwIcon className="w-4 h-4 animate-spin" /> : <RefreshCwIcon className="w-4 h-4" />}
                                Generate with DevBot
                            </button>
                        </div>

                        <div className="h-64 bg-slate-900 rounded-xl flex items-center justify-center relative overflow-hidden group border-4 border-slate-800">
                            {logoSvg ? (
                                <div className="w-48 h-48 drop-shadow-[0_0_15px_rgba(0,242,255,0.5)]" dangerouslySetInnerHTML={{ __html: logoSvg }} />
                            ) : (
                                <div className="text-slate-500 flex flex-col items-center gap-2">
                                    <PaletteIcon className="w-12 h-12 opacity-20" />
                                    <p className="text-sm">Click generate to preview living brand assets</p>
                                </div>
                            )}
                            
                            {logoSvg && (
                                <button 
                                    onClick={downloadLogo}
                                    className="absolute bottom-4 right-4 bg-white/10 backdrop-blur-md text-white p-2 rounded-lg hover:bg-white/20 transition-all opacity-0 group-hover:opacity-100"
                                    title="Download SVG"
                                >
                                    <DownloadIcon className="w-5 h-5" />
                                </button>
                            )}
                        </div>
                        <p className="text-xs text-gray-400 italic text-center">
                            Powered by **Project ECITON** Engine. Dynamic SVG generation based on collective intelligence math.
                        </p>
                    </div>

                    {/* Market Insight Section */}
                    <div className="bg-indigo-900 text-white p-6 rounded-2xl shadow-xl space-y-6 relative overflow-hidden">
                        <div className="relative z-10">
                            <h2 className="text-xl font-bold flex items-center gap-2">
                                <TrendingUpIcon className="w-5 h-5 text-indigo-300" />
                                Market Specs
                            </h2>
                            <p className="text-indigo-200 text-xs mt-1">AI-driven market trend analysis</p>
                            
                            {marketStats ? (
                                <div className="mt-8 space-y-6">
                                    <div className="grid grid-cols-2 gap-4">
                                        <div className="bg-white/10 p-4 rounded-xl border border-white/5">
                                            <p className="text-[10px] uppercase font-bold text-indigo-300">AI Trends</p>
                                            <p className="text-2xl font-mono font-bold mt-1">{Math.round((marketStats["AI/LLM"] / marketStats["Total Leads"]) * 100)}%</p>
                                        </div>
                                        <div className="bg-white/10 p-4 rounded-xl border border-white/5">
                                            <p className="text-[10px] uppercase font-bold text-indigo-300">Growth</p>
                                            <p className="text-2xl font-mono font-bold mt-1">+{marketStats["Total Leads"]}</p>
                                        </div>
                                    </div>
                                    
                                    <div className="space-y-4">
                                        <div className="bg-white/5 p-3 rounded-lg flex justify-between items-center">
                                            <span className="text-sm">LLM/Agent Frame</span>
                                            <span className="text-indigo-400 font-mono font-bold">{marketStats["AI/LLM"]}</span>
                                        </div>
                                        <div className="bg-white/5 p-3 rounded-lg flex justify-between items-center">
                                            <span className="text-sm">Data Analytics</span>
                                            <span className="text-indigo-400 font-mono font-bold">{marketStats["Data/BI"]}</span>
                                        </div>
                                    </div>
                                </div>
                            ) : (
                                <div className="animate-pulse space-y-4 mt-8">
                                    <div className="h-20 bg-white/5 rounded-xl"></div>
                                    <div className="h-32 bg-white/5 rounded-xl"></div>
                                </div>
                            )}
                        </div>
                        {/* Decorative circle */}
                        <div className="absolute -bottom-12 -right-12 w-48 h-48 bg-indigo-500 rounded-full blur-3xl opacity-20"></div>
                    </div>
                </div>

                {/* Blog Content Kanban */}
                <section className="space-y-4">
                    <div className="flex justify-between items-end">
                        <h2 className="text-xl font-bold text-gray-800 flex items-center gap-2">
                            <PlusIcon className="w-5 h-5 text-indigo-500" />
                            Content Pipeline
                        </h2>
                        <span className="text-xs text-gray-400">Drag-and-drop support coming soon</span>
                    </div>
                    
                    <div className="flex flex-col md:flex-row gap-6 overflow-x-auto pb-4">
                        <KanbanColumn status="draft" title="Ideas & Drafts" icon={FileEditIcon} colorClass="text-gray-600 border-gray-200" />
                        <KanbanColumn status="review" title="In Review" icon={EyeIcon} colorClass="text-amber-600 border-amber-200" />
                        <KanbanColumn status="published" title="Published" icon={CheckCircleIcon} colorClass="text-green-600 border-green-200" />
                    </div>
                </section>
            </div>
        </PermissionGuard>
    );
};

export default BrandPage;
