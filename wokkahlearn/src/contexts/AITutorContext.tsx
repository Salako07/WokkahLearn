// src/contexts/AITutorContext.tsx - Complete Integration with Backend

import React, { createContext, useContext, useReducer, useCallback, useEffect } from 'react';
import { aiTutorAPI } from '../services/api';

interface AIMessage {
  id: string;
  messageType: 'user' | 'assistant' | 'system';
  content: string;
  codeLanguage?: string;
  suggestedImprovements?: string[];
  conceptsReferenced?: string[];
  confidenceScore?: number;
  metadata?: any;
  createdAt: string;
}

interface AITutorSession {
  id: string;
  sessionType: string;
  status: string;
  title: string;
  initialQuery: string;
  totalMessages: number;
  startedAt: string;
  endedAt?: string;
  messages: AIMessage[];
  aiModel?: {
    id: string;
    name: string;
    provider: string;
  };
}

interface LearningRecommendation {
  id: string;
  recommendationType: string;
  title: string;
  description: string;
  priority: string;
  difficultyLevel: string;
  estimatedDuration: string;
  reasoning: string;
  status: string;
  metadata?: any;
  createdAt: string;
}

interface CodeAnalysis {
  overallScore: number;
  issuesFound: string[];
  suggestions: string[];
  strengths: string[];
  summary: string;
  detailedFeedback: string;
  improvementSuggestions: string;
  conceptsDemonstrated: string[];
  missingConcepts: string[];
  nextLearningSteps: string[];
}

interface AITutorState {
  currentSession: AITutorSession | null;
  sessions: AITutorSession[];
  recommendations: LearningRecommendation[];
  recentAnalysis: CodeAnalysis | null;
  isLoading: boolean;
  isGenerating: boolean;
  error: string | null;
  isConnected: boolean;
}

type AITutorAction =
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_GENERATING'; payload: boolean }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'SET_CONNECTED'; payload: boolean }
  | { type: 'SET_CURRENT_SESSION'; payload: AITutorSession | null }
  | { type: 'SET_SESSIONS'; payload: AITutorSession[] }
  | { type: 'ADD_MESSAGE'; payload: { sessionId: string; message: AIMessage } }
  | { type: 'ADD_MESSAGES'; payload: { sessionId: string; messages: AIMessage[] } }
  | { type: 'UPDATE_SESSION'; payload: AITutorSession }
  | { type: 'SET_RECOMMENDATIONS'; payload: LearningRecommendation[] }
  | { type: 'SET_CODE_ANALYSIS'; payload: CodeAnalysis };

const initialState: AITutorState = {
  currentSession: null,
  sessions: [],
  recommendations: [],
  recentAnalysis: null,
  isLoading: false,
  isGenerating: false,
  error: null,
  isConnected: false,
};

const aiTutorReducer = (state: AITutorState, action: AITutorAction): AITutorState => {
  switch (action.type) {
    case 'SET_LOADING':
      return { ...state, isLoading: action.payload };
    case 'SET_GENERATING':
      return { ...state, isGenerating: action.payload };
    case 'SET_ERROR':
      return { ...state, error: action.payload };
    case 'SET_CONNECTED':
      return { ...state, isConnected: action.payload };
    case 'SET_CURRENT_SESSION':
      return { ...state, currentSession: action.payload };
    case 'SET_SESSIONS':
      return { ...state, sessions: action.payload };
    case 'ADD_MESSAGE':
      if (state.currentSession?.id === action.payload.sessionId) {
        return {
          ...state,
          currentSession: {
            ...state.currentSession,
            messages: [...state.currentSession.messages, action.payload.message],
            totalMessages: state.currentSession.totalMessages + 1,
          },
        };
      }
      return state;
    case 'ADD_MESSAGES':
      if (state.currentSession?.id === action.payload.sessionId) {
        return {
          ...state,
          currentSession: {
            ...state.currentSession,
            messages: [...state.currentSession.messages, ...action.payload.messages],
            totalMessages: state.currentSession.totalMessages + action.payload.messages.length,
          },
        };
      }
      return state;
    case 'UPDATE_SESSION':
      return {
        ...state,
        currentSession: state.currentSession?.id === action.payload.id 
          ? action.payload 
          : state.currentSession,
        sessions: state.sessions.map(session =>
          session.id === action.payload.id ? action.payload : session
        ),
      };
    case 'SET_RECOMMENDATIONS':
      return { ...state, recommendations: action.payload };
    case 'SET_CODE_ANALYSIS':
      return { ...state, recentAnalysis: action.payload };
    default:
      return state;
  }
};

interface AITutorContextType {
  state: AITutorState;
  startSession: (type: string, query: string, context?: any) => Promise<void>;
  sendMessage: (message: string, context?: any) => Promise<void>;
  loadSessions: () => Promise<void>;
  loadSession: (sessionId: string) => Promise<void>;
  endSession: (sessionId: string, feedback?: any) => Promise<void>;
  regenerateMessage: (messageId: string) => Promise<void>;
  getRecommendations: () => Promise<void>;
  generateRecommendations: (goals?: string[]) => Promise<void>;
  acceptRecommendation: (recommendationId: string) => Promise<void>;
  dismissRecommendation: (recommendationId: string, feedback?: string) => Promise<void>;
  analyzeCode: (code: string, language: string, exerciseId?: string) => Promise<void>;
  clearError: () => void;
  checkConnection: () => Promise<void>;
}

const AITutorContext = createContext<AITutorContextType | undefined>(undefined);

export const useAITutor = () => {
  const context = useContext(AITutorContext);
  if (!context) {
    throw new Error('useAITutor must be used within an AITutorProvider');
  }
  return context;
};

interface AITutorProviderProps {
  children: React.ReactNode;
}

export const AITutorProvider: React.FC<AITutorProviderProps> = ({ children }) => {
  const [state, dispatch] = useReducer(aiTutorReducer, initialState);

  // Check connection status on mount
  useEffect(() => {
    checkConnection();
  }, []);

  const checkConnection = useCallback(async () => {
    try {
      // Test AI service availability
      await aiTutorAPI.getSessions();
      dispatch({ type: 'SET_CONNECTED', payload: true });
    } catch (error: any) {
      dispatch({ type: 'SET_CONNECTED', payload: false });
      console.warn('AI Tutor service not available:', error.message);
    }
  }, []);

  const startSession = useCallback(async (type: string, query: string, context?: any) => {
    dispatch({ type: 'SET_LOADING', payload: true });
    dispatch({ type: 'SET_ERROR', payload: null });

    try {
      const response = await aiTutorAPI.createSession({
        session_type: type,
        initial_query: query,
        context_data: context || {},
      });

      const session: AITutorSession = {
        id: response.data.id,
        sessionType: response.data.session_type,
        status: response.data.status,
        title: response.data.title,
        initialQuery: response.data.initial_query,
        totalMessages: response.data.total_messages,
        startedAt: response.data.started_at,
        endedAt: response.data.ended_at,
        messages: [],
        aiModel: response.data.ai_model,
      };

      dispatch({ type: 'SET_CURRENT_SESSION', payload: session });

      // Load messages for the session
      await loadSessionMessages(session.id);
    } catch (error: any) {
      dispatch({ type: 'SET_ERROR', payload: error.response?.data?.error || 'Failed to start AI session' });
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  }, []);

  const loadSessionMessages = useCallback(async (sessionId: string) => {
    try {
      const response = await aiTutorAPI.getSessionMessages(sessionId);
      const messages = response.data.map((msg: any) => ({
        id: msg.id,
        messageType: msg.message_type,
        content: msg.content,
        codeLanguage: msg.code_language,
        suggestedImprovements: msg.suggested_improvements || [],
        conceptsReferenced: msg.concepts_referenced || [],
        confidenceScore: msg.confidence_score,
        metadata: msg.metadata,
        createdAt: msg.created_at,
      }));

      dispatch({
        type: 'ADD_MESSAGES',
        payload: { sessionId, messages }
      });
    } catch (error) {
      console.error('Failed to load session messages:', error);
    }
  }, []);

  const sendMessage = useCallback(async (message: string, context?: any) => {
    if (!state.currentSession) {
      throw new Error('No active session');
    }

    dispatch({ type: 'SET_GENERATING', payload: true });
    dispatch({ type: 'SET_ERROR', payload: null });

    try {
      const response = await aiTutorAPI.sendMessage(state.currentSession.id, {
        content: message,
        context: context || {},
      });

      // Add user message
      const userMessage: AIMessage = {
        id: response.data.user_message.id,
        messageType: 'user',
        content: message,
        createdAt: response.data.user_message.createdAt,
      };

      dispatch({
        type: 'ADD_MESSAGE',
        payload: { sessionId: state.currentSession.id, message: userMessage },
      });

      // Add AI response
      const aiResponse = response.data.ai_response;
      const aiMessage: AIMessage = {
        id: aiResponse.id,
        messageType: aiResponse.message_type,
        content: aiResponse.content,
        codeLanguage: aiResponse.code_language,
        suggestedImprovements: aiResponse.suggested_improvements || [],
        conceptsReferenced: aiResponse.concepts_referenced || [],
        confidenceScore: aiResponse.confidence_score,
        metadata: aiResponse.metadata,
        createdAt: aiResponse.created_at,
      };

      dispatch({
        type: 'ADD_MESSAGE',
        payload: { sessionId: state.currentSession.id, message: aiMessage },
      });
    } catch (error: any) {
      dispatch({ 
        type: 'SET_ERROR', 
        payload: error.response?.data?.error || 'Failed to send message' 
      });
    } finally {
      dispatch({ type: 'SET_GENERATING', payload: false });
    }
  }, [state.currentSession]);

  const loadSessions = useCallback(async () => {
    dispatch({ type: 'SET_LOADING', payload: true });

    try {
      const response = await aiTutorAPI.getSessions();
      const sessions = response.data.results.map((session: any) => ({
        id: session.id,
        sessionType: session.session_type,
        status: session.status,
        title: session.title,
        initialQuery: session.initial_query,
        totalMessages: session.total_messages,
        startedAt: session.started_at,
        endedAt: session.ended_at,
        messages: [],
        aiModel: session.ai_model,
      }));

      dispatch({ type: 'SET_SESSIONS', payload: sessions });
    } catch (error: any) {
      dispatch({ 
        type: 'SET_ERROR', 
        payload: error.response?.data?.error || 'Failed to load sessions' 
      });
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  }, []);

  const loadSession = useCallback(async (sessionId: string) => {
    dispatch({ type: 'SET_LOADING', payload: true });

    try {
      const response = await aiTutorAPI.getSession(sessionId);
      const session: AITutorSession = {
        id: response.data.id,
        sessionType: response.data.session_type,
        status: response.data.status,
        title: response.data.title,
        initialQuery: response.data.initial_query,
        totalMessages: response.data.total_messages,
        startedAt: response.data.started_at,
        endedAt: response.data.ended_at,
        messages: [],
        aiModel: response.data.ai_model,
      };

      dispatch({ type: 'SET_CURRENT_SESSION', payload: session });
      await loadSessionMessages(sessionId);
    } catch (error: any) {
      dispatch({ 
        type: 'SET_ERROR', 
        payload: error.response?.data?.error || 'Failed to load session' 
      });
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  }, [loadSessionMessages]);

  const endSession = useCallback(async (sessionId: string, feedback?: any) => {
    try {
      await aiTutorAPI.endSession(sessionId, feedback);
      
      // Update current session if it's the one being ended
      if (state.currentSession?.id === sessionId) {
        dispatch({ type: 'SET_CURRENT_SESSION', payload: null });
      }

      // Reload sessions to get updated status
      await loadSessions();
    } catch (error: any) {
      dispatch({ 
        type: 'SET_ERROR', 
        payload: error.response?.data?.error || 'Failed to end session' 
      });
    }
  }, [state.currentSession, loadSessions]);

  const regenerateMessage = useCallback(async (messageId: string) => {
    dispatch({ type: 'SET_GENERATING', payload: true });
    dispatch({ type: 'SET_ERROR', payload: null });

    try {
      // This would call a regenerate endpoint
      // For now, we'll show an error that it's not implemented
      throw new Error('Message regeneration not yet implemented');
    } catch (error: any) {
      dispatch({ 
        type: 'SET_ERROR', 
        payload: error.message || 'Failed to regenerate message' 
      });
    } finally {
      dispatch({ type: 'SET_GENERATING', payload: false });
    }
  }, []);

  const getRecommendations = useCallback(async () => {
    try {
      const response = await aiTutorAPI.getRecommendations();
      const recommendations = response.data.map((rec: any) => ({
        id: rec.id,
        recommendationType: rec.recommendation_type,
        title: rec.title,
        description: rec.description,
        priority: rec.priority,
        difficultyLevel: rec.difficulty_level,
        estimatedDuration: rec.estimated_duration,
        reasoning: rec.reasoning,
        status: rec.status,
        metadata: rec.metadata,
        createdAt: rec.created_at,
      }));

      dispatch({ type: 'SET_RECOMMENDATIONS', payload: recommendations });
    } catch (error: any) {
      console.error('Failed to load recommendations:', error);
    }
  }, []);

  const generateRecommendations = useCallback(async (goals?: string[]) => {
    dispatch({ type: 'SET_LOADING', payload: true });

    try {
      // This would generate new recommendations
      const response = await fetch('/api/ai-tutor/recommendations/generate/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ goals }),
      });

      if (!response.ok) throw new Error('Failed to generate recommendations');

      await getRecommendations(); // Reload recommendations
    } catch (error: any) {
      dispatch({ 
        type: 'SET_ERROR', 
        payload: error.message || 'Failed to generate recommendations' 
      });
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false });
    }
  }, [getRecommendations]);

  const acceptRecommendation = useCallback(async (recommendationId: string) => {
    try {
      await aiTutorAPI.acceptRecommendation(recommendationId);
      await getRecommendations(); // Reload to get updated status
    } catch (error: any) {
      dispatch({ 
        type: 'SET_ERROR', 
        payload: error.response?.data?.error || 'Failed to accept recommendation' 
      });
    }
  }, [getRecommendations]);

  const dismissRecommendation = useCallback(async (recommendationId: string, feedback?: string) => {
    try {
      // This would call a dismiss endpoint
      await fetch(`/api/ai-tutor/recommendations/${recommendationId}/dismiss/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ feedback }),
      });
      
      await getRecommendations(); // Reload to get updated status
    } catch (error: any) {
      dispatch({ 
        type: 'SET_ERROR', 
        payload: error.message || 'Failed to dismiss recommendation' 
      });
    }
  }, [getRecommendations]);

  const analyzeCode = useCallback(async (code: string, language: string, exerciseId?: string) => {
    dispatch({ type: 'SET_GENERATING', payload: true });
    dispatch({ type: 'SET_ERROR', payload: null });

    try {
      const response = await fetch('/api/ai-tutor/code-analysis/analyze_code/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code, language, exercise_id: exerciseId }),
      });

      if (!response.ok) throw new Error('Failed to analyze code');

      const data = await response.json();
      const analysis: CodeAnalysis = {
        overallScore: data.analysis.overall_score,
        issuesFound: data.analysis.issues_found,
        suggestions: data.analysis.suggestions,
        strengths: data.analysis.strengths,
        summary: data.analysis.summary,
        detailedFeedback: data.analysis.detailed_feedback,
        improvementSuggestions: data.analysis.improvement_suggestions,
        conceptsDemonstrated: data.analysis.concepts_demonstrated,
        missingConcepts: data.analysis.missing_concepts,
        nextLearningSteps: data.analysis.next_learning_steps,
      };

      dispatch({ type: 'SET_CODE_ANALYSIS', payload: analysis });
    } catch (error: any) {
      dispatch({ 
        type: 'SET_ERROR', 
        payload: error.message || 'Failed to analyze code' 
      });
    } finally {
      dispatch({ type: 'SET_GENERATING', payload: false });
    }
  }, []);

  const clearError = useCallback(() => {
    dispatch({ type: 'SET_ERROR', payload: null });
  }, []);

  return (
    <AITutorContext.Provider
      value={{
        state,
        startSession,
        sendMessage,
        loadSessions,
        loadSession,
        endSession,
        regenerateMessage,
        getRecommendations,
        generateRecommendations,
        acceptRecommendation,
        dismissRecommendation,
        analyzeCode,
        clearError,
        checkConnection,
      }}
    >
      {children}
    </AITutorContext.Provider>
  );
};