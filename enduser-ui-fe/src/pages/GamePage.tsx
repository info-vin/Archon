import React from 'react';

const GamePage: React.FC = () => {
  return (
    <div className="container mx-auto px-4 py-8 flex flex-col items-center min-h-[90vh] justify-center bg-background text-foreground">
      <div className="w-full max-w-5xl mb-6 flex flex-col md:flex-row justify-between items-center gap-4">
        <div>
          <h1 className="text-3xl md:text-4xl font-extrabold text-primary tracking-tight" id="game-title">
            🎮 Archon: AI Card Battler
          </h1>
          <p className="text-muted-foreground mt-2 text-sm">
            TDD & MVC 模式開發的 AI 卡牌構建遊戲。卡牌數值將根據您本機最近的 Git Commit 記錄動態生成！
          </p>
        </div>
      </div>

      <div className="w-full max-w-5xl aspect-[16/10] overflow-hidden rounded-2xl border border-border bg-card/40 backdrop-blur-md shadow-2xl relative">
        <iframe
          src="/games/card-battler/index.html"
          title="Archon AI Card Battler Game"
          aria-labelledby="game-title"
          className="w-full h-full border-none bg-black"
          allow="autoplay"
        />
      </div>

      <div className="w-full max-w-5xl mt-6 p-4 rounded-xl border border-border/40 bg-secondary/20 text-xs text-muted-foreground leading-relaxed">
        <p className="font-semibold text-foreground mb-1">💡 如何在本機啟動遊戲？</p>
        <ol className="list-decimal pl-4 space-y-1">
          <li>
            使用 Godot 4.x 開啟目錄下的 <code className="text-primary font-mono">recontextualization</code> 專案。
          </li>
          <li>
            至選單選取 <strong>Project &gt; Export...</strong>，新增 <strong>Web</strong> 預設。
          </li>
          <li>
            匯出路徑指定為：<code className="text-primary font-mono">enduser-ui-fe/public/games/card-battler/index.html</code>。
          </li>
          <li>
            完成後重新整理此頁面，即可在此處直接開玩！
          </li>
        </ol>
      </div>
    </div>
  );
};

export default GamePage;
