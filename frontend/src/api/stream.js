// Streaming fetch call for POST /api/stream (needs a logged-in user).
//
// The server answers with Server-Sent Events: blocks of text like
//   data: {"token": "Hel", "text": "Hel", "percent": 0}
//   <blank line>
// EventSource cannot send a POST, so this uses fetch and reads the body
// piece by piece with a ReadableStream reader.
//
// A network read can end in the middle of a block (even in the middle of a
// letter), so everything read is kept in `buffer` and only complete blocks
// (ending with a blank line) are parsed. The unfinished rest waits for the
// next read. That way JSON.parse never sees half an event.
import { ApiError, errorMessage } from './client.js'

export async function streamAnswer(conversationId, content, { signal, onEvent }) {
  const response = await fetch('/api/stream', {
    method: 'POST',
    credentials: 'same-origin',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ conversation_id: conversationId, content }),
    signal, // AbortController.signal: lets the Stop button cancel the request
  })

  // 401 / 404 / 422 come back as normal JSON errors, before any streaming
  if (!response.ok) {
    const data = await response.json().catch(() => null)
    throw new ApiError(response.status, errorMessage(data, response.status))
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder() // bytes -> text; { stream: true } keeps a split letter for the next read
  let buffer = ''

  while (true) {
    const { value, done } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })

    // Hand out every complete block; keep the unfinished end in the buffer
    let end
    while ((end = buffer.indexOf('\n\n')) !== -1) {
      const block = buffer.slice(0, end)
      buffer = buffer.slice(end + 2)
      const event = parseBlock(block)
      if (event) onEvent(event)
    }
  }

  // Whatever is left when the server closes (normally nothing)
  buffer += decoder.decode()
  const last = parseBlock(buffer)
  if (last) onEvent(last)
}

// "data: {...}" -> the object. Anything else (empty, comments) is skipped.
function parseBlock(block) {
  const line = block.trim()
  if (!line.startsWith('data:')) return null
  return JSON.parse(line.slice('data:'.length).trim())
}
