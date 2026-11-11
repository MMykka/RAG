// Sidebar: left column of the app.
//   1. Profile (avatar + username). Clicking it opens a small menu with "Log out".
//   2. Navigation: Home (chat with the AI) and Documents (upload knowledge).
//   3. CHATS: every past conversation (newest first) with a truncated title
//      and a timestamp. Click one to open it; the trash icon deletes it
//      after a confirmation dialog.
//   4. Settings at the bottom (placeholder, no settings page in the plan yet).
import { useState } from 'react'
import {
  HomeIcon,
  DocumentsIcon,
  ChevronDownIcon,
  SettingsIcon,
  PlusIcon,
  TrashIcon,
  LogOutIcon,
} from './Icons.jsx'
import { formatRelative } from '../utils/time.js'

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
  onLogout,
}) {
  const [menuOpen, setMenuOpen] = useState(false) // profile menu open?
  const [pendingDelete, setPendingDelete] = useState(null) // chat waiting for "Delete?" confirmation

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
      </nav>

      {/* 3. Chats */}
      <div className="sidebar__section">
        <div className="sidebar__label">
          <span>Chats</span>
          <button className="icon-button" title="New chat" onClick={onNewChat}>
            <PlusIcon size={16} />
          </button>
        </div>

        <div className="chat-list">
          {loading && <div className="chat-list__empty">Loading…</div>}
          {!loading && conversations.length === 0 && (
            <div className="chat-list__empty">No chats yet</div>
          )}

          {conversations.map((chat) => (
            <div
              key={chat.id}
              className={`chat-item ${chat.id === activeId ? 'chat-item--active' : ''}`}
              onClick={() => onSelect(chat.id)}
              title={chat.title}
            >
              <span className="chat-item__title">{chat.title}</span>
              <span className="chat-item__time">{formatRelative(chat.updated_at)}</span>
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
          ))}
        </div>
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
