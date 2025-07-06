// src/contexts/CodeExecutionContext.tsx - Complete State Management

import React, { createContext, useContext, useReducer, useCallback, useEffect } from 'react';
import { codeExecutionAPI } from '../services/api';

interface ExecutionEnvironment {
  id: string;
  name: string;
  language: string;
  version: string;
  dockerImage: string;
  defaultTimeout: number;
  maxMemory: number;
  maxCpuTime: number;
  supportsInput: boolean;
  supportsGraphics: boolean;
  supportsNetworking: boolean;
  fileExtension: string;
  compilerCommand?: string;
  interpreterCommand?: string;
  installedPackages: string[];
  availableLibraries: string[];
  isDefault: boolean;
  status: string;
}

interface CodeExecution {
  id: string;
  user: string;
  environment: ExecutionEnvironment;
  executionType: string;
  sourceCode: string;
  stdinInput: string;
  output: string;
  stderr: string;
  exitCode: number;
  executionTime: number;
  memoryUsed: number;
  cpuTime: number;
  status: string;
  isSuccessful: boolean;
  qualityScore?: number;
  createdAt: string;
  startedAt?: string;
  completedAt?: string;
  testResults?: TestResult[];
}

interface TestResult {
  id: string;
  testCaseName: string;
  status: string;
  expectedOutput: string;
  actualOutput: string;
  feedback: string;
  points: number;
  executionTime: number;
  memoryUsed: number;
  similarity: number;
}

interface CodeTemplate {
  id: string;
  name: string;
  templateType: string;
  environment: ExecutionEnvironment;
  codeTemplate: string;
  description: string;
  instructions: string;
  tags: string[];
  difficultyLevel: string;
  usageCount: number;
  isFeatured: boolean;
}

interface ExecutionQuota {
  daily: {
    executions: {
      used: number;
      limit: number;
      remaining: number;
      percentage: number;
    };
    cpuTime: {
      used: number;
      limit: number;
    };
    memory: {
      used: number;
      limit: number;
    };
    isExceeded: boolean;
    resetDate: string;
  };
}

interface CodeExecutionState {
  environments: ExecutionEnvironment[];
  currentExecution: CodeExecution | null;
  executionHistory: CodeExecution[];
  templates: CodeTemplate[];
  quota: ExecutionQuota | null;
  isLoading: boolean;
  isExecuting: boolean;
  error: string | null;
  executionQueue: string[];
}

type CodeExecutionAction =
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_EXECUTING'; payload: boolean }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'SET_ENVIRONMENTS'; payload: ExecutionEnvironment[] }
  | { type: 'SET_CURRENT_EXECUTION'; payload: CodeExecution | null }
  | { type: 'SET_EXECUTION_HISTORY'; payload: CodeExecution[] }
  | { type: 'ADD_TO_HISTORY'; payload: CodeExecution }
  | { type: 'UPDATE_EXECUTION'; payload: CodeExecution }
  | { type: 'SET_TEMPLATES'; payload: CodeTemplate[] }
  | { type: 'SET_QUOTA'; payload: ExecutionQuota }
  | { type: 'ADD_TO_QUEUE'; payload: string }
  | { type: 'REMOVE_FROM_QUEUE'; payload: string };

const initialState: CodeExecutionState = {
  environments: [],
  currentExecution: null,
  executionHistory: [],
  templates: [],
  quota: null,
  isLoading: false,
  isExecuting: false,
  error: null,
  executionQueue: [],
};

const codeExecutionReducer = (state: CodeExecutionState, action: CodeExecutionAction): CodeExecutionState => {
  switch (action.type) {
    case 'SET_LOADING':
      return { ...state, isLoading: action.payload };
    case 'SET_EXECUTING':
      return { ...state, isExecuting: action.payload };
    case 'SET_ERROR':
      return { ...state, error: action.payload };
    case 'SET_ENVIRONMENTS':
      return { ...state, environments: action.payload };
    case 'SET_CURRENT_EXECUTION':
      return { ...state, currentExecution: action.payload };
    case 'SET_EXECUTION_HISTORY':
      return { ...state, executionHistory: action.payload };
    case 'ADD_TO_HISTORY':
      return {
        ...state,
        executionHistory: [action.payload, ...state.executionHistory.slice(0, 19)], // Keep last 20
      };
    case 'UPDATE_EXECUTION':
      return {
        ...state,
        currentExecution: state.currentExecution?.id === action.payload.id 
          ? action.payload 
          : state.currentExecution,
        executionHistory: state.executionHistory.map(exec =>
          exec.id === action.payload.id ? action.payload : exec
        ),
      };
    case 'SET_TEMPLATES':
      return { ...state, templates: action.payload };
    case 'SET_QUOTA':
      return { ...state, quota: action.payload };
    case 'ADD_TO_QUEUE':
      return { ...state, executionQueue: [...state.executionQueue, action.payload] };
    case 'REMOVE_FROM_QUEUE':
      return { 
        ...state, 
        executionQueue: state.executionQueue.filter(id => id !== action.payload) 
      };
    default:
      return state;
  }
};

interface ExecuteCodeParams {
  sourceCode: string;
  environmentId: string;
  stdinInput?: string;
  exerciseId?: string;
  executionType?: string;
  commandLineArgs?: string[];
  environmentVars?: Record<string, string>;
}

interface CodeExecutionContextType {
  state: CodeExecutionState;
  executeCode: (params: ExecuteCodeParams) => Promise<CodeExecution>;
  stopExecution: (executionId: string) => Promise<void>;
  getEnvironments: () => Promise<void>;
  getExecutionHistory: () => Promise<void>;
  getTemplates: (environmentId?: string) => Promise<void>;
  getQuotaStatus: () => Promise<void>;
  loadExecution: (executionId: string) => Promise<void>;
  clearError: () => void;
  clearHistory: () => void;
}

const CodeExecutionContext = createContext<CodeExecutionContextType | undefined>(undefined);

export const useCodeExecution = () => {
  const context = useContext(CodeExecutionContext);
  if (!context) {
    throw new Error('useCodeExecution must be used within a CodeExecutionProvider');
  }
  return context;
};

interface CodeExecutionProviderProps {
  children: React.ReactNode;
}

export const CodeExecutionProvider: React.FC<CodeExecutionProviderProps> = ({ children }) => {
  const [state, dispatch] = useReducer(codeExecutionReducer, initialState);

  // Auto-load environments and quota on mount
  useEffect(() => {
    getEnvironments();
    getQuotaStatus();
  }, []);

  const executeCode = useCallback(async (params: ExecuteCodeParams): Promise<CodeExecution> => {
    dispatch({ type: 'SET_EXECUTING', payload: true });
    dispatch({ type: 'SET_ERROR', payload: null });

    try {
      // Add to execution queue
      const tempId = Date.now().toString();
      dispatch({ type: 'ADD_TO_QUEUE', payload: tempId });

      const response = await codeExecutionAPI.executeCode({
        source_code: params.sourceCode,
        environment_id: params.environmentId,
        stdin_input: params.stdinInput || '',
        exercise_id: params.exerciseId,
        execution_type: params.executionType || 'playground',
        command_line_args: params.commandLineArgs || [],
        environment_vars: params.environmentVars || {},
      });

      const execution: CodeExecution = {
        id: response.data.id,
        user: response.data.user,
        environment: response.data.environment,
        executionType: response.data.execution_type,
        sourceCode: response.data.source_code,
        stdinInput: response.data.stdin_input,
        output: response.data.stdout_output || '',
        stderr: response.data.stderr_output || '',
        exitCode: response.data.exit_code || 0,
        executionTime: response.data.execution_time || 0,
        memoryUsed: response.data.memory_used || 0,
        cpuTime: response.data.cpu_time || 0,
        status: response.data.status,
        isSuccessful: response.data.is_successful || false,
        qualityScore: response.data.quality_score,
        createdAt: response.data.created_at,
        startedAt: response.data.started_at,
        completedAt: response.data.completed_at,
        testResults: response.data.test_results || [],
      };

      dispatch({ type: 'SET_CURRENT_EXECUTION', payload: execution });
      dispatch({ type: 'ADD_TO_HISTORY', payload: execution });
      dispatch({ type: 'REMOVE_FROM_QUEUE', payload: tempId });

      // Update quota after execution
      await getQuotaStatus();

      return execution;
    } catch (error: any) {
      dispatch({ 
        type: 'SET_ERROR', 
        payload: error.response?.data?.error || 'Code execution failed' 
      });
      throw error;
    } finally {
      dispatch({ type: 'SET_EXECUTING', payload: false });
    }
  }, []);

  const stopExecution = useCallback(async (executionId: string) => {
    try {
      await codeExecutionAPI.stopExecution(executionId);
      
      // Update execution status
      if (state.currentExecution?.id === executionId) {
        const updatedExecution = {
          ...state.currentExecution,
          status: 'cancelled',
          completedAt: new Date().toISOString(),
        };
        dispatch({ type: 'UPDATE_EXECUTION', payload: updatedExecution });
      }
    } catch (error: any) {
      dispatch({ 
        type: 'SET_ERROR', 
        payload: error.response?.data?.error || 'Failed to stop execution' 
      });
    }
  }, [state.currentExecution]);

  const getEnvironments = useCallback(async () => {
    dispatch({ type: 'SET_LOADING', payload: true });

    try {
      const response = await codeExecutionAPI.getEnvironments();
      const environments: ExecutionEnvironment[] = response.data.map((env: any) => ({
        id: env.id,
        name: env.name,
        language: env.language,
        version: env.version,
        dockerImage: env.docker_image,
        defaultTimeout: env.default_timeout,
        maxMemory: env.max_memory,
        maxCpuTime: env.max_cpu_time,
        supportsInput: env.supports_input,
        supportsGraphics: env.supports_graphics,
        supportsNetworking: env.supports_networking,
        fileExtension: env.file_extension,
        compilerCommand: env.compiler_command,
        interpreterCommand: env.interpreter_command,
        installedPackages: env.installed_packages || [],
        availableLibraries: env.available_libraries || [],
        isDefault: env.is_default,
        status: env.status,
      }));

      dispatch({ type: 'SET_ENVIRONMENTS', payload: environments });
    } catch (error: any) {
      dispatch({ 
        type: 'SET_ERROR', 
        payload: error.response?.data?.error || 'Failed to load environments' 
      });
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  }, []);

  const getExecutionHistory = useCallback(async () => {
    try {
      const response = await codeExecutionAPI.getExecutionHistory();
      const history: CodeExecution[] = response.data.results.map((exec: any) => ({
        id: exec.id,
        user: exec.user,
        environment: exec.environment,
        executionType: exec.execution_type,
        sourceCode: exec.source_code,
        stdinInput: exec.stdin_input,
        output: exec.stdout_output || '',
        stderr: exec.stderr_output || '',
        exitCode: exec.exit_code || 0,
        executionTime: exec.execution_time || 0,
        memoryUsed: exec.memory_used || 0,
        cpuTime: exec.cpu_time || 0,
        status: exec.status,
        isSuccessful: exec.is_successful || false,
        qualityScore: exec.quality_score,
        createdAt: exec.created_at,
        startedAt: exec.started_at,
        completedAt: exec.completed_at,
      }));

      dispatch({ type: 'SET_EXECUTION_HISTORY', payload: history });
    } catch (error: any) {
      console.error('Failed to load execution history:', error);
    }
  }, []);

  const getTemplates = useCallback(async (environmentId?: string) => {
    try {
      const params = environmentId ? { environment: environmentId } : {};
      const response = await codeExecutionAPI.getTemplates(params);
      
      const templates: CodeTemplate[] = response.data.map((template: any) => ({
        id: template.id,
        name: template.name,
        templateType: template.template_type,
        environment: template.environment,
        codeTemplate: template.code_template,
        description: template.description,
        instructions: template.instructions,
        tags: template.tags || [],
        difficultyLevel: template.difficulty_level,
        usageCount: template.usage_count,
        isFeatured: template.is_featured,
      }));

      dispatch({ type: 'SET_TEMPLATES', payload: templates });
    } catch (error: any) {
      console.error('Failed to load templates:', error);
    }
  }, []);

  const getQuotaStatus = useCallback(async () => {
    try {
      const response = await codeExecutionAPI.getQuota();
      const quota: ExecutionQuota = response.data;
      dispatch({ type: 'SET_QUOTA', payload: quota });
    } catch (error: any) {
      console.error('Failed to load quota status:', error);
    }
  }, []);

  const loadExecution = useCallback(async (executionId: string) => {
    dispatch({ type: 'SET_LOADING', payload: true });

    try {
      const response = await codeExecutionAPI.getExecution(executionId);
      const execution: CodeExecution = {
        id: response.data.id,
        user: response.data.user,
        environment: response.data.environment,
        executionType: response.data.execution_type,
        sourceCode: response.data.source_code,
        stdinInput: response.data.stdin_input,
        output: response.data.stdout_output || '',
        stderr: response.data.stderr_output || '',
        exitCode: response.data.exit_code || 0,
        executionTime: response.data.execution_time || 0,
        memoryUsed: response.data.memory_used || 0,
        cpuTime: response.data.cpu_time || 0,
        status: response.data.status,
        isSuccessful: response.data.is_successful || false,
        qualityScore: response.data.quality_score,
        createdAt: response.data.created_at,
        startedAt: response.data.started_at,
        completedAt: response.data.completed_at,
        testResults: response.data.test_results || [],
      };

      dispatch({ type: 'SET_CURRENT_EXECUTION', payload: execution });
    } catch (error: any) {
      dispatch({ 
        type: 'SET_ERROR', 
        payload: error.response?.data?.error || 'Failed to load execution' 
      });
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  }, []);

  const clearError = useCallback(() => {
    dispatch({ type: 'SET_ERROR', payload: null });
  }, []);

  const clearHistory = useCallback(() => {
    dispatch({ type: 'SET_EXECUTION_HISTORY', payload: [] });
  }, []);

  return (
    <CodeExecutionContext.Provider
      value={{
        state,
        executeCode,
        stopExecution,
        getEnvironments,
        getExecutionHistory,
        getTemplates,
        getQuotaStatus,
        loadExecution,
        clearError,
        clearHistory,
      }}
    >
      {children}
    </CodeExecutionContext.Provider>
  );
};