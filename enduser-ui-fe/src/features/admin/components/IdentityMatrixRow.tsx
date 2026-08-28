import React from 'react';
import { Employee, EmployeeRole } from '@/types.ts';
import UserAvatar from '@/components/UserAvatar.tsx';

interface IdentityMatrixRowProps {
    emp: Employee;
    isSelected: boolean;
    onToggleSelect: (id: string) => void;
    onEdit: (emp: Employee) => void;
    effectivePermissions: string[];
}

export const IdentityMatrixRow: React.FC<IdentityMatrixRowProps> = React.memo(({
    emp,
    isSelected,
    onToggleSelect,
    onEdit,
    effectivePermissions
}) => {
    const statusClasses = {
        active: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
        inactive: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
        suspended: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400'
    };
    const rowClasses = isSelected ? 'bg-primary/5' : 'hover:bg-muted/30';

    return (
        <React.Fragment>
            <tr 
                role="button"
                tabIndex={0}
                onClick={() => onToggleSelect(emp.id)}
                onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') onToggleSelect(emp.id); }}
                className={`cursor-pointer transition-colors ${rowClasses}`}
                aria-expanded={isSelected}
            >
                <td className="px-6 py-4 whitespace-nowrap min-w-0">
                    <div className="flex items-center min-w-0">
                        <UserAvatar name={emp.name || ''} role={emp.role} className="h-10 w-10 rounded-lg shadow-sm shrink-0" />
                        <div className="ml-4 min-w-0">
                            <div className="text-sm font-bold truncate">{emp.name}</div>
                            <div className="text-xs text-muted-foreground truncate">{emp.email}</div>
                        </div>
                    </div>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                    <span className="text-[10px] font-bold uppercase tracking-tight bg-secondary px-2 py-1 rounded border border-border">{emp.role}</span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap">
                    <span className={`px-2 py-1 inline-flex text-[10px] leading-4 font-bold uppercase tracking-widest rounded-full ${statusClasses[emp.status as keyof typeof statusClasses] || statusClasses.inactive}`}>
                        {emp.status}
                    </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                    <button 
                        onClick={(e) => { e.stopPropagation(); onEdit(emp); }}
                        className="text-primary hover:text-primary/90 font-bold transition-colors disabled:opacity-30" 
                        disabled={emp.role === EmployeeRole.SYSTEM_ADMIN}
                    >
                        Edit
                    </button>
                </td>
            </tr>
            {isSelected && (
                <tr className="bg-muted/10">
                    <td colSpan={4} className="px-6 py-4 border-b border-border">
                        <div className="flex flex-wrap gap-2">
                            <span className="text-[10px] font-bold text-muted-foreground uppercase mr-2">Effective Permissions:</span>
                            {effectivePermissions.map((p: string) => (
                                <span key={p} className="px-2 py-0.5 bg-background border border-border rounded text-[9px] font-mono text-muted-foreground italic">
                                    {p}
                                </span>
                            ))}
                        </div>
                    </td>
                </tr>
            )}
        </React.Fragment>
    );
});
