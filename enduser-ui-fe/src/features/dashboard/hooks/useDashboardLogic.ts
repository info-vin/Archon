import { useState, useEffect, useCallback, useMemo } from 'react';
import { api } from '../../../services/api';
import { Task, Project, TaskStatus, SortableTaskKeys, SortDirection, Employee } from '../../../types';
import { useAuth } from '../../../hooks/useAuth';

const STATUS_WEIGHTS: Record<string, number> = { 'todo': 1, 'doing': 2, 'review': 3, 'done': 4 };
const PRIORITY_WEIGHTS: Record<string, number> = { 'critical': 4, 'high': 3, 'medium': 2, 'low': 1 };

export const useDashboardLogic = (selectedProjectId: string) => {
  const [tasks, setTasks] = useState<Task[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [users, setUsers] = useState<Employee[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [sortConfig, setSortConfig] = useState<{ key: SortableTaskKeys; direction: SortDirection } | null>(null);
  
  const { user } = useAuth();

  const fetchData = useCallback(async () => {
    setIsLoading(true);
    try {
      // Alice (Sales) doesn't need to see the team members. 
      // Only managers and admins should call getEmployees to avoid 403 errors.
      const isManagerOrAdmin = user?.role?.toLowerCase() === 'manager' || 
                               user?.role?.toLowerCase() === 'admin' || 
                               user?.role?.toLowerCase() === 'system_admin';

      const promises: [Promise<Task[]>, Promise<Project[]>, Promise<Employee[]>] = [
        api.getTasks(true), // include closed
        api.getProjects(),
        isManagerOrAdmin ? api.getEmployees() : Promise.resolve([])
      ];

      const [tasksData, projectsData, usersData] = await Promise.all(promises);
      
      setTasks(tasksData);
      setProjects(projectsData);
      setUsers(usersData);
    } catch (error: any) {
      console.error('Failed to load dashboard data:', error);
      // alert(`Failed to load dashboard data: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  }, [user]);

  useEffect(() => {
    if (user) {
      fetchData();
    }
  }, [fetchData, user]);

  const userMap = useMemo(() => {
    const map: Record<string, any> = {};
    (users || []).forEach(u => { map[u.id] = u; });
    return map;
  }, [users]);

  const projectMap = useMemo(() => {
    const map: Record<string, string> = {};
    (projects || []).forEach(p => { map[p.id] = p.title; });
    return map;
  }, [projects]);

  const filteredTasks = useMemo(() => {
    if (!selectedProjectId || selectedProjectId === 'all') return tasks || [];
    return (tasks || []).filter(task => task.project_id === selectedProjectId);
  }, [tasks, selectedProjectId]);

  // PERFORMANCE: Pre-calculate sorting weights for O(1) lookups during the O(N log N) sort operation
  // to avoid redundant string allocations from calling .toLowerCase() repeatedly inside the sort comparator.
  const taskWeights = useMemo(() => {
    const weights: Record<string, { status: number; priority: number }> = {};
    filteredTasks.forEach(task => {
      weights[task.id] = {
        status: STATUS_WEIGHTS[(task.status || '').toLowerCase()] || 0,
        priority: PRIORITY_WEIGHTS[(task.priority || '').toLowerCase()] || 0
      };
    });
    return weights;
  }, [filteredTasks]);

  const sortedTasks = useMemo(() => {
    let sortableTasks = [...filteredTasks];
    if (sortConfig !== null) {
      sortableTasks.sort((a, b) => {
        let valA: any = a[sortConfig.key] || '';
        let valB: any = b[sortConfig.key] || '';

        if (sortConfig.key === 'status' || sortConfig.key === 'priority') {
            valA = taskWeights[a.id]?.[sortConfig.key] || 0;
            valB = taskWeights[b.id]?.[sortConfig.key] || 0;
        }

        if (valA < valB) return sortConfig.direction === 'ascending' ? -1 : 1;
        if (valA > valB) return sortConfig.direction === 'ascending' ? 1 : -1;
        return 0;
      });
    }
    return sortableTasks;
  }, [filteredTasks, sortConfig, taskWeights]);

  const requestSort = useCallback((key: SortableTaskKeys) => {
    setSortConfig((currentConfig) => {
        let direction: SortDirection = 'ascending';
        if (currentConfig && currentConfig.key === key && currentConfig.direction === 'ascending') {
          direction = 'descending';
        }
        return { key, direction };
    });
  }, []);

  const updateTaskStatus = useCallback(async (taskId: string, newStatus: TaskStatus) => {
    try {
      await api.updateTask(taskId, { status: newStatus });
      setTasks(prev => prev.map(t => t.id === taskId ? { ...t, status: newStatus } : t));
    } catch (error: any) {
      alert(`Failed to update status: ${error.message}`);
    }
  }, []);

  return {
    tasks,
    projects,
    users,
    userMap,
    projectMap,
    sortedTasks,
    filteredTasks,
    isLoading,
    sortConfig,
    fetchData,
    requestSort,
    updateTaskStatus
  };
};
