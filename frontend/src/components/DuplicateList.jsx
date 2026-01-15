function DuplicateList({ duplicates }) {
    if (duplicates.length === 0) {
        return (
            <div className="empty-state">
                <div className="empty-state-icon">✅</div>
                <h3 className="empty-state-title">No Duplicates Found</h3>
                <p className="empty-state-text">
                    Your GPOs don't have any redundant or duplicate policy settings.
                </p>
            </div>
        )
    }

    return (
        <div className="duplicates-container">
            <p className="duplicates-intro">
                Found <strong>{duplicates.length}</strong> duplicate or redundant configurations
                across your GPOs. Consolidating these can simplify management.
            </p>

            <div className="duplicate-list">
                {duplicates.map((dup, index) => (
                    <div key={dup.id || index} className="duplicate-card">
                        <div className="duplicate-header">
                            <span className={`badge badge-${dup.severity}`}>
                                {dup.severity?.toUpperCase()}
                            </span>
                            <h4>{dup.setting_name}</h4>
                        </div>

                        <div className="duplicate-body">
                            <p className="duplicate-category text-muted text-sm">
                                📁 {dup.category}
                            </p>

                            <div className="affected-gpos">
                                <span className="label">Affected GPOs:</span>
                                <div className="gpo-tags">
                                    {dup.affected_gpos?.map((gpo, i) => (
                                        <span key={i} className="gpo-tag">{gpo}</span>
                                    ))}
                                </div>
                            </div>

                            <div className="duplicate-desc">
                                <p>{dup.description}</p>
                            </div>

                            <div className="duplicate-recommendation">
                                <span className="label">💡 Recommendation:</span>
                                <p>{dup.recommendation}</p>
                            </div>
                        </div>
                    </div>
                ))}
            </div>

            <style>{`
        .duplicates-intro {
          margin-bottom: var(--space-lg);
          padding: var(--space-md);
          background: var(--color-bg-secondary);
          border-radius: var(--radius-md);
          border: 1px solid var(--color-border);
        }
        
        .duplicate-list {
          display: flex;
          flex-direction: column;
          gap: var(--space-md);
        }
        
        .duplicate-card {
          background: var(--color-bg-secondary);
          border: 1px solid var(--color-border);
          border-radius: var(--radius-lg);
          overflow: hidden;
        }
        
        .duplicate-header {
          display: flex;
          align-items: center;
          gap: var(--space-md);
          padding: var(--space-md);
          background: var(--color-bg-tertiary);
        }
        
        .duplicate-header h4 {
          margin: 0;
        }
        
        .duplicate-body {
          padding: var(--space-md);
        }
        
        .duplicate-category {
          margin-bottom: var(--space-md);
        }
        
        .affected-gpos {
          margin-bottom: var(--space-md);
        }
        
        .affected-gpos .label {
          display: block;
          font-size: 0.75rem;
          color: var(--color-text-muted);
          text-transform: uppercase;
          margin-bottom: var(--space-xs);
        }
        
        .gpo-tags {
          display: flex;
          flex-wrap: wrap;
          gap: var(--space-xs);
        }
        
        .gpo-tag {
          background: var(--color-bg-tertiary);
          padding: 2px 10px;
          border-radius: 999px;
          font-size: 0.75rem;
          font-weight: 500;
        }
        
        .duplicate-desc {
          padding: var(--space-sm);
          background: var(--color-bg-tertiary);
          border-radius: var(--radius-sm);
          margin-bottom: var(--space-md);
        }
        
        .duplicate-desc p {
          margin: 0;
          font-size: 0.875rem;
        }
        
        .duplicate-recommendation {
          padding: var(--space-sm);
          background: var(--color-info-bg);
          border: 1px solid var(--color-info);
          border-radius: var(--radius-sm);
        }
        
        .duplicate-recommendation .label {
          display: block;
          font-size: 0.75rem;
          font-weight: 600;
          margin-bottom: var(--space-xs);
        }
        
        .duplicate-recommendation p {
          margin: 0;
          font-size: 0.875rem;
        }
      `}</style>
        </div>
    )
}

export default DuplicateList
