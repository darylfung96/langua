import { lazy, Suspense } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';

// Layout
import Header from './components/layout/Header';
import ErrorBoundary from './components/ErrorBoundary';
import ProtectedRoute from './components/ProtectedRoute';
import { AuthProvider } from './contexts/AuthContext';
import LoadingSpinner from './components/common/LoadingSpinner';

// Pages — lazily loaded so each route is a separate chunk, reducing initial bundle size
const Dashboard = lazy(() => import('./pages/Dashboard'));
const StoryWeaver = lazy(() => import('./pages/StoryWeaver'));
const Melody = lazy(() => import('./pages/Melody'));
const Podcasts = lazy(() => import('./pages/Podcasts'));
const VisualMemory = lazy(() => import('./pages/VisualMemory'));
const Writing = lazy(() => import('./pages/Writing'));
const ResourceLearner = lazy(() => import('./pages/ResourceLearner'));
const NotFound = lazy(() => import('./pages/NotFound'));
const Login = lazy(() => import('./pages/Login'));

function App() {
  return (
    <Router>
      <AuthProvider>
        <div className="app-container">
          <Header />

          <main className="main-content">
            <ErrorBoundary>
              <Suspense fallback={<LoadingSpinner />}>
                <Routes>
                  <Route path="/login" element={<Login />} />
                  <Route element={<ProtectedRoute />}>
                    <Route path="/" element={<Dashboard />} />
                    <Route path="/story-weaver" element={<StoryWeaver />} />
                    <Route path="/melody" element={<Melody />} />
                    <Route path="/podcasts" element={<Podcasts />} />
                    <Route path="/visual-memory" element={<VisualMemory />} />
                    <Route path="/writing" element={<Writing />} />
                    <Route path="/resource-learner" element={<ResourceLearner />} />
                    <Route path="*" element={<NotFound />} />
                  </Route>
                </Routes>
              </Suspense>
            </ErrorBoundary>
          </main>
        </div>
      </AuthProvider>
    </Router>
  );
}

export default App;

