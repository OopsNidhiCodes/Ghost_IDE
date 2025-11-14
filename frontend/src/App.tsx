
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Layout } from './components/Layout/Layout';
import { IDEView } from './components/Views/IDEView';
import { WelcomeView } from './components/Views/WelcomeView';
import { ErrorBoundary } from './components/ErrorHandling/ErrorBoundary';
import { NotificationSystem } from './components/ErrorHandling/NotificationSystem';
import { ConnectionStatus } from './components/ErrorHandling/ConnectionStatus';
import './styles/globals.css';

function App() {
  return (
    <ErrorBoundary>
      <Router>
        <div className="App bg-ghost-950 text-ghost-100 min-h-screen">
          <Routes>
            <Route path="/" element={<Layout />}>
              <Route index element={<WelcomeView />} />
              <Route path="/ide" element={<IDEView />} />
              <Route path="/ide/:sessionId" element={<IDEView />} />
            </Route>
          </Routes>
          <NotificationSystem />
          <ConnectionStatus />
        </div>
      </Router>
    </ErrorBoundary>
  );
}

export default App;