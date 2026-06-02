import { useState, useEffect, RefObject } from 'react';

export function usePanelResize(chatPanelRef: RefObject<HTMLDivElement | null>) {
  const [width, setWidth] = useState(416); // Default width - increased by 30% from 320px
  const [isDragging, setIsDragging] = useState(false);

  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (isDragging && chatPanelRef.current) {
        const containerRect = chatPanelRef.current.parentElement?.getBoundingClientRect();
        if (containerRect) {
          const newWidth = window.innerWidth - e.clientX;
          if (newWidth >= 280 && newWidth <= 600) {
            setWidth(newWidth);
          }
        }
      }
    };

    const handleMouseUp = () => {
      setIsDragging(false);
      document.body.style.cursor = 'default';
      document.body.style.userSelect = 'auto';
    };

    if (isDragging) {
      document.addEventListener('mousemove', handleMouseMove);
      document.addEventListener('mouseup', handleMouseUp);
      document.body.style.cursor = 'ew-resize';
      document.body.style.userSelect = 'none';
    }

    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isDragging, chatPanelRef]);

  const handleDragStart = (e: React.MouseEvent) => {
    e.preventDefault();
    setIsDragging(true);
  };

  return {
    width,
    isDragging,
    handleDragStart
  };
}
