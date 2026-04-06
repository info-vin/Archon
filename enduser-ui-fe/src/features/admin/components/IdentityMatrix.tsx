import React, { useState, useEffect } from 'react';
import { api } from '@/services/api.ts';
import { Employee, EmployeeRole } from '@/types.ts';
import { PlusIcon, XIcon, CheckCircleIcon, KeyIcon, XCircleIcon } from '@/components/Icons.tsx';
import UserAvatar from '@/components/UserAvatar.tsx';

// --- ROLE TO PERMISSION MAPPING (Sync with Backend permissions.py) ---
const ROLE_PERMISSIONS_MAP: Record<string, string[]> = {
    "system_admin": ["task:*", "agent:*", "code:approve", "content:publish", "user:manage", "mcp:manage", "brand:manage"],
    "admin": ["task:*", "agent:*", "code:approve", "content:publish", "user:manage", "mcp:manage", "brand:manage"],
    "manager": ["task:create", "task:read:team", "agent:*", "code:approve", "content:publish", "stats:view:team", "user:manage:team"],
    "sales": ["task:create", "agent:trigger:mkt", "leads:view:all", "stats:view:own"],
    "marketing": ["task:create", "agent:trigger:mkt", "agent:trigger:know", "leads:view:all", "brand:manage"],
    "member": ["task:create", "task:read:own", "agent:trigger:know"],
    "viewer": ["task:read:own"]
};

// --- SUB-COMPONENTS ---

const EditUserModal: React.FC<{ user: Employee; onClose: () => void; onSave: (updatedUser: Employee) => void; }> = ({ user, onClose, onSave }) => {
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
            // State 1: Default -> Override to True (Grant)
            newOverrides[perm] = true;
        } else if (current === true) {
            // State 2: True -> Override to False (Revoke)
            newOverrides[perm] = false;
        } else {
            // State 3: False -> Back to Default (Remove Override)
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
                <button onClick={onClose} aria-label="Close modal" className="absolute top-4 right-4 p-2 rounded-full hover:bg-muted transition-colors"><XIcon className="w-6 h-6" /></button>
                
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

                    {/* Granular Permission Overrides */}
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

const NewUserModal: React.FC<{ onClose: () => void; onSave: (newUser: Employee) => void; }> = ({ onClose, onSave }) => {
    const [name, setName] = useState('');
    const [email, setEmail] = useState('');
    const [password, setPassword] = useState('');
    const [role, setRole] = useState<EmployeeRole>(EmployeeRole.MEMBER);
    const [status, setStatus] = useState<'active' | 'inactive' | 'suspended'>('active');
    const [isLoading, setIsLoading] = useState(false);

    const inputClass = "appearance-none rounded-md relative block w-full px-3 py-2 border border-border placeholder-muted-foreground text-foreground bg-input focus:outline-none focus:ring-ring focus:border-ring focus:z-10 sm:text-sm";
    
    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);
        try {
            const newUser = await api.adminCreateUser({ name, email, password, role, status });
            onSave(newUser);
            alert('User created successfully!');
            onClose();
        } catch (error: any) {
            alert(`Error creating user: ${error.message}`);
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
            <div className="bg-card rounded-2xl shadow-xl w-full max-lg p-6 relative animate-in fade-in zoom-in-95 duration-200">
                <h2 className="text-2xl font-bold mb-4">Create New User</h2>
                <button onClick={onClose} aria-label="Close modal" className="absolute top-4 right-4 p-2 rounded-full hover:bg-muted transition-colors"><XIcon className="w-6 h-6" /></button>
                <form onSubmit={handleSubmit} className="space-y-4">
                    <input type="text" placeholder="Full Name" value={name} onChange={e => setName(e.target.value)} className={inputClass} required />
                    <input type="email" placeholder="Email Address" value={email} onChange={e => setEmail(e.target.value)} className={inputClass} required />
                    <input type="password" placeholder="Password" value={password} onChange={e => setPassword(e.target.value)} className={inputClass} required />
                    <div>
                        <label htmlFor="role-new" className="block text-sm font-medium mb-1">Role Assignment</label>
                        <select id="role-new" value={role} onChange={e => setRole(e.target.value as EmployeeRole)} className={inputClass}>
                            {Object.values(EmployeeRole).map(r => <option key={r} value={r}>{r}</option>)}
                        </select>
                    </div>
                     <div>
                        <label htmlFor="status-new" className="block text-sm font-medium mb-1">Status</label>
                        <select id="status-new" value={status} onChange={e => setStatus(e.target.value as 'active' | 'inactive' | 'suspended')} className={inputClass}>
                            <option value="active">Active</option>
                            <option value="inactive">Inactive</option>
                            <option value="suspended">Suspended</option>
                        </select>
                    </div>
                    <div className="flex justify-end space-x-2 pt-4 border-t border-border mt-4">
                        <button type="button" onClick={onClose} className="px-4 py-2 rounded-md bg-secondary text-secondary-foreground hover:bg-secondary/80 transition-colors">Cancel</button>
                        <button type="submit" disabled={isLoading} className="px-4 py-2 rounded-md bg-primary text-primary-foreground hover:bg-primary/90 disabled:opacity-50 transition-all font-bold">{isLoading ? 'Creating...' : 'Create User'}</button>
                    </div>
                </form>
            </div>
        </div>
    );
};

// --- IDENTITY MATRIX COMPONENT ---

export const IdentityMatrix: React.FC = () => {
    const [employees, setEmployees] = useState<Employee[]>([]);
    const [rbacMatrix, setRBACMatrix] = useState<any[]>([]);
    const [allPermissions, setAllPermissions] = useState<string[]>([]);
    const [activeTab, setActiveTab] = useState<'personnel' | 'matrix'>('personnel');
    const [editingUser, setEditingUser] = useState<Employee | null>(null);
    const [isNewUserModalOpen, setIsNewUserModalOpen] = useState(false);
    const [loading, setLoading] = useState(true);
    const [selectedUserId, setSelectedUserId] = useState<string | null>(null);
    const [isSavingMatrix, setIsSavingMatrix] = useState(false);

    useEffect(() => {
        setLoading(true);
        Promise.all([
            api.getEmployees(),
            api.getRBACMatrix(),
            api.getSystemPermissions()
        ]).then(([emps, matrix, perms]) => {
            setEmployees(emps);
            setRBACMatrix(matrix);
            setAllPermissions(perms);
        }).catch(err => alert(`Failed to load Identity data: ${err.message}`))
          .finally(() => setLoading(false));
    }, []);

    const handleUpdateUserInList = (updatedUser: Employee) => {
        setEmployees(employees.map(e => e.id === updatedUser.id ? updatedUser : e));
    };

    const handleAddNewUserToList = (newUser: Employee) => {
        setEmployees(prev => [...prev, newUser]);
    };

    const toggleMatrixPermission = (roleName: string, permission: string) => {
        const updatedMatrix = rbacMatrix.map(item => {
            if (item.role === roleName) {
                const currentPerms = item.permissions || [];
                const newPerms = currentPerms.includes(permission)
                    ? currentPerms.filter((p: string) => p !== permission)
                    : [...currentPerms, permission];
                return { ...item, permissions: newPerms };
            }
            return item;
        });
        setRBACMatrix(updatedMatrix);
    };

    const saveMatrixChanges = async () => {
        setIsSavingMatrix(true);
        try {
            // Save each changed role (Simplified for MVP: save all current state)
            for (const row of rbacMatrix) {
                await api.updateRBACRole(row.role, row.permissions, row.description);
            }
            alert('RBAC Matrix saved successfully!');
        } catch (error: any) {
            alert(`Error saving matrix: ${error.message}`);
        } finally {
            setIsSavingMatrix(false);
        }
    };

    if (loading) return <div className="p-12 text-center text-muted-foreground italic">Loading Identity Matrix...</div>;

    const getPermissionsForRole = (roleName: string) => {
        const row = rbacMatrix.find(r => r.role.toLowerCase() === roleName.toLowerCase());
        return row ? row.permissions : [];
    };

    return (
        <div className="space-y-6">
            {/* Tab Navigation */}
            <div className="flex space-x-1 bg-muted/50 p-1 rounded-xl w-fit border border-border">
                <button 
                    onClick={() => setActiveTab('personnel')}
                    className={`px-4 py-2 rounded-lg text-xs font-bold transition-all ${activeTab === 'personnel' ? 'bg-background shadow-sm text-primary' : 'text-muted-foreground hover:text-foreground'}`}
                >
                    Personnel List
                </button>
                <button 
                    onClick={() => setActiveTab('matrix')}
                    className={`px-4 py-2 rounded-lg text-xs font-bold transition-all ${activeTab === 'matrix' ? 'bg-background shadow-sm text-primary' : 'text-muted-foreground hover:text-foreground'}`}
                >
                    Role Permissions Matrix
                </button>
            </div>

            {activeTab === 'personnel' ? (
                <div className="bg-card p-6 rounded-2xl border border-border shadow-sm">
                    <div className="flex justify-between items-center mb-6">
                        <div>
                            <h2 className="text-xl font-bold">Personnel Registry</h2>
                            <p className="text-xs text-muted-foreground">Manage system access levels and sync metadata for all personnel.</p>
                        </div>
                         <button onClick={() => setIsNewUserModalOpen(true)} className="flex items-center px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 font-bold transition-all shadow-sm">
                            <PlusIcon className="w-5 h-5 mr-2" />
                            NEW USER
                        </button>
                    </div>
                    <div className="overflow-x-auto -mx-6">
                        <table className="min-w-full divide-y divide-border">
                            <thead className="bg-muted/50">
                                <tr>
                                    <th className="px-6 py-3 text-left text-xs font-bold uppercase tracking-wider text-muted-foreground">Personnel</th>
                                    <th className="px-6 py-3 text-left text-xs font-bold uppercase tracking-wider text-muted-foreground">Assigned Role</th>
                                    <th className="px-6 py-3 text-left text-xs font-bold uppercase tracking-wider text-muted-foreground">Account Status</th>
                                    <th className="px-6 py-3 text-left text-xs font-bold uppercase tracking-wider text-muted-foreground text-right">Actions</th>
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-border bg-card">
                                {employees.filter(e => e && e.id).map(emp => {
                                    const isSelected = selectedUserId === emp.id;
                                    const statusClasses = {
                                        active: 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400',
                                        inactive: 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400',
                                        suspended: 'bg-amber-100 text-amber-700 dark:bg-amber-900/30 dark:text-amber-400'
                                    };
                                    const rowClasses = isSelected ? 'bg-primary/5' : 'hover:bg-muted/30';

                                    return (
                                        <React.Fragment key={emp.id}>
                                            <tr 
                                                role="button"
                                                tabIndex={0}
                                                onClick={() => setSelectedUserId(isSelected ? null : emp.id)}
                                                onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') setSelectedUserId(isSelected ? null : emp.id); }}
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
                                                    onClick={(e) => { e.stopPropagation(); setEditingUser(emp); }} 
                                                    className="text-primary hover:text-primary/90 font-bold transition-colors disabled:opacity-30" 
                                                    disabled={emp.role === EmployeeRole.SYSTEM_ADMIN}
                                                >
                                                    Edit
                                                </button>
                                            </td>
                                        </tr>
                                        {selectedUserId === emp.id && (
                                            <tr className="bg-muted/10">
                                                <td colSpan={4} className="px-6 py-4 border-b border-border">
                                                    <div className="flex flex-wrap gap-2">
                                                        <span className="text-[10px] font-bold text-muted-foreground uppercase mr-2">Effective Permissions:</span>
                                                        {getPermissionsForRole(emp.role).map((p: string) => (
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
                            })}
                            </tbody>
                        </table>
                    </div>
                </div>
            ) : (
                /* Dynamic RBAC Matrix Tab */
                <div className="bg-card p-6 rounded-2xl border border-border shadow-sm">
                    <div className="flex justify-between items-center mb-6">
                        <div>
                            <h2 className="text-xl font-bold">Role Capabilities Matrix</h2>
                            <p className="text-xs text-muted-foreground">Define what each role is permitted to do across the entire system.</p>
                        </div>
                        <button 
                            onClick={saveMatrixChanges} 
                            disabled={isSavingMatrix}
                            className="flex items-center px-6 py-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 font-bold transition-all shadow-lg shadow-indigo-100 disabled:opacity-50"
                        >
                            {isSavingMatrix ? 'SAVING...' : 'SAVE MATRIX'}
                        </button>
                    </div>

                    <div className="overflow-x-auto -mx-6">
                        <table className="min-w-full divide-y divide-border">
                            <thead className="bg-muted/50">
                                <tr>
                                    <th className="px-6 py-3 text-left text-[10px] font-black uppercase tracking-widest text-muted-foreground sticky left-0 bg-muted/50 z-10">Permission / Role</th>
                                    {rbacMatrix.map(row => (
                                        <th key={row.role} className="px-4 py-3 text-center text-[10px] font-black uppercase tracking-widest text-primary min-w-[100px]">
                                            {row.role}
                                        </th>
                                    ))}
                                </tr>
                            </thead>
                            <tbody className="divide-y divide-border bg-card">
                                {allPermissions.map(perm => (
                                    <tr key={perm} className="hover:bg-muted/20 transition-colors">
                                        <td className="px-6 py-3 whitespace-nowrap text-[10px] font-mono font-bold text-foreground sticky left-0 bg-card z-10 border-r border-border">
                                            {perm}
                                        </td>
                                        {rbacMatrix.map(row => {
                                            const hasPerm = (row.permissions || []).includes(perm);
                                            return (
                                                <td key={`${row.role}-${perm}`} className="px-4 py-3 text-center">
                                                    <button 
                                                        onClick={() => toggleMatrixPermission(row.role, perm)}
                                                        className={`w-6 h-6 rounded-md border flex items-center justify-center mx-auto transition-all ${hasPerm ? 'bg-green-500 border-green-600 text-white' : 'bg-background border-border text-transparent hover:border-primary/50'}`}
                                                    >
                                                        {hasPerm && <CheckCircleIcon className="w-4 h-4" />}
                                                    </button>
                                                </td>
                                            );
                                        })}
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                </div>
            )}

            {editingUser && <EditUserModal user={editingUser} onClose={() => setEditingUser(null)} onSave={handleUpdateUserInList} />}
            {isNewUserModalOpen && <NewUserModal onClose={() => setIsNewUserModalOpen(false)} onSave={handleAddNewUserToList} />}
        </div>
    );
};