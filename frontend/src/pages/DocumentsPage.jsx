// DocumentsPage: the "Upload Knowledge" panel (middle column of the design).
//   - Drop zone for PDF, TXT, MD or DOCX files
//   - "Home > Knowledge Base" breadcrumb with the "Add New" button
//   - Table of documents: file name, status (Indexed / Processing), added, size
//
// Layout only for now: the backend has no documents endpoint yet. Upload,
// chunking and embedding come in Week 2 (chunks table + embed script).
// Until then the table shows an empty state.
import { ChevronDownIcon, ChevronRightIcon, GridIcon, PlusIcon, UploadIcon, FileIcon } from '../components/Icons.jsx'

// Documents will come from the API in Week 2. Shape of one row, for reference:
// { id, name, status: 'indexed' | 'processing', added: 'Today', size: '2.4 MB' }
const documents = []

export default function DocumentsPage() {
  return (
    <section className="docs">
      <h2 className="docs__title">Upload Knowledge</h2>

      {/* Drop zone (not wired yet) */}
      <div className="dropzone" title="Document upload comes in Week 2">
        <div className="dropzone__icon">
          <UploadIcon size={20} />
        </div>
        <div className="dropzone__text">Click to upload or drag and drop</div>
        <div className="dropzone__hint">PDF, TXT, MD or DOCX (max. 10MB)</div>
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
        <button className="button button--primary" title="Document upload comes in Week 2">
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

        {documents.length === 0 && (
          <div className="docs__empty">No documents yet. Uploading and indexing arrive in Week 2.</div>
        )}

        {documents.map((doc) => (
          <div className="docs__row" key={doc.id}>
            <span className="docs__col-name">
              <span className={`file-icon ${doc.status === 'indexed' ? 'file-icon--blue' : 'file-icon--orange'}`}>
                <FileIcon size={18} />
              </span>
              <span className="docs__file">{doc.name}</span>
            </span>
            <span>
              <span className={`badge badge--${doc.status}`}>
                {doc.status === 'indexed' ? 'Indexed' : 'Processing'}
              </span>
            </span>
            <span className="docs__muted">{doc.added}</span>
            <span className="docs__muted docs__col-size">{doc.size}</span>
          </div>
        ))}
      </div>
    </section>
  )
}
