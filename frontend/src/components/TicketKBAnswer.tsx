import React, { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  CircularProgress,
  Alert,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Chip,
  List,
  ListItem,
  ListItemText,
  Divider,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  AutoAwesome as SparkleIcon,
  Send as SendIcon,
  ContentCopy as CopyIcon,
  CheckCircle as CheckIcon,
  Article as ArticleIcon,
  Refresh as RefreshIcon
} from '@mui/icons-material';
import { helpdeskAPI } from '../services/api';

interface TicketKBAnswerProps {
  ticketId: string;
  onAnswerGenerated?: (answer: string) => void;
}

const TicketKBAnswer: React.FC<TicketKBAnswerProps> = ({
  ticketId,
  onAnswerGenerated
}) => {
  const [generating, setGenerating] = useState(false);
  const [quickResponseGenerating, setQuickResponseGenerating] = useState(false);
  const [answer, setAnswer] = useState<string | null>(null);
  const [quickResponse, setQuickResponse] = useState<string | null>(null);
  const [sources, setSources] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [answerMode, setAnswerMode] = useState<'full' | 'quick'>('full');
  const [copied, setCopied] = useState(false);

  const handleGenerateAnswer = async () => {
    setGenerating(true);
    setError(null);
    setAnswer(null);
    setSources([]);

    try {
      const response = await helpdeskAPI.generateAnswerFromKB(ticketId);
      if (response.data.success) {
        setAnswer(response.data.answer);
        setSources(response.data.sources || []);
        setAnswerMode('full');
        setDialogOpen(true);
        if (onAnswerGenerated) {
          onAnswerGenerated(response.data.answer);
        }
      } else {
        // Even if KB generation fails, try AI-only generation
        setError(response.data.error || 'Failed to generate answer from KB');
      }
    } catch (error: any) {
      console.error('Error generating answer:', error);
      setError(error.response?.data?.detail || 'Failed to generate answer from knowledge base');
    } finally {
      setGenerating(false);
    }
  };

  const handleGenerateQuickResponse = async () => {
    setQuickResponseGenerating(true);
    setError(null);
    setQuickResponse(null);

    try {
      const response = await helpdeskAPI.generateQuickResponse(ticketId);
      if (response.data.success) {
        setQuickResponse(response.data.template);
        setAnswerMode('quick');
        setDialogOpen(true);
      } else {
        setError(response.data.error || 'Failed to generate quick response');
      }
    } catch (error: any) {
      console.error('Error generating quick response:', error);
      setError(error.response?.data?.detail || 'Failed to generate quick response');
    } finally {
      setQuickResponseGenerating(false);
    }
  };

  const handleCopyAnswer = () => {
    const textToCopy = answerMode === 'full' ? answer : quickResponse;
    if (textToCopy) {
      navigator.clipboard.writeText(textToCopy);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleUseAnswer = () => {
    const textToUse = answerMode === 'full' ? answer : quickResponse;
    if (textToUse && onAnswerGenerated) {
      onAnswerGenerated(textToUse);
    }
    setDialogOpen(false);
  };

  return (
    <Box>
      <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
        <Button
          variant="contained"
          startIcon={generating ? <CircularProgress size={16} /> : <SparkleIcon />}
          onClick={handleGenerateAnswer}
          disabled={generating}
        >
          {generating ? 'Generating...' : 'Generate AI Answer'}
        </Button>
        <Button
          variant="outlined"
          startIcon={quickResponseGenerating ? <CircularProgress size={16} /> : <SendIcon />}
          onClick={handleGenerateQuickResponse}
          disabled={quickResponseGenerating}
        >
          {quickResponseGenerating ? 'Generating...' : 'Quick Response'}
        </Button>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Answer Dialog */}
      <Dialog
        open={dialogOpen}
        onClose={() => setDialogOpen(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <Box>
              <Typography variant="h6">
                {answerMode === 'full' ? 'AI-Generated Answer' : 'Quick Response Template'}
              </Typography>
              {answerMode === 'full' && sources.length === 0 && (
                <Typography variant="caption" color="text.secondary">
                  Generated using AI (no knowledge base articles available)
                </Typography>
              )}
            </Box>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Tooltip title="Copy to clipboard">
                <IconButton size="small" onClick={handleCopyAnswer}>
                  {copied ? <CheckIcon color="success" /> : <CopyIcon />}
                </IconButton>
              </Tooltip>
            </Box>
          </Box>
        </DialogTitle>
        <DialogContent>
          {answerMode === 'full' && answer && (
            <Box>
              <Paper sx={{ p: 2, mb: 2, bgcolor: 'grey.50' }}>
                <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
                  {answer}
                </Typography>
              </Paper>

              {sources.length > 0 && (
                <Box>
                  <Typography variant="subtitle2" gutterBottom>
                    Sources:
                  </Typography>
                  <List dense>
                    {sources.map((source, index) => (
                      <ListItem key={index}>
                        <ListItemIcon>
                          <ArticleIcon fontSize="small" />
                        </ListItemIcon>
                        <ListItemText
                          primary={source.title}
                          secondary={`Relevance: ${source.relevance || 'high'}`}
                        />
                      </ListItem>
                    ))}
                  </List>
                </Box>
              )}
            </Box>
          )}

          {answerMode === 'quick' && quickResponse && (
            <TextField
              fullWidth
              multiline
              rows={10}
              value={quickResponse}
              onChange={(e) => setQuickResponse(e.target.value)}
              placeholder="Quick response template - customize as needed"
              sx={{ mt: 1 }}
            />
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Close</Button>
          <Button
            variant="contained"
            startIcon={<SendIcon />}
            onClick={handleUseAnswer}
          >
            Use Answer
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default TicketKBAnswer;

