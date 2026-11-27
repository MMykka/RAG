// DocumentsPage: the knowledge base (middle column of the design).
//   - Info panel where the upload drop zone will go: browser upload is not built yet,
//     so it says how documents are added today (the ingest script)
//   - "Home > Knowledge Base" breadcrumb
//   - Table of documents from GET /api/documents: file name, status, added, size
//
// Every document in the table has been cut into chunks and embedded, so its status is
// always "Indexed". The list is loaded each time the page is opened.
import { useEffect, useState } from 'react'
import { ChevronDownIcon, ChevronRightIcon, GridIcon, PlusIcon, UploadIcon, FileIcon } from '../components/Icons.jsx'
import { listDocuments } from '../api/documents.js'
import { formatRelative } from '../utils/time.js'

// 17496 -> "≈ 17.1 KB". The size is the text in the document's chunks, so it is close to,
// not exactly, the file size (long sections overlap a little between chunks).
function formatSize(bytes) {
  if (bytes < 1024) return `≈ ${bytes} B`
  if (bytes < 1024 * 1024) return `≈ ${(bytes / 1024).toFixed(1)} KB`
  return `≈ ${(bytes / 1024 / 1024).toFixed(1)} MB`
}

export default function DocumentsPage({ onSessionExpired }) {
  const [documents, setDocuments] = useState(null) // null = still loading
  const [error, setError] = useState(null)

  useEffect(() => {
    let current = true // ignore a late answer if the page was left in the meantime
    listDocuments()
      .then((data) => current && setDocuments(data))
      .catch((err) => {
        if (!current) return
        if (err.status === 401) onSessionExpired()
        else setError(err.message)
      })
    return () => {
      current = false
    }
  }, [onSessionExpired])

  return (
    <section className="docs">
      <h2 className="docs__title">Knowledge base</h2>

      {/* Where the upload drop zone will go. Not clickable: upload is not built yet. */}
      <div className="dropzone dropzone--info">
        <div className="dropzone__icon">
          <UploadIcon size={20} />
        </div>
        <div className="dropzone__text">Uploading from the browser is not available yet</div>
        <div className="dropzone__hint">An administrator adds .txt and .md files with the ingest script.</div>
      </div>

      {/* Breadcrumb + actions */}
      <div className="docs__toolbar">
        <div className="breadcrumb">
          <span className="breadcrumb__muted">Home</span>
          <ChevronRightIcon size={14} className="breadcrumb__sep" />
          <span className="breadcrumb__current">Knowledge Base</span>
        </div>
        <button className="icon-button docs__grid" title="Grid view">
          <GridIcon size={20} />
        </button>
        <button className="button button--primary" disabled title="Upload from the browser is not available yet">
          <PlusIcon size={18} /> Add New
        </button>
      </div>

      {/* Table */}
      <div className="docs__table">
        <div className="docs__head">
          <span className="docs__col-name">
            File name <ChevronDownIcon size={12} />
          </span>
          <span>Status</span>
          <span>Added</span>
          <span className="docs__col-size">Size</span>
        </div>

        {error && (
          <div className="chat__error" role="alert">
            {error}
          </div>
        )}

        {!error && documents === null && <div className="docs__empty">Loading documents…</div>}

        {!error && documents?.length === 0 && (
          <div className="docs__empty">No documents in the knowledge base yet. The AI answers without company documents until some are added.</div>
        )}

        {documents?.map((doc) => (
          <div className="docs__row" key={doc.name}>
            <span className="docs__col-name">
              <span className="file-icon file-icon--blue">
                <FileIcon size={18} />
              </span>
              <span className="docs__file" title={`${doc.name} · ${doc.chunks} chunks`}>
                {doc.name}
              </span>
            </span>
            <span>
              <span className="badge badge--indexed">Indexed</span>
            </span>
            <span className="docs__muted" title={new Date(doc.added).toLocaleString()}>
              {formatRelative(doc.added)}
            </span>
            <span className="docs__muted docs__col-size" title={`${doc.size_bytes.toLocaleString()} bytes`}>
              {formatSize(doc.size_bytes)}
            </span>
          </div>
        ))}
      </div>
    </section>
  )
}
