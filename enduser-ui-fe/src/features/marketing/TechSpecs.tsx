import React from 'react';

const TechSpecs: React.FC = () => {
    return (
        <div className="bg-white p-8 rounded-lg shadow-sm border border-border">
            <h1 className="text-3xl font-bold text-center mb-8 text-primary">專案技術與套件需求</h1>
            
            <div className="mb-10">
                <h2 className="text-2xl font-semibold mb-4 pb-2 border-b-2 border-blue-500 text-blue-700">JavaScript 函式庫與工具</h2>
                <ul className="list-disc list-inside space-y-3 text-muted-foreground">
                    <li>
                        <strong>Sortable.js:</strong>
                        <p className="ml-6 text-sm text-gray-500">一個輕量級的 JavaScript 函式庫，用於實現拖曳排序功能。在主儀表板的左側導航欄中使用，讓用戶可以自訂導航項目順序。</p>
                    </li>
                    <li>
                        <strong>Chart.js:</strong>
                        <p className="ml-6 text-sm text-gray-500">用於繪製互動式圖表，如長條圖、雷達圖、甜甜圈圖。在 `SAS智慧製造解決方案互動儀表板.html` 和 `RPA_canvas.html` 中被大量使用，以視覺化數據與效益。</p>
                    </li>
                    <li>
                        <strong>Mermaid.js:</strong>
                        <p className="ml-6 text-sm text-gray-500">用於從文本生成圖表和流程圖，如時序圖、甘特圖。在 `RPA_sas.html` 等提案文件中用於展示專案時程與系統互動流程。</p>
                    </li>
                     <li>
                        <strong>jQuery:</strong>
                        <p className="ml-6 text-sm text-gray-500">一個傳統的 JavaScript 函式庫，用於簡化 DOM 操作與事件處理。在 `製造業智慧排程與人力資源管理解決方案提案.html` (HackMD 匯出文件) 中被使用。</p>
                    </li>
                </ul>
            </div>

            <div className="mb-10">
                <h2 className="text-2xl font-semibold mb-4 pb-2 border-b-2 border-green-500 text-green-700">CSS 框架與函式庫</h2>
                <ul className="list-disc list-inside space-y-3 text-muted-foreground">
                    <li>
                        <strong>Tailwind CSS:</strong>
                        <p className="ml-6 text-sm text-gray-500">一個功能優先的 CSS 框架，用於快速建構現代化、響應式的網頁介面。在 `SAS智慧製造解決方案互動儀表板.html` 和 `RPA_canvas.html` 等多個核心頁面中作為主要的樣式工具。</p>
                    </li>
                     <li>
                        <strong>Bootstrap:</strong>
                        <p className="ml-6 text-sm text-gray-500">一個常見的前端框架，提供預設的 UI 元件。在 `製造業智慧排程與人力資源管理解決方案提案.html` (HackMD 匯出文件) 中被使用。</p>
                    </li>
                </ul>
            </div>

            <div className="mb-10">
                <h2 className="text-2xl font-semibold mb-4 pb-2 border-b-2 border-purple-500 text-purple-700">字體 (Fonts)</h2>
                <ul className="list-disc list-inside space-y-3 text-muted-foreground">
                    <li>
                        <strong>Google Fonts (Noto Sans TC, Murecho):</strong>
                        <p className="ml-6 text-sm text-gray-500">透過 Google Fonts 服務引入，用於改善網頁的中文與英文字體顯示效果，提升閱讀體驗。</p>
                    </li>
                </ul>
            </div>
            
            <div>
                <h2 className="text-2xl font-semibold mb-4 pb-2 border-b-2 border-red-500 text-red-700">外部資源</h2>
                <ul className="list-disc list-inside space-y-3 text-muted-foreground">
                    <li>
                        <strong>Unsplash:</strong>
                        <p className="ml-6 text-sm text-gray-500">在 `Employee Well-being Strategy Upgrade Plan.html` 中作為背景圖片的來源，提供高品質的免費圖片。</p>
                    </li>
                </ul>
            </div>
        </div>
    );
};

export default TechSpecs;
