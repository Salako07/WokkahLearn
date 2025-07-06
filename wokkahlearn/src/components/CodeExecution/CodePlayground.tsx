// src/components/CodeExecution/CodePlayground.tsx - Interactive Code Playground

import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  IconButton,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Grid,
  Card,
  CardContent,
  CardActions,
  Tooltip,
  Alert,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  ListItemSecondaryAction,
  Menu,
  Autocomplete,
} from '@mui/material';
import {
  Add,
  Save,
  Share,
  Download,
  Upload,
  Delete,
  Star,
  StarBorder,
  Visibility,
  VisibilityOff,
  ContentCopy,
  ForkRight,
  History,
  PlayArrow,
  Settings,
  Code,
  Public,
  Lock,
  Group,
  School,
  MoreVert,
} from '@mui/icons-material';
import { useParams, useNavigate } from 'react-router-dom';
import CodeExecutor from './CodeExecutor';
import { useCodeExecution } from '../../contexts/CodeExecutionContext';
import { useAuth } from '../../contexts/AuthContext';

interface CodePlayground {
  id: string;
  title: string;
  description: string;
  sourceCode: string;
  environment: {
    id: string;
    name: string;
    language: string;
  };
  visibility: string;
  tags: string[];
  user: {
    id: string;
    username: string;
    fullName: string;
  };
  collaborators: Array<{
    id: string;
    username: string;
    permission: string;
  }>;
  executionCount: number;
  forkCount: number;
  isFeatured: boolean;
  isTemplate: boolean;
  createdAt: string;
  updatedAt: string;
}

const CodePlayground: React.FC = () => {
  const { playgroundId } = useParams<{ playgroundId?: string }>();
  const navigate = useNavigate();
  const { user } = useAuth();
  const { state: execState, getEnvironments } = useCodeExecution();

  const [playground, setPlayground] = useState<CodePlayground | null>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [showShareDialog, setShowShareDialog] = useState(false);
  const [showSaveDialog, setShowSaveDialog] = useState(false);
  const [showTemplatesDialog, setShowTemplatesDialog] = useState(false);
  const [shareEmails, setShareEmails] = useState<string[]>([]);
  const [sharePermission, setSharePermission] = useState('view');
  const [menuAnchor, setMenuAnchor] = useState<null | HTMLElement>(null);

  // Form state
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [code, setCode] = useState('');
  const [selectedEnvironment, setSelectedEnvironment] = useState('');
  const [visibility, setVisibility] = useState('private');
  const [tags, setTags] = useState<string[]>([]);

  // Load playground if ID provided
  useEffect(() => {
    if (playgroundId) {
      loadPlayground(playgroundId);
    } else {
      // New playground
      setIsEditing(true);
      setTitle('Untitled Playground');
      setCode('# Welcome to WokkahLearn Code Playground!\n# Start coding here...\n\nprint("Hello, World!")');
    }
  }, [playgroundId]);

  // Load environments
  useEffect(() => {
    getEnvironments();
  }, []);

  const loadPlayground = async (id: string) => {
    try {
      // Mock loading playground - replace with actual API call
      const mockPlayground: CodePlayground = {
        id,
        title: 'My Python Playground',
        description: 'A place to experiment with Python code',
        sourceCode: 'print("Hello from playground!")\n\n# Write your code here',
        environment: {
          id: 'python-3.11',
          name: 'Python 3.11',
          language: 'python'
        },
        visibility: 'private',
        tags: ['python', 'learning'],
        user: {
          id: user?.id || '1',
          username: user?.username || 'testuser',
          fullName: user?.fullName || 'Test User'
        },
        collaborators: [],
        executionCount: 5,
        forkCount: 2,
        isFeatured: false,
        isTemplate: false,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
      };

      setPlayground(mockPlayground);
      setTitle(mockPlayground.title);
      setDescription(mockPlayground.description);
      setCode(mockPlayground.sourceCode);
      setSelectedEnvironment(mockPlayground.environment.id);
      setVisibility(mockPlayground.visibility);
      setTags(mockPlayground.tags);
    } catch (error) {
      console.error('Failed to load playground:', error);
    }
  };

  const handleSave = async () => {
    setIsSaving(true);
    try {
      if (playground) {
        // Update existing playground
        // Mock API call
        const updatedPlayground = {
          ...playground,
          title,
          description,
          sourceCode: code,
          tags,
          visibility,
          updatedAt: new Date().toISOString()
        };
        setPlayground(updatedPlayground);
      } else {
        // Create new playground
        // Mock API call
        const newPlayground: CodePlayground = {
          id: Date.now().toString(),
          title,
          description,
          sourceCode: code,
          environment: execState.environments.find(e => e.id === selectedEnvironment) || execState.environments[0],
          visibility,
          tags,
          user: {
            id: user?.id || '1',
            username: user?.username || 'testuser',
            fullName: user?.fullName || 'Test User'
          },
          collaborators: [],
          executionCount: 0,
          forkCount: 0,
          isFeatured: false,
          isTemplate: false,
          createdAt: new Date().toISOString(),
          updatedAt: new Date().toISOString()
        };
        setPlayground(newPlayground);
        navigate(`/playground/${newPlayground.id}`);
      }
      setIsEditing(false);
      setShowSaveDialog(false);
    } catch (error) {
      console.error('Failed to save playground:', error);
    } finally {
      setIsSaving(false);
    }
  };

  const handleFork = async () => {
    if (!playground) return;

    try {
      // Mock fork API call
      const forkedPlayground: CodePlayground = {
        ...playground,
        id: Date.now().toString(),
        title: `Fork of ${playground.title}`,
        user: {
          id: user?.id || '1',
          username: user?.username || 'testuser',
          fullName: user?.fullName || 'Test User'
        },
        collaborators: [],
        executionCount: 0,
        forkCount: 0,
        createdAt: new Date().toISOString(),
        updatedAt: new Date().toISOString()
      };

      navigate(`/playground/${forkedPlayground.id}`);
    } catch (error) {
      console.error('Failed to fork playground:', error);
    }
  };

  const handleShare = async () => {
    try {
      // Mock share API call
      console.log('Sharing with:', shareEmails, 'Permission:', sharePermission);
      setShowShareDialog(false);
      setShareEmails([]);
    } catch (error) {
      console.error('Failed to share playground:', error);
    }
  };

  const canEdit = () => {
    if (!playground) return true; // New playground
    if (playground.user.id === user?.id) return true; // Owner
    return playground.collaborators.some(
      c => c.id === user?.id && ['edit', 'admin'].includes(c.permission)
    );
  };

  const getVisibilityIcon = (vis: string) => {
    switch (vis) {
      case 'public': return <Public fontSize="small" />;
      case 'shared': return <Group fontSize="small" />;
      case 'course': return <School fontSize="small" />;
      default: return <Lock fontSize="small" />;
    }
  };

  return (
    <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Header */}
      <Paper elevation={1} sx={{ p: 2, mb: 1 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box sx={{ flex: 1 }}>
            {isEditing ? (
              <TextField
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                variant="outlined"
                size="small"
                placeholder="Playground title..."
                sx={{ mr: 2, minWidth: 200 }}
              />
            ) : (
              <Typography variant="h6" sx={{ mr: 2 }}>
                {playground?.title || 'New Playground'}
              </Typography>
            )}

            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 1 }}>
              {/* Visibility indicator */}
              <Chip
                icon={getVisibilityIcon(playground?.visibility || visibility)}
                label={playground?.visibility || visibility}
                size="small"
                variant="outlined"
              />

              {/* Tags */}
              {(playground?.tags || tags).map((tag, index) => (
                <Chip key={index} label={tag} size="small" />
              ))}

              {/* Stats */}
              {playground && (
                <>
                  <Chip
                    icon={<PlayArrow />}
                    label={`${playground.executionCount} runs`}
                    size="small"
                    variant="outlined"
                  />
                  <Chip
                    icon={<ForkRight />}
                    label={`${playground.forkCount} forks`}
                    size="small"
                    variant="outlined"
                  />
                </>
              )}
            </Box>
          </Box>

          {/* Actions */}
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            {canEdit() && (
              <>
                {isEditing ? (
                  <Button
                    variant="contained"
                    onClick={() => setShowSaveDialog(true)}
                    disabled={!title.trim() || isSaving}
                    startIcon={<Save />}
                  >
                    Save
                  </Button>
                ) : (
                  <Button
                    variant="outlined"
                    onClick={() => setIsEditing(true)}
                    startIcon={<Code />}
                  >
                    Edit
                  </Button>
                )}
              </>
            )}

            {playground && (
              <>
                <Button
                  variant="outlined"
                  onClick={handleFork}
                  startIcon={<ForkRight />}
                >
                  Fork
                </Button>

                <Button
                  variant="outlined"
                  onClick={() => setShowShareDialog(true)}
                  startIcon={<Share />}
                >
                  Share
                </Button>
              </>
            )}

            <IconButton onClick={(e) => setMenuAnchor(e.currentTarget)}>
              <MoreVert />
            </IconButton>
          </Box>
        </Box>
      </Paper>

      {/* Main Content */}
      <Box sx={{ flex: 1 }}>
        <CodeExecutor
          initialCode={code}
          language={
            execState.environments.find(e => e.id === selectedEnvironment)?.language || 'python'
          }
          onCodeChange={setCode}
          readOnly={!canEdit()}
        />
      </Box>

      {/* Save Dialog */}
      <Dialog open={showSaveDialog} onClose={() => setShowSaveDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Save Playground</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 1 }}>
            <TextField
              fullWidth
              label="Title"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              margin="normal"
            />

            <TextField
              fullWidth
              label="Description"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              multiline
              rows={3}
              margin="normal"
            />

            <FormControl fullWidth margin="normal">
              <InputLabel>Environment</InputLabel>
              <Select
                value={selectedEnvironment}
                onChange={(e) => setSelectedEnvironment(e.target.value)}
              >
                {execState.environments.map(env => (
                  <MenuItem key={env.id} value={env.id}>
                    {env.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            <FormControl fullWidth margin="normal">
              <InputLabel>Visibility</InputLabel>
              <Select
                value={visibility}
                onChange={(e) => setVisibility(e.target.value)}
              >
                <MenuItem value="private">
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Lock fontSize="small" />
                    Private
                  </Box>
                </MenuItem>
                <MenuItem value="public">
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Public fontSize="small" />
                    Public
                  </Box>
                </MenuItem>
                <MenuItem value="shared">
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Group fontSize="small" />
                    Shared
                  </Box>
                </MenuItem>
              </Select>
            </FormControl>

            <Autocomplete
              multiple
              freeSolo
              options={['python', 'javascript', 'tutorial', 'practice', 'algorithm']}
              value={tags}
              onChange={(_, newTags) => setTags(newTags)}
              renderInput={(params) => (
                <TextField
                  {...params}
                  label="Tags"
                  placeholder="Add tags..."
                  margin="normal"
                />
              )}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowSaveDialog(false)}>Cancel</Button>
          <Button onClick={handleSave} variant="contained" disabled={!title.trim() || isSaving}>
            {isSaving ? 'Saving...' : 'Save'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Share Dialog */}
      <Dialog open={showShareDialog} onClose={() => setShowShareDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Share Playground</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 1 }}>
            <Alert severity="info" sx={{ mb: 2 }}>
              Share your playground with others by adding their email addresses.
            </Alert>

            <Autocomplete
              multiple
              freeSolo
              options={[]}
              value={shareEmails}
              onChange={(_, newEmails) => setShareEmails(newEmails)}
              renderInput={(params) => (
                <TextField
                  {...params}
                  label="Email addresses"
                  placeholder="Enter email addresses..."
                  margin="normal"
                />
              )}
            />

            <FormControl fullWidth margin="normal">
              <InputLabel>Permission</InputLabel>
              <Select
                value={sharePermission}
                onChange={(e) => setSharePermission(e.target.value)}
              >
                <MenuItem value="view">View Only</MenuItem>
                <MenuItem value="edit">Can Edit</MenuItem>
                <MenuItem value="admin">Admin Access</MenuItem>
              </Select>
            </FormControl>

            {/* Current collaborators */}
            {playground?.collaborators.length > 0 && (
              <Box sx={{ mt: 2 }}>
                <Typography variant="subtitle2" gutterBottom>
                  Current Collaborators
                </Typography>
                <List dense>
                  {playground.collaborators.map(collaborator => (
                    <ListItem key={collaborator.id}>
                      <ListItemText
                        primary={collaborator.username}
                        secondary={collaborator.permission}
                      />
                      <ListItemSecondaryAction>
                        <IconButton size="small">
                          <Delete />
                        </IconButton>
                      </ListItemSecondaryAction>
                    </ListItem>
                  ))}
                </List>
              </Box>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowShareDialog(false)}>Cancel</Button>
          <Button 
            onClick={handleShare} 
            variant="contained"
            disabled={shareEmails.length === 0}
          >
            Share
          </Button>
        </DialogActions>
      </Dialog>

      {/* More Actions Menu */}
      <Menu
        anchorEl={menuAnchor}
        open={Boolean(menuAnchor)}
        onClose={() => setMenuAnchor(null)}
      >
        <MenuItem onClick={() => setShowTemplatesDialog(true)}>
          <ListItemIcon><Code /></ListItemIcon>
          <ListItemText>Load Template</ListItemText>
        </MenuItem>
        <MenuItem onClick={() => navigator.clipboard.writeText(window.location.href)}>
          <ListItemIcon><ContentCopy /></ListItemIcon>
          <ListItemText>Copy Link</ListItemText>
        </MenuItem>
        <MenuItem>
          <ListItemIcon><Download /></ListItemIcon>
          <ListItemText>Export Code</ListItemText>
        </MenuItem>
        <Divider />
        <MenuItem>
          <ListItemIcon><History /></ListItemIcon>
          <ListItemText>View History</ListItemText>
        </MenuItem>
        <MenuItem>
          <ListItemIcon><Settings /></ListItemIcon>
          <ListItemText>Settings</ListItemText>
        </MenuItem>
      </Menu>
    </Box>
  );
};

export default CodePlayground;