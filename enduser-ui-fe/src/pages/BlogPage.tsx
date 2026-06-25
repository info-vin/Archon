
import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { api } from '../services/api';
import { BlogPost } from '../types.ts';

// PERFORMANCE: Hoist Intl.DateTimeFormat instance outside the component to avoid expensive repeated instantiations (implicitly called by toLocaleDateString) inside the render loop.
const dateFormatter = new Intl.DateTimeFormat(undefined);

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
        <div className="flex flex-col min-h-screen">
             {/* Hero Section */}
             <section className="py-20 md:py-32">
                <div className="container mx-auto text-center px-4">
                    <h1 className="text-4xl md:text-6xl font-bold mb-4 text-primary tracking-tighter">
                        From the Archon Blog
                    </h1>
                    <p className="text-lg md:text-xl mb-8 max-w-3xl mx-auto text-muted-foreground">
                        News, updates, and insights from the team.
                    </p>
                </div>
            </section>

            {/* Content Section */}
            <section className="py-20 bg-secondary/50 flex-grow">
                <div className="container mx-auto px-4">
                    {loading ? (
                        <div className="text-center text-muted-foreground">Loading posts...</div>
                    ) : (
                        <div className="grid gap-8 md:grid-cols-2 lg:grid-cols-3">
                            {posts.filter(p => p.status === 'published').map(post => (
                                <div key={post.id} className="bg-card border border-border rounded-lg overflow-hidden flex flex-col hover:shadow-lg transition-all group">
                                    <Link to={`/blog/${post.id}`} className="block h-full flex flex-col">
                                        <div className="overflow-hidden h-48">
                                            <img 
                                                src={post.imageUrl} 
                                                alt={post.title} 
                                                className="w-full h-full object-cover transform group-hover:scale-105 transition-transform duration-300" 
                                            />
                                        </div>
                                        <div className="p-6 flex flex-col flex-grow">
                                            <h2 className="text-2xl font-semibold mb-3 text-card-foreground group-hover:text-primary transition-colors">{post.title}</h2>
                                            <p className="text-muted-foreground mb-4 flex-grow line-clamp-3 leading-relaxed">{post.excerpt}</p>
                                            <div className="flex items-center justify-between text-sm text-muted-foreground mt-auto pt-4 border-t border-border">
                                                <span className="font-medium">{post.authorName}</span>
                                                <time dateTime={post.publishDate}>{dateFormatter.format(new Date(post.publishDate))}</time>
                                            </div>
                                        </div>
                                    </Link>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </section>
        </div>
    );
};

export default BlogPage;
