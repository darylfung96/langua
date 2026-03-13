import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';

// Layout
import Header from './components/layout/Header';
import ErrorBoundary from './components/ErrorBoundary';
import ProtectedRoute from './components/ProtectedRoute';
import { AuthProvider } from './contexts/AuthContext';

// Pages
import Dashboard from './pages/Dashboard';
import StoryWeaver from './pages/StoryWeaver';
import Melody from './pages/Melody';
import Podcasts from './pages/Podcasts';
import VisualMemory from './pages/VisualMemory';
import Writing from './pages/Writing';
import ResourceLearner from './pages/ResourceLearner';
import NotFound from './pages/NotFound';
import Login from './pages/Login';

function App() {
  return (
    <Router>
      <AuthProvider>
        <div className="app-container">
          <Header />

          <main className="main-content">
            <ErrorBoundary>
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
            </ErrorBoundary>
          </main>
        </div>
      </AuthProvider>
    </Router>
  );
}

export default App;

