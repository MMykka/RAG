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

export function deleteConversation(id) {
  return apiFetch(`/api/conversations/${id}`, { method: 'DELETE' })
}
