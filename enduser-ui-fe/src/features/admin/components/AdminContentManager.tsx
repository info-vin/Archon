import React from 'react';
import { useNavigate } from 'react-router-dom';
import { PlusIcon } from '../../../components/Icons';
import { useBlogPosts } from '../hooks/useAdminDashboard';

export const AdminContentManager: React.FC = () => {
    const { posts, deletePost } = useBlogPosts();
    const navigate = useNavigate();

    return (
        <div className="bg-card p-6 rounded-2xl border border-border shadow-sm font-sans">
            <div className="flex justify-between items-center mb-6">
                <h2 className="text-xl font-bold text-gray-800 dark:text-white">Content Assets</h2>
                <button onClick={() => navigate('/admin/editor/new')} className="flex items-center px-4 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 font-bold transition-all shadow-sm">
                    <PlusIcon className="w-5 h-5 mr-2" />
                    NEW POST
                </button>
            </div>
             <div className="overflow-x-auto -mx-6">
                <table className="min-w-full divide-y divide-border">
                    <thead className="bg-muted/50">
                        <tr>
                            <th className="px-6 py-3 text-left text-xs font-bold uppercase tracking-wider text-muted-foreground">Title</th>
                            <th className="px-6 py-3 text-left text-xs font-bold uppercase tracking-wider text-muted-foreground">Author</th>
                            <th className="px-6 py-3 text-left text-xs font-bold uppercase tracking-wider text-muted-foreground">Status</th>
                            <th className="px-6 py-3 text-left text-xs font-bold uppercase tracking-wider text-muted-foreground">Date</th>
                            <th className="px-6 py-3 text-left text-xs font-bold uppercase tracking-wider text-muted-foreground text-right">Actions</th>
                        </tr>
                    </thead>
                    <tbody className="divide-y divide-border bg-card text-sm">
                        {posts.map(post => (
                            <tr key={post.id} className="hover:bg-muted/30 transition-colors cursor-pointer" onClick={() => navigate(`/admin/editor/${post.id}`)}>
                                <td className="px-6 py-4 whitespace-nowrap font-bold text-gray-900 dark:text-white">{post.title}</td>
                                <td className="px-6 py-4 whitespace-nowrap">{post.authorName}</td>
                                <td className="px-6 py-4 whitespace-nowrap">
                                    <span className={`px-2 py-0.5 text-[10px] font-bold uppercase rounded border ${post.status === 'published' ? 'bg-green-50 text-green-700 border-green-200' : 'bg-amber-50 text-amber-700 border-amber-200'}`}>{post.status}</span>
                                </td>
                                <td className="px-6 py-4 whitespace-nowrap text-xs text-muted-foreground">{new Date(post.publishDate).toLocaleDateString()}</td>
                                <td className="px-6 py-4 whitespace-nowrap text-right font-medium">
                                    <button onClick={(e) => { e.stopPropagation(); navigate(`/admin/editor/${post.id}`); }} className="text-indigo-600 hover:text-indigo-800 font-bold transition-colors">Edit</button>
                                    <button onClick={(e) => { e.stopPropagation(); deletePost(post.id); }} className="text-red-600 hover:text-red-800 font-bold ml-4 transition-colors">Delete</button>
                                </td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    );
};
