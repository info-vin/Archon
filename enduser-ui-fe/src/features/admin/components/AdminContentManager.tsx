import React from 'react';
import { useNavigate } from 'react-router-dom';
import { PlusIcon, TrashIcon } from '../../../components/Icons';
import { useBlogPosts } from '../hooks/useAdminDashboard';

export const AdminContentManager: React.FC = () => {
    const { posts, deletePost, loading } = useBlogPosts();
    const navigate = useNavigate();

    if (loading) return <div className="p-12 text-center">Loading posts...</div>;

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
                        {posts.length > 0 ? posts.map((post) => (
                            <tr key={post.id}>
                                <td className="px-6 py-4 font-bold">{post.title}</td>
                                <td className="px-6 py-4">{post.authorName || 'Admin'}</td>
                                <td className="px-6 py-4 capitalize">{post.status}</td>
                                <td className="px-6 py-4">{new Date(post.publishDate).toLocaleDateString()}</td>
                                <td className="px-6 py-4 text-right">
                                    <button
                                        onClick={() => deletePost(post.id)}
                                        className="p-1.5 text-red-500 hover:bg-red-50 rounded-md transition-colors focus-visible:ring-2 focus-visible:ring-red-500 outline-none"
                                        aria-label="Delete post"
                                        title="Delete post"
                                    >
                                        <TrashIcon className="w-4 h-4" />
                                    </button>
                                </td>
                            </tr>
                        )) : (
                            <tr>
                                <td colSpan={5} className="px-6 py-12 text-center text-muted-foreground italic">No blog posts found. Start by creating a new post.</td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>
        </div>
    );
};
