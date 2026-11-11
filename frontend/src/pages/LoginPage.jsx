// LoginPage: shown when nobody is logged in.
//   - "Log in" mode: username + password -> POST /api/auth/login
//   - "Create account" mode: username + email + password -> register, then log in
// On success the backend sets the httpOnly cookie, and onLoggedIn(user)
// tells App to show the chat screen.
import { useState } from 'react'
import { login, register } from '../api/auth.js'
import { MicIcon } from '../components/Icons.jsx'

export default function LoginPage({ onLoggedIn }) {
  const [mode, setMode] = useState('login') // 'login' or 'register'
  const [username, setUsername] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)

  const isRegister = mode === 'register'

  async function handleSubmit(event) {
    event.preventDefault()
    setError(null)
    setBusy(true)
    try {
      if (isRegister) await register(username, email, password)
      const user = await login(username, password)
      onLoggedIn(user)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  function switchMode() {
    setMode(isRegister ? 'login' : 'register')
    setError(null)
  }

  return (
    <div className="login">
      <form className="login__card" onSubmit={handleSubmit}>
        <div className="login__logo">
          <MicIcon size={22} />
        </div>
        <h1 className="login__title">{isRegister ? 'Create your account' : 'Welcome back'}</h1>
        <p className="login__subtitle">
          {isRegister ? 'Start chatting with your knowledge base.' : 'Log in to the AI Assistant.'}
        </p>

        <label className="field">
          <span>Username</span>
          <input value={username} onChange={(e) => setUsername(e.target.value)} autoComplete="username" required />
        </label>

        {isRegister && (
          <label className="field">
            <span>Email</span>
            <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="email" required />
          </label>
        )}

        <label className="field">
          <span>Password</span>
          <input
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete={isRegister ? 'new-password' : 'current-password'}
            required
          />
        </label>

        {error && <div className="login__error">{error}</div>}

        <button className="button button--primary login__submit" type="submit" disabled={busy}>
          {busy ? 'Please wait…' : isRegister ? 'Create account' : 'Log in'}
        </button>

        <button type="button" className="login__switch" onClick={switchMode}>
          {isRegister ? 'Already have an account? Log in' : "No account yet? Create one"}
        </button>
      </form>
    </div>
  )
}
