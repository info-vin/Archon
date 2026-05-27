import React, { useState, useEffect } from 'react';
import { api } from '@/services/api.ts';
import { Employee } from '@/types.ts';
import { PlusIcon, CheckCircleIcon } from '@/components/Icons.tsx';
import { IdentityMatrixRow } from './IdentityMatrixRow.tsx';
import { IdentityEditUserModal } from './IdentityEditUserModal.tsx';
import { IdentityNewUserModal } from './IdentityNewUserModal.tsx';

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
            // PERFORMANCE OPTIMIZATION: Converted sequential loop to parallel requests.
            // Impact: Reduces O(N) waiting time to O(1) concurrent waiting time, significantly speeding up matrix saves.
            await Promise.all(
                rbacMatrix.map(row => api.updateRBACRole(row.role, row.permissions, row.description))
            );
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
                                {employees.filter(e => e && e.id).map(emp => (
                                    <IdentityMatrixRow 
                                        key={emp.id}
                                        emp={emp}
                                        isSelected={selectedUserId === emp.id}
                                        onToggleSelect={() => setSelectedUserId(selectedUserId === emp.id ? null : emp.id)}
                                        onEdit={() => setEditingUser(emp)}
                                        effectivePermissions={getPermissionsForRole(emp.role)}
                                    />
                                ))}
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
                                                        aria-label={`Toggle permission ${perm} for role ${row.role}`}
                                                        aria-pressed={hasPerm}
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

            {editingUser && <IdentityEditUserModal user={editingUser} onClose={() => setEditingUser(null)} onSave={handleUpdateUserInList} />}
            {isNewUserModalOpen && <IdentityNewUserModal onClose={() => setIsNewUserModalOpen(false)} onSave={handleAddNewUserToList} />}
        </div>
    );
};