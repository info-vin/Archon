import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import Markdown from 'react-markdown';
import { api } from '../services/api.ts';
import { BlogPost } from '../types.ts';

const BlogDetailPage: React.FC = () => {
    const { id } = useParams<{ id: string }>();
    const [post, setPost] = useState<BlogPost | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        const fetchPost = async () => {
            if (!id) return;
            try {
                setLoading(true);
                const blogPost = await api.getBlogPost(id);
                setPost(blogPost);
            } catch (err: any) {
                console.error("Failed to fetch blog post:", err);
                setError("Failed to load blog post. It may have been deleted.");
            } finally {
                setLoading(false);
            }
        };
        fetchPost();
    }, [id]);

    if (loading) {
        return <div className="flex justify-center items-center h-64">Loading...</div>;
    }

    if (error || !post) {
        return (
            <div className="container mx-auto px-4 py-12 text-center">
                <h2 className="text-2xl font-bold text-red-600 mb-4">Error</h2>
                <p className="text-muted-foreground mb-6">{error || "Post not found."}</p>
                <Link to="/blog" className="text-primary hover:underline">Back to Blog</Link>
            </div>
        );
    }

    return (
        <div className="container mx-auto px-4 py-12 max-w-4xl">
            <Link to="/blog" className="text-primary hover:underline mb-8 inline-block">&larr; Back to Blog</Link>
            
            <article className="prose prose-lg dark:prose-invert max-w-none">
                <img src={post.imageUrl} alt={post.title} className="w-full h-64 md:h-96 object-cover rounded-xl mb-8" />
                
                <h1 className="text-4xl md:text-5xl font-bold mb-4">{post.title}</h1>
                
                <div className="flex items-center text-muted-foreground mb-8 text-sm">
                    <span className="font-semibold text-foreground mr-2">{post.authorName}</span>
                    <span>&middot;</span>
                    <span className="ml-2">{new Date(post.publishDate).toLocaleDateString()}</span>
                </div>

                <div className="markdown-content">
                    <Markdown>{post.content}</Markdown>
                </div>
            </article>
        </div>
    );
};

export default BlogDetailPage;
