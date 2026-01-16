import { useState, useEffect } from 'react'

function SaveLoadModal({ mode, onClose, onLoad }) {
    const [analysisName, setAnalysisName] = useState('')
    const [savedAnalyses, setSavedAnalyses] = useState([])
    const [loading, setLoading] = useState(false)
    const [error, setError] = useState(null)

    useEffect(() => {
        if (mode === 'load') {
            fetchSavedAnalyses()
        }
    }, [mode])

    const fetchSavedAnalyses = async () => {
        setLoading(true)
        try {
            const res = await fetch('/api/analysis/saved')
            if (res.ok) {
                const data = await res.json()
                setSavedAnalyses(data)
            }
        } catch (err) {
            setError('Failed to load saved analyses')
        } finally {
            setLoading(false)
        }
    }

    const handleSave = async () => {
        if (!analysisName.trim()) {
            setError('Please enter a name for the analysis')
            return
        }

        setLoading(true)
        setError(null)

        try {
            const res = await fetch(`/api/analysis/save?name=${encodeURIComponent(analysisName)}`, {
                method: 'POST'
            })

            if (!res.ok) {
                const data = await res.json()
                throw new Error(data.detail || 'Failed to save')
            }

            onClose('saved')
        } catch (err) {
            setError(err.message)
        } finally {
            setLoading(false)
        }
    }

    const handleLoad = async (filename) => {
        setLoading(true)
        setError(null)

        try {
            const res = await fetch(`/api/analysis/load/${encodeURIComponent(filename)}`)

            if (!res.ok) {
                const data = await res.json()
                throw new Error(data.detail || 'Failed to load')
            }

            if (onLoad) onLoad()
            onClose('loaded')
        } catch (err) {
            setError(err.message)
        } finally {
            setLoading(false)
        }
    }

    const handleDelete = async (filename, e) => {
        e.stopPropagation()
        if (!confirm('Are you sure you want to delete this saved analysis?')) return

        try {
            const res = await fetch(`/api/analysis/saved/${encodeURIComponent(filename)}`, {
                method: 'DELETE'
            })

            if (res.ok) {
                setSavedAnalyses(prev => prev.filter(a => a.filename !== filename))
            }
        } catch (err) {
            console.error('Delete failed:', err)
        }
    }

    const formatDate = (dateStr) => {
        if (!dateStr) return 'Unknown'
        try {
            return new Date(dateStr).toLocaleString()
        } catch {
            return dateStr
        }
    }

    return (
        <div className="modal-overlay" onClick={() => onClose()}>
            <div className="modal-content save-load-modal" onClick={e => e.stopPropagation()}>
                <div className="modal-header">
                    <h2>{mode === 'save' ? '💾 Save Analysis' : '📂 Load Analysis'}</h2>
                    <button className="modal-close" onClick={() => onClose()}>×</button>
                </div>

                {error && (
                    <div className="modal-error">
                        ⚠️ {error}
                    </div>
                )}

                <div className="modal-body">
                    {mode === 'save' ? (
                        <div className="save-form">
                            <label htmlFor="analysis-name">Analysis Name</label>
                            <input
                                id="analysis-name"
                                type="text"
                                placeholder="Enter a name for this analysis..."
                                value={analysisName}
                                onChange={e => setAnalysisName(e.target.value)}
                                className="save-input"
                                autoFocus
                            />
                            <p className="save-hint">
                                The analysis will be saved with the current date and time.
                            </p>
                        </div>
                    ) : (
                        <div className="load-list">
                            {loading ? (
                                <div className="loading-state">Loading saved analyses...</div>
                            ) : savedAnalyses.length === 0 ? (
                                <div className="empty-state">
                                    <p>No saved analyses found.</p>
                                    <p className="text-muted">Save an analysis first to see it here.</p>
                                </div>
                            ) : (
                                <div className="analysis-list">
                                    {savedAnalyses.map(analysis => (
                                        <div
                                            key={analysis.filename}
                                            className="analysis-item"
                                            onClick={() => handleLoad(analysis.filename)}
                                        >
                                            <div className="analysis-info">
                                                <span className="analysis-name">{analysis.name}</span>
                                                <span className="analysis-date">{formatDate(analysis.saved_at)}</span>
                                            </div>
                                            <div className="analysis-stats">
                                                <span className="stat">📋 {analysis.gpo_count} GPOs</span>
                                                <span className="stat">⚙️ {analysis.setting_count} Settings</span>
                                                {analysis.conflict_count > 0 && (
                                                    <span className="stat warn">⚠️ {analysis.conflict_count} Conflicts</span>
                                                )}
                                            </div>
                                            <button
                                                className="delete-btn"
                                                onClick={(e) => handleDelete(analysis.filename, e)}
                                                title="Delete"
                                            >
                                                🗑️
                                            </button>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>
                    )}
                </div>

                <div className="modal-footer">
                    <button className="btn btn-secondary" onClick={() => onClose()}>
                        Cancel
                    </button>
                    {mode === 'save' && (
                        <button
                            className="btn btn-primary"
                            onClick={handleSave}
                            disabled={loading || !analysisName.trim()}
                        >
                            {loading ? 'Saving...' : '💾 Save Analysis'}
                        </button>
                    )}
                </div>

                <style>{`
                    .save-load-modal {
                        max-width: 600px;
                    }

                    .modal-error {
                        background: rgba(244, 67, 54, 0.1);
                        color: #f44336;
                        padding: var(--space-sm) var(--space-md);
                        margin: 0 var(--space-lg);
                        border-radius: var(--radius-md);
                        font-size: 0.9rem;
                    }

                    .save-form {
                        padding: var(--space-md) 0;
                    }

                    .save-form label {
                        display: block;
                        font-weight: 600;
                        margin-bottom: var(--space-sm);
                    }

                    .save-input {
                        width: 100%;
                        padding: var(--space-md);
                        border: 1px solid var(--color-border);
                        border-radius: var(--radius-md);
                        background: var(--color-bg-secondary);
                        color: var(--color-text);
                        font-size: 1rem;
                    }

                    .save-input:focus {
                        outline: none;
                        border-color: var(--color-primary);
                    }

                    .save-hint {
                        color: var(--color-text-secondary);
                        font-size: 0.85rem;
                        margin-top: var(--space-sm);
                    }

                    .load-list {
                        min-height: 200px;
                    }

                    .loading-state,
                    .empty-state {
                        text-align: center;
                        padding: var(--space-xl);
                        color: var(--color-text-secondary);
                    }

                    .analysis-list {
                        display: flex;
                        flex-direction: column;
                        gap: var(--space-sm);
                    }

                    .analysis-item {
                        display: flex;
                        align-items: center;
                        gap: var(--space-md);
                        padding: var(--space-md);
                        background: var(--color-bg-tertiary);
                        border-radius: var(--radius-md);
                        cursor: pointer;
                        transition: all 0.2s;
                        border: 1px solid transparent;
                    }

                    .analysis-item:hover {
                        background: var(--color-bg-secondary);
                        border-color: var(--color-primary);
                    }

                    .analysis-info {
                        flex: 1;
                        display: flex;
                        flex-direction: column;
                        gap: 2px;
                    }

                    .analysis-name {
                        font-weight: 600;
                    }

                    .analysis-date {
                        font-size: 0.8rem;
                        color: var(--color-text-secondary);
                    }

                    .analysis-stats {
                        display: flex;
                        gap: var(--space-sm);
                        font-size: 0.8rem;
                    }

                    .analysis-stats .stat {
                        background: var(--color-bg-secondary);
                        padding: 2px 8px;
                        border-radius: var(--radius-sm);
                    }

                    .analysis-stats .stat.warn {
                        color: var(--color-medium);
                    }

                    .delete-btn {
                        background: none;
                        border: none;
                        cursor: pointer;
                        padding: var(--space-xs);
                        opacity: 0.5;
                        transition: opacity 0.2s;
                    }

                    .delete-btn:hover {
                        opacity: 1;
                    }

                    .modal-footer {
                        display: flex;
                        justify-content: flex-end;
                        gap: var(--space-sm);
                        padding: var(--space-md) var(--space-lg);
                        border-top: 1px solid var(--color-border);
                    }
                `}</style>
            </div>
        </div>
    )
}

export default SaveLoadModal
