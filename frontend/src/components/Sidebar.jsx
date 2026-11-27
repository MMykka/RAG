// Sidebar: left column of the app.
//   1. Profile (avatar + username). Clicking it opens a small menu with "Log out".
//   2. Navigation: Home (chat with the AI), Documents (upload knowledge) and
//      Stats (your usage numbers).
//   3. CHATS: every past conversation (newest first) with a truncated title
//      and a timestamp. Click one to open it; the pencil icon renames it in
//      place (Enter or clicking away saves, Escape cancels); the trash icon
//      deletes it after a confirmation dialog.
//      Above the list, a search box: from 2 letters on (after a short pause) your
//      chats whose title or messages match replace the list, each with a snippet
//      in which the matching words are highlighted. Click one to open it;
//      Escape or the x clears the search.
//   4. Settings at the bottom (placeholder, no settings page in the plan yet).
import { useEffect, useRef, useState } from 'react'
import {
  HomeIcon,
  DocumentsIcon,
  StatsIcon,
  ChevronDownIcon,
  SettingsIcon,
  PlusIcon,
  TrashIcon,
  PencilIcon,
  SearchIcon,
  CloseIcon,
  LogOutIcon,
} from './Icons.jsx'
import { formatRelative } from '../utils/time.js'

const MIN_SEARCH = 2 // letters before a search starts (the server needs at least 2)
const SEARCH_PAUSE_MS = 300 // wait until typing pauses, so not every key press is a request

// A snippet from the server marks each matching word as \u0002word\u0003.
// Turn that into text with <mark> around the matches (React escapes the text, so nothing in a
// message can turn into HTML).
function Highlighted({ text }) {
  // eslint-disable-next-line no-control-regex -- \u0002/\u0003 are the server's highlight markers, on purpose
  return text.split(/(\u0002[^\u0003]*\u0003)/).map((part, i) =>
    part.startsWith('\u0002') ? <mark key={i}>{part.slice(1, -1)}</mark> : <span key={i}>{part}</span>,
  )
}

export default function Sidebar({
  user,
  page,
  onNavigate,
  conversations,
  loading,
  activeId,
  onSelect,
  onNewChat,
  onDelete,
  onRename,
  onSearch,
  onLogout,
}) {
  const [query, setQuery] = useState('') // what is typed in the search box
  const [results, setResults] = useState(null) // search results (null = no search shown yet)
  const [searchError, setSearchError] = useState(null)
  const searching = query.trim().length >= MIN_SEARCH

  // Always call the latest onSearch without restarting the search effect every time the page re-renders
  const onSearchRef = useRef(onSearch)
  useEffect(() => {
    onSearchRef.current = onSearch
  }, [onSearch])

  // Search after typing pauses; a late answer for an older query is ignored
  useEffect(() => {
    const q = query.trim()
    if (q.length < MIN_SEARCH) return undefined
    let current = true
    const timer = setTimeout(() => {
      onSearchRef.current(q)
        .then((found) => {
          if (!current) return
          setResults(found)
          setSearchError(null)
        })
        .catch((err) => current && setSearchError(err.message))
    }, SEARCH_PAUSE_MS)
    return () => {
      current = false
      clearTimeout(timer)
    }
  }, [query])

  function clearSearch() {
    setQuery('')
    setResults(null)
    setSearchError(null)
  }

  const [menuOpen, setMenuOpen] = useState(false) // profile menu open?
  const [pendingDelete, setPendingDelete] = useState(null) // chat waiting for "Delete?" confirmation
  const [editingId, setEditingId] = useState(null) // chat whose title is being edited
  const [draft, setDraft] = useState('') // the title being typed
  // Escape removes the input; a browser may fire "blur" while removing it, which would save.
  // This flag tells finishRename that the edit was cancelled.
  const cancelled = useRef(false)

  function startRename(chat) {
    cancelled.current = false
    setEditingId(chat.id)
    setDraft(chat.title)
  }

  // Enter or clicking away: save if the title really changed and is not empty
  function finishRename(chat) {
    setEditingId(null)
    if (cancelled.current) return
    const title = draft.trim()
    if (title && title !== chat.title) onRename(chat.id, title.slice(0, 255))
  }

  function cancelRename() {
    cancelled.current = true
    setEditingId(null)
  }

  return (
    <aside className="sidebar">
      {/* 1. Profile */}
      <div className="profile">
        <button className="profile__button" onClick={() => setMenuOpen((open) => !open)}>
          <span className="profile__avatar">{user.username[0].toUpperCase()}</span>
          <span className="profile__name">{user.username}</span>
          <ChevronDownIcon size={16} className="profile__chevron" />
        </button>
        {menuOpen && (
          <div className="profile__menu">
            <div className="profile__email">{user.email}</div>
            <button className="profile__menu-item" onClick={onLogout}>
              <LogOutIcon size={16} /> Log out
            </button>
          </div>
        )}
      </div>

      {/* 2. Navigation */}
      <nav className="nav">
        <button
          className={`nav__item ${page === 'home' ? 'nav__item--active' : ''}`}
          onClick={() => onNavigate('home')}
        >
          <HomeIcon /> Home
        </button>
        <button
          className={`nav__item ${page === 'documents' ? 'nav__item--active' : ''}`}
          onClick={() => onNavigate('documents')}
        >
          <DocumentsIcon /> Documents
        </button>
        <button
          className={`nav__item ${page === 'stats' ? 'nav__item--active' : ''}`}
          onClick={() => onNavigate('stats')}
        >
          <StatsIcon /> Stats
        </button>
      </nav>

      {/* 3. Chats */}
      <div className="sidebar__section">
        <div className="sidebar__label">
          <span>Chats</span>
          <button className="icon-button" title="New chat" onClick={onNewChat}>
            <PlusIcon size={16} />
          </button>
        </div>

        <div className="chat-search">
          <SearchIcon size={15} className="chat-search__icon" />
          <input
            className="chat-search__input"
            type="search"
            placeholder="Search chats"
            aria-label="Search your chats"
            value={query}
            maxLength={200}
            onChange={(event) => setQuery(event.target.value)}
            onKeyDown={(event) => event.key === 'Escape' && clearSearch()}
          />
          {query && (
            <button className="chat-search__clear" title="Clear search" aria-label="Clear search" onClick={clearSearch}>
              <CloseIcon size={14} />
            </button>
          )}
        </div>

        {searching ? (
          <div className="chat-list" aria-live="polite">
            {searchError && <div className="chat-list__empty">{searchError}</div>}
            {!searchError && results === null && <div className="chat-list__empty">Searching…</div>}
            {!searchError && results?.length === 0 && <div className="chat-list__empty">No chats match “{query.trim()}”</div>}
            {!searchError &&
              results?.map((hit) => (
                <button
                  key={hit.id}
                  className={`search-hit ${hit.id === activeId ? 'search-hit--active' : ''}`}
                  onClick={() => {
                    onSelect(hit.id)
                    clearSearch()
                  }}
                >
                  <span className="search-hit__title">{hit.title}</span>
                  {hit.snippet && (
                    <span className="search-hit__snippet">
                      <Highlighted text={hit.snippet} />
                    </span>
                  )}
                </button>
              ))}
          </div>
        ) : (
        <div className="chat-list">
          {loading && <div className="chat-list__empty">Loading…</div>}
          {!loading && conversations.length === 0 && (
            <div className="chat-list__empty">No chats yet</div>
          )}

          {conversations.map((chat) =>
            chat.id === editingId ? (
              <div key={chat.id} className="chat-item chat-item--editing">
                <input
                  className="chat-item__input"
                  value={draft}
                  maxLength={255}
                  autoFocus
                  aria-label="Chat title"
                  onChange={(event) => setDraft(event.target.value)}
                  onFocus={(event) => event.target.select()}
                  onBlur={() => finishRename(chat)}
                  onKeyDown={(event) => {
                    if (event.key === 'Enter') event.target.blur() // blur saves (finishRename)
                    if (event.key === 'Escape') cancelRename() // keep the old title
                  }}
                />
              </div>
            ) : (
            <div
              key={chat.id}
              className={`chat-item ${chat.id === activeId ? 'chat-item--active' : ''}`}
              onClick={() => onSelect(chat.id)}
              title={chat.title}
            >
              <span className="chat-item__title">{chat.title}</span>
              <span className="chat-item__time">{formatRelative(chat.updated_at)}</span>
              <button
                className="chat-item__rename"
                title="Rename chat"
                aria-label={`Rename “${chat.title}”`}
                onClick={(event) => {
                  event.stopPropagation() // don't also open the chat
                  startRename(chat)
                }}
              >
                <PencilIcon size={14} />
              </button>
              <button
                className="chat-item__delete"
                title="Delete chat"
                onClick={(event) => {
                  event.stopPropagation() // don't also open the chat
                  setPendingDelete(chat)
                }}
              >
                <TrashIcon size={15} />
              </button>
            </div>
            ),
          )}
        </div>
        )}
      </div>

      {/* 4. Settings */}
      <div className="sidebar__footer">
        <button className="nav__item">
          <SettingsIcon /> Settings
        </button>
      </div>

      {/* Delete confirmation dialog */}
      {pendingDelete && (
        <div className="modal-backdrop" onClick={() => setPendingDelete(null)}>
          <div className="modal" onClick={(event) => event.stopPropagation()}>
            <h3 className="modal__title">Delete chat?</h3>
            <p className="modal__text">
              “{pendingDelete.title}” and all its messages will be deleted. This cannot be undone.
            </p>
            <div className="modal__actions">
              <button className="button button--ghost" onClick={() => setPendingDelete(null)}>
                Cancel
              </button>
              <button
                className="button button--danger"
                onClick={() => {
                  onDelete(pendingDelete.id)
                  setPendingDelete(null)
                }}
              >
                Delete
              </button>
            </div>
          </div>
        </div>
      )}
    </aside>
  )
}
