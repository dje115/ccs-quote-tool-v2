import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  TextField,
  Button,
  Alert,
  CircularProgress,
  Divider,
  List,
  ListItem,
  ListItemText,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  Refresh as RefreshIcon,
  Edit as EditIcon,
  History as HistoryIcon,
  PlayArrow as RegenerateIcon
} from '@mui/icons-material';
import { quoteAPI } from '../services/api';

interface QuotePromptManagerProps {
  quoteId: string;
}

const QuotePromptManager: React.FC<QuotePromptManagerProps> = ({ quoteId }) => {
  const [promptText, setPromptText] = useState<string>('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [history, setHistory] = useState<any[]>([]);
  const [historyDialogOpen, setHistoryDialogOpen] = useState(false);
  const [editing, setEditing] = useState(false);

  useEffect(() => {
    loadPrompt();
    loadHistory();
  }, [quoteId]);

  const loadPrompt = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await quoteAPI.getPrompt(quoteId);
      setPromptText(response.data.prompt_text || '');
    } catch (err: any) {
      console.error('Error loading prompt:', err);
      setError(err.response?.data?.detail || 'Failed to load prompt');
    } finally {
      setLoading(false);
    }
  };

  const loadHistory = async () => {
    try {
      const response = await quoteAPI.getPromptHistory(quoteId);
      setHistory(response.data.history || []);
    } catch (err: any) {
      console.error('Error loading history:', err);
    }
  };

  const handleRegenerate = async () => {
    if (!promptText.trim()) {
      setError('Prompt text cannot be empty');
      return;
    }

    try {
      setSaving(true);
      setError(null);
      setSuccess(null);
      
      const response = await quoteAPI.regenerateWithPrompt(quoteId, {
        prompt_text: promptText
      });

      setSuccess('Quote regenerated successfully! The page will refresh to show the new quote data.');
      setEditing(false);
      
      // Reload prompt and history
      await loadPrompt();
      await loadHistory();
      
      // Refresh the page after a short delay
      setTimeout(() => {
        window.location.reload();
      }, 2000);
    } catch (err: any) {
      console.error('Error regenerating quote:', err);
      setError(err.response?.data?.detail || 'Failed to regenerate quote');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      <Paper sx={{ p: 3 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6">AI Prompt</Typography>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Tooltip title="View History">
              <IconButton onClick={() => setHistoryDialogOpen(true)} size="small">
                <HistoryIcon />
              </IconButton>
            </Tooltip>
            <Tooltip title="Refresh">
              <IconButton onClick={loadPrompt} size="small">
                <RefreshIcon />
              </IconButton>
            </Tooltip>
          </Box>
        </Box>

        <Divider sx={{ mb: 3 }} />

        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        {success && (
          <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess(null)}>
            {success}
          </Alert>
        )}

        {!promptText && !editing ? (
          <Alert severity="info" sx={{ mb: 2 }}>
            No prompt text available. This quote may have been created before prompt tracking was enabled.
          </Alert>
        ) : (
          <>
            <Box sx={{ mb: 2 }}>
              <TextField
                fullWidth
                multiline
                rows={15}
                label="Prompt Text"
                value={promptText}
                onChange={(e) => setPromptText(e.target.value)}
                disabled={!editing}
                variant={editing ? 'outlined' : 'filled'}
                helperText={
                  editing
                    ? 'Modify the prompt text and click "Regenerate Quote" to create a new quote with this prompt.'
                    : 'Click "Edit" to modify the prompt text.'
                }
                sx={{
                  '& .MuiInputBase-root': {
                    fontFamily: 'monospace',
                    fontSize: '0.875rem'
                  }
                }}
              />
            </Box>

            <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
              {editing ? (
                <>
                  <Button
                    variant="outlined"
                    onClick={() => {
                      setEditing(false);
                      loadPrompt(); // Reset to original
                    }}
                    disabled={saving}
                  >
                    Cancel
                  </Button>
                  <Button
                    variant="contained"
                    startIcon={<RegenerateIcon />}
                    onClick={handleRegenerate}
                    disabled={saving || !promptText.trim()}
                  >
                    {saving ? 'Regenerating...' : 'Regenerate Quote'}
                  </Button>
                </>
              ) : (
                <Button
                  variant="contained"
                  startIcon={<EditIcon />}
                  onClick={() => setEditing(true)}
                >
                  Edit Prompt
                </Button>
              )}
            </Box>
          </>
        )}
      </Paper>

      {/* History Dialog */}
      <Dialog
        open={historyDialogOpen}
        onClose={() => setHistoryDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Typography variant="h6">Prompt History</Typography>
            <IconButton onClick={() => setHistoryDialogOpen(false)} size="small">
              ×
            </IconButton>
          </Box>
        </DialogTitle>
        <DialogContent>
          {history.length === 0 ? (
            <Alert severity="info">No prompt history available.</Alert>
          ) : (
            <List>
              {history.map((item, index) => (
                <ListItem
                  key={item.id}
                  sx={{
                    flexDirection: 'column',
                    alignItems: 'stretch',
                    border: '1px solid',
                    borderColor: 'divider',
                    borderRadius: 1,
                    mb: 2,
                    p: 2
                  }}
                >
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
                    <Typography variant="subtitle2" fontWeight="bold">
                      Version {history.length - index}
                    </Typography>
                    <Box sx={{ display: 'flex', gap: 1 }}>
                      <Chip
                        label={item.generation_successful ? 'Success' : 'Failed'}
                        color={item.generation_successful ? 'success' : 'error'}
                        size="small"
                      />
                      {item.ai_model && (
                        <Chip label={item.ai_model} size="small" variant="outlined" />
                      )}
                    </Box>
                  </Box>
                  <Typography variant="caption" color="text.secondary" sx={{ mb: 1 }}>
                    {new Date(item.created_at).toLocaleString()}
                  </Typography>
                  <Box
                    sx={{
                      bgcolor: 'grey.50',
                      p: 1,
                      borderRadius: 1,
                      maxHeight: 200,
                      overflow: 'auto',
                      fontFamily: 'monospace',
                      fontSize: '0.75rem'
                    }}
                  >
                    <Typography variant="body2" component="pre" sx={{ whiteSpace: 'pre-wrap', m: 0 }}>
                      {item.prompt_text.substring(0, 500)}
                      {item.prompt_text.length > 500 && '...'}
                    </Typography>
                  </Box>
                  {item.generation_error && (
                    <Alert severity="error" sx={{ mt: 1 }}>
                      {item.generation_error}
                    </Alert>
                  )}
                </ListItem>
              ))}
            </List>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setHistoryDialogOpen(false)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default QuotePromptManager;

