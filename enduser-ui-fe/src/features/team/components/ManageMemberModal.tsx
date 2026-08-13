import React, { useState } from 'react';
import { api } from '@/services/api';
import { Employee, EmployeeRole, ROLE_DISPLAY_NAMES } from '@/types';
import UserAvatar from '@/components/UserAvatar';
import { XIcon, RefreshCwIcon, ShieldCheckIcon, KeyIcon } from '@/components/Icons';


interface ManageMemberModalProps {
    member: Employee;
    onClose: () => void;
    onSuccess: () => void;
}

export const ManageMemberModal: React.FC<ManageMemberModalProps> = ({ member, onClose, onSuccess }) => {
    const [role, setRole] = useState(member.role);
    const [status, setStatus] = useState(member.status);
    const [position, setPosition] = useState(member.position);
    const [newPassword, setNewPassword] = useState('');
    const [isUpdating, setIsUpdating] = useState(false);
    const [isResetting, setIsResetting] = useState(false);

    // Unique IDs for accessibility
    const positionId = `position-${member.id}`;
    const statusId = `status-${member.id}`;
    const roleId = `role-${member.id}`;
    const passwordId = `password-${member.id}`;
    const modalTitleId = `modal-title-${member.id}`;

    const handleUpdate = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsUpdating(true);
        try {
            await api.updateEmployee(member.id, { role, status, position });
            onSuccess();
        } catch (err: any) {
            alert(err.message || "Update failed");
        } finally {
            setIsUpdating(false);
        }
    };

    const handleResetPassword = async () => {
        if (!newPassword) return alert("Please enter a new password");
        setIsResetting(true);
        try {
            await api.resetPassword(member.id, newPassword);
            alert("Password has been reset successfully.");
            setNewPassword('');
        } catch (err: any) {
            alert(err.message || "Password reset failed");
        } finally {
            setIsResetting(false);
        }
    };

    return (
        <div
            className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4"
            role="dialog"
            aria-modal="true"
            aria-labelledby={modalTitleId}
        >
            <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg overflow-hidden animate-in fade-in zoom-in-95 duration-200">
                <div className="p-6 border-b border-gray-100 flex justify-between items-center bg-gray-50/50">
                    <div className="flex items-center gap-3">
                        <UserAvatar name={member.name} role={member.role} className="w-10 h-10 shadow-sm" />
                        <div>
                            <h3 id={modalTitleId} className="font-bold text-gray-900">{member.name}</h3>
                            <p className="text-xs text-gray-500">{member.email}</p>
                        </div>
                    </div>
                    <button onClick={onClose} className="p-2 hover:bg-gray-200 rounded-full transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-2" aria-label="Close modal"><XIcon className="w-5 h-5" /></button>
                </div>

                <div className="p-6 space-y-8">
                    {/* Role & Status Form */}
                    <form onSubmit={handleUpdate} className="space-y-4">
                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label htmlFor={positionId} className="block text-xs font-bold text-gray-400 uppercase tracking-wider mb-1">Position</label>
                                <input 
                                    id={positionId}
                                    type="text" 
                                    value={position} 
                                    onChange={e => setPosition(e.target.value)}
                                    className="w-full p-2 bg-gray-50 border border-gray-200 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none text-sm"
                                />
                            </div>
                            <div>
                                <label htmlFor={statusId} className="block text-xs font-bold text-gray-400 uppercase tracking-wider mb-1">Status</label>
                                <select 
                                    id={statusId}
                                    value={status} 
                                    onChange={e => setStatus(e.target.value as any)}
                                    className="w-full p-2 bg-gray-50 border border-gray-200 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none text-sm"
                                >
                                    <option value="active">Active</option>
                                    <option value="inactive">Inactive</option>
                                    <option value="suspended">Suspended</option>
                                </select>
                            </div>
                        </div>
                        <div>
                            <label htmlFor={roleId} className="block text-xs font-bold text-gray-400 uppercase tracking-wider mb-1">Access Role</label>
                            <select 
                                id={roleId}
                                value={role} 
                                onChange={e => setRole(e.target.value as EmployeeRole)}
                                className="w-full p-2 bg-gray-50 border border-gray-200 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none text-sm"
                            >
                                {Object.values(EmployeeRole).map(r => <option key={r} value={r}>{ROLE_DISPLAY_NAMES[r] || r.replace('_', ' ').toUpperCase()}</option>)}
                            </select>
                        </div>
                        <button 
                            type="submit" 
                            disabled={isUpdating}
                            aria-disabled={isUpdating}
                            aria-busy={isUpdating}
                            className="w-full py-2 bg-indigo-600 text-white rounded-lg font-bold hover:bg-indigo-700 disabled:opacity-50 transition-colors flex items-center justify-center gap-2"
                        >
                            {isUpdating ? <RefreshCwIcon className="w-4 h-4 animate-spin" /> : <ShieldCheckIcon className="w-4 h-4" />}
                            Update Profile
                        </button>
                    </form>

                    {/* Password Reset Section */}
                    <div className="pt-6 border-t border-gray-100">
                        <h4 className="text-sm font-bold text-gray-800 flex items-center gap-2 mb-4">
                            <KeyIcon className="w-4 h-4 text-amber-500" />
                            Security Management
                        </h4>
                        <div className="flex gap-2">
                            <label htmlFor={passwordId} className="sr-only">New password</label>
                            <input 
                                id={passwordId}
                                type="password" 
                                placeholder="New password"
                                aria-label="New password"
                                value={newPassword}
                                onChange={e => setNewPassword(e.target.value)}
                                className="flex-1 p-2 bg-gray-50 border border-gray-200 rounded-lg focus:ring-2 focus:ring-amber-500 outline-none text-sm"
                            />
                            <button 
                                onClick={handleResetPassword}
                                disabled={isResetting}
                                aria-disabled={isResetting}
                                aria-busy={isResetting}
                                className="px-4 py-2 bg-amber-50 text-amber-700 border border-amber-200 rounded-lg font-bold text-xs hover:bg-amber-100 transition-colors flex items-center gap-2"
                            >
                                {isResetting ? <RefreshCwIcon className="w-3 h-3 animate-spin" /> : 'RESET'}
                            </button>
                        </div>
                        <p className="text-[10px] text-gray-400 mt-2 italic">Caution: This will take effect immediately upon confirmation.</p>
                    </div>
                </div>
            </div>
        </div>
    );
};
