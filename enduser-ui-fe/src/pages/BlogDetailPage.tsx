import React, { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import Markdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { api } from '../services/api';
import { BlogPost } from '../types.ts';
import { RAGCitation } from '../features/marketing/components/RAGCitation';
import { MermaidRenderer } from '../components/MermaidRenderer';

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

    // Preprocess markdown: replace [1] with a specific markdown link syntax: [1](#rag-citation-1)
    // Only match standalone [digits], avoiding existing links
    const processCitations = (text: string) => {
        if (!text) return '';
        // Look behind to avoid matching inside existing markdown links like [Text]([1])
        // This is a simple regex that works for most AI generated texts like "The sky is blue [1]."
        return text.replace(/(?<!\]\()\[(\d+)\](?!\()/g, '[$1](#rag-citation-$1)');
    };

    const processedContent = processCitations(post.content || '');
    const citations = post.generation_metadata?.citations || [];

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
                    <Markdown
                        remarkPlugins={[remarkGfm]}
                        components={{
                            a: ({ node, href, children, ...props }) => {
                                if (href?.startsWith('#rag-citation-')) {
                                    const citationId = href.replace('#rag-citation-', '');
                                    return <RAGCitation citationId={citationId} citations={citations} />;
                                }
                                return <a href={href} {...props}>{children}</a>;
                            },
                            code: ({ node, className, children, ...props }) => {
                                const match = /language-(\w+)/.exec(className || '');
                                const isMermaid = match && match[1] === 'mermaid';
                                if (isMermaid) {
                                    return <MermaidRenderer code={String(children).replace(/\n$/, '')} />;
                                }
                                return (
                                    <code className={className} {...props}>
                                        {children}
                                    </code>
                                );
                            }
                        }}
                    >
                        {processedContent}
                    </Markdown>
                </div>

                {post.hashtags && (
                    <div className="mt-12 pt-6 border-t border-border">
                        <div className="flex flex-wrap gap-2">
                            {post.hashtags.split(' ').map((tag, i) => (
                                <span key={i} className="px-3 py-1 bg-secondary text-secondary-foreground rounded-full text-sm font-medium hover:bg-secondary/80 transition-colors cursor-default">
                                    {tag}
                                </span>
                            ))}
                        </div>
                    </div>
                )}
            </article>
        </div>
    );
};

export default BlogDetailPage;
