// useStream: React state for one streamed answer from POST /api/stream.
//
//   const { streaming, text, tokens, start, stop } = useStream()
//
//   streaming  true while an answer is arriving
//   text       the answer so far (grows with every token)
//   tokens     how many tokens have arrived (one per event)
//   start(conversationId, content)  sends the question and resolves when the
//              stream ends, with one of:
//                { status: 'done',    text, sources }   the full answer (saved by the server)
//                { status: 'stopped', text }            Stop was pressed (not saved)
//                { status: 'error',   text, error }     the AI failed (not saved)
//              A failure before the stream starts (401, 404, network) is thrown.
//   stop()     cancels the running answer (AbortController)
import { useCallback, useEffect, useRef, useState } from 'react'
import { streamAnswer } from '../api/stream.js'

const STOPPED_UNEXPECTEDLY = 'The answer stopped unexpectedly. Please try again.'
const CONNECTION_LOST = 'Lost the connection to the server. Please try again.'

export default function useStream() {
  const [streaming, setStreaming] = useState(false)
  const [text, setText] = useState('')
  const [tokens, setTokens] = useState(0)
  const controllerRef = useRef(null) // the AbortController of the running answer

  const start = useCallback(async (conversationId, content) => {
    const controller = new AbortController()
    controllerRef.current = controller
    setStreaming(true)
    setText('')
    setTokens(0)

    let latest = '' // the answer so far, also outside React state
    let result = null

    try {
      await streamAnswer(conversationId, content, {
        signal: controller.signal,
        onEvent: (event) => {
          if (event.error) {
            result = { status: 'error', text: event.text ?? latest, error: event.error }
          } else if (event.done) {
            result = { status: 'done', text: event.text, sources: event.sources ?? [] }
          } else if (event.token !== undefined) {
            latest = event.text
            setText(event.text)
            setTokens((count) => count + 1)
          }
        },
      })
      // The server closed without "done" or "error" (e.g. it crashed)
      return result ?? { status: 'error', text: latest, error: STOPPED_UNEXPECTEDLY }
    } catch (err) {
      if (err.name === 'AbortError') return { status: 'stopped', text: latest }
      if (err.status) throw err // ApiError (401 / 404 / 422): the caller handles it
      if (latest) return { status: 'error', text: latest, error: CONNECTION_LOST } // dropped mid-answer
      throw new Error(CONNECTION_LOST) // could not reach the server at all
    } finally {
      if (controllerRef.current === controller) controllerRef.current = null
      setStreaming(false)
    }
  }, [])

  const stop = useCallback(() => controllerRef.current?.abort(), [])

  // Leaving the page cancels a running answer
  useEffect(() => () => controllerRef.current?.abort(), [])

  return { streaming, text, tokens, start, stop }
}
