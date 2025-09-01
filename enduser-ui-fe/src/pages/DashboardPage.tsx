
import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { api, NewTaskData } from '../services/api.ts';
import { Task, TaskStatus, TaskPriority, Employee, Project } from '../types.ts';
import { GanttChartIcon, KanbanIcon, ListIcon, TableIcon, PlusIcon, ChevronDownIcon, ChevronsUpDownIcon } from '../components/Icons.tsx';
import { TaskModal } from '../components/TaskModal.tsx';
import {
    select,
    extent,
    scaleTime,
    scaleBand,
    axisTop,
    timeFormat,
    timeDay,
    timeWeek,
    timeMonth
} from 'd3';

type ViewMode = 'list' | 'table' | 'kanban' | 'gantt';
type SortableTaskKeys = keyof Task;
type SortDirection = 'ascending' | 'descending';

const priorityColors: { [key in TaskPriority]: string } = {
  [TaskPriority.LOW]: 'bg-blue-500',
  [TaskPriority.MEDIUM]: 'bg-yellow-500',
  [TaskPriority.HIGH]: 'bg-orange-500',
  [TaskPriority.CRITICAL]: 'bg-red-500',
};

const statusColors: { [key in TaskStatus]: string } = {
  [TaskStatus.TODO]: 'bg-gray-500',
  [TaskStatus.DOING]: 'bg-blue-500',
  [TaskStatus.REVIEW]: 'bg-purple-500',
  [TaskStatus.DONE]: 'bg-green-500',
};

const DashboardPage: React.FC = () => {
  const [viewMode, setViewMode] = useState<ViewMode>('gantt');
  const [tasks, setTasks] = useState<Task[]>([]);
  const [employees, setEmployees] = useState<Employee[]>([]);
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProjectId, setSelectedProjectId] = useState<string>('all');
  const [loading, setLoading] = useState(true);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [sortConfig, setSortConfig] = useState<{ key: SortableTaskKeys; direction: SortDirection } | null>({ key: 'created_at', direction: 'ascending'});


  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        const [tasksData, employeesData, projectsData] = await Promise.all([
          api.getTasks(),
          api.getEmployees(),
          api.getProjects()
        ]);
        setTasks(tasksData);
        setEmployees(employeesData);
        setProjects(projectsData);
         if (projectsData.length > 0 && selectedProjectId === 'all') {
            setSelectedProjectId(projectsData[0].id);
        }
      } catch (error: any) {
        console.error("Failed to fetch data:", error);
        alert(`Failed to load dashboard data: ${error.message}`);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);
  
  const filteredTasks = useMemo(() => {
    if (selectedProjectId === 'all') {
      return tasks;
    }
    return tasks.filter(task => task.project_id === selectedProjectId);
  }, [tasks, selectedProjectId]);
  
  const sortedTasks = useMemo(() => {
    let sortableTasks = [...filteredTasks];
    if (sortConfig !== null) {
      sortableTasks.sort((a, b) => {
        if (a[sortConfig.key] < b[sortConfig.key]) {
          return sortConfig.direction === 'ascending' ? -1 : 1;
        }
        if (a[sortConfig.key] > b[sortConfig.key]) {
          return sortConfig.direction === 'ascending' ? 1 : -1;
        }
        return 0;
      });
    }
    return sortableTasks;
  }, [filteredTasks, sortConfig]);

  const requestSort = (key: SortableTaskKeys) => {
    let direction: SortDirection = 'ascending';
    if (sortConfig && sortConfig.key === key && sortConfig.direction === 'ascending') {
      direction = 'descending';
    }
    setSortConfig({ key, direction });
  };
  
  const currentProject = useMemo(() => {
    return projects.find(p => p.id === selectedProjectId);
  }, [projects, selectedProjectId]);


  const updateTaskStatus = useCallback((taskId: string, newStatus: TaskStatus) => {
    setTasks(prevTasks => prevTasks.map(task =>
      task.id === taskId ? { ...task, status: newStatus } : task
    ));
    // In a real app, you would also call api.updateTask here
  }, []);

  const handleCreateTask = async (taskData: NewTaskData) => {
    try {
      const newTask = await api.createTask(taskData);
      setTasks(prevTasks => [...prevTasks, newTask]);
      setIsModalOpen(false);
      alert('Task created successfully!');
    } catch (error: any) {
      console.error("Failed to create task:", error);
      alert(`Failed to create task: ${error.message}`);
    }
  };


  if (loading) return <div className="flex items-center justify-center h-full">Loading tasks...</div>;

  return (
    <div className="flex-1 flex flex-col h-full overflow-hidden p-6 bg-background">
      <header className="flex flex-col md:flex-row md:justify-between md:items-center mb-6 gap-4">
        <h1 className="text-3xl font-bold">{currentProject ? `${currentProject.title} Tasks` : 'All Tasks'}</h1>
        <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-2 w-full md:w-auto">
          <div className="flex items-center">
            <label htmlFor="project-filter" className="sr-only">Filter by project</label>
            <select
                id="project-filter"
                value={selectedProjectId}
                onChange={e => setSelectedProjectId(e.target.value)}
                className="bg-card border border-border rounded-md px-3 py-2 text-foreground focus:outline-none focus:ring-2 focus:ring-ring w-full"
            >
                <option value="all">All Projects</option>
                {projects.map(project => (
                    <option key={project.id} value={project.id}>{project.title}</option>
                ))}
            </select>
          </div>
          <div className="flex items-center bg-card border border-border rounded-md justify-around">
            <ViewButton icon={<ListIcon className="w-5 h-5" />} label="List" active={viewMode === 'list'} onClick={() => setViewMode('list')} />
            <ViewButton icon={<TableIcon className="w-5 h-5" />} label="Table" active={viewMode === 'table'} onClick={() => setViewMode('table')} />
            <ViewButton icon={<KanbanIcon className="w-5 h-5" />} label="Kanban" active={viewMode === 'kanban'} onClick={() => setViewMode('kanban')} />
            <ViewButton icon={<GanttChartIcon className="w-5 h-5" />} label="Gantt" active={viewMode === 'gantt'} onClick={() => setViewMode('gantt')} />
          </div>
          <button 
            onClick={() => setIsModalOpen(true)}
            className="flex items-center justify-center px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90"
          >
            <PlusIcon className="w-5 h-5 mr-2" />
            New Task
          </button>
        </div>
      </header>
       { (viewMode === 'list' || viewMode === 'table') && (
            <div className="mb-4 flex justify-end">
                 <select
                    onChange={(e) => requestSort(e.target.value as SortableTaskKeys)}
                    value={sortConfig?.key}
                    className="bg-card border border-border rounded-md px-3 py-1 text-foreground focus:outline-none focus:ring-2 focus:ring-ring text-sm"
                >
                    <option value="title">Sort by Title</option>
                    <option value="due_date">Sort by Due Date</option>
                    <option value="priority">Sort by Priority</option>
                    <option value="status">Sort by Status</option>
                </select>
            </div>
        )}

      <div className="flex-1 overflow-auto">
        {viewMode === 'list' && <ListView tasks={sortedTasks} />}
        {viewMode === 'table' && <TableView tasks={sortedTasks} requestSort={requestSort} sortConfig={sortConfig} />}
        {viewMode === 'kanban' && <KanbanView tasks={filteredTasks} onTaskStatusChange={updateTaskStatus} />}
        {viewMode === 'gantt' && <GanttView tasks={filteredTasks} employees={employees} />}
      </div>
      
      {isModalOpen && (
        <TaskModal
          onClose={() => setIsModalOpen(false)}
          onSubmit={handleCreateTask}
          employees={employees}
          projectId={selectedProjectId !== 'all' ? selectedProjectId : projects[0]?.id}
        />
      )}
    </div>
  );
};

// Sub-components for different views

const ViewButton: React.FC<{ icon: React.ReactNode, label: string, active: boolean, onClick: () => void }> = ({ icon, label, active, onClick }) => (
  <button
    title={label}
    onClick={onClick}
    className={`p-2 transition-colors flex-1 ${active ? 'bg-secondary text-primary' : 'hover:bg-accent'}`}
  >
    {icon}
  </button>
);

const ListView: React.FC<{ tasks: Task[] }> = ({ tasks }) => {
    return <div className="space-y-3">
        {tasks.map(task => (
            <div key={task.id} className="p-4 bg-card border border-border rounded-lg flex items-center justify-between">
                <div className="flex items-center">
                    <span className={`w-3 h-3 rounded-full mr-4 ${statusColors[task.status]}`}></span>
                    <div>
                        <p className="font-semibold">{task.title}</p>
                        <p className="text-sm text-muted-foreground">{new Date(task.due_date).toLocaleDateString()}</p>
                    </div>
                </div>
                <div className="flex items-center space-x-4">
                    <span className={`px-2 py-1 text-xs font-semibold rounded-full text-white ${priorityColors[task.priority]}`}>{task.priority}</span>
                    <span className="text-sm">{task.assignee || 'Unassigned'}</span>
                </div>
            </div>
        ))}
    </div>;
};

const TableView: React.FC<{ tasks: Task[], requestSort: (key: SortableTaskKeys) => void, sortConfig: {key: SortableTaskKeys, direction: SortDirection} | null }> = ({ tasks, requestSort, sortConfig }) => {
    const SortableHeader: React.FC<{ columnKey: SortableTaskKeys, title: string }> = ({ columnKey, title }) => {
        const isSorted = sortConfig?.key === columnKey;
        return (
            <th className="px-6 py-3 text-left text-xs font-medium text-muted-foreground uppercase tracking-wider">
                <button onClick={() => requestSort(columnKey)} className="flex items-center space-x-1">
                    <span>{title}</span>
                    {isSorted ? (
                        sortConfig?.direction === 'ascending' ? <ChevronDownIcon className="w-4 h-4" /> : <ChevronDownIcon className="w-4 h-4 transform rotate-180" />
                    ) : (
                        <ChevronsUpDownIcon className="w-4 h-4 opacity-30" />
                    )}
                </button>
            </th>
        );
    };

    return <div className="w-full">
        {/* Desktop Table */}
        <table className="min-w-full divide-y divide-border hidden md:table">
            <thead className="bg-card">
                <tr>
                    <SortableHeader columnKey="title" title="Title" />
                    <SortableHeader columnKey="assignee" title="Assignee" />
                    <SortableHeader columnKey="status" title="Status" />
                    <SortableHeader columnKey="priority" title="Priority" />
                    <SortableHeader columnKey="due_date" title="Due Date" />
                </tr>
            </thead>
            <tbody className="bg-card divide-y divide-border">
                {tasks.map(task => (
                    <tr key={task.id}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">{task.title}</td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                            {task.assignee || 'Unassigned'}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                            <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full text-white ${statusColors[task.status]}`}>{task.status}</span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm">
                             <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full text-white ${priorityColors[task.priority]}`}>{task.priority}</span>
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-muted-foreground">{new Date(task.due_date).toLocaleDateString()}</td>
                    </tr>
                ))}
            </tbody>
        </table>
        {/* Mobile Card View */}
        <div className="md:hidden space-y-3">
            {tasks.map(task => (
                <div key={task.id} className="p-4 bg-card border border-border rounded-lg">
                    <div className="flex justify-between items-start">
                        <p className="font-semibold text-lg mb-2 pr-2">{task.title}</p>
                        <span className={`flex-shrink-0 px-2 py-1 text-xs font-semibold rounded-full text-white ${priorityColors[task.priority]}`}>{task.priority}</span>
                    </div>
                    <div className="space-y-2 text-sm border-t border-border pt-2 mt-2">
                        <div className="flex justify-between">
                            <span className="text-muted-foreground">Status:</span>
                            <span className={`px-2 inline-flex text-xs leading-5 font-semibold rounded-full text-white ${statusColors[task.status]}`}>{task.status}</span>
                        </div>
                        <div className="flex justify-between">
                            <span className="text-muted-foreground">Assignee:</span>
                            <span>{task.assignee || 'Unassigned'}</span>
                        </div>
                        <div className="flex justify-between">
                            <span className="text-muted-foreground">Due Date:</span>
                            <span>{new Date(task.due_date).toLocaleDateString()}</span>
                        </div>
                    </div>
                </div>
            ))}
        </div>
    </div>;
};

const KanbanView: React.FC<{ tasks: Task[], onTaskStatusChange: (taskId: string, newStatus: TaskStatus) => void }> = ({ tasks, onTaskStatusChange }) => {
    const [draggedTaskId, setDraggedTaskId] = useState<string | null>(null);
    
    const onDragStart = (e: React.DragEvent<HTMLDivElement>, taskId: string) => {
        setDraggedTaskId(taskId);
    };

    const onDragOver = (e: React.DragEvent<HTMLDivElement>) => {
        e.preventDefault();
    };

    const onDrop = (e: React.DragEvent<HTMLDivElement>, newStatus: TaskStatus) => {
        e.preventDefault();
        if (draggedTaskId) {
            onTaskStatusChange(draggedTaskId, newStatus);
            setDraggedTaskId(null);
        }
    };
    
    const columns: { status: TaskStatus, title: string }[] = [
        { status: TaskStatus.TODO, title: 'To Do' },
        { status: TaskStatus.DOING, title: 'In Progress' },
        { status: TaskStatus.REVIEW, title: 'Review' },
        { status: TaskStatus.DONE, title: 'Done' },
    ];

    return <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-6 h-full">
        {columns.map(({ status, title }) => (
            <div key={status} className="flex flex-col bg-card rounded-lg" onDragOver={onDragOver} onDrop={(e) => onDrop(e, status)}>
                <h3 className="p-4 font-semibold text-lg border-b border-border">{title} ({tasks.filter(t => t.status === status).length})</h3>
                <div className="p-4 space-y-4 overflow-y-auto">
                    {tasks.filter(t => t.status === status).map(task => (
                        <div key={task.id} draggable onDragStart={(e) => onDragStart(e, task.id)} className="p-4 bg-secondary border border-border rounded-lg shadow-sm cursor-grab">
                            <p className="font-semibold mb-2">{task.title}</p>
                            <div className="flex justify-between items-center">
                                <span className="text-sm text-muted-foreground">{new Date(task.due_date).toLocaleDateString()}</span>
                                <span className="text-sm">{task.assignee || 'Unassigned'}</span>
                            </div>
                            <div className={`mt-2 h-1 rounded-full ${priorityColors[task.priority]}`}></div>
                        </div>
                    ))}
                </div>
            </div>
        ))}
    </div>;
};

const GanttView: React.FC<{ tasks: Task[], employees: Employee[] }> = ({ tasks, employees }) => {
    const svgRef = useRef<SVGSVGElement | null>(null);
    const wrapperRef = useRef<HTMLDivElement | null>(null);
    const [timeScale, setTimeScale] = useState<'weekly' | 'monthly'>('weekly');
    
    useEffect(() => {
        if (!svgRef.current || !wrapperRef.current || tasks.length === 0) {
            if (svgRef.current) select(svgRef.current).selectAll("*").remove();
            return;
        }

        const sortedTasks = [...tasks].sort((a, b) => new Date(a.created_at).getTime() - new Date(b.created_at).getTime());
        
        const svg = select(svgRef.current);
        svg.selectAll("*").remove();

        const rowHeight = 40;
        const rowPadding = 10;
        const barHeight = rowHeight - rowPadding * 2;
        const margin = { top: 50, right: 30, bottom: 40, left: 200 };
        const containerWidth = wrapperRef.current.clientWidth;
        const taskDates = sortedTasks.flatMap(d => [new Date(d.created_at), new Date(d.due_date)]);
        const timeDomain = extent(taskDates) as [Date, Date];
        timeDomain[0] = timeDay.offset(timeDomain[0], -3);
        timeDomain[1] = timeDay.offset(timeDomain[1], 3);

        const days = timeDay.count(timeDomain[0], timeDomain[1]);
        
        const pixelsPerDay = timeScale === 'monthly' ? 10 : 30;
        const calculatedWidth = days * pixelsPerDay;
        
        const width = Math.max(containerWidth, calculatedWidth);

        const height = sortedTasks.length * rowHeight;
        
        svg.attr("width", width + margin.left + margin.right)
           .attr("height", height + margin.top + margin.bottom);

        const g = svg.append("g").attr("transform", `translate(${margin.left},${margin.top})`);
        
        
        const xScale = scaleTime().domain(timeDomain).range([0, width]);
        const yScale = scaleBand().domain(sortedTasks.map(d => d.id)).range([0, height]).padding(0.2);
        
        // --- Draw Grid and Axes ---
        const borderHsl = getComputedStyle(document.documentElement).getPropertyValue('--border').trim();
        const foregroundHsl = getComputedStyle(document.documentElement).getPropertyValue('--foreground').trim();
        const mutedForegroundHsl = getComputedStyle(document.documentElement).getPropertyValue('--muted-foreground').trim();

        const tickColor = `hsl(${borderHsl})`;
        const textColor = `hsl(${foregroundHsl})`;
        const mutedColor = `hsl(${mutedForegroundHsl})`;
        
        const isDarkMode = document.documentElement.classList.contains('dark');
        const gridColor = isDarkMode ? 'rgba(255, 255, 255, 0.1)' : tickColor;


        const gridTicks = timeScale === 'weekly' ? timeDay.every(1) : timeWeek.every(1);

        // Vertical grid lines
        g.append("g").attr("class", "grid-lines")
          .selectAll("line")
          .data(xScale.ticks(gridTicks))
          .enter().append("line")
            .attr("x1", d => xScale(d))
            .attr("x2", d => xScale(d))
            .attr("y1", 0)
            .attr("y2", height)
            .attr("stroke", gridColor)
            .attr("stroke-opacity", 0.5)
            .attr("stroke-dasharray", "2,2");

        // Top Month Axis
        const monthAxis = axisTop(xScale).ticks(timeMonth.every(1)).tickFormat(timeFormat("%B %Y"));
        g.append("g").attr("class", "month-axis").call(monthAxis)
          .selectAll("text").style("fill", mutedColor).style("font-size", "14px");
          
        // Bottom "sub" Axis (days for weekly, weeks for monthly)
        if (timeScale === 'weekly') {
            const dayAxis = axisTop(xScale).ticks(timeDay.every(1)).tickFormat(timeFormat("%d"));
            g.append("g").attr("class", "day-axis").attr("transform", "translate(0, 25)").call(dayAxis)
              .selectAll("text").style("fill", textColor);
        } else { // 'monthly'
            const weekAxis = axisTop(xScale).ticks(timeWeek.every(1)).tickFormat(timeFormat("W%U")); // "W23" for week 23
            g.append("g").attr("class", "week-axis").attr("transform", "translate(0, 25)").call(weekAxis)
                .selectAll("text").style("fill", textColor).style("font-size", "10px");
        }
        
        g.selectAll(".domain").remove();
        g.selectAll(".tick line").attr("stroke", gridColor);

        // --- Today Marker ---
        const today = new Date();
        if (today >= timeDomain[0] && today <= timeDomain[1]) {
            g.append("line")
                .attr("class", "today-marker")
                .attr("x1", xScale(today))
                .attr("x2", xScale(today))
                .attr("y1", -25)
                .attr("y2", height)
                .attr("stroke", "hsl(var(--primary))")
                .attr("stroke-width", 2);
            g.append("text")
                .attr("x", xScale(today))
                .attr("y", -30)
                .attr("text-anchor", "middle")
                .text("Today")
                .style("fill", "hsl(var(--primary))")
                .style("font-weight", "bold");
        }
        
        // --- Draw Bars and Text ---
        const bars = g.selectAll(".task-group")
            .data(sortedTasks)
            .enter().append("g")
            .attr("class", "task-group")
            .attr("transform", d => `translate(0, ${yScale(d.id)!})`);
        
        const priorityColorMap: { [key in TaskPriority]: string } = {
            [TaskPriority.LOW]: "#3b82f6",
            [TaskPriority.MEDIUM]: "#f59e0b",
            [TaskPriority.HIGH]: "#ef4444",
            [TaskPriority.CRITICAL]: "#dc2626",
        };
        const statusColorMap: { [key in TaskStatus]: string } = {
            [TaskStatus.TODO]: "#a1a1aa",
            [TaskStatus.DOING]: "#60a5fa",
            [TaskStatus.REVIEW]: "#a78bfa",
            [TaskStatus.DONE]: "#4ade80",
        };
        
        bars.append("rect")
            .attr("class", "task-bar")
            .attr("x", d => xScale(new Date(d.created_at)))
            .attr("y", rowPadding)
            .attr("width", d => Math.max(0, xScale(new Date(d.due_date)) - xScale(new Date(d.created_at))))
            .attr("height", barHeight)
            .attr("rx", 8)
            .attr("ry", 8)
            .attr("fill", d => statusColorMap[d.status]);

        bars.append("clipPath")
           .attr("id", d => `clip-${d.id}`)
           .append("rect")
            .attr("x", d => xScale(new Date(d.created_at)) + 10)
            .attr("y", rowPadding)
            .attr("width", d => Math.max(0, xScale(new Date(d.due_date)) - xScale(new Date(d.created_at)) - 15))
            .attr("height", barHeight);

        bars.append("text")
            .attr("class", "task-label")
            .attr("x", d => xScale(new Date(d.created_at)) + 10)
            .attr("y", rowHeight / 2)
            .attr("dy", "0.35em")
            .text(d => d.title)
            .style("fill", "white")
            .style("font-weight", "500")
            .attr("clip-path", d => `url(#clip-${d.id})`);

        // Add assignee avatar
        bars.each(function(d: Task) {
            const assignee = employees.find(e => e.name === d.assignee);
            if (assignee?.avatar) {
                select(this).append("image")
                    .attr("xlink:href", assignee.avatar)
                    .attr("x", xScale(new Date(d.due_date)) - 30)
                    .attr("y", rowPadding + 2)
                    .attr("width", barHeight - 4)
                    .attr("height", barHeight - 4)
                    .attr("clip-path", "circle(50%)");
            }
        });
        
        // Task names on the left
        const yAxisLabels = g.append("g").attr("class", "y-axis-labels");
        yAxisLabels.selectAll("text")
          .data(sortedTasks)
          .enter().append("text")
            .attr("x", -10)
            .attr("y", d => yScale(d.id)! + rowHeight / 2)
            .attr("dy", "0.35em")
            .attr("text-anchor", "end")
            .text(d => d.title.length > 25 ? d.title.substring(0, 25) + "..." : d.title)
            .style("fill", textColor);

    }, [tasks, employees, timeScale]);

    if(tasks.length === 0) {
      return <div className="flex items-center justify-center h-full text-muted-foreground">No tasks for this project.</div>
    }

    return (
        <div className="w-full h-full flex flex-col">
            <div className="flex justify-end mb-4">
                <div className="inline-flex rounded-md shadow-sm bg-card border border-border">
                    <button onClick={() => setTimeScale('weekly')} className={`px-4 py-2 text-sm font-medium rounded-l-md transition-colors ${timeScale === 'weekly' ? 'bg-secondary text-primary' : 'hover:bg-accent'}`}>
                        Weekly
                    </button>
                    <button onClick={() => setTimeScale('monthly')} className={`px-4 py-2 text-sm font-medium rounded-r-md border-l border-border transition-colors ${timeScale === 'monthly' ? 'bg-secondary text-primary' : 'hover:bg-accent'}`}>
                        Monthly
                    </button>
                </div>
            </div>
            <div className="flex-1 overflow-x-auto" ref={wrapperRef}><svg ref={svgRef}></svg></div>
        </div>
    );
};

export default DashboardPage;