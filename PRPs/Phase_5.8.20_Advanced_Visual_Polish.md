# Phase 5.8.20 Advanced Visual Polish

## 目標 (Objective)
在完成基礎的 UI/UX 與 TDD 驗證後，我們針對使用者在遊玩過程中發現的「視覺認知斷層」與「排版缺陷」進行最後一哩路的精緻化打磨，達到真正可供玩家試玩 (Playtest-Ready) 的水準。

## 主要修復項目 (Key Fixes)

1. **HUD 與終端機 (AgentCompanion) 排版修正**
   - 將 AgentCompanion (代理人終端) 往下推移 20px (至 `offset_top = 160.0`)，徹底解決與頂部 HUD 的重疊問題。
   - 移除 `GameHUD.tscn` 中預設的硬編碼英文標籤 (如 `L3`, `SLA: 05:00`)，防止載入瞬間的語言閃爍。

2. **進度條底色與標籤中文化**
   - 為 HUD 中的 4 條進度條 (特務血量、純淨度、投毒率、系統危機) 分別掛載獨立暗色系、帶毛玻璃邊框的 `StyleBoxFlat`。
   - 補齊 `translations.csv` 中遺漏的 `hud_rank` 與 `hud_sla` 翻譯鍵，並在 `GameHUD.gd` 中將 SLA 顯示動態加上翻譯前綴 (`[SLA] 05:00`)。
   - 統一放大進度條內的標籤字體 (+5%) 以增加易讀性。

3. **實體卡牌展示**
   - 在自動化截圖/測試流程中，將 `mockup_sample_card.png` 替換為實際的 `action_keyword.png` 立繪，使新手教學與截圖展示更貼近真實遊戲體驗。
   - 補齊 `CardChip.tscn` 的 `pivot_offset`，修正手牌展開時的旋轉軸心。

4. **全域按鈕風格對齊與防呆機制**
   - 將 `GameBoard` 頂部的 4 個 Hub 導航按鈕從一般的 `Button` 重構為 `TextureButton`，並套用 `card_frame_blank.png`，使其與 `CharacterDashboard` 等子場景內部的「返回」按鈕視覺語言達到 100% 統一。
   - 同步修正 `GameBoard.gd` 內的強型別標註 (Type Hinting)，確保 TDD 自動化測試不因節點型別變更而崩潰。
   - 在 `PauseMenu` 中加入 `ConfirmationDialog` 雙重確認機制，防止玩家誤觸「返回主選單」或「離開遊戲」導致進度遺失。

## 視覺公證 (Visual Proof)
透過自動化截圖腳本產生了實機截圖，驗證了 `GameBoard` HUD 的修復以及 4 大 Hub 子場景的按鈕視覺統一性：

````carousel
![角色儀表板 (Character Dashboard)](/Users/vincenta/.gemini/antigravity/brain/5a96097b-d2b1-413f-bca7-2e7470174942/hub_1_CharacterDashboard.png)
<!-- slide -->
![卡牌管理 (Card Management)](/Users/vincenta/.gemini/antigravity/brain/5a96097b-d2b1-413f-bca7-2e7470174942/hub_2_CardManagementMenu.png)
<!-- slide -->
![合成中心 (Card Workshop)](/Users/vincenta/.gemini/antigravity/brain/5a96097b-d2b1-413f-bca7-2e7470174942/hub_3_CardWorkshop.png)
<!-- slide -->
![特務管理 (Teammate Dashboard)](/Users/vincenta/.gemini/antigravity/brain/5a96097b-d2b1-413f-bca7-2e7470174942/hub_4_TeammateDashboard.png)
````
