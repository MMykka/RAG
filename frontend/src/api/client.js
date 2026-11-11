// Shared fetch helper: every API call in the app goes through apiFetch.
// The auth token lives in an httpOnly cookie, so the browser attaches it
// automatically (same origin thanks to the Vite proxy / Nginx).

export class ApiError extends Error {
  constructor(status, message) {
    super(message)
    this.status = status
  }
}

export async function apiFetch(path, { method = 'GET', body } = {}) {
  const response = await fetch(path, {
    method,
    credentials: 'same-origin',
    headers: body !== undefined ? { 'Content-Type': 'application/json' } : undefined,
    body: body !== undefined ? JSON.stringify(body) : undefined,
  })

  if (response.status === 204) return null

  const data = await response.json().catch(() => null)
  if (!response.ok) {
    throw new ApiError(response.status, errorMessage(data, response.status))
  }
  return data
}

// FastAPI errors: {"detail": "text"} or {"detail": [{msg: ...}, ...]} for 422
function errorMessage(data, status) {
  const detail = data?.detail
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail) && detail.length > 0) {
    const field = detail[0].loc?.at(-1)
    return field ? `${field}: ${detail[0].msg}` : detail[0].msg
  }
  return `Request failed (${status})`
}

export function getHealth() {
  return apiFetch('/api/health')
}
