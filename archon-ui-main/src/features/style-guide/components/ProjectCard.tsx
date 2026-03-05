import { Pin } from "lucide-react";
import { StatPill } from "@/features/ui/primitives/pill";
import { SelectableCard } from "@/features/ui/primitives/selectable-card";
import { cn } from "@/features/ui/primitives/styles";

export const ProjectSidebarCard = ({
  project,
  isSelected,
  onSelect,
}: {
  project: any;
  isSelected: boolean;
  onSelect: () => void;
}) => {
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
      className={cn("p-2", getBackgroundClass())}
    >
      <div className="space-y-2">
        <div className="flex items-center justify-between">
          <h4
            className={cn(
              "font-medium text-sm line-clamp-1",
              isSelected ? "text-purple-700 dark:text-purple-300" : "text-gray-700 dark:text-gray-300",
            )}
          >
            {project.title}
          </h4>
          {project.pinned && (
            <div className="flex items-center gap-1 px-1.5 py-0.5 bg-purple-500 text-white text-[9px] font-bold rounded-full">
              <Pin className="w-2.5 h-2.5" />
            </div>
          )}
        </div>
        <div className="flex items-center gap-1.5 text-[9px]">
          <span className="text-gray-400">Tasks: {project.taskCounts.todo + project.taskCounts.doing + project.taskCounts.review + project.taskCounts.done}</span>
        </div>
      </div>
    </SelectableCard>
  );
};

export const ProjectCard = ({
  project,
  isSelected,
  onSelect,
}: {
  project: any;
  isSelected: boolean;
  onSelect: () => void;
}) => {
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
      blur="xl"
      className={cn("w-72 min-h-[180px] flex flex-col shrink-0", getBackgroundClass())}
    >
      <div className="flex-1 p-3 pb-2">
        <div className="flex flex-col items-center justify-center mb-4 min-h-[48px]">
          <h3
            className={cn(
              "font-medium text-center leading-tight line-clamp-2 transition-all duration-300",
              isSelected ? "text-gray-900 dark:text-white" : "text-gray-500 dark:text-gray-400",
            )}
          >
            {project.title}
          </h3>
        </div>
        <div className="flex items-stretch gap-2 w-full">
          <StatPill color="pink" value={project.taskCounts.todo} />
          <StatPill color="blue" value={project.taskCounts.doing + project.taskCounts.review} />
          <StatPill color="green" value={project.taskCounts.done} />
        </div>
      </div>
    </SelectableCard>
  );
};
