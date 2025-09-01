import React, { useState } from 'react';
import { useAuth } from '../hooks/useAuth.tsx';
import { api } from '../services/api.ts';

const SettingsPage: React.FC = () => {
    const { user } = useAuth();
    const [newEmail, setNewEmail] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [isEmailUpdating, setIsEmailUpdating] = useState(false);
    const [isPasswordUpdating, setIsPasswordUpdating] = useState(false);

    const handleEmailUpdate = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!newEmail) {
            alert('Please enter a new email.');
            return;
        }
        setIsEmailUpdating(true);
        try {
            await api.updateUserEmail(newEmail);
            alert('Email update request sent! Please check your new email address for a confirmation link.');
            setNewEmail('');
        } catch (error: any) {
            alert(`Failed to update email: ${error.message}`);
        } finally {
            setIsEmailUpdating(false);
        }
    };

    const handlePasswordUpdate = async (e: React.FormEvent) => {
        e.preventDefault();
        if (newPassword.length < 6) {
            alert('Password must be at least 6 characters long.');
            return;
        }
        if (newPassword !== confirmPassword) {
            alert('Passwords do not match.');
            return;
        }
        setIsPasswordUpdating(true);
        try {
            await api.updateUserPassword(newPassword);
            alert('Password updated successfully!');
            setNewPassword('');
            setConfirmPassword('');
        } catch (error: any) {
            alert(`Failed to update password: ${error.message}`);
        } finally {
            setIsPasswordUpdating(false);
        }
    };

    const inputClass = "appearance-none rounded-md relative block w-full px-3 py-2 border border-border placeholder-muted-foreground text-foreground bg-input focus:outline-none focus:ring-ring focus:border-ring focus:z-10 sm:text-sm";

    if (!user) {
        return <div className="p-6">Loading user data...</div>;
    }

    return (
        <div className="flex-1 flex flex-col h-full overflow-hidden p-6 bg-background">
            <h1 className="text-3xl font-bold mb-6">Settings</h1>
            <div className="flex-1 overflow-auto space-y-8">
                <div className="bg-card p-6 rounded-lg max-w-lg">
                    <h2 className="text-xl font-semibold mb-4">Update Email</h2>
                    <p className="text-muted-foreground mb-4">Current Email: <span className="font-medium text-foreground">{user.email}</span></p>
                    <form onSubmit={handleEmailUpdate} className="space-y-4">
                        <div>
                            <label htmlFor="new-email" className="block text-sm font-medium mb-1">New Email</label>
                            <input id="new-email" type="email" value={newEmail} onChange={e => setNewEmail(e.target.value)} className={inputClass} placeholder="new.email@example.com" required />
                        </div>
                        <button type="submit" disabled={isEmailUpdating} className="w-full py-2 px-4 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50">
                            {isEmailUpdating ? 'Updating...' : 'Update Email'}
                        </button>
                    </form>
                </div>

                <div className="bg-card p-6 rounded-lg max-w-lg">
                    <h2 className="text-xl font-semibold mb-4">Update Password</h2>
                    <form onSubmit={handlePasswordUpdate} className="space-y-4">
                        <div>
                            <label htmlFor="new-password">New Password</label>
                            <input id="new-password" type="password" value={newPassword} onChange={e => setNewPassword(e.target.value)} className={inputClass} placeholder="New Password" required />
                        </div>
                         <div>
                            <label htmlFor="confirm-password">Confirm New Password</label>
                            <input id="confirm-password" type="password" value={confirmPassword} onChange={e => setConfirmPassword(e.target.value)} className={inputClass} placeholder="Confirm New Password" required />
                        </div>
                        <button type="submit" disabled={isPasswordUpdating} className="w-full py-2 px-4 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50">
                            {isPasswordUpdating ? 'Updating...' : 'Update Password'}
                        </button>
                    </form>
                </div>
            </div>
        </div>
    );
};

export default SettingsPage;
