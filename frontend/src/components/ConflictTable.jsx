import { useState } from 'react'

function ConflictTable({ conflicts }) {
    const [expandedId, setExpandedId] = useState(null)
    const [filter, setFilter] = useState('all')

    const filteredConflicts = filter === 'all'
        ? conflicts
        : conflicts.filter(c => c.severity === filter)

    if (conflicts.length === 0) {
        return (
            <div className="empty-state">
                <div className="empty-state-icon">✅</div>
                <h3 className="empty-state-title">No Conflicts Detected</h3>
                <p className="empty-state-text">
                    Great news! Your GPO configurations don't have any conflicting settings.
                </p>
            </div>
        )
    }

    return (
        <div className="conflicts-container">
            <div className="filter-bar">
                <span className="filter-label">Filter by severity:</span>
                <div className="filter-buttons">
                    {['all', 'critical', 'high', 'medium', 'low'].map(level => (
                        <button
                            key={level}
                            className={`filter-btn ${filter === level ? 'active' : ''}`}
                            onClick={() => setFilter(level)}
                        >
                            {level === 'all' ? 'All' : level.charAt(0).toUpperCase() + level.slice(1)}
                            {level !== 'all' && (
                                <span className="filter-count">
                                    {conflicts.filter(c => c.severity === level).length}
                                </span>
                            )}
                        </button>
                    ))}
                </div>
            </div>

            <div className="conflict-list">
                {filteredConflicts.map((conflict, index) => (
                    <div
                        key={conflict.id || index}
                        className={`conflict-card ${expandedId === index ? 'expanded' : ''}`}
                    >
                        <div
                            className="conflict-header"
                            onClick={() => setExpandedId(expandedId === index ? null : index)}
                        >
                            <span className={`badge badge-${conflict.severity}`}>
                                {conflict.severity?.toUpperCase()}
                            </span>
                            <div className="conflict-info">
                                <h4>{conflict.setting_name}</h4>
                                <p className="text-muted text-sm">{conflict.category}</p>
                            </div>
                            <span className="expand-icon">
                                {expandedId === index ? '▼' : '▶'}
                            </span>
                        </div>

                        {expandedId === index && (
                            <div className="conflict-details">
                                <div className="detail-section">
                                    <h5>Description</h5>
                                    <p>{conflict.description}</p>
                                </div>

                                <div className="detail-section">
                                    <h5>Conflicting GPOs</h5>
                                    <div className="gpo-chips">
                                        {conflict.conflicting_policies?.map((policy, i) => (
                                            <div key={i} className="gpo-chip">
                                                <span className="gpo-name">{policy.gpo_name}</span>
                                                <span className="gpo-value">
                                                    {policy.state}: {policy.value || 'N/A'}
                                                </span>
                                            </div>
                                        ))}
                                    </div>
                                </div>

                                {conflict.winning_gpo && (
                                    <div className="detail-section">
                                        <h5>Winning GPO</h5>
                                        <p className="font-semibold">{conflict.winning_gpo}</p>
                                    </div>
                                )}

                                <div className="detail-section recommendation">
                                    <h5>💡 Recommendation</h5>
                                    <p>{conflict.recommendation}</p>
                                </div>
                            </div>
                        )}
                    </div>
                ))}
            </div>

            <style>{`
        .filter-bar {
          display: flex;
          align-items: center;
          gap: var(--space-md);
          margin-bottom: var(--space-lg);
          flex-wrap: wrap;
        }
        
        .filter-label {
          color: var(--color-text-secondary);
          font-size: 0.875rem;
        }
        
        .filter-buttons {
          display: flex;
          gap: var(--space-xs);
        }
        
        .filter-btn {
          display: flex;
          align-items: center;
          gap: var(--space-xs);
          padding: var(--space-xs) var(--space-sm);
          background: var(--color-bg-secondary);
          border: 1px solid var(--color-border);
          border-radius: var(--radius-md);
          font-size: 0.75rem;
          cursor: pointer;
          transition: all var(--transition-fast);
        }
        
        .filter-btn:hover {
          border-color: var(--color-primary);
        }
        
        .filter-btn.active {
          background: var(--color-primary);
          border-color: var(--color-primary);
          color: white;
        }
        
        .filter-count {
          background: rgba(0, 0, 0, 0.1);
          padding: 1px 6px;
          border-radius: 999px;
        }
        
        .conflict-list {
          display: flex;
          flex-direction: column;
          gap: var(--space-md);
        }
        
        .conflict-card {
          background: var(--color-bg-secondary);
          border: 1px solid var(--color-border);
          border-radius: var(--radius-lg);
          overflow: hidden;
          transition: all var(--transition-normal);
        }
        
        .conflict-card:hover {
          box-shadow: var(--shadow-md);
        }
        
        .conflict-header {
          display: flex;
          align-items: center;
          gap: var(--space-md);
          padding: var(--space-md);
          cursor: pointer;
        }
        
        .conflict-info {
          flex: 1;
        }
        
        .conflict-info h4 {
          margin-bottom: 2px;
        }
        
        .expand-icon {
          color: var(--color-text-muted);
          font-size: 0.75rem;
        }
        
        .conflict-details {
          padding: var(--space-md);
          padding-top: 0;
          animation: fadeIn var(--transition-normal);
        }
        
        .detail-section {
          padding: var(--space-md);
          background: var(--color-bg-tertiary);
          border-radius: var(--radius-md);
          margin-bottom: var(--space-sm);
        }
        
        .detail-section:last-child {
          margin-bottom: 0;
        }
        
        .detail-section h5 {
          font-size: 0.75rem;
          color: var(--color-text-muted);
          text-transform: uppercase;
          margin-bottom: var(--space-sm);
        }
        
        .detail-section.recommendation {
          background: var(--color-info-bg);
          border: 1px solid var(--color-info);
        }
        
        .gpo-chips {
          display: flex;
          flex-wrap: wrap;
          gap: var(--space-sm);
        }
        
        .gpo-chip {
          background: var(--color-bg-secondary);
          border: 1px solid var(--color-border);
          border-radius: var(--radius-md);
          padding: var(--space-sm);
        }
        
        .gpo-name {
          display: block;
          font-weight: 600;
          font-size: 0.875rem;
        }
        
        .gpo-value {
          display: block;
          font-size: 0.75rem;
          color: var(--color-text-muted);
        }
      `}</style>
        </div>
    )
}

export default ConflictTable
