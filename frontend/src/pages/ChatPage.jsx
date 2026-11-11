// ChatPage: the main screen after login. It holds the app state and talks
// to the API (through src/api/), then hands data down to the components:
//
//   [ Sidebar ] [ Home:      ChatWindow (full width)            ]
//               [ Documents: DocumentsPage | ChatWindow (right) ]
//
// State kept here:
//   conversations  list for the sidebar (newest updated first, from the API)
//   active         the open conversation with its messages (or null)
//   page           'home' or 'documents'
import { useCallback, useEffect, useState } from 'react'
import Sidebar from '../components/Sidebar.jsx'
import ChatWindow from '../components/ChatWindow.jsx'
import DocumentsPage from './DocumentsPage.jsx'
import {
  listConversations,
  getConversation,
  createConversation,
  saveMessage,
  deleteConversation,
} from '../api/conversations.js'
import { getHealth } from '../api/client.js'

export default function ChatPage({ user, onLogout, onSessionExpired }) {
  const [page, setPage] = useState('home')
  const [conversations, setConversations] = useState([])
  const [listLoading, setListLoading] = useState(true)
  const [active, setActive] = useState(null)
  const [chatLoading, setChatLoading] = useState(false)
  const [sending, setSending] = useState(false)
  const [error, setError] = useState(null)
  const [healthy, setHealthy] = useState(null)

  // Shared error handling: 401 means the login cookie expired -> back to login
  const handleError = useCallback(
    (err) => {
      if (err.status === 401) onSessionExpired()
      else setError(err.message)
    },
    [onSessionExpired],
  )

  // Reload the sidebar list (after creating, messaging or deleting a chat)
  async function refreshList() {
    try {
      setConversations(await listConversations())
    } catch (err) {
      handleError(err)
    }
  }

  // On first load: fetch the chat list and check the backend health
  useEffect(() => {
    listConversations()
      .then(setConversations)
      .catch(handleError)
      .finally(() => setListLoading(false))
    getHealth()
      .then(() => setHealthy(true))
      .catch(() => setHealthy(false))
  }, [handleError])

  // Click a chat in the sidebar -> load it with all its messages
  async function selectChat(id) {
    if (id === active?.id) return
    setError(null)
    setChatLoading(true)
    setActive({ id, messages: [] }) // highlight it in the sidebar right away
    try {
      setActive(await getConversation(id))
    } catch (err) {
      handleError(err)
      setActive(null)
    } finally {
      setChatLoading(false)
    }
  }

  // "+" button -> create a fresh, empty conversation and open it.
  // The POST already returns the new chat, so it is put at the top of the
  // sidebar list directly (no second request to reload the whole list).
  async function newChat() {
    setError(null)
    try {
      const chat = await createConversation()
      setActive({ ...chat, messages: [] })
      setConversations((list) => [chat, ...list])
    } catch (err) {
      handleError(err)
    }
  }

  // Send button -> save the user's message. If no chat is open yet, create
  // one first. (The AI's answer comes with streaming in Week 2.)
  // Returns true on success so ChatWindow knows it can clear the input.
  async function sendMessage(content) {
    setError(null)
    setSending(true)
    try {
      let chat = active
      if (!chat) {
        chat = { ...(await createConversation()), messages: [] }
      }
      const message = await saveMessage(chat.id, 'user', content)
      setActive({ ...chat, messages: [...chat.messages, message] })
      await refreshList() // the chat moves to the top of the list
      return true
    } catch (err) {
      handleError(err)
      return false
    } finally {
      setSending(false)
    }
  }

  // Confirmed in the sidebar dialog -> delete the chat (messages go with it)
  async function deleteChat(id) {
    setError(null)
    try {
      await deleteConversation(id)
      if (active?.id === id) setActive(null)
      await refreshList()
    } catch (err) {
      handleError(err)
    }
  }

  const chatWindow = (
    <ChatWindow
      conversation={active}
      loading={chatLoading}
      sending={sending}
      error={error}
      healthy={healthy}
      userInitial={user.username[0].toUpperCase()}
      onSend={sendMessage}
      onNewChat={newChat}
    />
  )

  return (
    <div className="app">
      <Sidebar
        user={user}
        page={page}
        onNavigate={setPage}
        conversations={conversations}
        loading={listLoading}
        activeId={active?.id}
        onSelect={selectChat}
        onNewChat={newChat}
        onDelete={deleteChat}
        onLogout={onLogout}
      />

      {page === 'home' ? (
        <main className="main main--home">{chatWindow}</main>
      ) : (
        <main className="main main--documents">
          <DocumentsPage />
          {chatWindow}
        </main>
      )}
    </div>
  )
}
