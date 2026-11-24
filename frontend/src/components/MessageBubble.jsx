// MessageBubble: one chat message.
//   - assistant: dark card on the left, with a round mic avatar
//   - user:      light bubble on the right, with the user's initial as avatar
// The time ("Just now", "14:03", ...) is shown under the bubble, or a note
// such as "Stopped · not saved".
//   live      the answer is still arriving: a blinking caret follows the text
//   children  shown under the bubble (the streaming indicator)
import { MicIcon } from './Icons.jsx'
import { formatMessageTime } from '../utils/time.js'

export default function MessageBubble({ role, content, createdAt, note, live, userInitial, children }) {
  const isUser = role === 'user'

  return (
    <div className={`message ${isUser ? 'message--user' : 'message--assistant'}`}>
      {/* Assistant avatar sits left of the bubble */}
      {!isUser && (
        <div className="message__avatar message__avatar--assistant">
          <MicIcon size={16} />
        </div>
      )}

      <div className="message__body">
        <div className={`message__bubble ${live ? 'message__bubble--live' : ''}`}>{content}</div>
        {children}
        {note ? (
          <div className="message__time message__note">{note}</div>
        ) : (
          createdAt && <div className="message__time">{formatMessageTime(createdAt)}</div>
        )}
      </div>

      {/* User avatar sits right of the bubble */}
      {isUser && <div className="message__avatar message__avatar--user">{userInitial}</div>}
    </div>
  )
}
