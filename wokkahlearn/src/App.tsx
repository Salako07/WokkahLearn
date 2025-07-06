
import { CodeExecutionProvider } from './contexts/CodeExecutionContext';

function App() {
  return (
    <AuthProvider>
      <AITutorProvider>
        <CodeExecutionProvider>  {/* Add this */}
          <Router>
            <Routes>
              <Route path="/playground" element={<CodePlayground />} />
              <Route path="/playground/:playgroundId" element={<CodePlayground />} />
              {/* Other routes */}
            </Routes>
          </Router>
        </CodeExecutionProvider>
      </AITutorProvider>
    </AuthProvider>
  );
}