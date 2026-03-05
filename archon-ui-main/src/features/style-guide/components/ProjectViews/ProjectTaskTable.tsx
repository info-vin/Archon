import { Tag, User } from "lucide-react";
import { cn } from "@/features/ui/primitives/styles";
import { MOCK_TASKS } from "../../mock/projectsMock";

export const ProjectTaskTable = () => {
  return (
    <div className="w-full">
      <div className="overflow-x-auto scrollbar-hide">
        <table className="w-full">
          <thead>
            <tr className="bg-gradient-to-r from-gray-50 to-gray-100 dark:from-gray-900 dark:to-gray-800 border-b-2 border-gray-200 dark:border-gray-700">
              <th className="w-1" />
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-700 dark:text-gray-300">Title</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-700 dark:text-gray-300 w-32">Status</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-700 dark:text-gray-300 w-40">Feature</th>
              <th className="px-4 py-3 text-left text-sm font-medium text-gray-700 dark:text-gray-300 w-36">Assignee</th>
            </tr>
          </thead>
          <tbody>
            {MOCK_TASKS.map((task, index) => {
              const getPriorityColor = (priority: string) => {
                if (priority === "high") return "bg-red-500";
                if (priority === "medium") return "bg-yellow-500";
                return "bg-green-500";
              };

              return (
                <tr key={task.id} className={cn("group transition-all duration-200", index % 2 === 0 ? "bg-white/50 dark:bg-black/50" : "bg-gray-50/80 dark:bg-gray-900/30", "hover:bg-gradient-to-r hover:from-cyan-50/70 hover:to-purple-50/70 dark:hover:from-cyan-900/20 dark:hover:to-purple-900/20", "border-b border-gray-200 dark:border-gray-800")}>
                  <td className="w-1 p-0"><div className={cn("w-1 h-full", getPriorityColor(task.priority))} /></td>
                  <td className="px-4 py-2"><span className="font-medium text-sm text-gray-900 dark:text-white">{task.title}</span></td>
                  <td className="px-4 py-2 w-32">
                    <span className={cn("px-2 py-1 text-xs rounded-md font-medium inline-block", 
                      task.status === "todo" && "bg-pink-500/10 text-pink-600",
                      task.status === "doing" && "bg-blue-500/10 text-blue-600",
                      task.status === "review" && "bg-purple-500/10 text-purple-600",
                      task.status === "done" && "bg-green-500/10 text-green-600"
                    )}>{task.status}</span>
                  </td>
                  <td className="px-4 py-2 w-40"><div className="flex items-center gap-1">{task.feature && <><Tag className="w-3 h-3 text-gray-500" /><span className="text-sm text-gray-700 dark:text-gray-300">{task.feature}</span></>}</div></td>
                  <td className="px-4 py-2 w-36"><div className="inline-flex items-center gap-1.5 px-2 py-1 rounded-md bg-white/70 dark:bg-black/40 border border-gray-300 dark:border-gray-600 backdrop-blur-sm"><User className="w-3 h-3 text-gray-500" /><span className="text-xs text-gray-700 dark:text-gray-300">{task.assignee}</span></div></td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};
