function Dashboard({ analysis }) {
    if (!analysis) return null

    const healthScore = Math.max(0, 100 - (
        analysis.critical_issues * 10 +
        analysis.high_issues * 5 +
        analysis.medium_issues * 2 +
        analysis.low_issues
    ) * 2)

    const healthClass = healthScore >= 80 ? 'good' : healthScore >= 50 ? 'warning' : 'critical'

    return (
        <div className="dashboard">
            {/* Stats Grid */}
            <div className="grid grid-4 mb-lg">
                <div className="stat-card">
                    <div className="stat-value">{analysis.gpo_count}</div>
                    <div className="stat-label">GPOs Analyzed</div>
                </div>
                <div className="stat-card">
                    <div className="stat-value">{analysis.setting_count}</div>
                    <div className="stat-label">Total Settings</div>
                </div>
                <div className="stat-card">
                    <div className="stat-value">{analysis.conflict_count}</div>
                    <div className="stat-label">Conflicts</div>
                </div>
                <div className="stat-card">
                    <div className="stat-value">{analysis.duplicate_count}</div>
                    <div className="stat-label">Duplicates</div>
                </div>
            </div>

            {/* Health Score & Issue Breakdown */}
            <div className="grid grid-2 mb-lg">
                <div className="card">
                    <div className="card-header">
                        <h3>Health Score</h3>
                    </div>
                    <div className="health-display">
                        <div className={`health-circle ${healthClass}`}>
                            <span className="health-value">{healthScore}%</span>
                        </div>
                        <p className="health-text">
                            {healthScore >= 80 && "Your GPO configuration looks healthy!"}
                            {healthScore >= 50 && healthScore < 80 && "Some issues require attention."}
                            {healthScore < 50 && "Significant issues detected. Review recommended."}
                        </p>
                    </div>
                </div>

                <div className="card">
                    <div className="card-header">
                        <h3>Issue Breakdown</h3>
                    </div>
                    <div className="issue-bars">
                        <div className="issue-row">
                            <span className="badge badge-critical">Critical</span>
                            <div className="issue-bar">
                                <div
                                    className="issue-fill critical"
                                    style={{ width: `${Math.min(100, analysis.critical_issues * 20)}%` }}
                                ></div>
                            </div>
                            <span className="issue-count">{analysis.critical_issues}</span>
                        </div>
                        <div className="issue-row">
                            <span className="badge badge-high">High</span>
                            <div className="issue-bar">
                                <div
                                    className="issue-fill high"
                                    style={{ width: `${Math.min(100, analysis.high_issues * 10)}%` }}
                                ></div>
                            </div>
                            <span className="issue-count">{analysis.high_issues}</span>
                        </div>
                        <div className="issue-row">
                            <span className="badge badge-medium">Medium</span>
                            <div className="issue-bar">
                                <div
                                    className="issue-fill medium"
                                    style={{ width: `${Math.min(100, analysis.medium_issues * 5)}%` }}
                                ></div>
                            </div>
                            <span className="issue-count">{analysis.medium_issues}</span>
                        </div>
                        <div className="issue-row">
                            <span className="badge badge-low">Low</span>
                            <div className="issue-bar">
                                <div
                                    className="issue-fill low"
                                    style={{ width: `${Math.min(100, analysis.low_issues * 5)}%` }}
                                ></div>
                            </div>
                            <span className="issue-count">{analysis.low_issues}</span>
                        </div>
                    </div>
                </div>
            </div>

            {/* GPO List */}
            <div className="card">
                <div className="card-header flex-between">
                    <h3>Analyzed GPOs ({analysis.gpos?.length || 0})</h3>
                    <a
                        href="https://learn.microsoft.com/en-us/windows/security/threat-protection/security-policy-settings/security-policy-settings"
                        target="_blank"
                        rel="noreferrer"
                        className="text-sm link"
                    >
                        📚 Microsoft Security Baselines
                    </a>
                </div>
                <div className="table-container">
                    <table>
                        <thead>
                            <tr>
                                <th>GPO Name</th>
                                <th>Domain</th>
                                <th>Modified</th>
                                <th>Source</th>
                            </tr>
                        </thead>
                        <tbody>
                            {analysis.gpos?.map((gpo, i) => (
                                <tr key={i}>
                                    <td className="font-semibold">{gpo.name}</td>
                                    <td>{gpo.domain || 'N/A'}</td>
                                    <td>{gpo.modified ? new Date(gpo.modified).toLocaleDateString() : 'N/A'}</td>
                                    <td className="text-muted text-sm">{gpo.source_file?.split(/[/\\]/).pop()}</td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            </div>

            <style>{`
        .health-display {
          text-align: center;
          padding: var(--space-lg);
        }
        
        /* ... existing styles ... */
        
        .table-container {
            max-height: 500px;
            overflow-y: auto;
            border: 1px solid var(--color-border);
            border-radius: var(--radius-md);
        }
        
        .flex-between {
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .link {
            color: var(--color-primary);
            text-decoration: none;
        }
        
        .link:hover {
            text-decoration: underline;
        }
        
        .health-circle {
          width: 150px;
          height: 150px;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          margin: 0 auto var(--space-lg);
          position: relative;
          background: var(--color-bg-tertiary);
        }
        
        .health-circle::before {
          content: '';
          position: absolute;
          inset: 8px;
          border-radius: 50%;
          background: var(--color-bg-secondary);
        }
        
        .health-circle.good {
          background: conic-gradient(
            var(--color-low) 0deg,
            var(--color-low) calc(var(--score, 0) * 3.6deg),
            var(--color-bg-tertiary) calc(var(--score, 0) * 3.6deg)
          );
          --score: ${healthScore};
        }
        
        .health-circle.warning {
          background: conic-gradient(
            var(--color-medium) 0deg,
            var(--color-medium) calc(var(--score, 0) * 3.6deg),
            var(--color-bg-tertiary) calc(var(--score, 0) * 3.6deg)
          );
          --score: ${healthScore};
        }
        
        .health-circle.critical {
          background: conic-gradient(
            var(--color-critical) 0deg,
            var(--color-critical) calc(var(--score, 0) * 3.6deg),
            var(--color-bg-tertiary) calc(var(--score, 0) * 3.6deg)
          );
          --score: ${healthScore};
        }
        
        .health-value {
          position: relative;
          font-size: 2rem;
          font-weight: 700;
          z-index: 1;
        }
        
        .health-circle.good .health-value { color: var(--color-low); }
        .health-circle.warning .health-value { color: var(--color-medium); }
        .health-circle.critical .health-value { color: var(--color-critical); }
        
        .health-text {
          color: var(--color-text-secondary);
        }
        
        .issue-bars {
          display: flex;
          flex-direction: column;
          gap: var(--space-md);
        }
        
        .issue-row {
          display: flex;
          align-items: center;
          gap: var(--space-md);
        }
        
        .issue-row .badge {
          min-width: 70px;
          justify-content: center;
        }
        
        .issue-bar {
          flex: 1;
          height: 8px;
          background: var(--color-bg-tertiary);
          border-radius: 4px;
          overflow: hidden;
        }
        
        .issue-fill {
          height: 100%;
          border-radius: 4px;
          transition: width var(--transition-slow);
        }
        
        .issue-fill.critical { background: var(--color-critical); }
        .issue-fill.high { background: var(--color-high); }
        .issue-fill.medium { background: var(--color-medium); }
        .issue-fill.low { background: var(--color-low); }
        
        .issue-count {
          min-width: 30px;
          text-align: right;
          font-weight: 600;
        }
      `}</style>
        </div>
    )
}

export default Dashboard
