
import React from 'react';
import { Link, Unlink } from 'lucide-react';
import { cn } from '@/lib/utils';
import { type CornerRadius, type GlowIntensity, type ColorOption, getColorConfig, getGlowConfig } from '@/components/ui/NeonButton';

interface PlaygroundControlsProps {
  showLayer2: boolean;
  setShowLayer2: (v: boolean) => void;
  layer2Inset: number;
  setLayer2Inset: (v: number) => void;
  layer1Color: ColorOption;
  setLayer1Color: (v: ColorOption) => void;
  layer2Color: ColorOption;
  setLayer2Color: (v: ColorOption) => void;
  layer1Border: boolean;
  setLayer1Border: (v: boolean) => void;
  layer2Border: boolean;
  setLayer2Border: (v: boolean) => void;
  coloredText: boolean;
  setColoredText: (v: boolean) => void;
  layer1Glow: GlowIntensity;
  setLayer1Glow: (v: GlowIntensity) => void;
  layer2Glow: GlowIntensity;
  setLayer2Glow: (v: GlowIntensity) => void;
  borderGlow: GlowIntensity;
  setBorderGlow: (v: GlowIntensity) => void;
  layer1Radius: CornerRadius;
  setLayer1Radius: React.Dispatch<React.SetStateAction<CornerRadius>>;
  layer2Radius: CornerRadius;
  setLayer2Radius: React.Dispatch<React.SetStateAction<CornerRadius>>;
  layer1Linked: any;
  setLayer1Linked: any;
  layer2Linked: any;
  setLayer2Linked: any;
  activeTab: 'layer1' | 'layer2';
  setActiveTab: (v: 'layer1' | 'layer2') => void;
}

export const PlaygroundControls: React.FC<PlaygroundControlsProps> = (props) => {
  const {
    showLayer2, setShowLayer2, layer2Inset, setLayer2Inset,
    layer1Color, setLayer1Color, layer2Color, setLayer2Color,
    layer1Border, setLayer1Border, layer2Border, setLayer2Border,
    coloredText, setColoredText, layer1Glow, setLayer1Glow,
    layer2Glow, setLayer2Glow, borderGlow, setBorderGlow,
    layer1Radius, setLayer1Radius, layer2Radius, setLayer2Radius,
    layer1Linked, setLayer1Linked, layer2Linked, setLayer2Linked,
    activeTab, setActiveTab
  } = props;

  const colors: ColorOption[] = ['none', 'purple', 'pink', 'blue', 'green', 'red'];
  const glowOptions: GlowIntensity[] = ['none', 'sm', 'md', 'lg', 'xl', 'xxl'];

  const handleCornerChange = (
    layer: 'layer1' | 'layer2',
    corner: keyof CornerRadius,
    value: number,
    linked: { [key in keyof CornerRadius]: boolean },
    setRadius: React.Dispatch<React.SetStateAction<CornerRadius>>
  ) => {
    const currentRadius = layer === 'layer1' ? layer1Radius : layer2Radius;
    if (linked[corner]) {
      const newRadius: CornerRadius = {};
      Object.keys(linked).forEach(key => {
        newRadius[key as keyof CornerRadius] = linked[key as keyof CornerRadius] ? value : (currentRadius[key as keyof CornerRadius] || 0);
      });
      setRadius(newRadius);
    } else {
      setRadius((prev: CornerRadius) => ({ ...prev, [corner]: value }));
    }
  };

  const toggleLink = (layer: 'layer1' | 'layer2', corner: keyof CornerRadius) => {
    if (layer === 'layer1') {
      setLayer1Linked((prev: any) => ({ ...prev, [corner]: !prev[corner] }));
    } else {
      setLayer2Linked((prev: any) => ({ ...prev, [corner]: !prev[corner] }));
    }
  };

  const CornerInput = ({ layer, corner, value, linked, onChange }: any) => (
    <div className="flex items-center gap-1">
      <button
        onClick={() => toggleLink(layer, corner)}
        className={cn(
          'w-5 h-5 rounded border transition-all flex items-center justify-center',
          linked ? 'bg-blue-500 border-blue-600 text-white' : 'bg-gray-200 dark:bg-gray-700 border-gray-300 dark:border-gray-600'
        )}
      >
        {linked ? <Link className="w-3 h-3" /> : <Unlink className="w-3 h-3" />}
      </button>
      <input
        type="number" min="0" max="50" value={value}
        onChange={(e) => onChange(parseInt(e.target.value) || 0)}
        className="w-12 px-1 py-0.5 text-sm text-center bg-white/50 dark:bg-black/50 border border-gray-300 dark:border-gray-600 rounded"
      />
    </div>
  );

  return (
    <div className="p-6">
      <div className="space-y-3 mb-6">
        <h3 className="text-sm font-medium text-gray-700 dark:text-gray-300">Controls</h3>
        <label className="flex items-center gap-2 text-sm text-gray-700 dark:text-gray-300">
          <input type="checkbox" checked={coloredText} onChange={(e) => setColoredText(e.target.checked)} className="w-4 h-4 rounded text-purple-600" />
          Colored Text (takes button color)
        </label>
        
        <div className="flex items-center gap-2 border-b border-gray-200 dark:border-gray-700">
          <button onClick={() => setActiveTab('layer1')} className={cn('px-4 py-2 text-sm font-medium relative', activeTab === 'layer1' ? 'text-purple-600' : 'text-gray-500')}>
            Layer 1 {activeTab === 'layer1' && <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-purple-600" />}
          </button>
          <div className="flex items-center gap-2">
            <button onClick={() => setActiveTab('layer2')} className={cn('px-4 py-2 text-sm font-medium relative', activeTab === 'layer2' ? 'text-purple-600' : 'text-gray-500')}>
              Layer 2 {activeTab === 'layer2' && <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-purple-600" />}
            </button>
            <input type="checkbox" checked={showLayer2} onChange={(e) => setShowLayer2(e.target.checked)} className="w-4 h-4 rounded text-purple-600" />
          </div>
        </div>
      </div>

      <div className="space-y-4">
        {activeTab === 'layer1' ? (
          <>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs text-gray-600 mb-1">Color</label>
                <select value={layer1Color} onChange={(e) => setLayer1Color(e.target.value as any)} className="w-full px-2 py-1 text-sm bg-white dark:bg-gray-900 border rounded">
                  {colors.map(c => <option key={c} value={c}>{c.toUpperCase()}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-xs text-gray-600 mb-1">Glow</label>
                <select value={layer1Glow} onChange={(e) => setLayer1Glow(e.target.value as any)} className="w-full px-2 py-1 text-sm bg-white dark:bg-gray-900 border rounded">
                  {glowOptions.map(o => <option key={o} value={o}>{o.toUpperCase()}</option>)}
                </select>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-2">
              <div className="flex items-center justify-between text-xs">TL <CornerInput layer="layer1" corner="topLeft" value={layer1Radius.topLeft} linked={layer1Linked.topLeft} onChange={(v:any) => handleCornerChange('layer1', 'topLeft', v, layer1Linked, setLayer1Radius)} /></div>
              <div className="flex items-center justify-between text-xs">TR <CornerInput layer="layer1" corner="topRight" value={layer1Radius.topRight} linked={layer1Linked.topRight} onChange={(v:any) => handleCornerChange('layer1', 'topRight', v, layer1Linked, setLayer1Radius)} /></div>
            </div>
          </>
        ) : (
          <>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-xs text-gray-600 mb-1">Color</label>
                <select disabled={!showLayer2} value={layer2Color} onChange={(e) => setLayer2Color(e.target.value as any)} className="w-full px-2 py-1 text-sm bg-white dark:bg-gray-900 border rounded">
                  {colors.map(c => <option key={c} value={c}>{c.toUpperCase()}</option>)}
                </select>
              </div>
              <div>
                <label className="block text-xs text-gray-600 mb-1">Glow</label>
                <select disabled={!showLayer2} value={layer2Glow} onChange={(e) => setLayer2Glow(e.target.value as any)} className="w-full px-2 py-1 text-sm bg-white dark:bg-gray-900 border rounded">
                  {glowOptions.map(o => <option key={o} value={o}>{o.toUpperCase()}</option>)}
                </select>
              </div>
            </div>
            <div>
              <label className="block text-xs text-gray-600 mb-1">Layer 2 Inset: {layer2Inset}px</label>
              <input type="range" min="-20" max="20" value={layer2Inset} onChange={(e) => setLayer2Inset(parseInt(e.target.value))} className="w-full" disabled={!showLayer2} />
            </div>
          </>
        )}
      </div>
    </div>
  );
};
