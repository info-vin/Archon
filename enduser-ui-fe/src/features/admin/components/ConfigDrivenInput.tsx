import React from 'react';
import { RefreshCwIcon } from '../../../components/Icons.tsx';

interface FieldConfig {
    key: string;
    type: string;
    label?: string;
    placeholder?: string;
    options?: { value: string; label: string }[];
    min?: number;
    max?: number;
}

interface ConfigDrivenInputProps {
    field: FieldConfig;
    value: any;
    onChange?: (val: any) => void;
    onBlur?: (val: any) => void;
    isSaving?: boolean;
    className?: string;
}

export const ConfigDrivenInput: React.FC<ConfigDrivenInputProps> = ({ 
    field, value, onChange, onBlur, isSaving, className 
}) => {
    // Local state allows the input to visibly update even when only `onBlur` is provided
    const [localValue, setLocalValue] = React.useState<any>(value ?? '');

    // Sync from props if external value changes (unless we are typing and it's temporary)
    // For simplicity, we sync when the incoming value differs from local state
    React.useEffect(() => {
        if (value !== undefined && value !== null) {
            setLocalValue(value);
        }
    }, [value]);

    const handleChange = (e: React.ChangeEvent<any>) => {
        const val = e.target.value;
        setLocalValue(val);
        
        if (onChange) {
            const parsedVal = field.type === 'number' && val !== '' ? (parseFloat(val) || 0) : val;
            onChange(parsedVal);
        }
    };

    const handleBlur = (e: React.FocusEvent<any>) => {
        if (onBlur) {
            const val = e.target.value;
            const parsedVal = field.type === 'number' && val !== '' ? (parseFloat(val) || 0) : val;
            onBlur(parsedVal);
        }
    };

    const baseInputClass = `bg-background border border-border rounded-lg outline-none focus:ring-2 transition-all ${className || 'p-2 w-full text-sm'}`;

    return (
        <div className="relative flex-1 flex items-center">
            {field.type === 'select' ? (
                <select 
                    value={localValue}
                    onChange={handleChange}
                    onBlur={handleBlur}
                    className={baseInputClass}
                >
                    {field.options?.map(opt => <option key={opt.value} value={opt.value}>{opt.label}</option>)}
                </select>
            ) : field.type === 'textarea' ? (
                <textarea 
                    value={localValue}
                    onChange={handleChange}
                    onBlur={handleBlur}
                    className={baseInputClass}
                    placeholder={field.placeholder}
                />
            ) : (
                <input 
                    type={field.type} 
                    value={localValue}
                    onChange={handleChange}
                    onBlur={handleBlur}
                    placeholder={field.placeholder}
                    min={field.min}
                    max={field.max}
                    className={baseInputClass}
                />
            )}
            
            {isSaving && (
                <div className="absolute -top-1 -right-1">
                    <RefreshCwIcon className="animate-spin w-3 h-3 text-primary" />
                </div>
            )}
        </div>
    );
};
