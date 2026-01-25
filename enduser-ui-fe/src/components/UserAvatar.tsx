import React from 'react';
import { stringToColor } from '../lib/utils';

interface UserAvatarProps {
  name: string;
  size?: number; // 頭像的大小（可選）
  isAI?: boolean; // 是否為 AI Agent
  className?: string; // 允許傳入自定義樣式
}

const UserAvatar: React.FC<UserAvatarProps> = ({ name, size = 40, isAI = false, className = '' }) => {
  const initial = name ? name.charAt(0).toUpperCase() : '?';
  const color = name ? stringToColor(name) : '#888888';

  const baseStyle: React.CSSProperties = {
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    // 如果 className 中沒有指定寬高，則使用 size
    width: className.includes('w-') ? undefined : `${size}px`,
    height: className.includes('h-') ? undefined : `${size}px`,
    color: '#ffffff',
    fontSize: `${size * 0.5}px`,
    fontWeight: 'bold',
    fontFamily: 'sans-serif',
  };

  const aiStyle: React.CSSProperties = {
    ...baseStyle,
    borderRadius: '8px', // 方形帶圓角
    backgroundColor: '#5A5A5A', // AI 固定用灰色
  };

  const userStyle: React.CSSProperties = {
    ...baseStyle,
    borderRadius: '50%', // 圓形
    backgroundColor: color,
  };

  return (
    <div className={className} style={isAI ? aiStyle : userStyle} title={name}>
      {isAI ? 'A' : initial}
    </div>
  );
};

export default UserAvatar;