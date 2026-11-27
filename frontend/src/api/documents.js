// Fetch call for GET /api/documents: the files in the knowledge base (shared by every user)
import { apiFetch } from './client.js'

export function listDocuments() {
  return apiFetch('/api/documents')
}
