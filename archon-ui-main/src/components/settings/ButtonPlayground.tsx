
import React, { useState } from 'react';
import { Copy, Check } from 'lucide-react';
import { NeonButton, type CornerRadius, type GlowIntensity, type ColorOption, getColorConfig, getGlowConfig } from '@/components/ui/NeonButton';
import { motion } from 'framer-motion';
import { copyToClipboard } from '@/features/shared/utils/clipboard';
import { PlaygroundControls } from './playground/PlaygroundControls';

export const ButtonPlayground: React.FC = () => {
  // State management
  const [showLayer2, setShowLayer2] = useState(true);
  const [layer2Inset, setLayer2Inset] = useState(8);
  const [layer1Color, setLayer1Color] = useState<ColorOption>('none');
  const [layer2Color, setLayer2Color] = useState<ColorOption>('pink');
  const [layer1Border, setLayer1Border] = useState(true);
  const [layer2Border, setLayer2Border] = useState(true);
  const [coloredText, setColoredText] = useState(true);
  const [activeTab, setActiveTab] = useState<'layer1' | 'layer2'>('layer1');
  const [layer1Glow, setLayer1Glow] = useState<GlowIntensity>('md');
  const [layer2Glow, setLayer2Glow] = useState<GlowIntensity>('md');
  const [borderGlow, setBorderGlow] = useState<GlowIntensity>('none');
  const [layer1Radius, setLayer1Radius] = useState<CornerRadius>({ topLeft: 12, topRight: 12, bottomRight: 12, bottomLeft: 12 });
  const [layer2Radius, setLayer2Radius] = useState<CornerRadius>({ topLeft: 24, topRight: 24, bottomRight: 24, bottomLeft: 24 });
  const [layer1Linked, setLayer1Linked] = useState({ topLeft: true, topRight: true, bottomRight: true, bottomLeft: true });
  const [layer2Linked, setLayer2Linked] = useState({ topLeft: true, topRight: true, bottomRight: true, bottomLeft: true });
  const [copied, setCopied] = useState(false);

  const generateCSS = () => {
    const l1BR = `${layer1Radius.topLeft}px ${layer1Radius.topRight}px ${layer1Radius.bottomRight}px ${layer1Radius.bottomLeft}px`;
    const l2BR = `${layer2Radius.topLeft}px ${layer2Radius.topRight}px ${layer2Radius.bottomRight}px ${layer2Radius.bottomLeft}px`;
    
    let css = `.neon-button {
  position: relative; padding: 12px 24px; font-weight: 500; transition: all 300ms; cursor: pointer; overflow: hidden;
  background: ${layer1Color === 'none' ? 'rgba(0,0,0,0.9)' : 'rgba(0,0,0,0.9)'}; backdrop-filter: blur(8px); border-radius: ${l1BR};
  ${layer1Border ? `border: 1px solid ${layer1Color === 'none' ? 'rgba(255,255,255,0.2)' : getColorConfig(layer1Color).border.split(' ')[1]};` : ''}
  ${layer1Glow !== 'none' ? `box-shadow: 0 0 ${getGlowConfig(layer1Glow).blur}px ${getColorConfig(layer1Color).glow};` : ''}
}
.neon-button span {
  position: relative; z-index: 10; font-weight: 500;
  ${coloredText ? `color: ${getColorConfig(showLayer2 && layer2Color !== 'none' ? layer2Color : layer1Color).text};` : 'color: rgba(255,255,255,0.8);'}
}`;
    if (showLayer2) {
      css += `\n.neon-button::before {
  content: ''; position: absolute; top: ${layer2Inset}px; left: ${layer2Inset}px; right: ${layer2Inset}px; bottom: ${layer2Inset}px;
  background: linear-gradient(to bottom, rgba(255,255,255,0.2), rgba(0,0,0,0.2)); backdrop-filter: blur(4px); border-radius: ${l2BR};
  ${layer2Border ? `border: 1px solid ${layer2Color === 'none' ? 'rgba(255,255,255,0.2)' : getColorConfig(layer2Color).border.split(' ')[1]};` : ''}
  ${layer2Glow !== 'none' ? `box-shadow: 0 0 ${getGlowConfig(layer2Glow).blur}px ${getColorConfig(layer2Color).glow};` : ''}
}`;
    }
    return css;
  };

  const handleCopyToClipboard = async () => {
    const result = await copyToClipboard(generateCSS());
    if (result.success) { setCopied(true); setTimeout(() => setCopied(false), 2000); }
  };

  return (
    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} className="space-y-8">
      <h2 className="text-2xl font-bold">Glass Button Lab</h2>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="relative rounded-xl backdrop-blur-md bg-card border border-border shadow-lg">
          <div className="p-6 border-b border-border">
            <h3 className="text-lg font-semibold mb-4">Preview</h3>
            <div className="flex items-center justify-center min-h-[150px] bg-muted rounded-lg p-8">
              <NeonButton showLayer2={showLayer2} layer2Inset={layer2Inset} layer1Color={layer1Color} layer2Color={layer2Color}
                layer1Border={layer1Border} layer2Border={layer2Border} layer1Radius={layer1Radius} layer2Radius={layer2Radius}
                layer1Glow={layer1Glow} layer2Glow={layer2Glow} borderGlow={borderGlow} coloredText={coloredText}>
                Click Me
              </NeonButton>
            </div>
          </div>
          <PlaygroundControls {...{
            showLayer2, setShowLayer2, layer2Inset, setLayer2Inset, layer1Color, setLayer1Color, layer2Color, setLayer2Color,
            layer1Border, setLayer1Border, layer2Border, setLayer2Border, coloredText, setColoredText, layer1Glow, setLayer1Glow,
            layer2Glow, setLayer2Glow, borderGlow, setBorderGlow, layer1Radius, setLayer1Radius, layer2Radius, setLayer2Radius,
            layer1Linked, setLayer1Linked, layer2Linked, setLayer2Linked, activeTab, setActiveTab
          }} />
        </div>
        <div className="relative rounded-xl backdrop-blur-md bg-card border border-border shadow-lg h-full">
          <div className="p-6 border-b border-border flex items-center justify-between">
            <h3 className="text-lg font-semibold">CSS Styles</h3>
            <button onClick={handleCopyToClipboard} className="px-4 py-2 bg-primary text-primary-foreground rounded-lg transition-colors flex items-center gap-2">
              {copied ? <Check className="w-4 h-4" /> : <Copy className="w-4 h-4" />}
              {copied ? 'Copied!' : 'Copy Styles'}
            </button>
          </div>
          <div className="p-6">
            <pre className="text-xs text-muted-foreground overflow-x-auto bg-black p-4 rounded-lg border border-border">
              <code>{generateCSS()}</code>
            </pre>
          </div>
        </div>
      </div>
    </motion.div>
  );
};
