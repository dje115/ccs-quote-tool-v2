import React, { useEffect, useMemo, useState } from 'react';
import {
  Box,
  Button,
  Chip,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Stack,
  TextField,
  Typography,
  Paper
} from '@mui/material';
import PsychologyIcon from '@mui/icons-material/Psychology';
import { quoteAPI } from '../services/api';

interface ManualQuoteReviewDialogProps {
  open: boolean;
  onClose: () => void;
  quoteId: string;
}

type ChatMessage = {
  role: 'user' | 'assistant';
  content: string;
};

const SUGGESTIONS = [
  'Highlight any missing assumptions or exclusions.',
  'Check pricing consistency and unit breakdowns.',
  'Suggest upsell/alternative tier ideas.',
  'Flag possible delivery or compliance risks.'
];

const ManualQuoteReviewDialog: React.FC<ManualQuoteReviewDialogProps> = ({ open, onClose, quoteId }) => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [sending, setSending] = useState(false);
  const [initialRequested, setInitialRequested] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!open) {
      setInput('');
      setError(null);
      setMessages([]);
      setInitialRequested(false);
      return;
    }

    if (open && !initialRequested) {
      setInitialRequested(true);
      handleSend('Review the current manual quote and highlight any issues or missing details.');
    }
  }, [open, initialRequested]);

  const handleSend = async (presetText?: string) => {
    const content = (presetText ?? input)?.trim();
    if (!content || sending) return;

    const nextMessages = [...messages, { role: 'user', content }];
    setMessages(nextMessages);
    setInput('');
    setError(null);
    setSending(true);
    try {
      const response = await quoteAPI.reviewManualQuote(quoteId, {
        messages: nextMessages,
        include_line_items: true
      });
      const assistantMessage = response.data?.message;
      if (assistantMessage) {
        setMessages((prev) => [...prev, { role: 'assistant', content: assistantMessage }]);
      } else {
        setError('AI response was empty. Please try again.');
      }
    } catch (err: any) {
      console.error('Manual quote review failed', err);
      setError(err.response?.data?.detail || 'Unable to contact QuoteCheckAI.');
    } finally {
      setSending(false);
    }
  };

  const summaryText = useMemo(() => {
    if (!messages.length) {
      return 'QuoteCheckAI will analyse your manual quote, ask questions, and help improve clarity.';
    }
    return null;
  }, [messages.length]);

  return (
    <Dialog open={open} onClose={sending ? undefined : onClose} maxWidth="md" fullWidth>
      <DialogTitle sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <PsychologyIcon color="primary" />
        GPT-5 QuoteCheckAI
      </DialogTitle>
      <DialogContent dividers sx={{ minHeight: 360 }}>
        <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
          QuoteCheckAI analyses your manual quote using GPT-5 Mini Conversation. It spots unclear scope, risks, and
          improvement ideas without changing your pricing unless you ask.
        </Typography>

        {summaryText && (
          <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
            <Typography variant="body2">{summaryText}</Typography>
          </Paper>
        )}

        <Stack spacing={2} sx={{ mb: 2 }}>
          {SUGGESTIONS.map((text) => (
            <Chip
              key={text}
              label={text}
              onClick={() => handleSend(text)}
              variant="outlined"
              size="small"
              sx={{ alignSelf: 'flex-start' }}
            />
          ))}
        </Stack>

        <Box
          sx={{
            maxHeight: 320,
            overflowY: 'auto',
            display: 'flex',
            flexDirection: 'column',
            gap: 2
          }}
        >
          {messages.map((msg, idx) => (
            <Box
              key={`${msg.role}-${idx}`}
              sx={{
                alignSelf: msg.role === 'assistant' ? 'flex-start' : 'flex-end',
                backgroundColor: msg.role === 'assistant' ? 'grey.100' : 'primary.light',
                color: msg.role === 'assistant' ? 'text.primary' : 'primary.contrastText',
                px: 2,
                py: 1.5,
                borderRadius: 2,
                maxWidth: '85%'
              }}
            >
              <Typography variant="caption" fontWeight={600} display="block" gutterBottom>
                {msg.role === 'assistant' ? 'QuoteCheckAI' : 'You'}
              </Typography>
              <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                {msg.content}
              </Typography>
            </Box>
          ))}
          {sending && (
            <Box display="flex" alignItems="center" gap={1}>
              <CircularProgress size={18} />
              <Typography variant="body2">QuoteCheckAI is thinking...</Typography>
            </Box>
          )}
        </Box>

        {error && (
          <Typography variant="body2" color="error" sx={{ mt: 2 }}>
            {error}
          </Typography>
        )}

        <TextField
          fullWidth
          multiline
          minRows={2}
          label="Ask QuoteCheckAI"
          placeholder="e.g. “Check for scope gaps”"
          value={input}
          onChange={(event) => setInput(event.target.value)}
          sx={{ mt: 3 }}
        />
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} disabled={sending}>
          Close
        </Button>
        <Button
          variant="contained"
          onClick={() => handleSend()}
          disabled={!input.trim() || sending}
          startIcon={sending ? <CircularProgress size={14} /> : undefined}
        >
          Send
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default ManualQuoteReviewDialog;
