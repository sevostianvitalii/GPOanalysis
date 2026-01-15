import { useState } from 'react'

function ExportButtons() {
    const [exporting, setExporting] = useState(null)

    const handleExport = async (format) => {
        setExporting(format)

        try {
            const response = await fetch(`/api/export/${format}`)

            if (!response.ok) {
                throw new Error('Export failed')
            }

            const blob = await response.blob()
            const filename = response.headers
                .get('content-disposition')
                ?.match(/filename=(.+)/)?.[1] || `gpo_analysis.${format}`

            // Download file
            const url = window.URL.createObjectURL(blob)
            const a = document.createElement('a')
            a.href = url
            a.download = filename
            document.body.appendChild(a)
            a.click()
            window.URL.revokeObjectURL(url)
            document.body.removeChild(a)

        } catch (error) {
            console.error('Export error:', error)
            alert('Export failed. Please try again.')
        } finally {
            setExporting(null)
        }
    }

    return (
        <div className="export-buttons">
            <button
                className="btn btn-secondary"
                onClick={() => handleExport('csv')}
                disabled={exporting !== null}
            >
                {exporting === 'csv' ? (
                    <span className="spinner"></span>
                ) : (
                    '📊'
                )}
                Export CSV
            </button>

            <button
                className="btn btn-primary"
                onClick={() => handleExport('pdf')}
                disabled={exporting !== null}
            >
                {exporting === 'pdf' ? (
                    <span className="spinner"></span>
                ) : (
                    '📄'
                )}
                Export PDF
            </button>

            <style>{`
        .export-buttons {
          display: flex;
          gap: var(--space-sm);
        }
        
        .export-buttons .btn {
          white-space: nowrap;
        }
      `}</style>
        </div>
    )
}

export default ExportButtons
