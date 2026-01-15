import { useState, useRef } from 'react'

function FileUpload({ onUpload, loading }) {
    const [dragOver, setDragOver] = useState(false)
    const [selectedFiles, setSelectedFiles] = useState([])
    const fileInputRef = useRef(null)

    const handleDragOver = (e) => {
        e.preventDefault()
        setDragOver(true)
    }

    const handleDragLeave = (e) => {
        e.preventDefault()
        setDragOver(false)
    }

    const handleDrop = (e) => {
        e.preventDefault()
        setDragOver(false)

        const files = Array.from(e.dataTransfer.files).filter(
            f => f.name.endsWith('.htm') || f.name.endsWith('.html') || f.name.endsWith('.xml')
        )

        if (files.length > 0) {
            setSelectedFiles(prev => [...prev, ...files])
        }
    }

    const handleFileSelect = (e) => {
        const files = Array.from(e.target.files)
        setSelectedFiles(prev => [...prev, ...files])
    }

    const removeFile = (index) => {
        setSelectedFiles(prev => prev.filter((_, i) => i !== index))
    }

    const handleUpload = () => {
        if (selectedFiles.length > 0) {
            onUpload(selectedFiles)
        }
    }

    return (
        <div className="upload-container">
            <div className="upload-header">
                <h1>📊 GPO Analysis Tool</h1>
                <p className="text-lg text-muted">
                    Analyze your Active Directory Group Policy Objects for conflicts, duplicates, and improvement opportunities
                </p>
            </div>

            <div
                className={`upload-zone ${dragOver ? 'drag-over' : ''}`}
                onDragOver={handleDragOver}
                onDragLeave={handleDragLeave}
                onDrop={handleDrop}
                onClick={() => fileInputRef.current?.click()}
            >
                <input
                    type="file"
                    ref={fileInputRef}
                    onChange={handleFileSelect}
                    accept=".htm,.html,.xml"
                    multiple
                    hidden
                />

                <div className="upload-icon">📁</div>
                <p className="upload-text">Drop GPO export files here or click to browse</p>
                <p className="upload-hint">Supports HTML, HTM, and XML files from Get-GPOReport</p>
            </div>

            {selectedFiles.length > 0 && (
                <div className="selected-files">
                    <h3>📎 Selected Files ({selectedFiles.length})</h3>

                    <div className="file-list">
                        {selectedFiles.map((file, index) => (
                            <div key={index} className="file-item">
                                <span className="file-icon">
                                    {file.name.endsWith('.xml') ? '📄' : '🌐'}
                                </span>
                                <span className="file-name">{file.name}</span>
                                <span className="file-size">
                                    {(file.size / 1024).toFixed(1)} KB
                                </span>
                                <button
                                    className="file-remove"
                                    onClick={(e) => {
                                        e.stopPropagation()
                                        removeFile(index)
                                    }}
                                >
                                    ✕
                                </button>
                            </div>
                        ))}
                    </div>

                    <button
                        className="btn btn-primary btn-lg w-full"
                        onClick={handleUpload}
                        disabled={loading}
                    >
                        {loading ? (
                            <>
                                <span className="spinner"></span>
                                Analyzing...
                            </>
                        ) : (
                            <>🚀 Analyze GPOs</>
                        )}
                    </button>
                </div>
            )}

            <div className="upload-info">
                <h3>How to export GPO reports</h3>
                <div className="info-cards">
                    <div className="info-card">
                        <h4>PowerShell (All GPOs)</h4>
                        <code>Get-GPOReport -All -ReportType HTML -Path "gpos.html"</code>
                    </div>
                    <div className="info-card">
                        <h4>PowerShell (Single GPO)</h4>
                        <code>Get-GPOReport -Name "GPO Name" -ReportType HTML -Path "gpo.htm"</code>
                    </div>
                    <div className="info-card">
                        <h4>gpresult (Current Machine)</h4>
                        <code>gpresult /H report.html</code>
                    </div>
                </div>
            </div>

            <style>{`
        .upload-container {
          max-width: 800px;
          margin: 0 auto;
        }
        
        .upload-header {
          text-align: center;
          margin-bottom: var(--space-xl);
        }
        
        .upload-header h1 {
          font-size: 2.5rem;
          margin-bottom: var(--space-md);
          background: linear-gradient(135deg, var(--color-text) 0%, var(--color-primary) 100%);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
        }
        
        .text-lg {
          font-size: 1.125rem;
        }
        
        .selected-files {
          margin-top: var(--space-xl);
          padding: var(--space-lg);
          background: var(--color-bg-secondary);
          border-radius: var(--radius-lg);
          border: 1px solid var(--color-border);
        }
        
        .selected-files h3 {
          margin-bottom: var(--space-md);
          font-size: 1rem;
        }
        
        .file-list {
          display: flex;
          flex-direction: column;
          gap: var(--space-sm);
          margin-bottom: var(--space-lg);
        }
        
        .file-item {
          display: flex;
          align-items: center;
          gap: var(--space-md);
          padding: var(--space-sm) var(--space-md);
          background: var(--color-bg-tertiary);
          border-radius: var(--radius-md);
        }
        
        .file-icon {
          font-size: 1.25rem;
        }
        
        .file-name {
          flex: 1;
          font-weight: 500;
          overflow: hidden;
          text-overflow: ellipsis;
          white-space: nowrap;
        }
        
        .file-size {
          color: var(--color-text-muted);
          font-size: 0.875rem;
        }
        
        .file-remove {
          background: transparent;
          border: none;
          color: var(--color-text-muted);
          cursor: pointer;
          padding: var(--space-xs);
          border-radius: var(--radius-sm);
          transition: all var(--transition-fast);
        }
        
        .file-remove:hover {
          background: var(--color-critical-bg);
          color: var(--color-critical);
        }
        
        .upload-info {
          margin-top: var(--space-2xl);
        }
        
        .upload-info h3 {
          text-align: center;
          color: var(--color-text-secondary);
          margin-bottom: var(--space-lg);
        }
        
        .info-cards {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
          gap: var(--space-md);
        }
        
        .info-card {
          padding: var(--space-md);
          background: var(--color-bg-secondary);
          border: 1px solid var(--color-border);
          border-radius: var(--radius-md);
        }
        
        .info-card h4 {
          font-size: 0.875rem;
          color: var(--color-text-secondary);
          margin-bottom: var(--space-sm);
        }
        
        .info-card code {
          display: block;
          font-family: 'Consolas', 'Monaco', monospace;
          font-size: 0.75rem;
          color: var(--color-primary);
          word-break: break-all;
        }
      `}</style>
        </div>
    )
}

export default FileUpload
