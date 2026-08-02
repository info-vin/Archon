import React, { useState, useEffect } from 'react';
import { api } from '@/services/api.ts';
import { Employee, EmployeeRole } from '@/types.ts';
import { XIcon, CheckCircleIcon, KeyIcon, XCircleIcon } from '@/components/Icons.tsx';

// --- ROLE TO PERMISSION MAPPING (Sync with Backend permissions.py) ---
export const ROLE_PERMISSIONS_MAP: Record<string, string[]> = {
    "system_admin": ["task:*", "agent:*", "code:approve", "content:publish", "user:manage", "mcp:manage", "brand:manage"],
    "admin": ["task:*", "agent:*", "code:approve", "content:publish", "user:manage", "mcp:manage", "brand:manage"],
    "manager": ["task:create", "task:read:team", "agent:*", "code:approve", "content:publish", "stats:view:team", "user:manage:team"],
    "sales": ["task:create", "agent:trigger:mkt", "leads:view:all", "stats:view:own"],
    "marketing": ["task:create", "agent:trigger:mkt", "agent:trigger:know", "leads:view:all", "brand:manage"],
    "member": ["task:create", "task:read:own", "agent:trigger:know"],
    "viewer": ["task:read:own"]
};

export const IdentityEditUserModal: React.FC<{ user: Employee; onClose: () => void; onSave: (updatedUser: Employee) => void; }> = ({ user, onClose, onSave }) => {
    const [role, setRole] = useState(user.role);
    const [status, setStatus] = useState(user.status);
    const [overrides, setOverrides] = useState<Record<string, boolean>>(user.permission_overrides || {});
    const [allPermissions, setAllPermissions] = useState<string[]>([]);
    const [isSaving, setIsSaving] = useState(false);
    const inputClass = "appearance-none rounded-md relative block w-full px-3 py-2 border border-border placeholder-muted-foreground text-foreground bg-input focus:outline-none focus:ring-ring focus:border-ring focus:z-10 sm:text-sm";

    useEffect(() => {
        api.getSystemPermissions().then(setAllPermissions).catch(console.error);
    }, []);

    const togglePermission = (perm: string) => {
        const current = overrides[perm];
        const newOverrides = { ...overrides };
        
        if (current === undefined) {
            newOverrides[perm] = true;
        } else if (current === true) {
            newOverrides[perm] = false;
        } else {
            delete newOverrides[perm];
        }
        setOverrides(newOverrides);
    };

    const handleSave = async () => {
        setIsSaving(true);
        try {
            const updatedUser = await api.updateEmployee(user.id, { 
                role, 
                status, 
                permission_overrides: overrides 
            } as any);
            onSave(updatedUser);
            alert('User permissions synchronized successfully!');
            onClose();
        } catch(error: any) {
            alert(`Error updating user: ${error.message}`);
        } finally {
            setIsSaving(false);
        }
    };

    const rolePermissions = ROLE_PERMISSIONS_MAP[role.toLowerCase()] || ROLE_PERMISSIONS_MAP['viewer'];

    return (
         <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
            <div className="bg-card rounded-2xl shadow-xl w-full max-w-2xl p-6 relative animate-in fade-in zoom-in-95 duration-200 flex flex-col max-h-[90vh]">
                <div className="flex items-center gap-3 mb-4 shrink-0">
                    <KeyIcon className="w-6 h-6 text-primary" />
                    <h2 className="text-2xl font-bold italic">Access Overrides: {user.name}</h2>
                </div>
                <button onClick={onClose} aria-label="Close modal" className="absolute top-4 right-4 p-2 rounded-full hover:bg-muted transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"><XIcon className="w-6 h-6" /></button>
                
                <div className="space-y-6 overflow-y-auto pr-2 flex-1">
                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label htmlFor="role" className="block text-xs font-bold uppercase text-muted-foreground mb-1">Base Role</label>
                            <select id="role" value={role} onChange={e => setRole(e.target.value as EmployeeRole)} className={inputClass}>
                                {Object.values(EmployeeRole).map(r => <option key={r} value={r}>{r}</option>)}
                            </select>
                        </div>
                        <div>
                            <label htmlFor="status" className="block text-xs font-bold uppercase text-muted-foreground mb-1">Account Status</label>
                            <select id="status" value={status} onChange={e => setStatus(e.target.value as 'active' | 'inactive' | 'suspended')} className={inputClass}>
                                <option value="active">Active</option>
                                <option value="inactive">Inactive</option>
                                <option value="suspended">Suspended</option>
                            </select>
                        </div>
                    </div>

                    <div className="bg-muted/30 p-5 rounded-2xl border border-border">
                        <div className="flex justify-between items-end mb-4">
                            <div>
                                <h4 className="text-xs font-black uppercase text-indigo-600 dark:text-indigo-400 tracking-widest">Granular Access Control</h4>
                                <p className="text-[10px] text-muted-foreground italic mt-1">Tap capability to Grant (+ON), Revoke (-OFF), or Reset to Default.</p>
                            </div>
                        </div>
                        
                        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                            {allPermissions.map(perm => {
                                const overrideValue = overrides[perm];
                                const isInheritedOn = rolePermissions.includes(perm) || rolePermissions.includes(perm.split(':')[0] + ':*');
                                
                                let statusLabel = "Inherited";
                                let bgClass = "bg-background/50 border-border text-muted-foreground";
                                let icon = null;

                                if (overrideValue === true) {
                                    statusLabel = "GRANTED (+ON)";
                                    bgClass = "bg-green-50 border-green-200 text-green-700 dark:bg-green-900/20 dark:border-green-800 dark:text-green-400 font-bold";
                                    icon = <CheckCircleIcon className="w-3 h-3" />;
                                } else if (overrideValue === false) {
                                    statusLabel = "REVOKED (-OFF)";
                                    bgClass = "bg-red-50 border-red-200 text-red-700 dark:bg-red-900/20 dark:border-red-800 dark:text-red-400 font-bold opacity-70";
                                    icon = <XCircleIcon className="w-3 h-3" />;
                                } else if (isInheritedOn) {
                                    bgClass = "bg-indigo-50 border-indigo-100 text-indigo-700 dark:bg-indigo-900/20 dark:border-indigo-800 dark:text-indigo-300";
                                }

                                return (
                                    <button 
                                        key={perm}
                                        onClick={() => togglePermission(perm)}
                                        className={`flex flex-col p-2 rounded-xl border transition-all text-left group ${bgClass} hover:ring-2 ring-primary/20`}
                                    >
                                        <div className="flex justify-between items-center">
                                            <span className="text-[10px] font-mono truncate">{perm}</span>
                                            {icon}
                                        </div>
                                        <div className="text-[8px] uppercase tracking-tighter mt-1 opacity-60">
                                            {statusLabel} {overrideValue === undefined && (isInheritedOn ? '(Active)' : '(Inactive)')}
                                        </div>
                                    </button>
                                );
                            })}
                        </div>
                    </div>

                    <div className="flex justify-end space-x-3 pt-4 border-t border-border mt-4 shrink-0">
                        <button onClick={onClose} className="px-6 py-2 rounded-xl bg-secondary text-secondary-foreground hover:bg-secondary/80 font-bold transition-colors">Cancel</button>
                        <button onClick={handleSave} disabled={isSaving} className="px-6 py-2 rounded-xl bg-indigo-600 text-white hover:bg-indigo-700 transition-all font-black shadow-lg shadow-indigo-200 disabled:opacity-50">
                            {isSaving ? 'Syncing...' : 'APPLY ACCESS OVERRIDE'}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
};
