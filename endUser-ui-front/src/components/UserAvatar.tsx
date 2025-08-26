import React from 'react';
import { stringToColor } from '../lib/utils';

interface UserAvatarProps {
  name: string;
  size?: number; // 頭像的大小（可選）
}

const UserAvatar: React.FC<UserAvatarProps> = ({ name, size = 40 }) => {
  const initial = name ? name.charAt(0).toUpperCase() : '?';
  const color = name ? stringToColor(name) : '#888888';

  const avatarStyle: React.CSSProperties = {
    display: 'inline-flex',
    alignItems: 'center',
    justifyContent: 'center',
    borderRadius: '50%',
    width: `${size}px`,
    height: `${size}px`,
    backgroundColor: color,
    color: '#ffffff',
    fontSize: `${size * 0.5}px`,
    fontWeight: 'bold',
    fontFamily: 'sans-serif',
  };

  return (
    <div style={avatarStyle} title={name}>
      {initial}
    </div>
  );
};

export default UserAvatar;
