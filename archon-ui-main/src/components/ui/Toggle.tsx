import React from 'react';
import '../../styles/toggle.css';
interface ToggleProps {
  checked: boolean;
  onCheckedChange: (checked: boolean) => void;
  accentColor?: 'purple' | 'green' | 'pink' | 'blue' | 'orange';
  icon?: React.ReactNode;
  disabled?: boolean;
  ariaLabel?: string;
}
export const Toggle: React.FC<ToggleProps> = ({
  checked,
  onCheckedChange,
  accentColor = 'blue',
  icon,
  disabled = false,
  ariaLabel
}) => {
  const handleClick = () => {
    if (!disabled) {
      onCheckedChange(!checked);
    }
  };
  return <button role="switch" aria-checked={checked} aria-label={ariaLabel || "Toggle"} onClick={handleClick} disabled={disabled} className={`
        toggle-switch
        ${checked ? 'toggle-checked' : ''}
        ${disabled ? 'toggle-disabled' : ''}
        toggle-${accentColor}
      `}>
      <div className="toggle-thumb">
        {icon && <div className="toggle-icon">{icon}</div>}
      </div>
    </button>;
};