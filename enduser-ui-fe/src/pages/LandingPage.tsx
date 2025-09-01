
import React from 'react';
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

    return (
        <div className="flex flex-col">
            {/* Hero Section */}
            <section className="py-20 md:py-32">
                <div className="container mx-auto text-center px-4">
                    <h1 className="text-4xl md:text-6xl font-bold mb-4 text-primary tracking-tighter">
                        The Command Center for Your Projects
                    </h1>
                    <p className="text-lg md:text-xl mb-8 max-w-3xl mx-auto text-muted-foreground">
                        Manage knowledge, context, and tasks with unparalleled efficiency.
                        Archon provides project-based access, ensuring only assigned employees can view and manage tasks.
                    </p>
                    <button
                        onClick={() => navigate('/auth')}
                        className="px-8 py-4 bg-primary text-primary-foreground rounded-md font-semibold hover:bg-primary/90 transition-colors text-lg"
                    >
                        Get Started
                    </button>
                </div>
            </section>

            {/* Features Section */}
            <section className="py-20 bg-secondary/50">
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
