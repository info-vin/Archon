
import React, { useState, useEffect } from 'react';
import { api } from '../../../services/api.ts';
import { Employee, EmployeeRole } from '../../../types.ts';
import { PlusIcon, XIcon } from '../../../components/Icons.tsx';
import UserAvatar from '../../../components/UserAvatar.tsx';

// --- SUB-COMPONENTS (Originally from AdminPage.tsx) ---

const EditUserModal: React.FC<{ user: Employee; onClose: () => void; onSave: (updatedUser: Employee) => void; }> = ({ user, onClose, onSave }) => {
    const [role, setRole] = useState(user.role);
    const [status, setStatus] = useState(user.status);
    const inputClass = "appearance-none rounded-md relative block w-full px-3 py-2 border border-border placeholder-muted-foreground text-foreground bg-input focus:outline-none focus:ring-ring focus:border-ring focus:z-10 sm:text-sm";

    const handleSave = async () => {
        try {
            const updatedUser = await api.updateEmployee(user.id, { role, status });
            onSave(updatedUser);
            alert('User updated successfully!');
            onClose();
        } catch(error: any) {
            alert(`Error updating user: ${error.message}`);
        }
    };

    return (
         <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
            <div className="bg-card rounded-2xl shadow-xl w-full max-w-lg p-6 relative animate-in fade-in zoom-in-95 duration-200">
                <h2 className="text-2xl font-bold mb-4">Edit User: {user.name}</h2>
                <button onClick={onClose} className="absolute top-4 right-4 p-2 rounded-full hover:bg-muted transition-colors"><XIcon className="w-6 h-6" /></button>
                <div className="space-y-4">
                    <div>
                        <label htmlFor="role" className="block text-sm font-medium mb-1">Role</label>
                        <select id="role" value={role} onChange={e => setRole(e.target.value as EmployeeRole)} className={inputClass}>
                            {Object.values(EmployeeRole).map(r => <option key={r} value={r}>{r}</option>)}
                        </select>
                    </div>
                     <div>
                        <label htmlFor="status" className="block text-sm font-medium mb-1">Status</label>
                        <select id="status" value={status} onChange={e => setStatus(e.target.value as 'active' | 'inactive' | 'suspended')} className={inputClass}>
                            <option value="active">Active</option>
                            <option value="inactive">Inactive</option>
                            <option value="suspended">Suspended</option>
                        </select>
                    </div>
                    <div className="flex justify-end space-x-2 pt-4 border-t border-border mt-4">
                        <button onClick={onClose} className="px-4 py-2 rounded-md bg-secondary text-secondary-foreground hover:bg-secondary/80 transition-colors">Cancel</button>
                        <button onClick={handleSave} className="px-4 py-2 rounded-md bg-primary text-primary-foreground hover:bg-primary/90 transition-all font-bold">Save Changes</button>
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
            <div className="bg-card rounded-2xl shadow-xl w-full max-w-lg p-6 relative animate-in fade-in zoom-in-95 duration-200">
                <h2 className="text-2xl font-bold mb-4">Create New User</h2>
                <button onClick={onClose} className="absolute top-4 right-4 p-2 rounded-full hover:bg-muted transition-colors"><XIcon className="w-6 h-6" /></button>
                <form onSubmit={handleSubmit} className="space-y-4">
                    <input type="text" placeholder="Full Name" value={name} onChange={e => setName(e.target.value)} className={inputClass} required />
                    <input type="email" placeholder="Email Address" value={email} onChange={e => setEmail(e.target.value)} className={inputClass} required />
                    <input type="password" placeholder="Password" value={password} onChange={e => setPassword(e.target.value)} className={inputClass} required />
                    <div>
                        <label htmlFor="role-new" className="block text-sm font-medium mb-1">Role</label>
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
    const [editingUser, setEditingUser] = useState<Employee | null>(null);
    const [isNewUserModalOpen, setIsNewUserModalOpen] = useState(false);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        setLoading(true);
        api.getEmployees()
            .then(setEmployees)
            .catch(err => alert(`Failed to load employees: ${err.message}`))
            .finally(() => setLoading(false));
    }, []);
    
    const handleUpdateUserInList = (updatedUser: Employee) => {
        setEmployees(employees.map(e => e.id === updatedUser.id ? updatedUser : e));
    };

    const handleAddNewUserToList = (newUser: Employee) => {
        setEmployees(prev => [...prev, newUser]);
    };

    if (loading) return <div>Loading Identity Matrix...</div>;

    return (
        <>
            <div className="bg-card p-6 rounded-2xl border border-border shadow-sm">
                <div className="flex justify-between items-center mb-6">
                    <h2 className="text-xl font-bold">Identity Matrix (RBAC)</h2>
                     <button onClick={() => setIsNewUserModalOpen(true)} className="flex items-center px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 font-bold transition-all shadow-sm">
                        <PlusIcon className="w-5 h-5 mr-2" />
                        NEW USER
                    </button>
                </div>
                <div className="overflow-x-auto -mx-6">
                    <table className="min-w-full divide-y divide-border">
                        <thead className="bg-muted/50">
                            <tr>
                                <th className="px-6 py-3 text-left text-xs font-bold uppercase tracking-wider text-muted-foreground">Name</th>
                                <th className="px-6 py-3 text-left text-xs font-bold uppercase tracking-wider text-muted-foreground">Role</th>
                                <th className="px-6 py-3 text-left text-xs font-bold uppercase tracking-wider text-muted-foreground">Status</th>
                                <th className="px-6 py-3 text-left text-xs font-bold uppercase tracking-wider text-muted-foreground text-right">Actions</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-border bg-card">
                            {employees.map(emp => (
                                <tr key={emp.id} className="hover:bg-muted/30 transition-colors">
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <div className="flex items-center">
                                            <UserAvatar name={emp.name || ''} role={emp.role} className="h-10 w-10 rounded-lg shadow-sm" />
                                            <div className="ml-4">
                                                <div className="text-sm font-bold">{emp.name}</div>
                                                <div className="text-xs text-muted-foreground">{emp.email}</div>
                                            </div>
                                        </div>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <span className="text-xs font-mono bg-secondary px-2 py-1 rounded border border-border">{emp.role}</span>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <span className={`px-2 py-1 inline-flex text-[10px] leading-4 font-bold uppercase tracking-widest rounded-full ${emp.status === 'active' ? 'bg-green-100 text-green-700 dark:bg-green-900/30 dark:text-green-400' : 'bg-red-100 text-red-700 dark:bg-red-900/30 dark:text-red-400'}`}>
                                            {emp.status}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                        <button onClick={() => setEditingUser(emp)} className="text-primary hover:text-primary/90 font-bold transition-colors disabled:opacity-30" disabled={emp.role === EmployeeRole.SYSTEM_ADMIN}>Edit</button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>
            {editingUser && <EditUserModal user={editingUser} onClose={() => setEditingUser(null)} onSave={handleUpdateUserInList} />}
            {isNewUserModalOpen && <NewUserModal onClose={() => setIsNewUserModalOpen(false)} onSave={handleAddNewUserToList} />}
        </>
    );
};
