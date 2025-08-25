import React, { useMemo } from 'react';

const Avatar: React.FC<{ src?: string; name: string; className?: string }> = ({ src, name, className }) => {
    const getInitials = (name: string) => {
        const names = name.split(' ');
        if (names.length > 1) {
            return `${names[0][0]}${names[names.length - 1][0]}`.toUpperCase();
        }
        return name.substring(0, 2).toUpperCase();
    };

    const colors = ['bg-red-500', 'bg-green-500', 'bg-blue-500', 'bg-yellow-500', 'bg-indigo-500', 'bg-purple-500', 'bg-pink-500'];
    const color = useMemo(() => colors[name.length % colors.length], [name]);

    if (src) {
        return <img src={src} alt={name} className={`w-10 h-10 rounded-full object-cover ${className}`} />;
    }

    return (
        <div className={`w-10 h-10 rounded-full flex items-center justify-center text-white font-bold ${color} ${className}`}>
            {getInitials(name)}
        </div>
    );
};

export default Avatar;