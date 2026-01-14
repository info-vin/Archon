import React from 'react';

const SmartManufacturing: React.FC = () => {
    return (
        <div className="bg-white p-8 rounded-lg shadow-sm border border-border">
            <h1 className="text-3xl font-bold text-primary mb-6 border-b border-border pb-4">專案綜合說明 (v1.2)</h1>

            <div className="space-y-6">
                <div>
                    <h2 className="text-xl font-semibold text-primary mb-2">1. 專案目標</h2>
                    <p className="text-muted-foreground">
                        本專案旨在將多份圍繞「智慧製造與流程自動化」主題的 HTML 文件，整合成一個具備現代化風格、響應式設計、且易於導航的單一網頁儀表板。目標是提供一個清晰、連貫的視圖，讓使用者能方便地查閱從高階策略到技術細節的各項內容。
                    </p>
                </div>
                
                <div>
                    <h2 className="text-xl font-semibold text-primary mb-2">2. 主要功能與特色</h2>
                    <ul className="list-disc list-inside text-muted-foreground space-y-2">
                        <li><b>統一風格介面：</b>採用全新的色彩主題與雙欄佈局，提升整體視覺一致性與專業感。</li>
                        <li><b>可拖曳導航：</b>左側導航欄項目支援拖曳排序，使用者可根據自身偏好調整瀏覽順序，實現高度客製化。</li>
                        <li><b>響應式設計：</b>自動適應桌面、平板與手機螢幕，確保在所有設備上均有最佳瀏覽體驗。</li>
                        <li><b>模組化內容嵌入：</b>使用 `&lt;iframe&gt;` 嵌入各個獨立的互動圖表與文件，有效隔離樣式與腳本，便於日後獨立維護與更新。</li>
                        <li><b>整合說明文件：</b>將專案說明、文件關聯圖、技術需求等輔助文件一併整合至儀表板中，方便使用者一站式查閱所有相關資訊。</li>
                    </ul>
                </div>

                <div>
                    <h2 className="text-xl font-semibold text-primary mb-2">3. 儀表板內容結構</h2>
                    <p className="text-muted-foreground mb-3">儀表板的內容被劃分為以下幾個邏輯區塊，可透過左側導航欄訪問：</p>
                    <div className="grid md:grid-cols-2 gap-4">
                        <div className="bg-secondary p-4 rounded-lg border border-border">
                            <h3 className="font-bold text-foreground">智慧製造方案</h3>
                            <p className="text-sm text-muted-foreground">包含解決方案提案、技術核心、流程細節與導入效益，是本專案的核心主線。</p>
                        </div>
                        <div className="bg-secondary p-4 rounded-lg border border-border">
                            <h3 className="font-bold text-foreground">員工福祉策略</h3>
                            <p className="text-sm text-muted-foreground">一個獨立的解決方案簡報，展示了在員工福祉領域的策略規劃。</p>
                        </div>
                        <div className="bg-secondary p-4 rounded-lg border border-border col-span-full">
                            <h3 className="font-bold text-foreground">專案說明文件</h3>
                            <p className="text-sm text-muted-foreground">整合了本說明、文件關聯圖與技術需求列表，提供專案的元數據信息。</p>
                        </div>
                    </div>
                </div>
                
                <div>
                    <h2 className="text-xl font-semibold text-primary mb-2">4. 如何使用</h2>
                    <p className="text-muted-foreground">
                        點擊左側導航欄的項目，即可在右側內容區加載對應的內容。對於包含多個子項目的區塊（如「技術核心」），右側內容區會出現頁籤，供您切換查看。您可以按住導航項目並上下拖曳來改變它們的順序。
                    </p>
                </div>
            </div>
        </div>
    );
};

export default SmartManufacturing;
