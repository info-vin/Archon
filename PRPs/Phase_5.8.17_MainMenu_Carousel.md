# Phase 5.8.17: MainMenu Carousel Overhaul (主選單 3D 輪播重構)

## 狀態 (Status)
**🟢 已完成 (Completed)**

## 執行摘要 (Executive Summary)
本階段完成了 Godot 客戶端 (`recontextualization`) 主選單介面的全面升級，將原有的垂直按鈕選單徹底重構為極具賽博龐克風格的「實體卡牌水平圓型輪播 (Carousel)」介面。同時物理根除了場景跳轉的斷層問題，並大幅提升了輸入回饋 (SFX/VFX) 與聽覺體驗。

## 關鍵實作細節 (Key Implementations)

### 1. 斷層修復與生命週期對齊
* **斷點**：`TransitionVideo.tscn` 遺失了 `next_scene` 的指向，導致影片播完後畫面卡死。
* **修復**：直接在 `TransitionVideo.tscn` 中綁定 `ExtResource`，確保播完動畫後 100% 成功實例化並跳轉至 `GameBoard.tscn`。

### 2. 3D 水平輪播架構 (Carousel Integration)
* **組件置換**：移除 `VBoxContainer`，全面改用 `CarouselContainer` (設定為 `is_vertical = false`)。
* **座標與大小最佳化**：
  * 卡牌基礎尺寸定為 `240x336`。
  * 輪播中心點設定為偏左上方 (`offset_top = -500`, `offset_left = -700`)，以避開主視覺背景動畫的中央標題文字。
  * 調整 `ellipse_radius` 為 `(450, 100)`，使其呈現更完美的景深感。
* **圖示與多語系**：
  * 使用全新的 `gem_*.png` (如 `gem_new_career.png`) 作為卡牌內部寶石圖示。
  * 卡牌標題統一綁定 Translation Keys (如 `menu_continue`)，確保多語系切換時字串自動對齊。

### 3. 動態回饋與聽覺重構 (Juice & SFX)
* **實體抖動 (Elastic Shake)**：透過 `Tween` 實作卡牌被選中時的左右快速偏移，給予玩家極具彈性的點擊感。
* **輸入擴展**：透過 `_unhandled_input` 完美支援鍵盤 Left/Right 切換與 Enter 確認。
* **音效與音樂**：
  * 新增 `BGMPlayer` 自動播放 `Of Far Different Nature - Ganxta (CC-BY).ogg`。
  * 新增 `SFXClick` 於卡牌觸發時播放 `240776__f4ngy__card-flip_1.ogg`。

### 4. 系統設定選單降級
* 將「語言」與「音量」滑桿移至畫面右下角。
* 套用 40% 透明度的深色 `ColorRect` 背板，使其不干擾主畫面的輪播與背景動畫。

## 物理公證與測試 (Physical Verification)
1. 透過無頭環境的截圖腳本 (`tests/MainMenu_Screenshotter.gd`) 進行實體驗證。
2. 腳本成功延遲 6.5 秒等待開場動畫完成後擷取畫面，並模擬輸入 `ui_right` 後再次擷取，證實輪播旋轉邏輯正確，卡牌層級無重疊問題。
