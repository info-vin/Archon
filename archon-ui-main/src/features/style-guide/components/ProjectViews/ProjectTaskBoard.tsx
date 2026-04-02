import { DndProvider } from "react-dnd";
import { HTML5Backend } from "react-dnd-html5-backend";
import { DraggableCard } from "@/features/ui/primitives/draggable-card";
import { cn } from "@/features/ui/primitives/styles";
import { Edit, Trash2, Tag, User } from "lucide-react";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/features/ui/primitives/tooltip";
import { MOCK_TASKS } from "../../mock/projectsMock";

const TaskCardExample = ({ task, index }: { task: any; index: number }) => {
  const getPriorityColor = (priority: string) => {
    if (priority === "high") return { color: "bg-red-500", glow: "shadow-[0_0_10px_rgba(239,68,68,0.3)]" };
    if (priority === "medium") return { color: "bg-yellow-500", glow: "shadow-[0_0_10px_rgba(234,179,8,0.3)]" };
    return { color: "bg-green-500", glow: "shadow-[0_0_10px_rgba(34,197,94,0.3)]" };
  };

  const priorityStyle = getPriorityColor(task.priority);

  return (
    <div className="relative group">
      <DraggableCard itemType="task" itemId={task.id} index={index} size="none" className="min-h-[140px]">
        <div className={cn("absolute left-0 top-0 bottom-0 w-[3px] rounded-l-lg opacity-80 group-hover:w-[4px] group-hover:opacity-100 transition-all duration-300", priorityStyle.color, priorityStyle.glow)} />
        <div className="flex flex-col h-full p-3">
          <div className="flex items-center gap-2 mb-2 pl-1.5">
            {task.feature && (
              <div className="px-2 py-1 rounded-md text-xs font-medium flex items-center gap-1 backdrop-blur-md bg-cyan-500/10 text-cyan-600 dark:text-cyan-400 shadow-sm">
                <Tag className="w-3 h-3" />
                {task.feature}
              </div>
            )}
            <div className="ml-auto flex items-center gap-1" role="group" aria-label="Task actions">
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <button type="button" aria-label="Edit task" className="p-1 rounded hover:bg-cyan-500/10 text-gray-500 hover:text-cyan-500 transition-colors"><Edit className="w-3 h-3" /></button>
                  </TooltipTrigger>
                  <TooltipContent>Edit task</TooltipContent>
                </Tooltip>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <button type="button" aria-label="Delete task" className="p-1 rounded hover:bg-red-500/10 text-gray-500 hover:text-red-500 transition-colors"><Trash2 className="w-3 h-3" /></button>
                  </TooltipTrigger>
                  <TooltipContent>Delete task</TooltipContent>
                </Tooltip>
              </TooltipProvider>
            </div>
          </div>
          <h4 className="text-xs font-medium text-gray-900 dark:text-white mb-2 pl-1.5 line-clamp-2">{task.title}</h4>
          <div className="flex-1" />
          <div className="flex items-center justify-between mt-auto pt-2 pl-1.5 pr-3">
            <div className="flex items-center gap-1.5 px-2 py-1 rounded-md bg-white/50 dark:bg-black/30 border border-gray-200 dark:border-gray-700 text-xs">
              <User className="w-3 h-3 text-gray-500 dark:text-gray-400" />
              <span className="text-gray-700 dark:text-gray-300">{task.assignee}</span>
            </div>
            <div className={cn("w-2 h-2 rounded-full", priorityStyle.color)} />
          </div>
        </div>
      </DraggableCard>
    </div>
  );
};

export const ProjectTaskBoard = () => {
  const columns = [
    { status: "todo" as const, title: "Todo", color: "text-pink-500", glow: "bg-pink-500" },
    { status: "doing" as const, title: "Doing", color: "text-blue-500", glow: "bg-blue-500" },
    { status: "review" as const, title: "Review", color: "text-purple-500", glow: "bg-purple-500" },
    { status: "done" as const, title: "Done", color: "text-green-500", glow: "bg-green-500" },
  ];

  return (
    <DndProvider backend={HTML5Backend}>
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-2 min-h-[500px]">
        {columns.map(({ status, title, color, glow }) => {
          const tasks = MOCK_TASKS.filter((t: any) => t.status === status);
          return (
            <div key={status} className="flex flex-col">
              <div className="text-center py-3 relative">
                <h3 className={cn("font-mono text-sm font-medium", color)}>{title}</h3>
                <div className="mt-1 text-xs text-gray-500 dark:text-gray-400">{tasks.length}</div>
                <div className={cn("absolute bottom-0 left-[15%] right-[15%] w-[70%] mx-auto h-[1px]", glow, "shadow-md")} />
              </div>
              <div className="flex-1 p-2 space-y-2">
                {tasks.map((task: any, idx: number) => <TaskCardExample key={task.id} task={task} index={idx} />)}
              </div>
            </div>
          );
        })}
      </div>
    </DndProvider>
  );
};
