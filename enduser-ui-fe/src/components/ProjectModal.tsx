import React, { useState } from 'react';
import { api } from '../services/api';
import { Project } from '../types';
import { XIcon, RefreshCwIcon } from './Icons';

interface ProjectModalProps {
  onClose: () => void;
  onProjectCreated: (newProject: Project) => void;
}

export const ProjectModal: React.FC<ProjectModalProps> = ({ onClose, onProjectCreated }) => {
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!title.trim()) {
      setError('Project title is required.');
      return;
    }
    setIsSubmitting(true);
    setError(null);

    try {
      // Assuming api.createProject returns an object with a `project` property
      const response = await api.createProject({ title, description });
      onProjectCreated(response.project);
      onClose();
    } catch (err: any) {
      setError(err.message || 'Failed to create project.');
      console.error(err);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 z-50 flex justify-center items-center p-4" onClick={onClose}>
      <div className="bg-card rounded-lg shadow-xl p-6 w-full max-w-md relative" onClick={(e) => e.stopPropagation()}>
        <div className="flex justify-between items-center mb-4 flex-shrink-0">
          <h2 className="text-2xl font-bold">New Project</h2>
          <button onClick={onClose} className="p-1 rounded-full hover:bg-secondary focus-visible:ring-2 focus-visible:outline-none" aria-label="Close" title="Close">
            <XIcon className="w-6 h-6" />
          </button>
        </div>
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label htmlFor="project-title" className="block text-sm font-medium text-muted-foreground mb-1">
              Project Title
            </label>
            <input
              id="project-title"
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full bg-input border border-border rounded-md px-3 py-2 text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
              required
            />
          </div>
          <div className="mb-6">
            <label htmlFor="project-description" className="block text-sm font-medium text-muted-foreground mb-1">
              Description (Optional)
            </label>
            <textarea
              id="project-description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              rows={4}
              className="w-full bg-input border border-border rounded-md px-3 py-2 text-foreground focus:outline-none focus:ring-2 focus:ring-ring"
            />
          </div>
          {error && <p className="text-red-500 text-sm mb-4">{error}</p>}
          <div className="flex justify-end gap-4">
            <button
              type="button"
              onClick={onClose}
              className="px-4 py-2 bg-secondary text-secondary-foreground rounded-md hover:bg-secondary/90"
              disabled={isSubmitting}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 disabled:opacity-50 flex items-center justify-center gap-2"
              disabled={isSubmitting}
              aria-busy={isSubmitting}
              aria-label={isSubmitting ? 'Creating project...' : 'Create project'}
            >
              {isSubmitting && <RefreshCwIcon className="w-4 h-4 animate-spin" />}
              {isSubmitting ? 'Creating...' : 'Create Project'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};