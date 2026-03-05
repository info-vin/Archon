export const MOCK_PROJECTS = [
  {
    id: "1",
    title: "Design System Refactor",
    pinned: true,
    taskCounts: { todo: 5, doing: 2, review: 1, done: 12 },
  },
  {
    id: "2",
    title: "API Integration Layer",
    pinned: false,
    taskCounts: { todo: 3, doing: 1, review: 0, done: 8 },
  },
  {
    id: "3",
    title: "Mobile App Development",
    pinned: false,
    taskCounts: { todo: 8, doing: 0, review: 0, done: 0 },
  },
  {
    id: "4",
    title: "Documentation Updates",
    pinned: false,
    taskCounts: { todo: 2, doing: 1, review: 2, done: 15 },
  },
];

export const MOCK_TASKS = [
  {
    id: "1",
    title: "Update color palette",
    status: "todo" as const,
    assignee: "User",
    feature: "Design",
    priority: "high" as const,
  },
  {
    id: "2",
    title: "Refactor button component",
    status: "todo" as const,
    assignee: "AI",
    feature: "Components",
    priority: "medium" as const,
  },
  {
    id: "3",
    title: "Implement glassmorphism effects",
    status: "doing" as const,
    assignee: "User",
    feature: "Styling",
    priority: "high" as const,
  },
  {
    id: "4",
    title: "Add documentation",
    status: "review" as const,
    assignee: "User",
    feature: "Docs",
    priority: "low" as const,
  },
  {
    id: "5",
    title: "Setup project structure",
    status: "done" as const,
    assignee: "AI",
    feature: "Setup",
    priority: "high" as const,
  },
  {
    id: "6",
    title: "Create initial components",
    status: "done" as const,
    assignee: "User",
    feature: "Components",
    priority: "medium" as const,
  },
];

export const MOCK_DOCUMENTS = [
  { id: "1", title: "Project Overview", type: "spec" as const },
  { id: "2", title: "API Documentation", type: "api" as const },
  { id: "3", title: "Design Notes", type: "note" as const },
];
