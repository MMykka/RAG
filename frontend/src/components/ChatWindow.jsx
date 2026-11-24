// ChatWindow: the "AI Assistant" panel.
//   - Header: mic avatar, "AI Assistant", status dot (green when /api/health
//     says the backend + database are up, red when not), download = export
//     the open chat as Markdown or JSON, "+" = new chat.
//   - Messages of the open conversation (a greeting is shown while empty).
//   - While the AI answers: a live bubble that grows token by token, with an
//     indicator under it ("Thinking…" until the first token, then the count).
//   - Input box with the send button. Enter sends. While an answer streams
//     sending is off and the send button turns into a Stop button (square icon).
// It does not call the API itself: ChatPage passes the data and the
// onSend / onStop / onNewChat functions in as props.
import { useEffect, useRef, useState } from 'react'
import MessageBubble from './MessageBubble.jsx'
import { DownloadIcon, MicIcon, PlusIcon, SendIcon, StopIcon } from './Icons.jsx'
import { exportUrl } from '../api/conversations.js'

const GREETING = "Hello! I'm ready to answer questions about your knowledge base."

export default function ChatWindow({
  conversation, // { id, title, messages: [...] } or null when no chat is open
  loading, // true while a chat is being fetched
  sending, // true while a new chat is being created for the first question
  streaming, // true while the AI's answer is arriving
  streamText, // the answer so far
  streamTokens, // how many tokens have arrived
  error, // text of the last error, or null
  healthy, // true / false / null (unknown yet)
  userInitial,
  onSend,
  onStop,
  onNewChat,
}) {
  const [text, setText] = useState('')
  const [exportOpen, setExportOpen] = useState(false) // download menu open?
  const bottomRef = useRef(null)
  const exportRef = useRef(null)
  const messages = conversation?.messages ?? []
  const busy = sending || streaming
  // Export needs a saved chat; while an answer streams the file would miss it
  const canExport = Boolean(conversation?.id) && !loading && !streaming

  // Close the download menu on a click outside it or on Escape
  useEffect(() => {
    if (!exportOpen) return
    const onPointer = (event) => {
      if (!exportRef.current?.contains(event.target)) setExportOpen(false)
    }
    const onKey = (event) => {
      if (event.key === 'Escape') setExportOpen(false)
    }
    document.addEventListener('mousedown', onPointer)
    document.addEventListener('keydown', onKey)
    return () => {
      document.removeEventListener('mousedown', onPointer)
      document.removeEventListener('keydown', onKey)
    }
  }, [exportOpen])

  // Scroll to the newest message whenever the list changes or the answer grows
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ block: 'end' })
  }, [messages.length, conversation?.id, streamText])

  async function handleSubmit(event) {
    event.preventDefault()
    const content = text.trim()
    if (!content || busy) return
    setText('') // clear at once; the question shows in the chat
    const ok = await onSend(content)
    if (!ok) setText(content) // it never reached the server: put it back, so nothing is lost
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
        <div className="chat__actions">
          <div className="export" ref={exportRef}>
            <button
              className="icon-button"
              title={canExport ? 'Download this chat' : 'Open a chat to download it'}
              aria-label="Download this chat"
              aria-haspopup="menu"
              aria-expanded={exportOpen}
              disabled={!canExport}
              onClick={() => setExportOpen((open) => !open)}
            >
              <DownloadIcon size={20} />
            </button>
            {exportOpen && canExport && (
              <div className="export__menu" role="menu">
                <div className="export__label">Download chat as</div>
                {/* Plain links: the server answers with Content-Disposition: attachment, so the browser saves the file */}
                <a className="export__item" role="menuitem" href={exportUrl(conversation.id, 'md')} onClick={() => setExportOpen(false)}>
                  Markdown <span className="export__ext">.md</span>
                </a>
                <a className="export__item" role="menuitem" href={exportUrl(conversation.id, 'json')} onClick={() => setExportOpen(false)}>
                  JSON <span className="export__ext">.json</span>
                </a>
              </div>
            )}
          </div>
          <button className="icon-button" title="New chat" onClick={onNewChat}>
            <PlusIcon size={20} />
          </button>
        </div>
      </header>

      {/* Messages */}
      <div className="chat__messages" aria-busy={streaming}>
        {loading ? (
          <div className="chat__loading">Loading chat…</div>
        ) : (
          <>
            {messages.length === 0 && !streaming && <MessageBubble role="assistant" content={GREETING} />}
            {messages.map((message) => (
              <MessageBubble
                key={message.id}
                role={message.role}
                content={message.content}
                createdAt={message.created_at}
                note={message.stopped ? 'Stopped · not saved' : null}
                userInitial={userInitial}
              />
            ))}
            {streaming && (
              <MessageBubble role="assistant" content={streamText} live>
                <div className="stream-status" role="status">
                  <span className="stream-status__dot" />
                  {streamTokens === 0 ? 'Thinking…' : `Writing · ${streamTokens} ${streamTokens === 1 ? 'token' : 'tokens'}`}
                </div>
              </MessageBubble>
            )}
          </>
        )}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <form className="chat__composer" onSubmit={handleSubmit}>
        {error && (
          <div className="chat__error" role="alert">
            {error}
          </div>
        )}
        <div className="chat__input-wrap">
          <input
            className="chat__input"
            placeholder="Ask a question about your documents..."
            value={text}
            onChange={(event) => setText(event.target.value)}
            disabled={loading}
          />
          {streaming ? (
            // While the answer arrives, the send button turns into Stop (same place, square icon).
            // type="button", so pressing Enter in the box can never send while it streams.
            <button className="chat__send chat__send--stop" type="button" onClick={onStop} title="Stop the answer" aria-label="Stop the answer">
              <StopIcon size={16} />
            </button>
          ) : (
            <button
              className={`chat__send ${sending ? 'chat__send--busy' : ''}`}
              type="submit"
              disabled={!text.trim() || sending || loading}
              title="Send"
              aria-label="Send"
            >
              <SendIcon size={16} />
            </button>
          )}
        </div>
        <div className="chat__disclaimer">AI can make mistakes. Verify important information.</div>
      </form>
    </section>
  )
}
