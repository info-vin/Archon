import React from 'react';
import '../../styles/toggle.css';
interface ToggleProps {
  checked: boolean;
  onCheckedChange: (checked: boolean) => void;
  accentColor?: 'purple' | 'green' | 'pink' | 'blue' | 'orange';
  icon?: React.ReactNode;
  disabled?: boolean;
  'aria-label'?: string;
  id?: string;
}
export const Toggle: React.FC<ToggleProps> = ({
  checked,
  onCheckedChange,
  accentColor = 'blue',
  icon,
  disabled = false,
  'aria-label': ariaLabel,
  id
}) => {
  const handleClick = () => {
    if (!disabled) {
      onCheckedChange(!checked);
    }
  };
  return <button id={id} role="switch" aria-checked={checked} aria-label={ariaLabel} onClick={handleClick} disabled={disabled} className={`
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