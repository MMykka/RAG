// Fetch calls for /api/conversations (all need a logged-in user)
import { apiFetch } from './client.js'

export function listConversations({ limit = 100, offset = 0 } = {}) {
  return apiFetch(`/api/conversations?limit=${limit}&offset=${offset}`)
}

export function getConversation(id) {
  return apiFetch(`/api/conversations/${id}`)
}

export function createConversation(title) {
  return apiFetch('/api/conversations', { method: 'POST', body: title ? { title } : {} })
}

export function saveMessage(conversationId, role, content) {
  return apiFetch(`/api/conversations/${conversationId}/messages`, {
    method: 'POST',
    body: { role, content },
  })
}

// Download link for a chat as a file (format 'md' or 'json'). The server sends
// it with Content-Disposition: attachment, so the browser saves it; no fetch needed.
export function exportUrl(id, format) {
  return `/api/conversations/${id}/export?format=${format}`
}

export function deleteConversation(id) {
  return apiFetch(`/api/conversations/${id}`, { method: 'DELETE' })
}
