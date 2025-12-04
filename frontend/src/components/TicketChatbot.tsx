import React, { useState, useEffect, useRef } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  CircularProgress,
  Stack,
  Chip,
  Alert,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  ListItemSecondaryAction,
  Menu,
  MenuItem,
  Tooltip
} from '@mui/material';
import {
  Send as SendIcon,
  Psychology as PsychologyIcon,
  AttachFile as AttachFileIcon,
  Description as DescriptionIcon,
  Delete as DeleteIcon,
  Close as CloseIcon,
  Assignment as AssignmentIcon,
  CheckCircle as CheckCircleIcon,
  Add as AddIcon,
  MoreVert as MoreVertIcon
} from '@mui/icons-material';
import { helpdeskAPI } from '../services/api';

interface TicketChatbotProps {
  ticketId: string;
}

type ChatMessage = {
  id?: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp?: Date | string;
  ai_status?: string;
  ai_model?: string;
  ai_task_id?: string;  // Celery task ID for tracking
  linked_to_npa_id?: string;
  is_solution?: boolean;
  solution_notes?: string;
};

type Attachment = {
  id: string;
  filename: string;
  content: string;
  type?: string;
};

const SUGGESTIONS = [
  'What questions should I ask the customer?',
  'What are the next steps for this ticket?',
  'How should I respond to this issue?',
  'What information is missing?',
  'Suggest troubleshooting steps',
  'What similar issues have we resolved?'
];

const TicketChatbot: React.FC<TicketChatbotProps> = ({ ticketId }) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [attachments, setAttachments] = useState<Attachment[]>([]);
  const [logFiles, setLogFiles] = useState<string[]>([]);
  const [showLogDialog, setShowLogDialog] = useState(false);
  const [logInput, setLogInput] = useState('');
  const [showAttachDialog, setShowAttachDialog] = useState(false);
  const [loadingHistory, setLoadingHistory] = useState(true);
  const [pollingTaskId, setPollingTaskId] = useState<string | null>(null);
  const [messageMenuAnchor, setMessageMenuAnchor] = useState<{ anchor: HTMLElement; messageId: string } | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Load chat history on mount
  useEffect(() => {
    loadChatHistory();
  }, [ticketId]);

  // Poll for task status
  useEffect(() => {
    if (pollingTaskId) {
      pollingIntervalRef.current = setInterval(() => {
        checkTaskStatus(pollingTaskId);
      }, 2000); // Poll every 2 seconds
    } else {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
        pollingIntervalRef.current = null;
      }
    }

    return () => {
      if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current);
      }
    };
  }, [pollingTaskId]);

  const loadChatHistory = async () => {
    try {
      setLoadingHistory(true);
      setError(null); // Clear any previous errors
      const response = await helpdeskAPI.getAgentChatHistory(ticketId);
      
      // Always clear error on successful response
      setError(null);
      
      // Handle response - messages might be undefined if table doesn't exist yet
      const messagesArray = response.data?.messages || [];
      
      if (Array.isArray(messagesArray)) {
        const loadedMessages: ChatMessage[] = messagesArray.map((msg: any) => ({
          id: msg.id,
          role: msg.role,
          content: msg.content,
          timestamp: msg.timestamp ? new Date(msg.timestamp) : undefined,
          ai_status: msg.ai_status,
          ai_model: msg.ai_model,
          ai_task_id: msg.ai_task_id,  // Include task ID for polling
          linked_to_npa_id: msg.linked_to_npa_id,
          is_solution: msg.is_solution,
          solution_notes: msg.solution_notes
        }));
        setMessages(loadedMessages);
        
        // Check if any message is still processing and resume polling
        const processingMessage = loadedMessages.find(m => 
          (m.ai_status === 'processing' || m.ai_status === 'pending') && m.ai_task_id
        );
        if (processingMessage?.ai_task_id) {
          // Resume polling for this task
          setPollingTaskId(processingMessage.ai_task_id);
        }
      } else {
        // No messages yet - this is fine, just set empty array
        setMessages([]);
      }
    } catch (err: any) {
      console.error('Failed to load chat history:', err);
      // Only show error for actual failures, not for missing table (which returns empty array)
      if (err.response?.status && err.response.status >= 400 && err.response.status !== 500) {
        setError('Failed to load chat history');
      } else if (err.response?.status === 500) {
        // 500 might be table missing, but also might be real error
        // Check error message
        const errorDetail = err.response?.data?.detail || '';
        if (!errorDetail.includes('table') && !errorDetail.includes('relation') && !errorDetail.includes('does not exist')) {
          setError('Failed to load chat history');
        }
      } else if (!err.response) {
        // Network error or other non-HTTP error
        setError('Failed to load chat history');
      }
      // Set empty messages array so UI still works
      setMessages([]);
    } finally {
      setLoadingHistory(false);
    }
  };

  const checkTaskStatus = async (taskId: string) => {
    try {
      const response = await helpdeskAPI.getAgentChatTaskStatus(ticketId, taskId);
      if (response.data?.status === 'completed') {
        setPollingTaskId(null);
        // Reload chat history to get the completed AI response
        // Use a flag to prevent scrolling during this reload
        await loadChatHistory();
      } else if (response.data?.status === 'failed') {
        setPollingTaskId(null);
        setError(response.data?.error || 'AI response failed');
        // Update the pending message to show error without full reload
        setMessages((prev) => 
          prev.map(msg => 
            msg.ai_task_id === taskId && msg.ai_status === 'processing' 
              ? { ...msg, ai_status: 'failed', content: 'Sorry, I encountered an error. Please try again.' }
              : msg
          )
        );
      }
      // If still processing, no action needed - will poll again
    } catch (err: any) {
      console.error('Failed to check task status:', err);
    }
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    // Only scroll if we're not polling (to avoid jumps during polling)
    if (!pollingTaskId) {
      scrollToBottom();
    }
  }, [messages, pollingTaskId]);

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = event.target.files;
    if (!files) return;

    Array.from(files).forEach((file) => {
      const reader = new FileReader();
      reader.onload = (e) => {
        const content = e.target?.result as string;
        const newAttachment: Attachment = {
          id: Date.now().toString() + Math.random(),
          filename: file.name,
          content: content.substring(0, 10000), // Limit to 10KB
          type: file.type || 'text/plain'
        };
        setAttachments((prev) => [...prev, newAttachment]);
      };
      reader.readAsText(file);
    });

    // Reset input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const handleRemoveAttachment = (id: string) => {
    setAttachments((prev) => prev.filter((att) => att.id !== id));
  };

  const handleAddLogFile = () => {
    if (logInput.trim()) {
      setLogFiles((prev) => [...prev, logInput.trim()]);
      setLogInput('');
      setShowLogDialog(false);
    }
  };

  const handleRemoveLogFile = (index: number) => {
    setLogFiles((prev) => prev.filter((_, i) => i !== index));
  };

  const handleSend = async (presetText?: string) => {
    const content = (presetText ?? input)?.trim();
    if (!content || sending) return;

    const userMessage: ChatMessage = {
      role: 'user',
      content,
      timestamp: new Date()
    };

    const nextMessages = [...messages, userMessage];
    setMessages(nextMessages);
    setInput('');
    setError(null);
    setSending(true);

    try {
      // Prepare attachments and log files
      const attachmentData = attachments.map((att) => ({
        filename: att.filename,
        content: att.content,
        type: att.type
      }));

      // Call the agent chat endpoint (now uses Celery)
      const response = await helpdeskAPI.agentChat(ticketId, {
        messages: nextMessages.map((msg) => ({
          role: msg.role,
          content: msg.content
        })),
        attachments: attachmentData.length > 0 ? attachmentData : undefined,
        log_files: logFiles.length > 0 ? logFiles : undefined
      });

      if (response.data?.task_id) {
        // Start polling for task completion
        setPollingTaskId(response.data.task_id);
        
        // Add placeholder for AI response with task ID for tracking
        const placeholderMessage: ChatMessage = {
          id: response.data.user_message_id,
          role: 'assistant',
          content: 'AI is thinking...',
          ai_status: 'processing',
          ai_task_id: response.data.task_id,  // Store task ID for polling
          timestamp: new Date()
        };
        setMessages((prev) => [...prev, placeholderMessage]);
      }

      // Clear attachments and logs after sending
      setAttachments([]);
      setLogFiles([]);
    } catch (err: any) {
      console.error('Agent chat failed', err);
      setError(err.response?.data?.detail || 'Unable to contact AI assistant. Please try again.');
      
      // Add error message to chat
      const errorMessage: ChatMessage = {
        role: 'assistant',
        content: 'Sorry, I encountered an error. Please try again or rephrase your question.',
        timestamp: new Date()
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setSending(false);
    }
  };

  const handleSaveToNPA = async (messageId: string, createNew: boolean = false) => {
    try {
      await helpdeskAPI.saveChatToNPA(ticketId, messageId, undefined, createNew);
      setMessageMenuAnchor(null);
      setError(null);
      // Reload chat to update linked_to_npa_id
      await loadChatHistory();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to save to NPA');
    }
  };

  const handleMarkAsSolution = async (messageId: string) => {
    try {
      await helpdeskAPI.markChatAsSolution(ticketId, messageId);
      setMessageMenuAnchor(null);
      setError(null);
      await loadChatHistory();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to mark as solution');
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
      <Paper 
        variant="outlined" 
        sx={{ 
          p: 2, 
          mb: 2, 
          bgcolor: 'info.50',
          borderColor: 'info.main'
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
          <PsychologyIcon color="primary" />
          <Typography variant="h6">AI Agent Assistant</Typography>
        </Box>
        <Typography variant="body2" color="text.secondary">
          Ask questions about this ticket. You can attach files and paste log files for analysis. Chat history is saved automatically.
        </Typography>
      </Paper>

      {/* Attachments and Log Files Summary */}
      {(attachments.length > 0 || logFiles.length > 0) && (
        <Paper variant="outlined" sx={{ p: 1.5, mb: 2, bgcolor: 'grey.50' }}>
          <Typography variant="caption" color="text.secondary" sx={{ mb: 1, display: 'block' }}>
            Attached ({attachments.length} file{attachments.length !== 1 ? 's' : ''}, {logFiles.length} log{logFiles.length !== 1 ? 's' : ''})
          </Typography>
          <Stack direction="row" spacing={1} flexWrap="wrap" gap={1}>
            {attachments.map((att) => (
              <Chip
                key={att.id}
                icon={<AttachFileIcon />}
                label={att.filename}
                onDelete={() => handleRemoveAttachment(att.id)}
                size="small"
                color="primary"
                variant="outlined"
              />
            ))}
            {logFiles.map((_, idx) => (
              <Chip
                key={`log-${idx}`}
                icon={<DescriptionIcon />}
                label={`Log File ${idx + 1}`}
                onDelete={() => handleRemoveLogFile(idx)}
                size="small"
                color="secondary"
                variant="outlined"
              />
            ))}
          </Stack>
        </Paper>
      )}

      {/* Suggested Questions */}
      {messages.length === 0 && !loadingHistory && (
        <Box sx={{ mb: 2 }}>
          <Typography variant="subtitle2" color="text.secondary" gutterBottom>
            Suggested questions:
          </Typography>
          <Stack direction="row" spacing={1} flexWrap="wrap" gap={1}>
            {SUGGESTIONS.map((text) => (
              <Chip
                key={text}
                label={text}
                onClick={() => handleSend(text)}
                variant="outlined"
                size="small"
                sx={{ cursor: 'pointer' }}
              />
            ))}
          </Stack>
        </Box>
      )}

      {/* Chat Messages */}
      <Box
        sx={{
          flex: 1,
          overflowY: 'auto',
          display: 'flex',
          flexDirection: 'column',
          gap: 2,
          mb: 2,
          p: 1,
          bgcolor: 'grey.50',
          borderRadius: 1,
          minHeight: 300,
          maxHeight: 500
        }}
      >
        {loadingHistory && (
          <Box sx={{ display: 'flex', justifyContent: 'center', p: 3 }}>
            <CircularProgress />
          </Box>
        )}

        {!loadingHistory && messages.length === 0 && (
          <Paper variant="outlined" sx={{ p: 2, textAlign: 'center' }}>
            <Typography variant="body2" color="text.secondary">
              Start a conversation by asking a question or clicking a suggestion above.
            </Typography>
          </Paper>
        )}

        {!loadingHistory && messages.map((msg, idx) => (
          <Box
            key={msg.id || `${msg.role}-${idx}`}
            sx={{
              alignSelf: msg.role === 'assistant' ? 'flex-start' : 'flex-end',
              maxWidth: '85%',
              display: 'flex',
              flexDirection: 'column',
              gap: 0.5
            }}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, px: 1 }}>
              <Typography variant="caption" color="text.secondary">
                {msg.role === 'assistant' ? 'AI Assistant' : 'You'}
                {msg.timestamp && ` • ${new Date(msg.timestamp).toLocaleTimeString()}`}
              </Typography>
              {msg.is_solution && (
                <Chip label="Solution" size="small" color="success" icon={<CheckCircleIcon />} />
              )}
              {msg.linked_to_npa_id && (
                <Chip label="Saved to NPA" size="small" color="info" icon={<AssignmentIcon />} />
              )}
              {msg.id && msg.role === 'assistant' && (
                <IconButton
                  size="small"
                  onClick={(e) => setMessageMenuAnchor({ anchor: e.currentTarget, messageId: msg.id! })}
                >
                  <MoreVertIcon fontSize="small" />
                </IconButton>
              )}
            </Box>
            <Paper
              elevation={1}
              sx={{
                p: 2,
                bgcolor: msg.role === 'assistant' ? 'background.paper' : 'primary.main',
                color: msg.role === 'assistant' ? 'text.primary' : 'primary.contrastText',
                borderRadius: 2,
                position: 'relative'
              }}
            >
              {(msg.ai_status === 'processing' || msg.ai_status === 'pending') && (
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                  <CircularProgress size={16} />
                  <Typography variant="caption" color="text.secondary">
                    AI is thinking...
                  </Typography>
                </Box>
              )}
              <Typography 
                variant="body2" 
                sx={{ 
                  whiteSpace: 'pre-wrap',
                  color: msg.role === 'assistant' ? 'text.primary' : 'inherit'
                }}
              >
                {msg.content}
              </Typography>
            </Paper>
          </Box>
        ))}

        <div ref={messagesEndRef} />
      </Box>

      {/* Message Actions Menu */}
      <Menu
        anchorEl={messageMenuAnchor?.anchor}
        open={!!messageMenuAnchor}
        onClose={() => setMessageMenuAnchor(null)}
      >
        <MenuItem onClick={() => messageMenuAnchor && handleSaveToNPA(messageMenuAnchor.messageId, false)}>
          <ListItemIcon>
            <AssignmentIcon fontSize="small" />
          </ListItemIcon>
          Save to Current NPA
        </MenuItem>
        <MenuItem onClick={() => messageMenuAnchor && handleSaveToNPA(messageMenuAnchor.messageId, true)}>
          <ListItemIcon>
            <AddIcon fontSize="small" />
          </ListItemIcon>
          Create New NPA & Close Current
        </MenuItem>
        <MenuItem onClick={() => messageMenuAnchor && handleMarkAsSolution(messageMenuAnchor.messageId)}>
          <ListItemIcon>
            <CheckCircleIcon fontSize="small" />
          </ListItemIcon>
          Mark as Solution
        </MenuItem>
      </Menu>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Input Area */}
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <TextField
            fullWidth
            multiline
            minRows={2}
            maxRows={4}
            label="Ask the AI assistant"
            placeholder="e.g., 'What should I ask the customer?' or 'Analyze these logs...'"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyPress={handleKeyPress}
            disabled={sending}
          />
          <Stack direction="column" spacing={1}>
            <IconButton
              color="primary"
              onClick={() => setShowAttachDialog(true)}
              title="Attach file"
            >
              <AttachFileIcon />
            </IconButton>
            <IconButton
              color="secondary"
              onClick={() => setShowLogDialog(true)}
              title="Paste log file"
            >
              <DescriptionIcon />
            </IconButton>
          </Stack>
          <Button
            variant="contained"
            onClick={() => handleSend()}
            disabled={!input.trim() || sending}
            startIcon={sending ? <CircularProgress size={16} /> : <SendIcon />}
            sx={{ minWidth: 100, alignSelf: 'flex-end' }}
          >
            {sending ? 'Sending...' : 'Send'}
          </Button>
        </Box>
      </Box>

      {/* Hidden file input */}
      <input
        ref={fileInputRef}
        type="file"
        multiple
        style={{ display: 'none' }}
        onChange={handleFileSelect}
      />

      {/* Log File Dialog */}
      <Dialog open={showLogDialog} onClose={() => setShowLogDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          Paste Log File
          <IconButton
            aria-label="close"
            onClick={() => setShowLogDialog(false)}
            sx={{ position: 'absolute', right: 8, top: 8 }}
          >
            <CloseIcon />
          </IconButton>
        </DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            multiline
            minRows={10}
            maxRows={20}
            label="Paste log file content"
            placeholder="Paste your log file content here..."
            value={logInput}
            onChange={(e) => setLogInput(e.target.value)}
            sx={{ mt: 1 }}
          />
          {logFiles.length > 0 && (
            <Box sx={{ mt: 2 }}>
              <Typography variant="subtitle2" gutterBottom>
                Existing Log Files:
              </Typography>
              <List dense>
                {logFiles.map((_, idx) => (
                  <ListItem key={idx}>
                    <ListItemIcon>
                      <DescriptionIcon />
                    </ListItemIcon>
                    <ListItemText primary={`Log File ${idx + 1}`} secondary={`${logFiles[idx].length} characters`} />
                    <ListItemSecondaryAction>
                      <IconButton edge="end" onClick={() => handleRemoveLogFile(idx)} size="small">
                        <DeleteIcon />
                      </IconButton>
                    </ListItemSecondaryAction>
                  </ListItem>
                ))}
              </List>
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowLogDialog(false)}>Cancel</Button>
          <Button onClick={handleAddLogFile} variant="contained" disabled={!logInput.trim()}>
            Add Log File
          </Button>
        </DialogActions>
      </Dialog>

      {/* Attach File Dialog */}
      <Dialog open={showAttachDialog} onClose={() => setShowAttachDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          Attach Files
          <IconButton
            aria-label="close"
            onClick={() => setShowAttachDialog(false)}
            sx={{ position: 'absolute', right: 8, top: 8 }}
          >
            <CloseIcon />
          </IconButton>
        </DialogTitle>
        <DialogContent>
          <Box sx={{ mb: 2 }}>
            <Button
              variant="outlined"
              component="label"
              startIcon={<AttachFileIcon />}
              fullWidth
            >
              Select Files
              <input
                type="file"
                multiple
                hidden
                ref={fileInputRef}
                onChange={handleFileSelect}
              />
            </Button>
          </Box>
          {attachments.length > 0 && (
            <>
              <Divider sx={{ my: 2 }} />
              <Typography variant="subtitle2" gutterBottom>
                Attached Files:
              </Typography>
              <List dense>
                {attachments.map((att) => (
                  <ListItem key={att.id}>
                    <ListItemIcon>
                      <AttachFileIcon />
                    </ListItemIcon>
                    <ListItemText 
                      primary={att.filename} 
                      secondary={`${att.content.length} characters`} 
                    />
                    <ListItemSecondaryAction>
                      <IconButton edge="end" onClick={() => handleRemoveAttachment(att.id)} size="small">
                        <DeleteIcon />
                      </IconButton>
                    </ListItemSecondaryAction>
                  </ListItem>
                ))}
              </List>
            </>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowAttachDialog(false)} variant="contained">
            Done
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default TicketChatbot;
