import { useState } from 'react'

function ImprovementPanel({ improvements }) {
    const [selectedCategory, setSelectedCategory] = useState('all')

    const categories = ['all', 'consolidation', 'security', 'performance', 'naming', 'cleanup']

    const filteredImprovements = selectedCategory === 'all'
        ? improvements
        : improvements.filter(i => i.category === selectedCategory)

    const getCategoryIcon = (category) => {
        const icons = {
            consolidation: '🔗',
            security: '🔒',
            performance: '⚡',
            naming: '🏷️',
            cleanup: '🧹',
            organization: '📂'
        }
        return icons[category] || '💡'
    }

    if (improvements.length === 0) {
        return (
            <div className="empty-state">
                <div className="empty-state-icon">🎉</div>
                <h3 className="empty-state-title">Great Job!</h3>
                <p className="empty-state-text">
                    Your GPO configuration follows best practices. No improvements suggested.
                </p>
            </div>
        )
    }

    return (
        <div className="improvements-container">
            {/* Category Filter */}
            <div className="category-filter">
                {categories.map(cat => {
                    const count = cat === 'all'
                        ? improvements.length
                        : improvements.filter(i => i.category === cat).length

                    if (cat !== 'all' && count === 0) return null

                    return (
                        <button
                            key={cat}
                            className={`category-btn ${selectedCategory === cat ? 'active' : ''}`}
                            onClick={() => setSelectedCategory(cat)}
                        >
                            {cat !== 'all' && <span className="cat-icon">{getCategoryIcon(cat)}</span>}
                            <span className="cat-name">{cat === 'all' ? 'All' : cat}</span>
                            <span className="cat-count">{count}</span>
                        </button>
                    )
                })}
            </div>

            {/* Improvements List */}
            <div className="improvements-list">
                {filteredImprovements.map((improvement, index) => (
                    <div key={improvement.id || index} className="improvement-card">
                        <div className="improvement-header">
                            <span className="improvement-icon">
                                {getCategoryIcon(improvement.category)}
                            </span>
                            <div className="improvement-title-area">
                                <h4>{improvement.title}</h4>
                                <div className="improvement-meta">
                                    <span className={`badge badge-${improvement.severity}`}>
                                        {improvement.severity?.toUpperCase()}
                                    </span>
                                    <span className="category-label">{improvement.category}</span>
                                </div>
                            </div>
                        </div>

                        <div className="improvement-content">
                            <p className="improvement-desc">{improvement.description}</p>

                            {improvement.affected_gpos?.length > 0 && (
                                <div className="affected-area">
                                    <span className="label">Affected GPOs:</span>
                                    <div className="gpo-list">
                                        {improvement.affected_gpos.map((gpo, i) => (
                                            <span key={i} className="gpo-pill">{gpo}</span>
                                        ))}
                                    </div>
                                </div>
                            )}

                            <div className="action-box">
                                <div className="action-label">🎯 Recommended Action</div>
                                <p>{improvement.action}</p>
                            </div>

                            {improvement.estimated_impact && (
                                <div className="impact-box">
                                    <span className="impact-label">Expected Impact:</span>
                                    <span className="impact-text">{improvement.estimated_impact}</span>
                                </div>
                            )}
                        </div>
                    </div>
                ))}
            </div>

            <style>{`
        .category-filter {
          display: flex;
          flex-wrap: wrap;
          gap: var(--space-sm);
          margin-bottom: var(--space-xl);
        }
        
        .category-btn {
          display: flex;
          align-items: center;
          gap: var(--space-sm);
          padding: var(--space-sm) var(--space-md);
          background: var(--color-bg-secondary);
          border: 1px solid var(--color-border);
          border-radius: var(--radius-md);
          cursor: pointer;
          transition: all var(--transition-fast);
          text-transform: capitalize;
        }
        
        .category-btn:hover {
          border-color: var(--color-primary);
        }
        
        .category-btn.active {
          background: var(--color-primary);
          border-color: var(--color-primary);
          color: white;
        }
        
        .cat-icon {
          font-size: 1rem;
        }
        
        .cat-name {
          font-weight: 500;
          font-size: 0.875rem;
        }
        
        .cat-count {
          background: rgba(0, 0, 0, 0.1);
          padding: 2px 8px;
          border-radius: 999px;
          font-size: 0.75rem;
        }
        
        .improvements-list {
          display: flex;
          flex-direction: column;
          gap: var(--space-lg);
        }
        
        .improvement-card {
          background: var(--color-bg-secondary);
          border: 1px solid var(--color-border);
          border-radius: var(--radius-lg);
          overflow: hidden;
          transition: box-shadow var(--transition-normal);
        }
        
        .improvement-card:hover {
          box-shadow: var(--shadow-md);
        }
        
        .improvement-header {
          display: flex;
          align-items: flex-start;
          gap: var(--space-md);
          padding: var(--space-lg);
          background: var(--color-bg-tertiary);
        }
        
        .improvement-icon {
          font-size: 1.5rem;
          background: var(--color-bg-secondary);
          padding: var(--space-sm);
          border-radius: var(--radius-md);
        }
        
        .improvement-title-area {
          flex: 1;
        }
        
        .improvement-title-area h4 {
          margin-bottom: var(--space-xs);
        }
        
        .improvement-meta {
          display: flex;
          align-items: center;
          gap: var(--space-sm);
        }
        
        .category-label {
          font-size: 0.75rem;
          color: var(--color-text-muted);
          text-transform: capitalize;
        }
        
        .improvement-content {
          padding: var(--space-lg);
        }
        
        .improvement-desc {
          margin-bottom: var(--space-md);
        }
        
        .affected-area {
          margin-bottom: var(--space-md);
        }
        
        .affected-area .label {
          display: block;
          font-size: 0.75rem;
          color: var(--color-text-muted);
          text-transform: uppercase;
          margin-bottom: var(--space-xs);
        }
        
        .gpo-list {
          display: flex;
          flex-wrap: wrap;
          gap: var(--space-xs);
        }
        
        .gpo-pill {
          background: var(--color-bg-tertiary);
          padding: 2px 10px;
          border-radius: 999px;
          font-size: 0.75rem;
        }
        
        .action-box {
          background: var(--color-low-bg);
          border: 1px solid var(--color-low);
          border-radius: var(--radius-md);
          padding: var(--space-md);
          margin-bottom: var(--space-md);
        }
        
        .action-label {
          font-weight: 600;
          font-size: 0.875rem;
          margin-bottom: var(--space-sm);
        }
        
        .action-box p {
          margin: 0;
          font-size: 0.875rem;
        }
        
        .impact-box {
          display: flex;
          gap: var(--space-sm);
          padding: var(--space-sm);
          background: var(--color-bg-tertiary);
          border-radius: var(--radius-sm);
          font-size: 0.875rem;
        }
        
        .impact-label {
          font-weight: 600;
          color: var(--color-text-secondary);
        }
        
        .impact-text {
          color: var(--color-text);
        }
      `}</style>
        </div>
    )
}

export default ImprovementPanel
