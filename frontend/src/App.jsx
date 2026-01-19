import { useState, useEffect } from 'react'
import Header from './components/Header'
import FileUpload from './components/FileUpload'
import Dashboard from './components/Dashboard'
import ConflictTable from './components/ConflictTable'
import DuplicateList from './components/DuplicateList'
import ImprovementPanel from './components/ImprovementPanel'
import ExportButtons from './components/ExportButtons'
import SaveLoadModal from './components/SaveLoadModal'
import LibraryPanel from './components/LibraryPanel'
import ObjectAnalysis from './components/ObjectAnalysis'

function App() {
    const [theme, setTheme] = useState('light')
    const [stats, setStats] = useState(null)
    const [analysis, setAnalysis] = useState(null)
    const [loading, setLoading] = useState(false)
    const [activeTab, setActiveTab] = useState('dashboard')
    const [saveLoadModal, setSaveLoadModal] = useState(null) // 'save' | 'load' | null

    // Initialize theme
    useEffect(() => {
        const savedTheme = localStorage.getItem('theme') || 'light'
        setTheme(savedTheme)
        document.documentElement.setAttribute('data-theme', savedTheme)
    }, [])

    // Toggle theme
    const toggleTheme = () => {
        const newTheme = theme === 'light' ? 'dark' : 'light'
        setTheme(newTheme)
        localStorage.setItem('theme', newTheme)
        document.documentElement.setAttribute('data-theme', newTheme)
    }

    // Fetch stats on mount and after upload
    const fetchStats = async () => {
        try {
            const res = await fetch('/api/stats')
            const data = await res.json()
            setStats(data)

            if (data.has_analysis) {
                const analysisRes = await fetch('/api/analysis')
                const analysisData = await analysisRes.json()
                setAnalysis(analysisData)
            }
        } catch (err) {
            console.error('Failed to fetch stats:', err)
        }
    }

    useEffect(() => {
        fetchStats()
    }, [])

    // Handle file upload
    const handleUpload = async (files) => {
        setLoading(true)

        const formData = new FormData()
        files.forEach(file => formData.append('files', file))

        try {
            // Add timeout for large uploads (5 minutes)
            const controller = new AbortController()
            const timeoutId = setTimeout(() => controller.abort(), 300000) // 5 min

            const res = await fetch('/api/upload', {
                method: 'POST',
                body: formData,
                signal: controller.signal
            })

            clearTimeout(timeoutId)

            if (!res.ok) {
                const error = await res.json().catch(() => ({ message: 'Upload failed' }))
                throw new Error(error.message || `Server error: ${res.status}`)
            }

            const result = await res.json()

            if (result.success) {
                await fetchStats()
                setActiveTab('dashboard')
            } else {
                const errorMsg = result.message || 'Upload failed'
                const detailedErrors = result.errors?.length > 0
                    ? '\n\nDetails:\n' + result.errors.join('\n')
                    : ''
                alert(errorMsg + detailedErrors)
            }
        } catch (err) {
            console.error('Upload error:', err)
            if (err.name === 'AbortError') {
                alert('Upload timed out. Try uploading fewer files at once (e.g., 50-100 files).')
            } else if (err.message.includes('Failed to fetch')) {
                alert('Network error. Check your connection and try again.')
            } else {
                alert(`Upload failed: ${err.message}`)
            }
        } finally {
            setLoading(false)
        }
    }

    // Clear analysis
    const handleClear = async () => {
        if (!confirm('Clear current analysis?')) return

        try {
            await fetch('/api/upload', { method: 'DELETE' })
            setStats(null)
            setAnalysis(null)
            setActiveTab('dashboard')
            // Fetch stats to ensure UI properly reflects cleared state
            await fetchStats()
        } catch (err) {
            console.error('Clear error:', err)
            alert('Failed to clear analysis')
        }
    }

    const hasAnalysis = stats?.has_analysis

    const tabs = [
        { id: 'dashboard', label: 'Dashboard', icon: '📊' },
        { id: 'upload', label: 'Upload', icon: '📤' },
        { id: 'library', label: 'Library', icon: '📚' },
        { id: 'object-analysis', label: 'Object Lookup', icon: '🔍' },
    ]

    if (hasAnalysis) {
        tabs.push(
            { id: 'conflicts', label: 'Conflicts', icon: '⚠️', count: analysis?.conflict_count },
            { id: 'duplicates', label: 'Duplicates', icon: '📋', count: analysis?.duplicate_count },
            { id: 'improvements', label: 'Improvements', icon: '💡', count: analysis?.improvement_count }
        )
    }

    return (
        <div className="app">
            <Header
                theme={theme}
                onToggleTheme={toggleTheme}
                hasAnalysis={hasAnalysis}
                onClear={handleClear}
            />

            <main className="main-content">
                <div className="container">

                    {/* Tab Navigation - Always visible */}
                    <div className="tab-nav">
                        {tabs.map(tab => (
                            <button
                                key={tab.id}
                                className={`tab-btn ${activeTab === tab.id ? 'active' : ''}`}
                                onClick={() => setActiveTab(tab.id)}
                            >
                                <span className="tab-icon">{tab.icon}</span>
                                <span className="tab-label">{tab.label}</span>
                                {tab.count !== undefined && tab.count > 0 && (
                                    <span className="tab-count">{tab.count}</span>
                                )}
                            </button>
                        ))}

                        <div className="tab-actions">
                            {hasAnalysis && (
                                <>
                                    <button
                                        className="btn btn-secondary"
                                        onClick={() => setSaveLoadModal('save')}
                                        title="Save current analysis"
                                    >
                                        💾 Save
                                    </button>
                                    <ExportButtons />
                                </>
                            )}
                        </div>
                    </div>

                    {/* Tab Content */}
                    <div className="tab-content animate-fade-in">
                        {activeTab === 'dashboard' && (
                            !hasAnalysis ? (
                                <div className="upload-section">
                                    <FileUpload onUpload={handleUpload} loading={loading} />
                                    <div className="load-previous">
                                        <button
                                            className="btn btn-secondary"
                                            onClick={() => setSaveLoadModal('load')}
                                        >
                                            📂 Load Previous Analysis
                                        </button>
                                    </div>
                                    <p className="text-center text-muted mt-4">
                                        or select GPOs from the <a href="#" onClick={(e) => { e.preventDefault(); setActiveTab('library') }}>Library</a>
                                    </p>
                                </div>
                            ) : (
                                <Dashboard analysis={analysis} />
                            )
                        )}

                        {activeTab === 'upload' && (
                            <div className="upload-tab-content">
                                <FileUpload onUpload={handleUpload} loading={loading} />
                                <p className="text-center text-muted mt-4">
                                    New uploads will replace the current analysis view but are saved to the Library.
                                </p>
                            </div>
                        )}

                        {activeTab === 'library' && (
                            <LibraryPanel onAnalyze={(result) => {
                                setAnalysis(result)
                                setActiveTab('dashboard')
                            }} />
                        )}

                        {activeTab === 'object-analysis' && (
                            <ObjectAnalysis />
                        )}

                        {hasAnalysis && (
                            <>
                                {activeTab === 'conflicts' && (
                                    <ConflictTable conflicts={analysis?.conflicts || []} />
                                )}
                                {activeTab === 'duplicates' && (
                                    <DuplicateList duplicates={analysis?.duplicates || []} />
                                )}
                                {activeTab === 'improvements' && (
                                    <ImprovementPanel improvements={analysis?.improvements || []} />
                                )}
                            </>
                        )}
                    </div>

                </div>
            </main>

            <footer className="footer">
                <div className="container">
                    <p className="text-muted text-sm text-center">
                        GPO Analysis Tool • Analyze Group Policy Objects for conflicts, duplicates, and improvements
                    </p>
                    <p className="text-muted text-sm text-center" style={{ marginTop: '0.5rem' }}>
                        <a
                            href="https://github.com/sevostianvitalii/GPOanalysis"
                            target="_blank"
                            rel="noopener noreferrer"
                            style={{ color: 'var(--color-primary)', textDecoration: 'none' }}
                        >
                            GitHub Repository
                        </a>
                        {' • '}
                        <span style={{ opacity: 0.7 }}>Licensed under CC BY-NC 4.0</span>
                    </p>
                </div>
            </footer>

            <style>{`
        .tab-nav {
          display: flex;
          gap: var(--space-sm);
          margin-bottom: var(--space-xl);
          padding: var(--space-sm);
          background: var(--color-bg-secondary);
          border-radius: var(--radius-lg);
          border: 1px solid var(--color-border);
          flex-wrap: wrap;
        }
        
        .tab-btn {
          display: flex;
          align-items: center;
          gap: var(--space-sm);
          padding: var(--space-sm) var(--space-md);
          background: transparent;
          border: none;
          border-radius: var(--radius-md);
          color: var(--color-text-secondary);
          font-size: 0.875rem;
          font-weight: 500;
          cursor: pointer;
          transition: all var(--transition-fast);
        }
        
        .tab-btn:hover {
          background: var(--color-bg-tertiary);
          color: var(--color-text);
        }
        
        .tab-btn.active {
          background: var(--color-primary);
          color: white;
        }
        
        .tab-icon {
          font-size: 1rem;
        }
        
        .tab-count {
          background: rgba(255, 255, 255, 0.2);
          padding: 2px 8px;
          border-radius: 999px;
          font-size: 0.75rem;
        }
        
        .tab-btn:not(.active) .tab-count {
          background: var(--color-bg-tertiary);
          color: var(--color-text-secondary);
        }
        
        .tab-actions {
          margin-left: auto;
          display: flex;
          gap: var(--space-sm);
        }
        
        .footer {
          padding: var(--space-lg) 0;
          border-top: 1px solid var(--color-border);
          margin-top: auto;
        }
        
        @media (max-width: 768px) {
          .tab-nav {
            flex-direction: column;
          }
          
          .tab-actions {
            margin-left: 0;
            width: 100%;
            justify-content: center;
          }
        }
        
        .upload-section {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: var(--space-lg);
        }
        
        .load-previous {
          text-align: center;
          padding: var(--space-md);
          border-top: 1px solid var(--color-border);
          width: 100%;
          max-width: 600px;
        }
      `}</style>

            {/* Save/Load Modal */}
            {saveLoadModal && (
                <SaveLoadModal
                    mode={saveLoadModal}
                    onClose={(result) => {
                        setSaveLoadModal(null)
                        if (result === 'saved' || result === 'loaded') {
                            fetchStats()
                        }
                    }}
                    onLoad={() => fetchStats()}
                />
            )}
            <style>{`
                .upload-tab-content {
                    max-width: 800px;
                    margin: 0 auto;
                    padding: var(--space-xl) 0;
                }
            `}</style>
        </div>
    )
}

export default App
