import React, { useEffect, useState } from 'react';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { api } from '../services/api';
import { TaskStats, MemberPerformance, EmployeeRole } from '../types';
import { useAuth } from '../hooks/useAuth';
import { PermissionGuard } from '../features/auth/components/PermissionGuard';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8'];

const StatsPage: React.FC = () => {
  const { user } = useAuth();
  const [taskStats, setTaskStats] = useState<TaskStats[]>([]);
  const [memberStats, setMemberStats] = useState<MemberPerformance[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  /**
   * DESIGN DECISION (RBAC Strategy):
   * 1. Transparency: All employees can see team task status distribution to foster collaboration.
   * 2. Privacy: Member performance rankings are restricted. Only Managers see the full list; 
   *    Employees see only their own completed task count.
   */
  const isManager = user?.role === EmployeeRole.MANAGER || 
                    user?.role === EmployeeRole.SYSTEM_ADMIN || 
                    user?.role === EmployeeRole.ADMIN ||
                    user?.role === EmployeeRole.PROJECT_MANAGER;

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const [tasks, members] = await Promise.all([
          api.getTaskDistribution(),
          api.getMemberPerformance()
        ]);
        
        setTaskStats(tasks);

        // RBAC Filter: Managers see all; Employees see only themselves
        if (isManager) {
            setMemberStats(members);
        } else if (user) {
            // Filter for current user's name only
            const myStats = members.filter(m => m.name === user.name);
            setMemberStats(myStats.length > 0 ? myStats : [{ name: user.name, completed_tasks: 0 }]);
        }
      } catch (err: any) {
        console.error("Failed to fetch stats:", err);
        setError("Failed to load statistics. Please try again.");
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [user, isManager]);

  if (loading) {
    return (
      <div className="flex justify-center items-center h-full p-10">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-8 text-center text-red-500">
        <h2 className="text-xl font-bold">Error</h2>
        <p>{error}</p>
      </div>
    );
  }

  return (
    <PermissionGuard 
        permission="stats:view:own" 
        userRole={user?.role} 
        fallback={<div className="p-8 text-center">Access Denied: You do not have permission to view statistics.</div>}
    >
      <div className="p-6 max-w-7xl mx-auto space-y-8">
        <header>
          <h1 className="text-3xl font-bold text-gray-800">
              {isManager ? "Team Analytics Dashboard" : "My Performance Dashboard"}
          </h1>
          <p className="text-gray-500 mt-2">
              {isManager ? "Overview of team velocity and task distribution." : "Track your personal contributions and impact."}
          </p>
        </header>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {/* Task Distribution Chart - Shared Transparency */}
          <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
            <h2 className="text-xl font-semibold mb-6 text-gray-700 text-center">Team Tasks by Status</h2>
            <div className="h-80 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={taskStats as any[]}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, percent }) => `${name} ${((percent || 0) * 100).toFixed(0)}%`}
                    outerRadius={100}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {taskStats.map((_, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Member Performance Chart - RBAC Protected */}
          <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
            <h2 className="text-xl font-semibold mb-6 text-gray-700 text-center">
                {isManager ? "Top Performers (Completed)" : "My Completed Tasks"}
            </h2>
            <div className="h-80 w-full">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart
                  data={memberStats}
                  layout="vertical"
                  margin={{ top: 5, right: 30, left: 40, bottom: 5 }}
                >
                  <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                  <XAxis type="number" allowDecimals={false} />
                  <YAxis type="category" dataKey="name" width={100} />
                  <Tooltip cursor={{fill: 'transparent'}} />
                  <Legend />
                  <Bar dataKey="completed_tasks" fill="#82ca9d" name="Tasks Completed" radius={[0, 4, 4, 0]} barSize={isManager ? 20 : 40} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>
      </div>
    </PermissionGuard>
  );
};

export default StatsPage;
