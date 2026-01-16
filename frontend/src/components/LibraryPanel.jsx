import { useState, useEffect } from 'react'

export default function LibraryPanel({ onAnalyze }) {
    const [gpos, setGpos] = useState([])
    const [selected, setSelected] = useState(new Set())
    const [loading, setLoading] = useState(true)
    const [analyzing, setAnalyzing] = useState(false)

    useEffect(() => {
        fetch('/api/library')
            .then(res => res.json())
            .then(data => {
                setGpos(data)
                setLoading(false)
            })
            .catch(err => {
                console.error("Failed to load library", err)
                setLoading(false)
            })
    }, [])

    const toggleSelect = (id) => {
        const newSelected = new Set(selected)
        if (newSelected.has(id)) {
            newSelected.delete(id)
        } else {
            newSelected.add(id)
        }
        setSelected(newSelected)
    }

    const handleAnalyze = async () => {
        if (selected.size === 0) return
        setAnalyzing(true)
        try {
            const res = await fetch('/api/analysis/start', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(Array.from(selected))
            })
            if (!res.ok) {
                const err = await res.json()
                throw new Error(err.detail || "Analysis failed")
            }
            const result = await res.json()
            onAnalyze(result)
        } catch (err) {
            alert("Analysis failed: " + err.message)
        } finally {
            setAnalyzing(false)
        }
    }

    const handleDelete = async () => {
        if (selected.size === 0) return
        if (!confirm(`Delete ${selected.size} GPOs? This cannot be undone.`)) return

        for (const id of selected) {
            await fetch(`/api/library/${id}`, { method: 'DELETE' })
        }

        // Refresh
        const res = await fetch('/api/library')
        const data = await res.json()
        setGpos(data)
        setSelected(new Set())
    }

    if (loading) return <div className="p-4 text-center">Loading Library...</div>

    return (
        <div className="panel">
            <div className="panel-header">
                <h2>GPO Library</h2>
                <div className="actions">
                    <span className="text-sm text-muted">{selected.size} selected</span>
                    {selected.size > 0 && (
                        <button
                            className="btn btn-danger btn-sm"
                            style={{ marginRight: '8px' }}
                            onClick={handleDelete}
                        >
                            Delete
                        </button>
                    )}
                    <button
                        className="btn btn-primary"
                        disabled={selected.size === 0 || analyzing}
                        onClick={handleAnalyze}
                    >
                        {analyzing ? 'Analyzing...' : 'Analyze Selected'}
                    </button>
                </div>
            </div>

            <div className="table-container">
                <table className="data-table">
                    <thead>
                        <tr>
                            <th width="40">
                                <input
                                    type="checkbox"
                                    onChange={(e) => {
                                        if (e.target.checked) setSelected(new Set(gpos.map(g => g.id)))
                                        else setSelected(new Set())
                                    }}
                                    checked={gpos.length > 0 && selected.size === gpos.length}
                                />
                            </th>
                            <th>Name</th>
                            <th>Domain</th>
                            <th>Links</th>
                            <th>Modified</th>
                            <th>Source</th>
                        </tr>
                    </thead>
                    <tbody>
                        {gpos.map(gpo => (
                            <tr key={gpo.id} className={selected.has(gpo.id) ? 'selected-row' : ''}>
                                <td>
                                    <input
                                        type="checkbox"
                                        checked={selected.has(gpo.id)}
                                        onChange={() => toggleSelect(gpo.id)}
                                    />
                                </td>
                                <td>{gpo.name}</td>
                                <td>{gpo.domain || '-'}</td>
                                <td>{gpo.link_count}</td>
                                <td>{new Date(gpo.modified).toLocaleDateString()}</td>
                                <td className="text-muted text-sm">{gpo.source}</td>
                            </tr>
                        ))}
                        {gpos.length === 0 && (
                            <tr>
                                <td colSpan="6" className="text-center p-4">No GPOs in library. Upload some files first.</td>
                            </tr>
                        )}
                    </tbody>
                </table>
            </div>

            <style>{`
                .panel {
                    background: var(--color-bg-secondary);
                    border-radius: var(--radius-lg);
                    border: 1px solid var(--color-border);
                    overflow: hidden;
                }
                .panel-header {
                    padding: var(--space-md);
                    border-bottom: 1px solid var(--color-border);
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                }
                .table-container {
                    overflow-x: auto;
                }
                .data-table {
                    width: 100%;
                    border-collapse: collapse;
                }
                .data-table th, .data-table td {
                    padding: var(--space-sm) var(--space-md);
                    text-align: left;
                    border-bottom: 1px solid var(--color-border);
                }
                .data-table th {
                    background: var(--color-bg-tertiary);
                    font-weight: 600;
                    font-size: 0.875rem;
                }
                .selected-row {
                    background: rgba(var(--color-primary-rgb), 0.05);
                }
                .actions {
                    display: flex;
                    align-items: center;
                    gap: var(--space-md);
                }
            `}</style>
        </div>
    )
}
