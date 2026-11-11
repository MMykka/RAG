// Turn an ISO timestamp from the API into a short label.

const MINUTE = 60 * 1000
const HOUR = 60 * MINUTE

function isSameDay(a, b) {
  return a.toDateString() === b.toDateString()
}

// Sidebar: "Just now", "5m ago", "14:03", "Yesterday", "Nov 3"
export function formatRelative(iso) {
  const date = new Date(iso)
  const now = new Date()
  const diff = now - date

  if (diff < MINUTE) return 'Just now'
  if (diff < HOUR) return `${Math.floor(diff / MINUTE)}m ago`
  if (isSameDay(date, now)) {
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  }
  const yesterday = new Date(now)
  yesterday.setDate(now.getDate() - 1)
  if (isSameDay(date, yesterday)) return 'Yesterday'
  return date.toLocaleDateString([], { month: 'short', day: 'numeric' })
}

// Message bubbles: "Just now" for fresh messages, else time (and date if not today)
export function formatMessageTime(iso) {
  const date = new Date(iso)
  const now = new Date()
  if (now - date < MINUTE) return 'Just now'
  const time = date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  if (isSameDay(date, now)) return time
  return `${date.toLocaleDateString([], { month: 'short', day: 'numeric' })}, ${time}`
}
