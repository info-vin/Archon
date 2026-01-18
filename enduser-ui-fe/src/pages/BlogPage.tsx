
import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../services/api.ts';
import { BlogPost } from '../types.ts';

const BlogPage: React.FC = () => {
    const [posts, setPosts] = useState<BlogPost[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        const fetchPosts = async () => {
            try {
                setLoading(true);
                const blogPosts = await api.getBlogPosts();
                console.log("Blog posts fetched:", blogPosts);
                setPosts(blogPosts);
            } catch (error) {
                console.error("Failed to fetch blog posts:", error);
            } finally {
                setLoading(false);
            }
        };
        fetchPosts();
    }, []);

    return (
        <div className="container mx-auto px-4 py-12">
            <h1 className="text-4xl font-bold text-center mb-4">From the Archon Blog</h1>
            <p className="text-xl text-muted-foreground text-center mb-12">
                News, updates, and insights from the team.
            </p>
            {loading ? (
                <div className="text-center">Loading posts...</div>
            ) : (
                <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-3">
                    {posts.map(post => (
                        <div key={post.id} className="bg-card border border-border rounded-lg overflow-hidden flex flex-col hover:shadow-lg transition-shadow">
                            <Link to={`/blog/${post.id}`} className="block h-full flex flex-col">
                                <img src={post.imageUrl} alt={post.title} className="w-full h-48 object-cover" />
                                <div className="p-6 flex flex-col flex-grow">
                                    <h2 className="text-2xl font-semibold mb-2 text-card-foreground">{post.title}</h2>
                                    <p className="text-muted-foreground mb-4 flex-grow line-clamp-3">{post.excerpt}</p>
                                    <div className="text-sm text-muted-foreground mt-auto">
                                        <span>{post.authorName}</span> &middot; <span>{new Date(post.publishDate).toLocaleDateString()}</span>
                                    </div>
                                </div>
                            </Link>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

export default BlogPage;
