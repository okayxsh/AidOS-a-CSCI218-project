import { Component, type ErrorInfo, type ReactNode } from 'react';
import { ErrorState } from './States';

interface Props {
  children: ReactNode;
}

interface State {
  error: Error | null;
}

/**
 * Catches a page that fails to render (or a lazy page chunk that fails to load) so the
 * rest of the app stays usable. Give it a `key` per route so moving to another page
 * clears the error.
 */
export class RouteErrorBoundary extends Component<Props, State> {
  state: State = { error: null };

  static getDerivedStateFromError(error: Error): State {
    return { error };
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('Page failed to render', error, info.componentStack);
  }

  render() {
    if (!this.state.error) return this.props.children;
    return (
      <div className="page">
        <ErrorState
          title="This page could not be displayed"
          error={this.state.error}
          onRetry={() => window.location.reload()}
        />
      </div>
    );
  }
}
