/**
 * 從字串生成一個顏色。
 * @param str 用於生成顏色的字串。
 * @returns 一個 HSL 顏色字串。
 */
export const stringToColor = (str: string): string => {
  let hash = 0;
  for (let i = 0; i < str.length; i++) {
    hash = str.charCodeAt(i) + ((hash << 5) - hash);
  }
  const h = hash % 360;
  // 使用固定的飽和度和亮度以保持外觀一致
  return `hsl(${h}, 70%, 40%)`; 
};
