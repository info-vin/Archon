import { Lock, ShieldAlert } from "lucide-react";
import type React from "react";
import { useId, useState } from "react";
import { Button } from "@/components/ui/Button";
import { useAuth } from "../contexts/AuthContext";

export const AdminAuthGate: React.FC = () => {
  const { loginWithSecret, error } = useAuth();
  const [secret, setSecret] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);
  const secretInputId = useId();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!secret.trim()) {
      setSubmitError("Please enter the Admin Secret.");
      return;
    }
    setSubmitting(true);
    setSubmitError(null);
    try {
      await loginWithSecret(secret.trim());
    } catch (err) {
      setSubmitError(err instanceof Error ? err.message : "Authentication failed");
    } finally {
      setSubmitting(false);
    }
  };

  const displayError = submitError || error;

  return (
    <div className="min-h-screen bg-slate-950 text-white flex items-center justify-center p-6">
      <div className="w-full max-w-md rounded-xl border border-cyan-500/30 bg-slate-900/80 p-8 shadow-2xl backdrop-blur">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-2.5 rounded-lg bg-cyan-500/10 border border-cyan-500/30 text-cyan-400">
            <Lock className="w-5 h-5" />
          </div>
          <div>
            <h1 className="text-xl font-semibold text-white">Archon Admin Console</h1>
            <p className="text-xs text-slate-400">Authentication required to access Knowledge Engine</p>
          </div>
        </div>

        {displayError && (
          <div
            role="alert"
            className="mb-4 flex items-start gap-2 rounded-lg border border-red-500/30 bg-red-500/10 p-3 text-xs text-red-300"
          >
            <ShieldAlert className="w-4 h-4 shrink-0 mt-0.5 text-red-400" />
            <span>{displayError}</span>
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-1.5">
            <label
              htmlFor={secretInputId}
              className="block text-xs font-medium uppercase tracking-wider text-slate-300"
            >
              Admin Secret
            </label>
            <input
              id={secretInputId}
              type="password"
              value={secret}
              onChange={(e) => setSecret(e.target.value)}
              placeholder="Enter X-Admin-Secret"
              autoComplete="current-password"
              className="w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-white placeholder-slate-500 focus:border-cyan-400 focus:outline-none focus:ring-1 focus:ring-cyan-400"
            />
          </div>
          <Button type="submit" disabled={submitting} className="w-full" accentColor="cyan">
            {submitting ? "Verifying..." : "Unlock Admin Console"}
          </Button>
        </form>
      </div>
    </div>
  );
};
