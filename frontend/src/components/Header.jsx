function Header({ theme, onToggleTheme, hasAnalysis, onClear }) {
    return (
        <header className="header">
            <div className="container">
                <div className="header-content">
                    <div className="header-brand">
                        <div className="logo">
                            <span className="logo-icon">🔍</span>
                            <div className="logo-text">
                                <span className="logo-title">GPO Analyzer</span>
                                <span className="logo-subtitle">Active Directory Policy Analysis</span>
                            </div>
                        </div>
                    </div>

                    <nav className="header-nav">
                        {hasAnalysis && (
                            <button className="btn btn-ghost" onClick={onClear}>
                                🗑️ Clear Analysis
                            </button>
                        )}

                        <button
                            className="btn btn-icon btn-ghost theme-toggle"
                            onClick={onToggleTheme}
                            title={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
                        >
                            {theme === 'light' ? '🌙' : '☀️'}
                        </button>
                    </nav>
                </div>
            </div>

            <style>{`
        .header {
          background: var(--glass-bg);
          backdrop-filter: var(--glass-blur);
          -webkit-backdrop-filter: var(--glass-blur);
          border-bottom: 1px solid var(--color-border);
          position: sticky;
          top: 0;
          z-index: 100;
        }
        
        .header-content {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: var(--space-md) 0;
        }
        
        .logo {
          display: flex;
          align-items: center;
          gap: var(--space-md);
        }
        
        .logo-icon {
          font-size: 2rem;
          background: linear-gradient(135deg, var(--color-primary) 0%, var(--color-primary-light) 100%);
          -webkit-background-clip: text;
          -webkit-text-fill-color: transparent;
          background-clip: text;
        }
        
        .logo-text {
          display: flex;
          flex-direction: column;
        }
        
        .logo-title {
          font-size: 1.25rem;
          font-weight: 700;
          color: var(--color-text);
          line-height: 1.2;
        }
        
        .logo-subtitle {
          font-size: 0.75rem;
          color: var(--color-text-muted);
        }
        
        .header-nav {
          display: flex;
          align-items: center;
          gap: var(--space-sm);
        }
        
        .theme-toggle {
          font-size: 1.25rem;
        }
        
        @media (max-width: 640px) {
          .logo-subtitle {
            display: none;
          }
        }
      `}</style>
        </header>
    )
}

export default Header
