// App: decides which screen to show.
//   1. On start it asks GET /api/auth/me whether the login cookie is still valid.
//   2. Logged in  -> ChatPage
//      Not logged -> LoginPage
import { useCallback, useEffect, useState } from 'react'
import ChatPage from './pages/ChatPage.jsx'
import LoginPage from './pages/LoginPage.jsx'
import { getMe, logout } from './api/auth.js'

export default function App() {
  const [user, setUser] = useState(null)
  const [checking, setChecking] = useState(true) // true until /me has answered

  useEffect(() => {
    getMe()
      .then(setUser)
      .catch(() => setUser(null)) // 401 = not logged in
      .finally(() => setChecking(false))
  }, [])

  // Log out button: clear the cookie on the server, then show the login page
  async function handleLogout() {
    try {
      await logout()
    } finally {
      setUser(null)
    }
  }

  // The API answered 401 (cookie expired): show the login page.
  // useCallback keeps the same function between renders.
  const handleSessionExpired = useCallback(() => setUser(null), [])

  if (checking) return <div className="splash">Loading…</div>
  if (!user) return <LoginPage onLoggedIn={setUser} />
  return <ChatPage user={user} onLogout={handleLogout} onSessionExpired={handleSessionExpired} />
}
