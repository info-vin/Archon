import React from 'react';
import { stringToColor } from '../lib/utils';

interface UserAvatarProps {
  name: string;
  size?: number; // 頭像的大小（可選）
  isAI?: boolean; // 是否為 AI Agent
  role?: string; // 用於決定背景顏色
  className?: string; // 允許傳入自定義樣式
}

const getRoleColor = (role?: string) => {
    if (!role) return null;
    const r = role.toLowerCase().trim();
    if (['admin', 'system_admin'].includes(r)) return '#DC2626'; // Red-600
    if (['sales', 'sales_rep'].includes(r)) return '#2563EB'; // Blue-600
    if (['marketing', 'brand'].includes(r)) return '#D97706'; // Amber-600
    if (['manager'].includes(r)) return '#7C3AED'; // Violet-600
    if (['manager'].includes(r)) return '#7C3AED'; // Violet-600
    // Agents now use Hash Color for distinctiveness
    return null;
};

const UserAvatar: React.FC<UserAvatarProps> = ({ name, size = 40, isAI = false, role, className = '' }) => {
  const initial = name ? name.charAt(0).toUpperCase() : '?';
  
  // Priority: Role Color > AI Color > Hash Color
  const roleColor = getRoleColor(role);
  const hashColor = name ? stringToColor(name) : '#888888';
  // Rule: Humans = Role Color, Bots = Hash Color (Distinct). 
  // If roleColor exists (Humans), use it. Otherwise (Bots/Unknown), use hashColor.
  const finalColor = roleColor || hashColor;

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
    borderRadius: className.includes('rounded') ? undefined : '8px', // Default to Square (8px) unless overridden
    backgroundColor: finalColor,
  };

  return (
    <div className={className} style={baseStyle} title={name}>
      {isAI ? 'A' : initial}
    </div>
  );
};

export default UserAvatar;