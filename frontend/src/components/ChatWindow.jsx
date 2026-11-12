// ChatWindow: the "AI Assistant" panel.
//   - Header: mic avatar, "AI Assistant", status dot (green when /api/health
//     says the backend + database are up, red when not), "+" = new chat.
//   - Messages of the open conversation (a greeting is shown while empty).
//   - Input box with the send button. Enter sends.
// It does not call the API itself: ChatPage passes the data and the
// onSend / onNewChat functions in as props.
import { useEffect, useRef, useState } from 'react'
import MessageBubble from './MessageBubble.jsx'
import { MicIcon, PlusIcon, SendIcon } from './Icons.jsx'

const GREETING = "Hello! I'm ready to answer questions about your knowledge base."

export default function ChatWindow({
  conversation, // { id, title, messages: [...] } or null when no chat is open
  loading, // true while a chat is being fetched
  sending, // true while a message is being saved
  error, // text of the last error, or null
  healthy, // true / false / null (unknown yet)
  userInitial,
  onSend,
  onNewChat,
}) {
  const [text, setText] = useState('')
  const bottomRef = useRef(null)
  const messages = conversation?.messages ?? []

  // Scroll to the newest message whenever the list changes
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ block: 'end' })
  }, [messages.length, conversation?.id])

  async function handleSubmit(event) {
    event.preventDefault()
    const content = text.trim()
    if (!content || sending) return
    const ok = await onSend(content)
    if (ok) setText('') // keep the text if saving failed, so nothing is lost
  }

  return (
    <section className="chat">
      {/* Header */}
      <header className="chat__header">
        <div className="chat__header-avatar">
          <MicIcon size={20} />
        </div>
        <div>
          <div className="chat__header-title">AI Assistant</div>
          <div className="chat__header-status">
            <span className={`status-dot ${healthy === false ? 'status-dot--down' : ''}`} />
            {healthy === false ? 'Offline' : 'RAG Active'}
          </div>
        </div>
        <button className="icon-button chat__new" title="New chat" onClick={onNewChat}>
          <PlusIcon size={20} />
        </button>
      </header>

      {/* Messages */}
      <div className="chat__messages">
        {loading ? (
          <div className="chat__loading">Loading chat…</div>
        ) : (
          <>
            {messages.length === 0 && <MessageBubble role="assistant" content={GREETING} />}
            {messages.map((message) => (
              <MessageBubble
                key={message.id}
                role={message.role}
                content={message.content}
                createdAt={message.created_at}
                userInitial={userInitial}
              />
            ))}
          </>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <form className="chat__composer" onSubmit={handleSubmit}>
        {error && <div className="chat__error">{error}</div>}
        <div className="chat__input-wrap">
          <input
            className="chat__input"
            placeholder="Ask a question about your documents..."
            value={text}
            onChange={(event) => setText(event.target.value)}
            disabled={loading}
          />
          <button
            className={`chat__send ${sending ? 'chat__send--busy' : ''}`}
            type="submit"
            disabled={!text.trim() || sending || loading}
            title="Send"
          >
            <SendIcon size={16} />
          </button>
        </div>
        <div className="chat__disclaimer">AI can make mistakes. Verify important information.</div>
      </form>
    </section>
  )
}
