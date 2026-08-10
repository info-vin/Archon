import { useMemo, useState } from "react";
import { KanbanColumn } from "../components/KanbanColumn";
import type { Task } from "../types";

interface BoardViewProps {
  tasks: Task[];
  projectId: string;
  onTaskMove: (taskId: string, newStatus: Task["status"]) => void;
  onTaskReorder: (taskId: string, targetIndex: number, status: Task["status"]) => void;
  onTaskEdit?: (task: Task) => void;
  onTaskDelete?: (task: Task) => void;
}

// PERFORMANCE: Move static columns array outside component to prevent recreation on every render.
const columns: Array<{ status: Task["status"]; title: string }> = [
  { status: "todo", title: "Todo" },
  { status: "doing", title: "Doing" },
  { status: "review", title: "Review" },
  { status: "done", title: "Done" },
];

export const BoardView = ({
  tasks,
  projectId,
  onTaskMove,
  onTaskReorder,
  onTaskEdit,
  onTaskDelete,
}: BoardViewProps) => {
  const [hoveredTaskId, setHoveredTaskId] = useState<string | null>(null);

  // PERFORMANCE: Memoize task grouping and sorting to prevent O(N) array filtering and sorting on every render, especially during frequent hoveredTaskId state changes.
  const groupedTasks = useMemo(() => {
    const groups: Record<Task["status"], Task[]> = {
      todo: [],
      doing: [],
      review: [],
      done: [],
    };

    tasks.forEach((task) => {
      groups[task.status].push(task);
    });

    Object.keys(groups).forEach((status) => {
      groups[status as Task["status"]].sort((a, b) => a.task_order - b.task_order);
    });

    return groups;
  }, [tasks]);

  return (
    <div className="flex flex-col relative w-full">
      {/* Board Columns Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-2 flex-1 p-2 min-h-[500px]">
        {columns.map(({ status }) => (
          <KanbanColumn
            key={status}
            status={status}
            tasks={groupedTasks[status]}
            projectId={projectId}
            onTaskMove={onTaskMove}
            onTaskReorder={onTaskReorder}
            onTaskEdit={onTaskEdit}
            onTaskDelete={onTaskDelete}
            hoveredTaskId={hoveredTaskId}
            onTaskHover={setHoveredTaskId}
          />
        ))}
      </div>
    </div>
  );
};
