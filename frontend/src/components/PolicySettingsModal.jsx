import { useState } from 'react'

function PolicySettingsModal({ gpo, settings, onClose }) {
    const [searchTerm, setSearchTerm] = useState('')
    const [scopeFilter, setScopeFilter] = useState('all')

    if (!gpo) return null

    // Filter settings for this GPO
    const gpoSettings = settings.filter(s => s.gpo_id === gpo.id || s.gpo_name === gpo.name)

    // Apply search and scope filters
    const filteredSettings = gpoSettings.filter(setting => {
        const matchesSearch = !searchTerm ||
            setting.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
            setting.category.toLowerCase().includes(searchTerm.toLowerCase()) ||
            (setting.value || '').toLowerCase().includes(searchTerm.toLowerCase())

        const matchesScope = scopeFilter === 'all' ||
            setting.scope.toLowerCase() === scopeFilter.toLowerCase()

        return matchesSearch && matchesScope
    })

    // Group settings by category
    const settingsByCategory = filteredSettings.reduce((acc, setting) => {
        const category = setting.category || 'Uncategorized'
        if (!acc[category]) acc[category] = []
        acc[category].push(setting)
        return acc
    }, {})

    const getStateClass = (state) => {
        switch (state?.toLowerCase()) {
            case 'enabled': return 'state-enabled'
            case 'disabled': return 'state-disabled'
            default: return 'state-notconfigured'
        }
    }

    return (
        <div className="modal-overlay" onClick={onClose}>
            <div className="modal-content" onClick={e => e.stopPropagation()}>
                <div className="modal-header">
                    <div>
                        <h2>📋 Policy Settings</h2>
                        <p className="modal-subtitle">{gpo.name}</p>
                    </div>
                    <button className="modal-close" onClick={onClose}>×</button>
                </div>

                <div className="modal-filters">
                    <div className="search-box">
                        <input
                            type="text"
                            placeholder="Search settings..."
                            value={searchTerm}
                            onChange={e => setSearchTerm(e.target.value)}
                            className="search-input"
                        />
                    </div>
                    <div className="scope-filter">
                        <button
                            className={`filter-btn ${scopeFilter === 'all' ? 'active' : ''}`}
                            onClick={() => setScopeFilter('all')}
                        >
                            All ({gpoSettings.length})
                        </button>
                        <button
                            className={`filter-btn ${scopeFilter === 'computer' ? 'active' : ''}`}
                            onClick={() => setScopeFilter('computer')}
                        >
                            💻 Computer
                        </button>
                        <button
                            className={`filter-btn ${scopeFilter === 'user' ? 'active' : ''}`}
                            onClick={() => setScopeFilter('user')}
                        >
                            👤 User
                        </button>
                    </div>
                </div>

                <div className="modal-body">
                    {Object.keys(settingsByCategory).length === 0 ? (
                        <div className="empty-state">
                            <p>No settings found{searchTerm ? ' matching your search' : ' for this GPO'}.</p>
                        </div>
                    ) : (
                        Object.entries(settingsByCategory).map(([category, catSettings]) => (
                            <div key={category} className="settings-category">
                                <h3 className="category-header">{category}</h3>
                                <div className="settings-table-container">
                                    <table className="settings-table">
                                        <thead>
                                            <tr>
                                                <th>Setting Name</th>
                                                <th>State</th>
                                                <th>Value</th>
                                                <th>Scope</th>
                                            </tr>
                                        </thead>
                                        <tbody>
                                            {catSettings.map((setting, idx) => (
                                                <tr key={idx}>
                                                    <td className="setting-name">{setting.name}</td>
                                                    <td>
                                                        <span className={`state-badge ${getStateClass(setting.state)}`}>
                                                            {setting.state || 'N/A'}
                                                        </span>
                                                    </td>
                                                    <td className="setting-value">{setting.value || '-'}</td>
                                                    <td>
                                                        <span className="scope-badge">
                                                            {setting.scope === 'Computer' ? '💻' : '👤'} {setting.scope}
                                                        </span>
                                                    </td>
                                                </tr>
                                            ))}
                                        </tbody>
                                    </table>
                                </div>
                            </div>
                        ))
                    )}
                </div>

                <div className="modal-footer">
                    <span className="settings-count">
                        Showing {filteredSettings.length} of {gpoSettings.length} settings
                    </span>
                    <button className="btn btn-secondary" onClick={onClose}>Close</button>
                </div>

                <style>{`
                    .modal-overlay {
                        position: fixed;
                        top: 0;
                        left: 0;
                        right: 0;
                        bottom: 0;
                        background: rgba(0, 0, 0, 0.6);
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        z-index: 1000;
                        animation: fadeIn 0.2s ease;
                    }

                    @keyframes fadeIn {
                        from { opacity: 0; }
                        to { opacity: 1; }
                    }

                    .modal-content {
                        background: var(--color-bg-secondary);
                        border-radius: var(--radius-lg);
                        width: 90%;
                        max-width: 1000px;
                        max-height: 85vh;
                        display: flex;
                        flex-direction: column;
                        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
                        border: 1px solid var(--color-border);
                        animation: slideUp 0.3s ease;
                    }

                    @keyframes slideUp {
                        from { transform: translateY(20px); opacity: 0; }
                        to { transform: translateY(0); opacity: 1; }
                    }

                    .modal-header {
                        display: flex;
                        justify-content: space-between;
                        align-items: flex-start;
                        padding: var(--space-lg);
                        border-bottom: 1px solid var(--color-border);
                    }

                    .modal-header h2 {
                        margin: 0;
                        font-size: 1.5rem;
                    }

                    .modal-subtitle {
                        margin: var(--space-xs) 0 0 0;
                        color: var(--color-text-secondary);
                        font-size: 0.9rem;
                    }

                    .modal-close {
                        background: none;
                        border: none;
                        font-size: 2rem;
                        cursor: pointer;
                        color: var(--color-text-secondary);
                        line-height: 1;
                        padding: 0;
                        transition: color 0.2s;
                    }

                    .modal-close:hover {
                        color: var(--color-text);
                    }

                    .modal-filters {
                        display: flex;
                        gap: var(--space-md);
                        padding: var(--space-md) var(--space-lg);
                        background: var(--color-bg-tertiary);
                        flex-wrap: wrap;
                    }

                    .search-box {
                        flex: 1;
                        min-width: 200px;
                    }

                    .search-input {
                        width: 100%;
                        padding: var(--space-sm) var(--space-md);
                        border: 1px solid var(--color-border);
                        border-radius: var(--radius-md);
                        background: var(--color-bg-secondary);
                        color: var(--color-text);
                        font-size: 0.9rem;
                    }

                    .search-input:focus {
                        outline: none;
                        border-color: var(--color-primary);
                    }

                    .scope-filter {
                        display: flex;
                        gap: var(--space-xs);
                    }

                    .filter-btn {
                        padding: var(--space-sm) var(--space-md);
                        border: 1px solid var(--color-border);
                        border-radius: var(--radius-md);
                        background: var(--color-bg-secondary);
                        color: var(--color-text-secondary);
                        cursor: pointer;
                        font-size: 0.85rem;
                        transition: all 0.2s;
                    }

                    .filter-btn:hover {
                        border-color: var(--color-primary);
                    }

                    .filter-btn.active {
                        background: var(--color-primary);
                        border-color: var(--color-primary);
                        color: white;
                    }

                    .modal-body {
                        flex: 1;
                        overflow-y: auto;
                        padding: var(--space-lg);
                    }

                    .empty-state {
                        text-align: center;
                        padding: var(--space-xl);
                        color: var(--color-text-secondary);
                    }

                    .settings-category {
                        margin-bottom: var(--space-lg);
                    }

                    .category-header {
                        font-size: 0.9rem;
                        font-weight: 600;
                        color: var(--color-text-secondary);
                        margin-bottom: var(--space-sm);
                        padding-bottom: var(--space-xs);
                        border-bottom: 1px solid var(--color-border);
                    }

                    .settings-table-container {
                        overflow-x: auto;
                    }

                    .settings-table {
                        width: 100%;
                        border-collapse: collapse;
                    }

                    .settings-table th,
                    .settings-table td {
                        padding: var(--space-sm) var(--space-md);
                        text-align: left;
                        border-bottom: 1px solid var(--color-border);
                    }

                    .settings-table th {
                        font-weight: 600;
                        font-size: 0.8rem;
                        text-transform: uppercase;
                        color: var(--color-text-secondary);
                        background: var(--color-bg-tertiary);
                    }

                    .setting-name {
                        font-weight: 500;
                    }

                    .setting-value {
                        font-family: monospace;
                        font-size: 0.85rem;
                        color: var(--color-text-secondary);
                        max-width: 200px;
                        overflow: hidden;
                        text-overflow: ellipsis;
                        white-space: nowrap;
                    }

                    .state-badge {
                        display: inline-block;
                        padding: 2px 8px;
                        border-radius: var(--radius-sm);
                        font-size: 0.75rem;
                        font-weight: 500;
                        text-transform: capitalize;
                    }

                    .state-enabled {
                        background: rgba(76, 175, 80, 0.15);
                        color: #4caf50;
                    }

                    .state-disabled {
                        background: rgba(244, 67, 54, 0.15);
                        color: #f44336;
                    }

                    .state-notconfigured {
                        background: var(--color-bg-tertiary);
                        color: var(--color-text-secondary);
                    }

                    .scope-badge {
                        font-size: 0.85rem;
                    }

                    .modal-footer {
                        display: flex;
                        justify-content: space-between;
                        align-items: center;
                        padding: var(--space-md) var(--space-lg);
                        border-top: 1px solid var(--color-border);
                    }

                    .settings-count {
                        font-size: 0.85rem;
                        color: var(--color-text-secondary);
                    }
                `}</style>
            </div>
        </div>
    )
}

export default PolicySettingsModal
