import { useState } from 'react'

export default function ObjectAnalysis() {
    const [query, setQuery] = useState('')
    const [results, setResults] = useState(null)
    const [loading, setLoading] = useState(false)

    const handleSearch = async (e) => {
        e.preventDefault()
        if (!query.trim()) return

        setLoading(true)
        try {
            const res = await fetch(`/api/analysis/object?query=${encodeURIComponent(query)}`)
            const data = await res.json()
            setResults(data)
        } catch (err) {
            console.error(err)
            alert("Search failed")
        } finally {
            setLoading(false)
        }
    }

    const handleExport = () => {
        if (!query) return
        window.location.href = `/api/export/object?query=${encodeURIComponent(query)}&format=csv`
    }

    return (
        <div className="panel">
            <div className="panel-header">
                <h2>Object Analysis</h2>
                <p className="subtitle">Find policies applied to a User, Computer, or OU.</p>
            </div>

            <div className="panel-body">
                <form onSubmit={handleSearch} className="search-form">
                    <input
                        type="text"
                        value={query}
                        onChange={(e) => setQuery(e.target.value)}
                        placeholder="Enter Computer Name, User Name, or OU (e.g., OU=Sales,DC=example,DC=com)"
                        className="search-input"
                    />
                    <button type="submit" className="btn btn-primary" disabled={loading}>
                        {loading ? 'Searching...' : 'Search'}
                    </button>
                </form>

                {results && (
                    <div className="results-area animate-fade-in">
                        <div className="results-header">
                            <h3>Results for "{results.query}"</h3>
                            <button className="btn btn-secondary btn-sm" onClick={handleExport}>
                                Export CSV
                            </button>
                        </div>

                        <div className="match-info">
                            <span className="label">Match Type:</span>
                            <span className="badge">{results.match_type}</span>
                        </div>

                        {results.applied_gpos.length > 0 ? (
                            <table className="data-table">
                                <thead>
                                    <tr>
                                        <th>GPO Name</th>
                                        <th>Reason</th>
                                        <th>Location</th>
                                        <th>Enforced</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {results.applied_gpos.map((gpo, i) => (
                                        <tr key={i}>
                                            <td> {gpo.name} </td>
                                            <td> {gpo.reason} </td>
                                            <td> {gpo.location || '-'} </td>
                                            <td> {gpo.enforced ? 'Yes' : 'No'} </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        ) : (
                            <div className="no-results">
                                No applied GPOs found for this object.
                            </div>
                        )}
                    </div>
                )}
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
                }
                .subtitle {
                    color: var(--color-text-secondary);
                    font-size: 0.875rem;
                    margin-top: 4px;
                }
                .panel-body {
                    padding: var(--space-lg);
                }
                .search-form {
                    display: flex;
                    gap: var(--space-md);
                    margin-bottom: var(--space-xl);
                }
                .search-input {
                    flex: 1;
                    padding: var(--space-sm) var(--space-md);
                    border: 1px solid var(--color-border);
                    border-radius: var(--radius-md);
                    font-size: 1rem;
                    background: var(--color-bg-tertiary);
                    color: var(--color-text);
                }
                .results-header {
                    display: flex;
                    justify-content: space-between;
                    align-items: center;
                    margin-bottom: var(--space-md);
                }
                .data-table {
                    width: 100%;
                    border-collapse: collapse;
                    margin-top: var(--space-md);
                }
                .data-table th, .data-table td {
                    padding: var(--space-sm) var(--space-md);
                    text-align: left;
                    border-bottom: 1px solid var(--color-border);
                }
                .data-table th {
                    background: var(--color-bg-tertiary);
                    font-weight: 600;
                }
                .match-info {
                    margin-bottom: var(--space-md);
                }
                .badge {
                    display: inline-block;
                    padding: 2px 8px;
                    border-radius: 4px;
                    background: var(--color-bg-tertiary);
                    border: 1px solid var(--color-border);
                    font-size: 0.8rem;
                    margin-left: 8px;
                    text-transform: uppercase;
                }
                .no-results {
                    padding: var(--space-lg);
                    text-align: center;
                    color: var(--color-text-secondary);
                    background: var(--color-bg-tertiary);
                    border-radius: var(--radius-md);
                }
            `}</style>
        </div>
    )
}
