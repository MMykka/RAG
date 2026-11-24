// StatsPage: "Your usage". Loads the user's stats from GET /api/users/:id/stats
// every time the page is opened, so the numbers include the latest chats,
// then hands them to StatsDashboard.
import { useEffect, useState } from 'react'
import StatsDashboard from '../components/StatsDashboard.jsx'
import { getStats } from '../api/stats.js'

export default function StatsPage({ user, onSessionExpired }) {
  const [stats, setStats] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    let current = true // ignore a late answer if the page was left in the meantime
    getStats(user.id)
      .then((data) => current && setStats(data))
      .catch((err) => {
        if (!current) return
        if (err.status === 401) onSessionExpired()
        else setError(err.message)
      })
    return () => {
      current = false
    }
  }, [user.id, onSessionExpired])

  return (
    <section className="stats">
      <h2 className="stats__title">Your usage</h2>
      <p className="stats__intro">Counted from your own chats only.</p>

      {error ? (
        <div className="chat__error" role="alert">
          {error}
        </div>
      ) : stats ? (
        <StatsDashboard stats={stats} />
      ) : (
        <div className="chat__loading">Loading stats…</div>
      )}
    </section>
  )
}
