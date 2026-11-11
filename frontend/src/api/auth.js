// Fetch calls for /api/auth. Login sets the httpOnly cookie; logout clears it.
import { apiFetch } from './client.js'

export function login(username, password) {
  return apiFetch('/api/auth/login', { method: 'POST', body: { username, password } })
}

export function register(username, email, password) {
  return apiFetch('/api/auth/register', { method: 'POST', body: { username, email, password } })
}

export function logout() {
  return apiFetch('/api/auth/logout', { method: 'POST' })
}

export function getMe() {
  return apiFetch('/api/auth/me')
}
