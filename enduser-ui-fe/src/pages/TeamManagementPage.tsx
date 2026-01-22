import React, { useState, useEffect } from 'react';
import { api } from '../services/api';
import { Employee, EmployeeRole } from '../types';
import { useAuth } from '../hooks/useAuth';
import { PermissionGuard } from '../features/auth/components/PermissionGuard';
import UserAvatar from '../components/UserAvatar';
import { ShieldCheckIcon, UserIcon, MailIcon, BadgeCheckIcon, XIcon, RefreshCwIcon, KeyIcon } from '../components/Icons';

const TeamManagementPage: React.FC = () => {
    const { user } = useAuth();
    const [team, setTeam] = useState<Employee[]>([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [editingMember, setEditingMember] = useState<Employee | null>(null);

    useEffect(() => {
        fetchTeam();
    }, []);

    const fetchTeam = async () => {
        setLoading(true);
        try {
            const data = await api.getEmployees();
            setTeam(data);
        } catch (err: any) {
            setError(err.message || "Failed to fetch team data.");
        } finally {
            setLoading(false);
        }
    };

    return (
        <PermissionGuard permission="user:manage:team" userRole={user?.role} fallback={<div className="p-8 text-center text-gray-500">Access Denied: Team Management is for Managers and Admins only.</div>}>
            <div className="p-6 max-w-7xl mx-auto space-y-8">
                <header className="flex justify-between items-end">
                    <div>
                        <h1 className="text-3xl font-bold text-gray-800">Team Management</h1>
                        <p className="text-gray-500 mt-2">Manage your team members and oversee AI resource allocation.</p>
                    </div>
                    <div className="bg-white px-4 py-2 rounded-lg border border-gray-100 shadow-sm flex items-center gap-4">
                        <div className="text-right">
                            <p className="text-xs text-gray-400 uppercase font-bold tracking-wider">Team AI Budget</p>
                            <p className="text-xl font-mono font-bold text-indigo-600">842 / 1,000</p>
                        </div>
                        <div className="w-12 h-12 rounded-full border-4 border-indigo-100 border-t-indigo-600 flex items-center justify-center text-xs font-bold">
                            84%
                        </div>
                    </div>
                </header>

                {error && (
                    <div className="bg-red-50 text-red-700 p-4 rounded-lg border border-red-100">
                        {error}
                    </div>
                )}

                {loading ? (
                    <div className="flex justify-center p-12">
                        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                        {team.map((member) => (
                            <div key={member.id} className="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden hover:shadow-md transition-shadow">
                                <div className="h-2 bg-indigo-500"></div>
                                <div className="p-6">
                                    <div className="flex items-start gap-4">
                                        <UserAvatar name={member.name} className="w-16 h-16 rounded-xl text-xl" />
                                        <div className="flex-1">
                                            <h3 className="font-bold text-lg text-gray-900">{member.name}</h3>
                                            <p className="text-sm text-gray-500">{member.position}</p>
                                            <div className="mt-1 flex items-center gap-1 text-xs font-medium text-indigo-600 bg-indigo-50 px-2 py-0.5 rounded-full w-fit">
                                                <BadgeCheckIcon className="w-3 h-3" />
                                                {member.role.toUpperCase()}
                                            </div>
                                        </div>
                                    </div>

                                    <div className="mt-6 space-y-3">
                                        <div className="flex items-center text-sm text-gray-600 gap-3">
                                            <MailIcon className="w-4 h-4 text-gray-400" />
                                            <span className="truncate">{member.email}</span>
                                        </div>
                                        <div className="flex items-center text-sm text-gray-600 gap-3">
                                            <ShieldCheckIcon className="w-4 h-4 text-gray-400" />
                                            Dept: {member.department}
                                        </div>
                                    </div>

                                    <div className="mt-6 pt-6 border-t border-gray-50 flex gap-2">
                                        <button 
                                            onClick={() => setEditingMember(member)}
                                            className="flex-1 text-sm font-medium py-2 rounded-lg bg-gray-50 text-gray-700 hover:bg-gray-100 transition-colors"
                                        >
                                            Manage Role
                                        </button>
                                        <button className="flex-1 text-sm font-medium py-2 rounded-lg border border-gray-200 text-gray-600 hover:bg-gray-50 transition-colors">
                                            View Stats
                                        </button>
                                    </div>
                                </div>
                            </div>
                        ))}

                        {/* AI Agents Section */}
                        <div className="bg-indigo-900 rounded-xl shadow-sm overflow-hidden text-white md:col-span-2 lg:col-span-1 border border-indigo-800">
                            <div className="p-6 space-y-6">
                                <div className="flex justify-between items-center">
                                    <h2 className="text-xl font-bold flex items-center gap-2">
                                        <span className="text-2xl">🤖</span> AI Fleet
                                    </h2>
                                    <span className="text-xs bg-indigo-800 px-2 py-1 rounded-full text-indigo-200">ACTIVE</span>
                                </div>
                                
                                <div className="space-y-4">
                                    <div className="flex items-center justify-between p-3 bg-indigo-800/50 rounded-lg">
                                        <div className="flex items-center gap-3">
                                            <div className="w-10 h-10 bg-indigo-700 rounded-lg flex items-center justify-center">🛠️</div>
                                            <div>
                                                <p className="font-bold text-sm">DevBot</p>
                                                <p className="text-xs text-indigo-300">Code Engineering</p>
                                            </div>
                                        </div>
                                        <div className="text-right">
                                            <p className="text-xs text-indigo-400">Quota</p>
                                            <p className="text-sm font-bold">128/200</p>
                                        </div>
                                    </div>

                                    <div className="flex items-center justify-between p-3 bg-indigo-800/50 rounded-lg">
                                        <div className="flex items-center gap-3">
                                            <div className="w-10 h-10 bg-indigo-700 rounded-lg flex items-center justify-center">📈</div>
                                            <div>
                                                <p className="font-bold text-sm">MarketBot</p>
                                                <p className="text-xs text-indigo-300">Market Research</p>
                                            </div>
                                        </div>
                                        <div className="text-right">
                                            <p className="text-xs text-indigo-400">Quota</p>
                                            <p className="text-sm font-bold">452/500</p>
                                        </div>
                                    </div>
                                </div>

                                <button className="w-full py-3 bg-white text-indigo-900 rounded-xl font-bold hover:bg-indigo-50 transition-colors shadow-lg">
                                    Allocate AI Credits
                                </button>
                            </div>
                        </div>
                    </div>
                )}

                {/* MODAL */}
                {editingMember && (
                    <ManageMemberModal 
                        member={editingMember} 
                        onClose={() => setEditingMember(null)} 
                        onSuccess={() => { setEditingMember(null); fetchTeam(); }}
                    />
                )}
            </div>
        </PermissionGuard>
    );
};

const ManageMemberModal: React.FC<{ member: Employee; onClose: () => void; onSuccess: () => void }> = ({ member, onClose, onSuccess }) => {
    const [role, setRole] = useState(member.role);
    const [status, setStatus] = useState(member.status);
    const [position, setPosition] = useState(member.position);
    const [newPassword, setNewPassword] = useState('');
    const [isUpdating, setIsUpdating] = useState(false);
    const [isResetting, setIsResetting] = useState(false);

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
        <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
            <div className="bg-white rounded-2xl shadow-xl w-full max-w-lg overflow-hidden animate-in fade-in zoom-in-95 duration-200">
                <div className="p-6 border-b border-gray-100 flex justify-between items-center bg-gray-50/50">
                    <div className="flex items-center gap-3">
                        <UserAvatar name={member.name} className="w-10 h-10 rounded-lg shadow-sm" />
                        <div>
                            <h3 className="font-bold text-gray-900">{member.name}</h3>
                            <p className="text-xs text-gray-500">{member.email}</p>
                        </div>
                    </div>
                    <button onClick={onClose} className="p-2 hover:bg-gray-200 rounded-full transition-colors"><XIcon className="w-5 h-5" /></button>
                </div>

                <div className="p-6 space-y-8">
                    {/* Role & Status Form */}
                    <form onSubmit={handleUpdate} className="space-y-4">
                        <div className="grid grid-cols-2 gap-4">
                            <div>
                                <label className="block text-xs font-bold text-gray-400 uppercase tracking-wider mb-1">Position</label>
                                <input 
                                    type="text" 
                                    value={position} 
                                    onChange={e => setPosition(e.target.value)}
                                    className="w-full p-2 bg-gray-50 border border-gray-200 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none text-sm"
                                />
                            </div>
                            <div>
                                <label className="block text-xs font-bold text-gray-400 uppercase tracking-wider mb-1">Status</label>
                                <select 
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
                            <label className="block text-xs font-bold text-gray-400 uppercase tracking-wider mb-1">Access Role</label>
                            <select 
                                value={role} 
                                onChange={e => setRole(e.target.value as EmployeeRole)}
                                className="w-full p-2 bg-gray-50 border border-gray-200 rounded-lg focus:ring-2 focus:ring-indigo-500 outline-none text-sm"
                            >
                                {Object.values(EmployeeRole).map(r => <option key={r} value={r}>{r.replace('_', ' ').toUpperCase()}</option>)}
                            </select>
                        </div>
                        <button 
                            type="submit" 
                            disabled={isUpdating}
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
                            <input 
                                type="password" 
                                placeholder="New password" 
                                value={newPassword}
                                onChange={e => setNewPassword(e.target.value)}
                                className="flex-1 p-2 bg-gray-50 border border-gray-200 rounded-lg focus:ring-2 focus:ring-amber-500 outline-none text-sm"
                            />
                            <button 
                                onClick={handleResetPassword}
                                disabled={isResetting}
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

export default TeamManagementPage;