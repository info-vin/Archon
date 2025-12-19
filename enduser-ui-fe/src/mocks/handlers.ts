import { http, HttpResponse } from 'msw';

// Define the mock data for assignable users
const mockAssignableUsers = [
  { id: '2', name: 'Alice Johnson', role: 'Engineer' },
  { id: '3', name: 'Bob Williams', role: 'Marketer' },
];

const mockAiAgents = [
  { id: 'ai-researcher-1', name: '(AI) Market Researcher', role: 'Market Researcher' },
  { id: 'ai-knowledge-expert-1', name: '(AI) Internal Knowledge Expert', role: 'Internal Knowledge Expert' },
];

export const handlers = [
  // Handler for the new assignable users API
  http.get('/api/assignable-users', () => {
    return HttpResponse.json(mockAssignableUsers);
  }),

  // Handler for the new assignable AI agents API
  http.get('/api/agents/assignable', () => {
    return HttpResponse.json(mockAiAgents);
  }),

  // It's good practice to have a fallback for other api calls
  // to avoid test errors. For now, we can return empty arrays.
  http.get('/api/projects', () => {
    return HttpResponse.json([]);
  }),

  http.get('/api/tasks', () => {
    return HttpResponse.json([]);
  }),
];

