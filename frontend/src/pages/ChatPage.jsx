// ChatPage: the main screen after login. It holds the app state and talks
// to the API (through src/api/), then hands data down to the components:
//
//   [ Sidebar ] [ Home:      ChatWindow (full width)            ]
//               [ Documents: DocumentsPage | ChatWindow (right) ]
//               [ Stats:     StatsPage (full width)             ]
//
// State kept here:
//   conversations  list for the sidebar (newest updated first, from the API)
//   active         the open conversation with its messages (or null)
//   page           'home', 'documents' or 'stats'
//   stream         the answer being streamed right now (hooks/useStream.js)
import { useCallback, useEffect, useRef, useState } from 'react'
import Sidebar from '../components/Sidebar.jsx'
import ChatWindow from '../components/ChatWindow.jsx'
import DocumentsPage from './DocumentsPage.jsx'
import StatsPage from './StatsPage.jsx'
import {
  listConversations,
  getConversation,
  createConversation,
  deleteConversation,
  renameConversation,
} from '../api/conversations.js'
import { getHealth } from '../api/client.js'
import useStream from '../hooks/useStream.js'

export default function ChatPage({ user, onLogout, onSessionExpired }) {
  const [page, setPage] = useState('home')
  const [conversations, setConversations] = useState([])
  const [listLoading, setListLoading] = useState(true)
  const [active, setActive] = useState(null)
  const [chatLoading, setChatLoading] = useState(false)
  const [sending, setSending] = useState(false)
  const [error, setError] = useState(null)
  const [healthy, setHealthy] = useState(null)
  const stream = useStream()

  // The id of the open chat, readable inside a running send. If the user
  // opens another chat while an answer streams, the late answer must not
  // replace the chat they are looking at now.
  const activeIdRef = useRef(null)
  useEffect(() => {
    activeIdRef.current = active?.id ?? null
  }, [active?.id])

  // Shared error handling: 401 means the login cookie expired -> back to login
  const handleError = useCallback(
    (err) => {
      if (err.status === 401) onSessionExpired()
      else setError(err.message)
    },
    [onSessionExpired],
  )

  // Reload the sidebar list from the database. After sending or deleting it
  // runs in the background (no "await") to correct the list the browser
  // already updated itself.
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
    stream.stop() // switching chats cancels an answer that is still arriving
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
    stream.stop()
    setError(null)
    try {
      const chat = await createConversation()
      setActive({ ...chat, messages: [] })
      setConversations((list) => [chat, ...list])
    } catch (err) {
      handleError(err)
    }
  }

  // Send button -> ask the AI. If no chat is open yet, create one first.
  //   1. Show the question at once (a temporary copy until the server's is loaded).
  //   2. Stream the answer: ChatWindow shows it growing token by token. The
  //      server saves the question and, when it finishes, the full answer.
  //   3. Load the saved messages (real ids, the answer with its sources).
  // Returns true when the question went out, false if it never reached the
  // server (then ChatWindow puts the text back in the input box).
  async function sendMessage(content) {
    setError(null)
    setSending(true)
    let chat = active
    try {
      if (!chat) {
        chat = { ...(await createConversation()), messages: [] }
      }
    } catch (err) {
      handleError(err)
      setSending(false)
      return false
    }

    const now = new Date().toISOString()
    const question = { id: `pending-${Date.now()}`, role: 'user', content, created_at: now }
    activeIdRef.current = chat.id
    setActive({ ...chat, messages: [...chat.messages, question] })

    // Show first: move this chat to the top of the sidebar right away
    const { messages: _messages, ...summary } = chat // the sidebar does not need the messages
    setConversations((list) => [{ ...summary, updated_at: now }, ...list.filter((c) => c.id !== chat.id)])
    setSending(false)

    try {
      const result = await stream.start(chat.id, content)
      if (result.status === 'error') setError(result.error)

      // Correct after: the chat as the database has it now
      const saved = await getConversation(chat.id)
      if (activeIdRef.current === chat.id) {
        // A stopped answer is not saved; keep what had arrived on screen, marked as stopped
        const extra = result.status === 'stopped' && result.text
          ? [{ id: `stopped-${Date.now()}`, role: 'assistant', content: result.text, stopped: true }]
          : []
        setActive({ ...saved, messages: [...saved.messages, ...extra] })
      }
      refreshList() // background, no "await"
      return true
    } catch (err) {
      // Never reached the stream (401 / 404 / no connection): take the question back off the screen
      if (activeIdRef.current === chat.id) setActive(chat)
      handleError(err)
      return false
    }
  }

  // Confirmed in the sidebar dialog -> delete the chat (messages go with it).
  // Show first: the chat disappears at once. Then the server deletes it.
  // If the server fails, the old list comes back and the error is shown.
  async function deleteChat(id) {
    setError(null)
    const before = conversations // remember the list, in case we need to undo
    const wasActive = active?.id === id ? active : null
    if (wasActive) stream.stop() // its answer has nowhere to go any more
    setConversations((list) => list.filter((c) => c.id !== id))
    if (wasActive) setActive(null)
    try {
      await deleteConversation(id)
      refreshList() // correct after: background check with the database (no "await")
    } catch (err) {
      setConversations(before) // server said no -> put it back
      if (wasActive) setActive(wasActive)
      handleError(err)
    }
  }

  // Renamed in the sidebar. Show first: the new title appears at once (list and open chat).
  // If the server refuses, the old title comes back and the error is shown.
  async function renameChat(id, title) {
    setError(null)
    const old = conversations.find((c) => c.id === id)?.title
    const setTitle = (t) => {
      setConversations((list) => list.map((c) => (c.id === id ? { ...c, title: t } : c)))
      setActive((chat) => (chat?.id === id ? { ...chat, title: t } : chat))
    }
    setTitle(title)
    try {
      const saved = await renameConversation(id, title)
      setTitle(saved.title) // the server's version (spaces trimmed)
    } catch (err) {
      if (old !== undefined) setTitle(old)
      handleError(err)
    }
  }

  const chatWindow = (
    <ChatWindow
      conversation={active}
      loading={chatLoading}
      sending={sending}
      streaming={stream.streaming}
      streamText={stream.text}
      streamTokens={stream.tokens}
      onStop={stream.stop}
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
        onRename={renameChat}
        onLogout={onLogout}
      />

      {page === 'home' ? (
        <main className="main main--home">{chatWindow}</main>
      ) : page === 'stats' ? (
        <main className="main main--stats">
          <StatsPage user={user} onSessionExpired={onSessionExpired} />
        </main>
      ) : (
        <main className="main main--documents">
          <DocumentsPage onSessionExpired={onSessionExpired} />
          {chatWindow}
        </main>
      )}
    </div>
  )
}
