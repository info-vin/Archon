import React from 'react';
import { LayoutGridIcon, ShieldCheckIcon, SettingsIcon, BarChartIcon, FileTextIcon, ActivityIcon, UsersIcon, DatabaseIcon } from '../../components/Icons.tsx';
import SmartManufacturing from './SmartManufacturing.tsx';
import TechSpecs from './TechSpecs.tsx';

export type SolutionItemType = 'component' | 'legacy';

export interface SolutionItem {
    id: string;
    label: string;
    type: SolutionItemType;
    icon?: React.ReactNode;
    component?: React.FC<any>;
    src?: string;
    protected?: boolean;
    items?: SolutionItem[]; // For nested sub-items
}

export const solutionsConfig: SolutionItem[] = [
    {
        id: 'overview',
        label: 'Overview',
        type: 'component', // This is actually a group header in the UI, but we can treat the first item as default? No, let's make it a section.
        // Actually, the plan calls for sections like "Overview", "Core Technology".
        // Let's structure it as sections.
        icon: <LayoutGridIcon className="w-4 h-4" />,
        items: [
            { id: 'summary', label: 'Project Summary', type: 'component', component: SmartManufacturing },
            { id: 'tech-specs', label: 'Tech Specs', type: 'component', component: TechSpecs },
            { id: 'linkage', label: 'Linkage Analysis', type: 'legacy', src: '/ai/contents/linkage.html' },
        ]
    } as any, // Using 'any' briefly to bypass strict type checking for the group structure if we change it.
    // Wait, the plan says "Navigation Structure". Let's flatten it or use a nested structure that `SolutionsPage` can iterate.
    // The previous `navItems` was flat. The new plan implies categories.
    // Let's define `solutionsConfig` as categories.
];

export interface SolutionCategory {
    title: string;
    items: SolutionItem[];
}

export const solutionsCategories: SolutionCategory[] = [
    {
        title: 'Overview',
        items: [
            { id: 'summary', label: 'Project Summary', type: 'component', component: SmartManufacturing, icon: <LayoutGridIcon className="w-4 h-4" /> },
            { id: 'tech-specs', label: 'Tech Specs', type: 'component', component: TechSpecs, icon: <ShieldCheckIcon className="w-4 h-4" /> },
            { id: 'linkage', label: 'Linkage Analysis', type: 'legacy', src: '/ai/contents/linkage.html', icon: <ActivityIcon className="w-4 h-4" /> },
        ]
    },
    {
        title: 'Core Technology',
        items: [
            { id: 'sas-arch', label: 'SAS Viya Architecture', type: 'legacy', src: '/ai/original_files/sas_viya_arc.html', icon: <SettingsIcon className="w-4 h-4" /> },
            { id: 'rpa-flow', label: 'RPA Workflow', type: 'legacy', src: '/ai/original_files/RPA_canvas.html', icon: <ActivityIcon className="w-4 h-4" /> },
            { id: 'rpa-full', label: 'Full RPA Detail', type: 'legacy', src: '/ai/original_files/RPA_sas.html', icon: <DatabaseIcon className="w-4 h-4" /> },
        ]
    },
    {
        title: 'High-Tech Manufacturing',
        items: [
            { id: 'oee', label: 'OEE Maximization', type: 'legacy', src: '/ai/hightech/SAS in hightech manufacturing_ Maximizing OEE.html', icon: <BarChartIcon className="w-4 h-4" /> },
            { id: 'yield', label: 'Yield & Quality', type: 'legacy', src: '/ai/hightech/SAS in hightech manufacturing_ Yield & Quality.html', icon: <ActivityIcon className="w-4 h-4" /> },
            { id: 'supply-chain', label: 'Supply Chain', type: 'legacy', src: '/ai/hightech/SAS in hightech manufacturing_ Transforming High-Tech Supply Chains.html', icon: <DatabaseIcon className="w-4 h-4" /> },
            { id: 'arch-diagram', label: 'Architecture Diagram', type: 'legacy', src: '/ai/hightech/SAS in hightech manufacturing_ architecture diagram.html', icon: <SettingsIcon className="w-4 h-4" /> },
        ]
    },
    {
        title: 'Process & Benefits',
        items: [
            { id: 'process', label: 'Process Details', type: 'legacy', src: '/ai/original_files/互動資料機制列表.html', protected: true, icon: <FileTextIcon className="w-4 h-4" /> },
            { id: 'benefits', label: 'Adoption Benefits', type: 'legacy', src: '/ai/original_files/adoption_process_chart.html', icon: <BarChartIcon className="w-4 h-4" /> },
            { id: 'wellbeing', label: 'Employee Well-being', type: 'legacy', src: '/ai/original_files/Employee Well-being Strategy Upgrade Plan.html', icon: <UsersIcon className="w-4 h-4" /> },
        ]
    },
    {
        title: 'Reports & Proposals',
        items: [
            { id: 'proposal', label: 'Solution Proposal', type: 'legacy', src: '/ai/original_files/NBllm.html', protected: true, icon: <FileTextIcon className="w-4 h-4" /> },
            { id: 'smart-sched', label: 'Smart Scheduling Report', type: 'legacy', src: '/ai/original_files/製造業智慧排程與人力資源管理解決方案提案.html', protected: true, icon: <FileTextIcon className="w-4 h-4" /> },
            { id: 'biotech', label: 'BioTech Platform', type: 'legacy', src: '/ai/original_files/生技醫藥資訊整合平台.html', protected: true, icon: <ActivityIcon className="w-4 h-4" /> },
        ]
    }
];
