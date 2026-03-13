import { Component } from 'react';
import type { ErrorInfo, ReactNode } from 'react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

class ErrorBoundary extends Component<Props, State> {
  state: State = { hasError: false, error: null };

  static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    // In production, forward to an error reporting service here.
    if (import.meta.env.DEV) {
      console.error('ErrorBoundary caught an error:', error, info.componentStack);
    }
  }

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }
      return (
        <div
          style={{
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            minHeight: '60vh',
            gap: '1rem',
            textAlign: 'center',
            padding: '2rem',
          }}
        >
          <h2>Something went wrong</h2>
          <p style={{ color: 'var(--text-muted, #888)', maxWidth: '480px' }}>
            An unexpected error occurred. Please refresh the page or navigate back to the
            dashboard.
          </p>
          <button
            onClick={() => this.setState({ hasError: false, error: null })}
            style={{
              padding: '0.5rem 1.25rem',
              borderRadius: '6px',
              cursor: 'pointer',
              border: '1px solid var(--accent-primary, #6366f1)',
              background: 'transparent',
              color: 'var(--accent-primary, #6366f1)',
            }}
          >
            Try again
          </button>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;
