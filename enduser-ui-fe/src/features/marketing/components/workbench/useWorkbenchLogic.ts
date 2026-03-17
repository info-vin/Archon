import { useState, useEffect } from 'react';
import { ContentSource } from '../VictoryFeedList';

export const INDUSTRIES = ["製造業", "高科技", "零售業", "生技醫療", "金融科技"];
export const CHARTS = ["柱狀圖", "趨勢圖", "數據表格", "Sankey 圖", "漏斗圖"];
export const STYLES = ["專業商務", "敘事故事", "技術深挖", "輕鬆科普"];
export const LENGTHS = [
  { id: 'compact', label: '精簡 (300字)' },
  { id: 'standard', label: '標準 (800字)' },
  { id: 'deep', label: '深度報導 (1500字+)' }
];

interface UseWorkbenchLogicProps {
  activeSource: ContentSource | null;
  usedPrompt?: string;
  content: string;
}

export const useWorkbenchLogic = ({ activeSource, usedPrompt, content }: UseWorkbenchLogicProps) => {
  const [promptTab, setPromptTab] = useState<'config' | 'inspect'>('config');

  // Advanced Config State
  const [config, setConfig] = useState({
    industry: [] as string[],
    charts: [] as string[],
    length: 'standard',
    style: [] as string[],
    enableWebSearch: false
  });

  // Automatically switch to 'inspect' tab when a new prompt is received
  useEffect(() => {
    if (usedPrompt) setPromptTab('inspect');
  }, [usedPrompt]);

  const toggleItem = (category: 'industry' | 'charts' | 'style', item: string) => {
    setConfig(prev => ({
      ...prev,
      [category]: prev[category].includes(item)
        ? prev[category].filter((i: string) => i !== item)
        : [...prev[category], item]
    }));
  };

  const getTempPromptPreview = () => {
    if (!activeSource) return "";
    const indStr = config.industry.length > 0 ? config.industry.join("與") : "通用";
    const lenStr = LENGTHS.find(l => l.id === config.length)?.label || "標準";
    const styleStr = config.style.length > 0 ? config.style.join("且") : "專業";
    const chartStr = config.charts.length > 0 ? `預留 ${config.charts.join("、")}。` : "";
    const searchStr = config.enableWebSearch ? "結合 Google 搜尋。" : "";

    return `針對「${indStr}」的「${lenStr}」文章。風格「${styleStr}」。${chartStr}${searchStr}`;
  };

  // Helper to extract image from content for Visual Header
  const getPreviewImage = () => {
    if (!content) return null;
    const match = content.match(/!\[.*?\]\((.*?)\)/);
    return match ? match[1] : null;
  };

  return {
    promptTab,
    setPromptTab,
    config,
    setConfig,
    toggleItem,
    getTempPromptPreview,
    getPreviewImage
  };
};
