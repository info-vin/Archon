import type React from "react";
import { Activity, CheckCircle2, ListTodo, Pin } from "lucide-react";
import { isOptimistic } from "../../shared/utils/optimistic";
import { OptimisticIndicator } from "../../ui/primitives/OptimisticIndicator";
import { SelectableCard } from "../../ui/primitives";
import { StatPill } from "../../ui/primitives/pill";
import { cn } from "../../ui/primitives/styles";
import type { Project } from "../types";

export interface SidebarProjectCardProps {
  project: Project;
  isSelected: boolean;
  taskCounts: {
    todo: number;
    doing: number;
    review: number;
    done: number;
  };
  onSelect: () => void;
}

export const SidebarProjectCard: React.FC<SidebarProjectCardProps> = ({
  project,
  isSelected,
  taskCounts,
  onSelect,
}) => {
  const optimistic = isOptimistic(project);

  const getBackgroundClass = () => {
    if (project.pinned)
      return "bg-gradient-to-b from-purple-100/80 via-purple-50/30 to-purple-100/50 dark:from-purple-900/30 dark:via-purple-900/20 dark:to-purple-900/10";
    if (isSelected)
      return "bg-gradient-to-b from-white/70 via-purple-50/20 to-white/50 dark:from-white/5 dark:via-purple-900/5 dark:to-black/20";
    return "bg-gradient-to-b from-white/80 to-white/60 dark:from-white/10 dark:to-black/30";
  };

  return (
    <SelectableCard
      isSelected={isSelected}
      isPinned={project.pinned}
      showAuroraGlow={isSelected}
      onSelect={onSelect}
      size="none"
      blur="md"
      className={cn("p-2", getBackgroundClass(), optimistic && "opacity-80 ring-1 ring-cyan-400/30")}
    >
      <div className="space-y-2">
        {/* Title */}
        <div className="flex items-center justify-between">
          <h4
            className={cn(
              "font-medium text-sm line-clamp-1 flex-1",
              isSelected ? "text-purple-700 dark:text-purple-300" : "text-gray-700 dark:text-gray-300",
            )}
          >
            {project.title}
          </h4>
          <div className="flex items-center gap-1">
            {project.pinned && (
              <div
                className="flex items-center gap-1 px-1.5 py-0.5 bg-purple-500 dark:bg-purple-600 text-white text-[9px] font-bold rounded-full"
                aria-label="Pinned"
              >
                <Pin className="w-2.5 h-2.5" aria-hidden="true" />
              </div>
            )}
            <OptimisticIndicator isOptimistic={optimistic} />
          </div>
        </div>

        {/* Status Pills - horizontal layout with icons */}
        <div className="flex items-center gap-1.5">
          <StatPill color="pink" value={taskCounts.todo} size="sm" icon={<ListTodo className="w-3 h-3" />} />
          <StatPill
            color="blue"
            value={taskCounts.doing + taskCounts.review}
            size="sm"
            icon={<Activity className="w-3 h-3" />}
          />
          <StatPill color="green" value={taskCounts.done} size="sm" icon={<CheckCircle2 className="w-3 h-3" />} />
        </div>
      </div>
    </SelectableCard>
  );
};
