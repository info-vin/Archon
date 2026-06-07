import React, { useState, useEffect } from 'react';
import { AlertTriangleIcon, CheckCircleIcon, CpuIcon } from '../../../components/Icons';
import { api } from '../../../services/api';

export const AdminFallbackConfig: React.FC = () => {
    const [hfToken, setHfToken] = useState('');
    const [originalHfToken, setOriginalHfToken] = useState('');
    const [fallbackTier, setFallbackTier] = useState('0');
    const [isLoading, setIsLoading] = useState(true);
    const [isSaving, setIsSaving] = useState(false);

    useEffect(() => {
        const loadSettings = async () => {
            try {
                const apiKeys = await api.getSystemSettings('api_keys');
                const ragSettings = await api.getSystemSettings('rag_strategy');
                
                const tokenSetting = apiKeys.find((s: any) => s.key === 'HF_TOKEN');
                if (tokenSetting) {
                    setHfToken(tokenSetting.value);
                    setOriginalHfToken(tokenSetting.value);
                }
                
                const tierSetting = ragSettings.find((s: any) => s.key === 'forced_fallback_tier');
                if (tierSetting && tierSetting.value !== undefined && tierSetting.value !== null) {
                    setFallbackTier(String(tierSetting.value));
                }
            } catch (err) {
                console.error("Failed to load fallback settings", err);
            } finally {
                setIsLoading(false);
            }
        };
        loadSettings();
    }, []);

    const handleSave = async () => {
        setIsSaving(true);
        try {
            if (hfToken !== originalHfToken) {
                await api.updateSystemSetting('HF_TOKEN', { 
                    value: hfToken, 
                    description: 'Hugging Face Token for Tier 2 Fallback' 
                });
                setOriginalHfToken(hfToken);
            }
            
            await api.updateSystemSetting('forced_fallback_tier', { 
                value: fallbackTier, 
                description: 'Forced Fallback Tier (0=Auto, 1=Gemini, 2=HF, 3=Ollama)' 
            });
            
            alert('Fallback settings saved successfully!');
        } catch (err: any) {
            alert('Failed to save settings: ' + err.message);
        } finally {
            setIsSaving(false);
        }
    };

    if (isLoading) return null;

    return (
        <div className="bg-card p-6 rounded-2xl border border-border shadow-sm mb-6">
            <div className="flex items-center gap-3 mb-6">
                <AlertTriangleIcon className="w-6 h-6 text-amber-500" />
                <h3 className="text-xl font-bold">Hugging Face Fallback (3-Tier 降階架構)</h3>
            </div>
            
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Left Column: Token Input & Warning */}
                <div className="space-y-4">
                    <div>
                        <label className="block text-sm font-medium mb-1">Hugging Face API Token (HF_TOKEN)</label>
                        <div className="flex gap-2">
                            <input 
                                type="password" 
                                value={hfToken} 
                                onChange={(e) => setHfToken(e.target.value)} 
                                placeholder={hfToken === '[ENCRYPTED]' ? "Encrypted - Enter new to change" : "hf_xxxxxxxxxxxxxxxxxxxx"}
                                className="flex-1 px-3 py-2 bg-input border border-border rounded-md text-sm focus:ring-2 focus:ring-indigo-500 text-foreground"
                            />
                        </div>
                        <p className="text-xs text-muted-foreground mt-2">
                            需具備 <strong>Read</strong> 權限的 Access Token，用於在主要雲端 (Tier 1) 失效時，呼叫 Serverless Inference API。
                        </p>
                    </div>

                    <div className="bg-amber-50 dark:bg-amber-900/20 border border-amber-200 dark:border-amber-700/30 p-4 rounded-lg">
                        <h4 className="text-sm font-bold text-amber-800 dark:text-amber-400 mb-2 flex items-center gap-2">
                            <CpuIcon className="w-4 h-4" />
                            使用限制與警示
                        </h4>
                        <ul className="text-xs text-amber-700 dark:text-amber-500 space-y-2 list-disc pl-4">
                            <li><strong>速率限制 (Rate Limits):</strong> 免費 API 共享叢集流量。若回傳 429 或 503，系統將自動無縫降階至 <strong>Tier 3 (本地 Ollama)</strong>。</li>
                            <li><strong>冷啟動 (Cold Start):</strong> 首次請求閒置模型時可能需要 10~30 秒喚醒叢集，期間會有載入延遲。</li>
                        </ul>
                    </div>
                </div>

                {/* Right Column: Routing Strategy */}
                <div>
                    <label className="block text-sm font-medium mb-3">路由策略 (Routing Strategy)</label>
                    <div className="space-y-3">
                        <label className={`flex items-start gap-3 p-3 border rounded-lg cursor-pointer transition-colors ${fallbackTier === '0' ? 'bg-indigo-50 dark:bg-indigo-900/20 border-indigo-500' : 'border-border hover:bg-muted'}`}>
                            <input type="radio" name="fallbackTier" value="0" checked={fallbackTier === '0'} onChange={(e) => setFallbackTier(e.target.value)} className="mt-1" />
                            <div>
                                <div className="font-semibold text-sm">自動容災 (Auto Fallback)</div>
                                <div className="text-xs text-muted-foreground">預設。Tier 1 失敗時嘗試 Tier 2，若再失敗則進入 Tier 3 離線模式。</div>
                            </div>
                        </label>

                        <label className={`flex items-start gap-3 p-3 border rounded-lg cursor-pointer transition-colors ${fallbackTier === '1' ? 'bg-emerald-50 dark:bg-emerald-900/20 border-emerald-500' : 'border-border hover:bg-muted'}`}>
                            <input type="radio" name="fallbackTier" value="1" checked={fallbackTier === '1'} onChange={(e) => setFallbackTier(e.target.value)} className="mt-1" />
                            <div>
                                <div className="font-semibold text-sm">強制主要雲端 (Tier 1 Only)</div>
                                <div className="text-xs text-muted-foreground">永遠使用 Gemini/OpenAI，不進行降階備援。</div>
                            </div>
                        </label>

                        <label className={`flex items-start gap-3 p-3 border rounded-lg cursor-pointer transition-colors ${fallbackTier === '2' ? 'bg-amber-50 dark:bg-amber-900/20 border-amber-500' : 'border-border hover:bg-muted'}`}>
                            <input type="radio" name="fallbackTier" value="2" checked={fallbackTier === '2'} onChange={(e) => setFallbackTier(e.target.value)} className="mt-1" />
                            <div>
                                <div className="font-semibold text-sm">強制 HF 雲端運算 (Tier 2)</div>
                                <div className="text-xs text-muted-foreground">測試用。強制路由至 Hugging Face Serverless API。</div>
                            </div>
                        </label>

                        <label className={`flex items-start gap-3 p-3 border rounded-lg cursor-pointer transition-colors ${fallbackTier === '3' ? 'bg-orange-50 dark:bg-orange-900/20 border-orange-500' : 'border-border hover:bg-muted'}`}>
                            <input type="radio" name="fallbackTier" value="3" checked={fallbackTier === '3'} onChange={(e) => setFallbackTier(e.target.value)} className="mt-1" />
                            <div>
                                <div className="font-semibold text-sm">強制本地離線 (Tier 3)</div>
                                <div className="text-xs text-muted-foreground">測試用。強制進入 OFFLINE_MODE 並使用本地 Ollama。</div>
                            </div>
                        </label>
                    </div>
                </div>
            </div>

            <div className="mt-6 flex justify-end">
                <button 
                    onClick={handleSave} 
                    disabled={isSaving}
                    className="flex items-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white px-6 py-2 rounded-lg font-medium transition-colors disabled:opacity-50"
                >
                    <CheckCircleIcon className="w-5 h-5" />
                    {isSaving ? 'Saving...' : 'Save Fallback Settings'}
                </button>
            </div>
        </div>
    );
};
