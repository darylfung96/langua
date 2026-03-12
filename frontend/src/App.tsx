import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';

// Layout
import Header from './components/layout/Header';

// Pages
import Dashboard from './pages/Dashboard';
import StoryWeaver from './pages/StoryWeaver';
import Melody from './pages/Melody';
import Podcasts from './pages/Podcasts';
import VisualMemory from './pages/VisualMemory';
import Writing from './pages/Writing';
import ResourceLearner from './pages/ResourceLearner';

function App() {
  return (
    <Router>
      <div className="app-container">
        <Header />
        
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/story-weaver" element={<StoryWeaver />} />
            <Route path="/melody" element={<Melody />} />
            <Route path="/podcasts" element={<Podcasts />} />
            <Route path="/visual-memory" element={<VisualMemory />} />
            <Route path="/writing" element={<Writing />} />
            <Route path="/resource-learner" element={<ResourceLearner />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
