
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { LayoutGridIcon, BarChartIcon, ShieldCheckIcon } from '../components/Icons.tsx';

const FeatureCard = ({ icon, title, description }: { icon: React.ReactNode, title: string, description: string }) => (
    <div className="flex flex-col items-center p-6 text-center bg-card rounded-lg border border-border">
        <div className="mb-4 p-3 rounded-full bg-secondary text-primary">
            {icon}
        </div>
        <h3 className="mb-2 text-xl font-semibold">{title}</h3>
        <p className="text-muted-foreground">{description}</p>
    </div>
);

const LandingPage: React.FC = () => {
    const navigate = useNavigate();
    const [isHeroExpanded, setIsHeroExpanded] = useState(true);

    useEffect(() => {
        // Trigger shrink animation after 3.5 seconds to let the fire effect play
        const timer = setTimeout(() => {
            setIsHeroExpanded(false);
        }, 3500);

        return () => clearTimeout(timer);
    }, []);

    return (
        <div className="flex flex-col overflow-x-hidden">
            {/* Hero Section */}
            <section className="relative py-20 md:py-32 min-h-[80vh] flex items-center bg-background">
                <div className="container mx-auto px-4 relative z-10 w-full">
                    <div className="flex flex-col md:flex-row gap-12 items-center min-h-[400px] relative justify-center">
                        
                        {/* Video Container */}
                        <div className={`
                            transition-all duration-1000 ease-in-out flex justify-center
                            ${isHeroExpanded 
                                ? 'w-full md:w-[60%] mx-auto translate-y-8 md:translate-y-12' 
                                : 'w-full md:w-1/3 translate-y-0'
                            }
                        `}>
                            <div className={`
                                w-full aspect-video rounded-3xl overflow-hidden transition-all duration-1000 bg-black
                                ${isHeroExpanded ? 'shadow-[0_20px_60px_rgba(0,0,0,0.4)]' : 'shadow-2xl border border-border/50'}
                            `}>
                                <video 
                                    src="/assets/videos/hero_animation.mp4" 
                                    autoPlay 
                                    loop 
                                    muted 
                                    playsInline 
                                    className="w-full h-full object-cover"
                                />
                            </div>
                        </div>

                        {/* Text and Button Container */}
                        <div className={`
                            transition-all duration-1000 delay-300 w-full text-center md:text-left flex-1
                            ${isHeroExpanded 
                                ? 'opacity-0 translate-x-10 absolute pointer-events-none' 
                                : 'opacity-100 translate-x-0 relative'
                            }
                        `}>
                            <h1 className="text-5xl md:text-7xl font-extrabold mb-6 text-primary tracking-tighter">
                                Managerial Nexus
                            </h1>
                            <p className="text-xl mb-10 max-w-2xl mx-auto md:mx-0 text-muted-foreground leading-relaxed">
                                Manage knowledge, context, and tasks with unparalleled efficiency.
                                Archon provides project-based access, ensuring only assigned employees can view and manage tasks.
                            </p>
                            <button
                                onClick={() => navigate('/auth')}
                                className="px-10 py-5 bg-primary text-primary-foreground rounded-full font-bold hover:bg-primary/90 transition-all hover:scale-105 active:scale-95 text-xl shadow-xl shadow-primary/20"
                            >
                                Get Started
                            </button>
                        </div>
                    </div>
                </div>
            </section>

            {/* Features Section */}
            <section className="py-20 bg-secondary/30">
                <div className="container mx-auto px-4">
                    <h2 className="text-3xl font-bold text-center mb-12">Powerful Features, Seamlessly Integrated</h2>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
                        <FeatureCard 
                            icon={<LayoutGridIcon className="w-8 h-8" />} 
                            title="Multiple Task Views"
                            description="Visualize your workflow with List, Table, Kanban, and Gantt chart views to suit your project's needs."
                        />
                        <FeatureCard 
                            icon={<BarChartIcon className="w-8 h-8" />} 
                            title="Project-Based Access"
                            description="Ensure security and focus. Employees can only access projects they are explicitly assigned to."
                        />
                        <FeatureCard 
                            icon={<ShieldCheckIcon className="w-8 h-8" />} 
                            title="Administrator Oversight"
                            description="A dedicated admin panel for user management, data auditing, and secure handover of responsibilities."
                        />
                    </div>
                </div>
            </section>
        </div>
    );
};

export default LandingPage;
