

import CodePlayground from '../components/CodeExecution/CodePlayground';
import CodeExecutor from '../components/CodeExecution/CodeExecutor';

const AppRoutes = () => {
  return (
    <Routes>
      {/* Existing routes */}
      <Route path="/playground" element={<CodePlayground />} />
      <Route path="/playground/:playgroundId" element={<CodePlayground />} />
      <Route path="/code-editor" element={<CodeExecutor />} />
      {/* Other routes */}
    </Routes>
  );
};