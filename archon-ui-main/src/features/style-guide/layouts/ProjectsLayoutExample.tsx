import { LayoutGrid, List, FileText, ListTodo } from "lucide-react";
import { useState } from "react";
import { Button } from "@/features/ui/primitives/button";
import { PillNavigation, type PillNavigationItem } from "@/features/ui/primitives/pill-navigation";
import { cn } from "@/features/ui/primitives/styles";
import { MOCK_PROJECTS, MOCK_DOCUMENTS } from "../mock/projectsMock";
import { ProjectCard, ProjectSidebarCard } from "../components/ProjectCard";
import { ProjectTaskBoard } from "../components/ProjectViews/ProjectTaskBoard";
import { ProjectTaskTable } from "../components/ProjectViews/ProjectTaskTable";
import { ProjectDocView } from "../components/ProjectViews/ProjectDocView";

export const ProjectsLayoutExample = () => {
  const [selectedId, setSelectedId] = useState("1");
  const [activeTab, setActiveTab] = useState<"docs" | "tasks">("tasks");
  const [viewMode, setViewMode] = useState<"board" | "table">("board");
  const [selectedDoc, setSelectedDoc] = useState(MOCK_DOCUMENTS[0]);
  const [layoutMode, setLayoutMode] = useState<"horizontal" | "sidebar">("horizontal");
  const [sidebarExpanded, setSidebarExpanded] = useState(true);

  const selectedProject = MOCK_PROJECTS.find((p) => p.id === selectedId);

  const tabItems: PillNavigationItem[] = [
    { id: "docs", label: "Docs", icon: <FileText className="w-4 h-4" /> },
    { id: "tasks", label: "Tasks", icon: <ListTodo className="w-4 h-4" /> },
  ];

  const renderContent = () => {
    if (activeTab === "docs") {
      return <ProjectDocView doc={selectedDoc} onDocSelect={setSelectedDoc} />;
    }
    return viewMode === "board" ? <ProjectTaskBoard /> : <ProjectTaskTable />;
  };

  return (
    <div className="space-y-6 font-sans">
      <div className="flex justify-end">
        <div className="flex gap-1 p-1 bg-black/30 rounded-lg border border-white/10">
          <Button variant="ghost" size="sm" onClick={() => setLayoutMode("horizontal")} className={cn("px-3", layoutMode === "horizontal" && "bg-purple-500/20 text-purple-400")}><LayoutGrid className="w-4 h-4" /></Button>
          <Button variant="ghost" size="sm" onClick={() => setLayoutMode("sidebar")} className={cn("px-3", layoutMode === "sidebar" && "bg-purple-500/20 text-purple-400")}><List className="w-4 h-4" /></Button>
        </div>
      </div>

      {layoutMode === "horizontal" ? (
        <>
          <div className="w-full max-w-full">
            <div className="overflow-x-auto py-8 -mx-6 px-6 scrollbar-hide">
              <div className="flex gap-4 min-w-max">
                {MOCK_PROJECTS.map((project) => (
                  <ProjectCard key={project.id} project={project} isSelected={selectedId === project.id} onSelect={() => setSelectedId(project.id)} />
                ))}
              </div>
            </div>
          </div>
          <div className="flex items-center justify-between">
            <div className="flex-1" />
            <PillNavigation items={tabItems} activeSection={activeTab} onSectionClick={(id) => setActiveTab(id as any)} colorVariant="orange" size="small" showIcons={true} showText={true} />
            <div className="flex-1 flex justify-end">
              {activeTab === "tasks" && (
                <div className="flex gap-1 p-1 bg-black/30 rounded-lg border border-white/10">
                  <Button variant="ghost" size="sm" onClick={() => setViewMode("board")} className={cn("px-3", viewMode === "board" && "bg-cyan-500/20 text-cyan-400")}><LayoutGrid className="w-4 h-4" /></Button>
                  <Button variant="ghost" size="sm" onClick={() => setViewMode("table")} className={cn("px-3", viewMode === "table" && "bg-cyan-500/20 text-cyan-400")}><List className="w-4 h-4" /></Button>
                </div>
              )}
            </div>
          </div>
          <div className="mt-6 animate-in fade-in slide-in-from-bottom-4 duration-500">{renderContent()}</div>
        </>
      ) : (
        <div className="flex h-[800px] gap-6 bg-black/20 rounded-2xl border border-white/5 overflow-hidden">
          <aside className={cn("bg-black/40 border-r border-white/10 transition-all duration-300 flex flex-col", sidebarExpanded ? "w-64" : "w-16")}>
            <div className="p-4 border-b border-white/10 flex justify-between items-center">{sidebarExpanded && <span className="font-bold text-xs uppercase tracking-widest text-purple-400">Projects</span>}<Button variant="ghost" size="sm" onClick={() => setSidebarExpanded(!sidebarExpanded)}><List className="w-4 h-4" /></Button></div>
            <div className="flex-1 overflow-y-auto p-2 space-y-2">{MOCK_PROJECTS.map(p => (<ProjectSidebarCard key={p.id} project={p} isSelected={selectedId === p.id} onSelect={() => setSelectedId(p.id)} />))}</div>
          </aside>
          <main className="flex-1 flex flex-col p-6 overflow-hidden">
            <header className="flex justify-between items-center mb-8">
              <div><h2 className="text-2xl font-bold text-white">{selectedProject?.title}</h2><div className="flex gap-4 mt-2"><PillNavigation items={tabItems} activeSection={activeTab} onSectionClick={id => setActiveTab(id as any)} colorVariant="orange" size="small" /></div></div>
              {activeTab === "tasks" && (<div className="flex gap-1 p-1 bg-black/30 rounded-lg border border-white/10"><Button variant="ghost" size="sm" onClick={() => setViewMode("board")} className={cn("px-3", viewMode === "board" && "bg-cyan-500/20 text-cyan-400")}><LayoutGrid className="w-4 h-4" /></Button><Button variant="ghost" size="sm" onClick={() => setViewMode("table")} className={cn("px-3", viewMode === "table" && "bg-cyan-500/20 text-cyan-400")}><List className="w-4 h-4" /></Button></div>)}
            </header>
            <div className="flex-1 overflow-y-auto">{renderContent()}</div>
          </main>
        </div>
      )}
    </div>
  );
};
