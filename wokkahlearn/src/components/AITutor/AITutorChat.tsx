// src/components/AITutor/AITutorChat.tsx - Complete AI Tutor Integration

import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  IconButton,
  Button,
  Avatar,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  CircularProgress,
  Alert,
  Tooltip,
  Menu,
  MenuItem,
  Fade,
  LinearProgress,
} from '@mui/material';
import {
  Send,
  Psychology,
  Code,
  Help,
  Lightbulb,
  BugReport,
  School,
  History,
  MoreVert,
  Copy,
  ThumbUp,
  ThumbDown,
  Refresh,
  Close,
} from '@mui/icons-material';
import { useAITutor } from '../../contexts/AITutorContext';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { tomorrow } from 'react-syntax-highlighter/dist/esm/styles/prism';
import ReactMarkdown from 'react-markdown';

interface AITutorChatProps {
  open: boolean;
  onClose: () => void;
  initialSessionType?: string;
  initialQuery?: string;
  context?: any;
}

const AITutorChat: React.FC<AITutorChatProps> = ({
  open,
  onClose,
  initialSessionType = 'help_request',
  initialQuery = '',
  context = {}
}) => {
  const {
    state,
    startSession,
    sendMessage,
    loadSessions,
    endSession,
    clearError
  } = useAITutor();

  const [message, setMessage] = useState('');
  const [sessionStarted, setSessionStarted] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const [menuAnchor, setMenuAnchor] = useState<null | HTMLElement>(null);
  
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    scrollToBottom();
  }, [state.currentSession?.messages]);

  // Focus input when dialog opens
  useEffect(() => {
    if (open && inputRef.current) {
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [open]);

  // Auto-start session if initial query provided
  useEffect(() => {
    if (open && initialQuery && !sessionStarted) {
      handleStartSession(initialSessionType, initialQuery);
      setSessionStarted(true);
    }
  }, [open, initialQuery, sessionStarted]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleStartSession = async (type: string, query: string) => {
    try {
      await startSession(type, query, context);
      setMessage('');
      setSessionStarted(true);
    } catch (error) {
      console.error('Failed to start session:', error);
    }
  };

  const handleSendMessage = async () => {
    if (!message.trim()) return;

    if (!state.currentSession) {
      await handleStartSession(initialSessionType, message);
      return;
    }

    try {
      await sendMessage(message, context);
      setMessage('');
    } catch (error) {
      console.error('Failed to send message:', error);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleCopyMessage = (content: string) => {
    navigator.clipboard.writeText(content);
  };

  const handleEndSession = async () => {
    if (state.currentSession) {
      await endSession(state.currentSession.id);
      setSessionStarted(false);
      onClose();
    }
  };

  const getSessionTypeInfo = (type: string) => {
    const types = {
      help_request: { icon: Help, label: 'Get Help', color: '#2196f3' },
      code_review: { icon: Code, label: 'Code Review', color: '#ff9800' },
      concept_explanation: { icon: School, label: 'Learn Concept', color: '#4caf50' },
      debugging: { icon: BugReport, label: 'Debug Code', color: '#f44336' },
      general: { icon: Psychology, label: 'AI Tutor', color: '#9c27b0' }
    };
    return types[type] || types.general;
  };

  const MessageComponent = ({ message: msg, isLast }: { message: any, isLast: boolean }) => {
    const isUser = msg.messageType === 'user';
    const isSystem = msg.messageType === 'system';

    return (
      <Box
        sx={{
          display: 'flex',
          justifyContent: isUser ? 'flex-end' : 'flex-start',
          mb: 2,
          opacity: isLast && state.isGenerating ? 0.7 : 1
        }}
      >
        <Box
          sx={{
            maxWidth: '85%',
            display: 'flex',
            flexDirection: isUser ? 'row-reverse' : 'row',
            alignItems: 'flex-start',
            gap: 1
          }}
        >
          {/* Avatar */}
          <Avatar
            sx={{
              bgcolor: isUser ? 'primary.main' : isSystem ? 'warning.main' : 'secondary.main',
              width: 32,
              height: 32
            }}
          >
            {isUser ? '👤' : isSystem ? '⚠️' : '🤖'}
          </Avatar>

          {/* Message Content */}
          <Paper
            elevation={1}
            sx={{
              p: 2,
              bgcolor: isUser ? 'primary.main' : isSystem ? 'warning.light' : 'grey.50',
              color: isUser ? 'primary.contrastText' : 'text.primary',
              borderRadius: '12px',
              position: 'relative'
            }}
          >
            {/* Message Text */}
            <Box sx={{ mb: msg.codeLanguage ? 1 : 0 }}>
              <ReactMarkdown
                components={{
                  code: ({ node, inline, className, children, ...props }) => {
                    const match = /language-(\w+)/.exec(className || '');
                    return !inline && match ? (
                      <SyntaxHighlighter
                        style={tomorrow}
                        language={match[1]}
                        PreTag="div"
                        {...props}
                      >
                        {String(children).replace(/\n$/, '')}
                      </SyntaxHighlighter>
                    ) : (
                      <code className={className} {...props}>
                        {children}
                      </code>
                    );
                  }
                }}
              >
                {msg.content}
              </ReactMarkdown>
            </Box>

            {/* Suggested Improvements */}
            {msg.suggestedImprovements && msg.suggestedImprovements.length > 0 && (
              <Box sx={{ mt: 1 }}>
                <Typography variant="caption" sx={{ fontWeight: 'bold', color: 'success.main' }}>
                  💡 Suggestions:
                </Typography>
                {msg.suggestedImprovements.map((suggestion: string, idx: number) => (
                  <Chip
                    key={idx}
                    label={suggestion}
                    size="small"
                    variant="outlined"
                    sx={{ mr: 0.5, mt: 0.5 }}
                  />
                ))}
              </Box>
            )}

            {/* Concepts Referenced */}
            {msg.conceptsReferenced && msg.conceptsReferenced.length > 0 && (
              <Box sx={{ mt: 1 }}>
                <Typography variant="caption" sx={{ fontWeight: 'bold', color: 'info.main' }}>
                  📚 Concepts:
                </Typography>
                {msg.conceptsReferenced.map((concept: string, idx: number) => (
                  <Chip
                    key={idx}
                    label={concept}
                    size="small"
                    color="info"
                    variant="outlined"
                    sx={{ mr: 0.5, mt: 0.5 }}
                  />
                ))}
              </Box>
            )}

            {/* Message Actions */}
            {!isUser && (
              <Box sx={{ mt: 1, display: 'flex', gap: 1 }}>
                <Tooltip title="Copy message">
                  <IconButton
                    size="small"
                    onClick={() => handleCopyMessage(msg.content)}
                    sx={{ opacity: 0.7 }}
                  >
                    <Copy fontSize="small" />
                  </IconButton>
                </Tooltip>
                <Tooltip title="Helpful">
                  <IconButton size="small" sx={{ opacity: 0.7 }}>
                    <ThumbUp fontSize="small" />
                  </IconButton>
                </Tooltip>
                <Tooltip title="Not helpful">
                  <IconButton size="small" sx={{ opacity: 0.7 }}>
                    <ThumbDown fontSize="small" />
                  </IconButton>
                </Tooltip>
              </Box>
            )}

            {/* Timestamp */}
            <Typography
              variant="caption"
              sx={{
                position: 'absolute',
                bottom: -20,
                right: isUser ? 0 : 'auto',
                left: isUser ? 'auto' : 0,
                color: 'text.secondary',
                fontSize: '0.7rem'
              }}
            >
              {new Date(msg.createdAt).toLocaleTimeString([], {
                hour: '2-digit',
                minute: '2-digit'
              })}
            </Typography>
          </Paper>
        </Box>
      </Box>
    );
  };

  const QuickActions = () => {
    const actions = [
      { type: 'help_request', label: 'Get Help', icon: Help },
      { type: 'code_review', label: 'Review Code', icon: Code },
      { type: 'concept_explanation', label: 'Explain Concept', icon: School },
      { type: 'debugging', label: 'Debug Issue', icon: BugReport },
    ];

    return (
      <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mb: 2 }}>
        {actions.map(action => {
          const Icon = action.icon;
          return (
            <Button
              key={action.type}
              variant="outlined"
              size="small"
              startIcon={<Icon />}
              onClick={() => {
                const queries = {
                  help_request: "I need help with my code. Can you assist me?",
                  code_review: "Can you review my code and provide feedback?",
                  concept_explanation: "Can you explain a programming concept to me?",
                  debugging: "I have a bug in my code. Can you help me fix it?"
                };
                handleStartSession(action.type, queries[action.type]);
              }}
              sx={{ borderRadius: '20px' }}
            >
              {action.label}
            </Button>
          );
        })}
      </Box>
    );
  };

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="md"
      fullWidth
      PaperProps={{
        sx: {
          height: '80vh',
          display: 'flex',
          flexDirection: 'column'
        }
      }}
    >
      {/* Header */}
      <DialogTitle
        sx={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          borderBottom: 1,
          borderColor: 'divider',
          pb: 1
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Avatar sx={{ bgcolor: 'secondary.main' }}>
            <Psychology />
          </Avatar>
          <Box>
            <Typography variant="h6">AI Tutor</Typography>
            {state.currentSession && (
              <Typography variant="caption" color="text.secondary">
                {getSessionTypeInfo(state.currentSession.sessionType).label}
              </Typography>
            )}
          </Box>
        </Box>

        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          {state.currentSession && (
            <Tooltip title="Session options">
              <IconButton
                onClick={(e) => setMenuAnchor(e.currentTarget)}
              >
                <MoreVert />
              </IconButton>
            </Tooltip>
          )}
          <IconButton onClick={onClose}>
            <Close />
          </IconButton>
        </Box>
      </DialogTitle>

      {/* Progress Bar */}
      {(state.isLoading || state.isGenerating) && (
        <LinearProgress />
      )}

      {/* Chat Content */}
      <DialogContent
        sx={{
          flex: 1,
          display: 'flex',
          flexDirection: 'column',
          p: 0
        }}
      >
        {/* Error Display */}
        {state.error && (
          <Alert
            severity="error"
            onClose={clearError}
            sx={{ m: 2, mb: 1 }}
          >
            {state.error}
          </Alert>
        )}

        {/* Messages Container */}
        <Box
          sx={{
            flex: 1,
            overflow: 'auto',
            p: 2,
            display: 'flex',
            flexDirection: 'column'
          }}
        >
          {!state.currentSession ? (
            <Box sx={{ textAlign: 'center', py: 4 }}>
              <Psychology sx={{ fontSize: 60, color: 'text.secondary', mb: 2 }} />
              <Typography variant="h6" gutterBottom>
                How can I help you today?
              </Typography>
              <Typography color="text.secondary" sx={{ mb: 3 }}>
                I'm your AI programming tutor. I can help with coding questions, 
                debug issues, explain concepts, and review your code.
              </Typography>
              
              <QuickActions />
            </Box>
          ) : (
            <>
              {/* Messages */}
              {state.currentSession.messages.map((msg, index) => (
                <MessageComponent
                  key={msg.id || index}
                  message={msg}
                  isLast={index === state.currentSession.messages.length - 1}
                />
              ))}

              {/* Typing Indicator */}
              {state.isGenerating && (
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                  <Avatar sx={{ bgcolor: 'secondary.main', width: 32, height: 32 }}>
                    🤖
                  </Avatar>
                  <Paper elevation={1} sx={{ p: 2, borderRadius: '12px' }}>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <CircularProgress size={16} />
                      <Typography variant="body2" color="text.secondary">
                        AI is thinking...
                      </Typography>
                    </Box>
                  </Paper>
                </Box>
              )}

              <div ref={messagesEndRef} />
            </>
          )}
        </Box>
      </DialogContent>

      {/* Input Area */}
      <DialogActions
        sx={{
          borderTop: 1,
          borderColor: 'divider',
          p: 2,
          alignItems: 'flex-end'
        }}
      >
        <TextField
          ref={inputRef}
          fullWidth
          multiline
          maxRows={4}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder={
            state.currentSession
              ? "Type your message..."
              : "Ask me anything about programming..."
          }
          disabled={state.isLoading || state.isGenerating}
          variant="outlined"
          size="small"
          sx={{ mr: 1 }}
        />
        <Tooltip title="Send message">
          <span>
            <IconButton
              onClick={handleSendMessage}
              disabled={!message.trim() || state.isLoading || state.isGenerating}
              color="primary"
              sx={{
                bgcolor: 'primary.main',
                color: 'white',
                '&:hover': { bgcolor: 'primary.dark' },
                '&:disabled': { bgcolor: 'grey.300' }
              }}
            >
              <Send />
            </IconButton>
          </span>
        </Tooltip>
      </DialogActions>

      {/* Session Menu */}
      <Menu
        anchorEl={menuAnchor}
        open={Boolean(menuAnchor)}
        onClose={() => setMenuAnchor(null)}
      >
        <MenuItem onClick={() => { /* TODO: Save session */ }}>
          <History sx={{ mr: 1 }} /> Save Session
        </MenuItem>
        <MenuItem onClick={handleEndSession}>
          <Close sx={{ mr: 1 }} /> End Session
        </MenuItem>
      </Menu>
    </Dialog>
  );
};

export default AITutorChat;