import React, { useState } from 'react';
import { api } from '@/services/api.ts';
import { Employee, EmployeeRole } from '@/types.ts';
import { XIcon } from '@/components/Icons.tsx';

export const IdentityNewUserModal: React.FC<{ onClose: () => void; onSave: (newUser: Employee) => void; }> = ({ onClose, onSave }) => {
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
