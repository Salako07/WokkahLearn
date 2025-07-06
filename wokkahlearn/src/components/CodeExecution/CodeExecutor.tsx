// src/components/CodeExecution/CodeExecutor.tsx - Main Code Execution Component

import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  IconButton,
  Tabs,
  Tab,
  CircularProgress,
  Alert,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Tooltip,
  Card,
  CardContent,
  LinearProgress,
  Grid,
  Collapse,
} from '@mui/material';
import {
  PlayArrow,
  Stop,
  Save,
  Share,
  Download,
  Upload,
  Settings,
  Terminal,
  Assessment,
  Speed,
  Memory,
  Timer,
  CheckCircle,
  Error,
  Warning,
  ExpandMore,
  ExpandLess,
} from '@mui/icons-material';
import { Editor } from '@monaco-editor/react';
import { useCodeExecution } from '../../contexts/CodeExecutionContext';

interface CodeExecutorProps {
  initialCode?: string;
  language?: string;
  exerciseId?: string;
  readOnly?: boolean;
  showTests?: boolean;
  onCodeChange?: (code: string) => void;
  onExecutionComplete?: (result: any) => void;
}

const CodeExecutor: React.FC<CodeExecutorProps> = ({
  initialCode = '',
  language = 'python',
  exerciseId,
  readOnly = false,
  showTests = false,
  onCodeChange,
  onExecutionComplete,
}) => {
  const {
    state,
    executeCode,
    stopExecution,
    getEnvironments,
    getExecutionHistory,
    clearError,
  } = useCodeExecution();

  const [code, setCode] = useState(initialCode);
  const [input, setInput] = useState('');
  const [selectedEnvironment, setSelectedEnvironment] = useState('');
  const [activeTab, setActiveTab] = useState(0);
  const [showSettings, setShowSettings] = useState(false);
  const [showInput, setShowInput] = useState(false);
  const [showTestResults, setShowTestResults] = useState(false);
  const [executionTime, setExecutionTime] = useState(0);

  const editorRef = useRef<any>(null);
  const outputRef = useRef<HTMLDivElement>(null);

  // Load environments on component mount
  useEffect(() => {
    getEnvironments();
  }, []);

  // Set default environment when environments are loaded
  useEffect(() => {
    if (state.environments.length > 0 && !selectedEnvironment) {
      const defaultEnv = state.environments.find(
        env => env.language.toLowerCase() === language.toLowerCase() && env.isDefault
      ) || state.environments.find(
        env => env.language.toLowerCase() === language.toLowerCase()
      );
      
      if (defaultEnv) {
        setSelectedEnvironment(defaultEnv.id);
      }
    }
  }, [state.environments, language, selectedEnvironment]);

  // Track execution time
  useEffect(() => {
    let interval: NodeJS.Timeout;
    if (state.isExecuting) {
      setExecutionTime(0);
      interval = setInterval(() => {
        setExecutionTime(prev => prev + 0.1);
      }, 100);
    }
    return () => clearInterval(interval);
  }, [state.isExecuting]);

  // Auto-scroll output
  useEffect(() => {
    if (outputRef.current) {
      outputRef.current.scrollTop = outputRef.current.scrollHeight;
    }
  }, [state.currentExecution?.output]);

  const handleCodeChange = (value: string | undefined) => {
    const newCode = value || '';
    setCode(newCode);
    onCodeChange?.(newCode);
  };

  const handleExecute = async () => {
    if (!selectedEnvironment || !code.trim()) return;

    try {
      const result = await executeCode({
        sourceCode: code,
        environmentId: selectedEnvironment,
        stdinInput: input,
        exerciseId,
        executionType: exerciseId ? 'exercise' : 'playground'
      });

      if (result.testResults && showTests) {
        setShowTestResults(true);
      }

      onExecutionComplete?.(result);
    } catch (error) {
      console.error('Execution failed:', error);
    }
  };

  const handleStop = () => {
    if (state.currentExecution) {
      stopExecution(state.currentExecution.id);
    }
  };

  const handleEditorMount = (editor: any) => {
    editorRef.current = editor;
    
    // Add keyboard shortcuts
    editor.addCommand(monaco.KeyMod.CtrlCmd | monaco.KeyCode.Enter, () => {
      handleExecute();
    });
  };

  const getLanguageFromEnvironment = () => {
    const env = state.environments.find(e => e.id === selectedEnvironment);
    return env?.language.toLowerCase() || 'python';
  };

  const formatExecutionTime = (time: number) => {
    return `${time.toFixed(1)}s`;
  };

  const formatMemoryUsage = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <Paper elevation={1} sx={{ p: 2, mb: 1 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <FormControl size="small" sx={{ minWidth: 150 }}>
              <InputLabel>Language</InputLabel>
              <Select
                value={selectedEnvironment}
                onChange={(e) => setSelectedEnvironment(e.target.value)}
                disabled={readOnly || state.isExecuting}
              >
                {state.environments.map(env => (
                  <MenuItem key={env.id} value={env.id}>
                    {env.name} ({env.version})
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            {/* Execution Controls */}
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Tooltip title="Run Code (Ctrl/Cmd + Enter)">
                <span>
                  <Button
                    variant="contained"
                    startIcon={state.isExecuting ? <Stop /> : <PlayArrow />}
                    onClick={state.isExecuting ? handleStop : handleExecute}
                    disabled={!selectedEnvironment || !code.trim()}
                    color={state.isExecuting ? 'error' : 'primary'}
                  >
                    {state.isExecuting ? 'Stop' : 'Run'}
                  </Button>
                </span>
              </Tooltip>

              <Tooltip title="Settings">
                <IconButton onClick={() => setShowSettings(true)}>
                  <Settings />
                </IconButton>
              </Tooltip>

              <Tooltip title="Input">
                <IconButton 
                  onClick={() => setShowInput(!showInput)}
                  color={showInput ? 'primary' : 'default'}
                >
                  <Terminal />
                </IconButton>
              </Tooltip>

              {showTests && (
                <Tooltip title="Test Results">
                  <IconButton 
                    onClick={() => setShowTestResults(!showTestResults)}
                    color={showTestResults ? 'primary' : 'default'}
                  >
                    <Assessment />
                  </IconButton>
                </Tooltip>
              )}
            </Box>
          </Box>

          {/* Execution Status */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            {state.isExecuting && (
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <CircularProgress size={16} />
                <Typography variant="body2" color="text.secondary">
                  Running... {formatExecutionTime(executionTime)}
                </Typography>
              </Box>
            )}

            {state.currentExecution && !state.isExecuting && (
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Chip
                  icon={
                    state.currentExecution.isSuccessful ? (
                      <CheckCircle />
                    ) : (
                      <Error />
                    )
                  }
                  label={state.currentExecution.status}
                  color={state.currentExecution.isSuccessful ? 'success' : 'error'}
                  size="small"
                />
                
                {state.currentExecution.executionTime && (
                  <Tooltip title="Execution Time">
                    <Chip
                      icon={<Timer />}
                      label={`${state.currentExecution.executionTime.toFixed(2)}s`}
                      size="small"
                      variant="outlined"
                    />
                  </Tooltip>
                )}
                
                {state.currentExecution.memoryUsed && (
                  <Tooltip title="Memory Used">
                    <Chip
                      icon={<Memory />}
                      label={formatMemoryUsage(state.currentExecution.memoryUsed)}
                      size="small"
                      variant="outlined"
                    />
                  </Tooltip>
                )}
              </Box>
            )}
          </Box>
        </Box>

        {/* Input Section */}
        <Collapse in={showInput}>
          <Box sx={{ mt: 2 }}>
            <TextField
              fullWidth
              multiline
              rows={3}
              label="Input (stdin)"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              placeholder="Enter input for your program..."
              disabled={state.isExecuting}
            />
          </Box>
        </Collapse>
      </Paper>

      {/* Error Display */}
      {state.error && (
        <Alert severity="error" onClose={clearError} sx={{ mb: 1 }}>
          {state.error}
        </Alert>
      )}

      {/* Main Content */}
      <Box sx={{ flex: 1, display: 'flex', gap: 1 }}>
        {/* Code Editor */}
        <Paper elevation={1} sx={{ flex: 1, overflow: 'hidden' }}>
          <Editor
            height="100%"
            language={getLanguageFromEnvironment()}
            value={code}
            onChange={handleCodeChange}
            onMount={handleEditorMount}
            options={{
              readOnly,
              fontSize: 14,
              wordWrap: 'on',
              minimap: { enabled: false },
              scrollBeyondLastLine: false,
              automaticLayout: true,
              tabSize: 2,
              insertSpaces: true,
              renderWhitespace: 'selection',
              bracketPairColorization: { enabled: true },
            }}
            theme="vs-dark"
          />
        </Paper>

        {/* Output Panel */}
        <Paper elevation={1} sx={{ width: '40%', display: 'flex', flexDirection: 'column' }}>
          <Tabs
            value={activeTab}
            onChange={(_, newValue) => setActiveTab(newValue)}
            variant="fullWidth"
          >
            <Tab label="Output" />
            <Tab label="Errors" />
            {showTests && <Tab label="Tests" />}
          </Tabs>

          {/* Output Content */}
          <Box sx={{ flex: 1, p: 2, overflow: 'auto' }} ref={outputRef}>
            {/* Output Tab */}
            {activeTab === 0 && (
              <Box>
                {state.isExecuting ? (
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <CircularProgress size={16} />
                    <Typography variant="body2">Executing...</Typography>
                  </Box>
                ) : (
                  <Typography
                    component="pre"
                    sx={{
                      fontFamily: 'monospace',
                      fontSize: 12,
                      whiteSpace: 'pre-wrap',
                      wordBreak: 'break-word',
                    }}
                  >
                    {state.currentExecution?.output || 'No output'}
                  </Typography>
                )}
              </Box>
            )}

            {/* Errors Tab */}
            {activeTab === 1 && (
              <Box>
                <Typography
                  component="pre"
                  sx={{
                    fontFamily: 'monospace',
                    fontSize: 12,
                    whiteSpace: 'pre-wrap',
                    wordBreak: 'break-word',
                    color: 'error.main',
                  }}
                >
                  {state.currentExecution?.stderr || 'No errors'}
                </Typography>
              </Box>
            )}

            {/* Tests Tab */}
            {activeTab === 2 && showTests && (
              <TestResultsPanel 
                results={state.currentExecution?.testResults}
                isLoading={state.isExecuting}
              />
            )}
          </Box>
        </Paper>
      </Box>

      {/* Settings Dialog */}
      <Dialog open={showSettings} onClose={() => setShowSettings(false)}>
        <DialogTitle>Execution Settings</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 1 }}>
            <Typography variant="body2" color="text.secondary" paragraph>
              Customize your code execution environment and preferences.
            </Typography>
            
            {/* Environment Settings */}
            <Typography variant="subtitle2" gutterBottom>
              Environment Settings
            </Typography>
            
            {/* Add more settings as needed */}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowSettings(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

// Test Results Panel Component
interface TestResultsPanelProps {
  results?: any[];
  isLoading?: boolean;
}

const TestResultsPanel: React.FC<TestResultsPanelProps> = ({ results, isLoading }) => {
  const [expandedTest, setExpandedTest] = useState<string | null>(null);

  if (isLoading) {
    return (
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <CircularProgress size={16} />
        <Typography variant="body2">Running tests...</Typography>
      </Box>
    );
  }

  if (!results || results.length === 0) {
    return (
      <Typography variant="body2" color="text.secondary">
        No test results available
      </Typography>
    );
  }

  return (
    <Box>
      {/* Test Summary */}
      <Card sx={{ mb: 2 }}>
        <CardContent sx={{ py: 1.5 }}>
          <Typography variant="subtitle2" gutterBottom>
            Test Summary
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={6}>
              <Typography variant="body2" color="text.secondary">
                Passed: {results.filter(r => r.status === 'passed').length}
              </Typography>
            </Grid>
            <Grid item xs={6}>
              <Typography variant="body2" color="text.secondary">
                Failed: {results.filter(r => r.status === 'failed').length}
              </Typography>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Individual Test Results */}
      {results.map((result, index) => (
        <Card key={result.testCaseName || index} sx={{ mb: 1 }}>
          <CardContent sx={{ py: 1 }}>
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                cursor: 'pointer',
              }}
              onClick={() => setExpandedTest(
                expandedTest === result.testCaseName ? null : result.testCaseName
              )}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                {result.status === 'passed' ? (
                  <CheckCircle color="success" fontSize="small" />
                ) : (
                  <Error color="error" fontSize="small" />
                )}
                <Typography variant="body2" fontWeight="medium">
                  {result.testCaseName}
                </Typography>
                <Chip
                  label={`${result.points || 0} pts`}
                  size="small"
                  variant="outlined"
                />
              </Box>
              {expandedTest === result.testCaseName ? <ExpandLess /> : <ExpandMore />}
            </Box>

            <Collapse in={expandedTest === result.testCaseName}>
              <Box sx={{ mt: 1, pt: 1, borderTop: 1, borderColor: 'divider' }}>
                {result.feedback && (
                  <Typography variant="body2" color="text.secondary" paragraph>
                    {result.feedback}
                  </Typography>
                )}

                {result.expectedOutput && (
                  <Box sx={{ mb: 1 }}>
                    <Typography variant="caption" color="text.secondary">
                      Expected Output:
                    </Typography>
                    <Typography
                      component="pre"
                      variant="body2"
                      sx={{
                        fontFamily: 'monospace',
                        bgcolor: 'grey.100',
                        p: 1,
                        borderRadius: 1,
                        fontSize: 11,
                      }}
                    >
                      {result.expectedOutput}
                    </Typography>
                  </Box>
                )}

                {result.actualOutput && (
                  <Box sx={{ mb: 1 }}>
                    <Typography variant="caption" color="text.secondary">
                      Actual Output:
                    </Typography>
                    <Typography
                      component="pre"
                      variant="body2"
                      sx={{
                        fontFamily: 'monospace',
                        bgcolor: result.status === 'passed' ? 'success.light' : 'error.light',
                        p: 1,
                        borderRadius: 1,
                        fontSize: 11,
                        opacity: 0.8,
                      }}
                    >
                      {result.actualOutput}
                    </Typography>
                  </Box>
                )}
              </Box>
            </Collapse>
          </CardContent>
        </Card>
      ))}
    </Box>
  );
};

export default CodeExecutor;