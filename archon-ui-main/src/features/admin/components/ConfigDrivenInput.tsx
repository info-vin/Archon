import React from 'react';
import { Loader } from 'lucide-react';

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
    onChange?: (val: any, key?: string) => void;
    onBlur?: (val: any, key?: string) => void;
    isSaving?: boolean;
    className?: string;
}

export const ConfigDrivenInput: React.FC<ConfigDrivenInputProps> = ({ 
    field, value, onChange, onBlur, isSaving, className 
}) => {
    const handleChange = (e: React.ChangeEvent<any>) => {
        const newVal = field.type === 'number' ? (Number(e.target.value) || 0) : e.target.value;
        if (onChange) onChange(newVal, field.key);
    };

    const handleBlur = (e: React.FocusEvent<any>) => {
        const newVal = field.type === 'number' ? (Number(e.target.value) || 0) : e.target.value;
        if (onBlur) onBlur(newVal, field.key);
    };

    const baseInputClass = `bg-background border border-border rounded-lg outline-none focus:ring-2 transition-all ${className || 'p-2 w-full text-sm'}`;

    return (
        <div className="relative flex-1 flex items-center">
            {field.type === 'select' ? (
                <select 
                    value={value || ''}
                    onChange={handleChange}
                    onBlur={handleBlur}
                    className={baseInputClass}
                >
                    {field.options?.map(opt => <option key={opt.value} value={opt.value}>{opt.label}</option>)}
                </select>
            ) : field.type === 'textarea' ? (
                <textarea 
                    value={value || ''}
                    onChange={handleChange}
                    onBlur={handleBlur}
                    className={baseInputClass}
                    placeholder={field.placeholder}
                />
            ) : (
                <input 
                    type={field.type} 
                    value={value ?? ''}
                    onChange={handleChange}
                    onBlur={handleBlur}
                    placeholder={field.placeholder}
                    min={field.min}
                    max={field.max}
                    className={baseInputClass}
                />
            )}
            
            {isSaving && (
                    <Loader className="animate-spin w-3 h-3 text-primary" />
            )}
        </div>
    );
};
