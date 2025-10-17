import { http, HttpResponse } from 'msw';

// Define the mock data for assignable users
const mockAssignableUsers = [
  { id: '2', name: 'Alice Johnson', role: 'Engineer' },
  { id: '3', name: 'Bob Williams', role: 'Marketer' },
];

export const handlers = [
  // Handler for the new assignable users API
  http.get('/api/assignable-users', () => {
    return HttpResponse.json(mockAssignableUsers);
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
