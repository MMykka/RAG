// Fetch call for GET /api/users/:id/stats (a user may only read their own)
import { apiFetch } from './client.js'

export function getStats(userId) {
  return apiFetch(`/api/users/${userId}/stats`)
}
