import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Typography,
  Alert,
  CircularProgress,
  Box,
  List,
  ListItem,
  ListItemText,
  Chip,
  Divider,
  Paper
} from '@mui/material';
import {
  MergeType as MergeIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon
} from '@mui/icons-material';
import { helpdeskAPI } from '../services/api';

interface Ticket {
  id: string;
  ticket_number: string;
  subject: string;
  status: string;
  priority: string;
  created_at: string;
}

interface TicketMergeDialogProps {
  open: boolean;
  onClose: () => void;
  sourceTicket: Ticket;
  onMergeSuccess: () => void;
}

const TicketMergeDialog: React.FC<TicketMergeDialogProps> = ({
  open,
  onClose,
  sourceTicket,
  onMergeSuccess
}) => {
  const [targetTicketNumber, setTargetTicketNumber] = useState('');
  const [targetTicket, setTargetTicket] = useState<Ticket | null>(null);
  const [loading, setLoading] = useState(false);
  const [merging, setMerging] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchError, setSearchError] = useState<string | null>(null);

  useEffect(() => {
    if (!open) {
      // Reset state when dialog closes
      setTargetTicketNumber('');
      setTargetTicket(null);
      setError(null);
      setSearchError(null);
    }
  }, [open]);

  const handleSearchTicket = async () => {
    if (!targetTicketNumber.trim()) {
      setSearchError('Please enter a ticket number');
      return;
    }

    setLoading(true);
    setSearchError(null);
    setTargetTicket(null);

    try {
      // Search for ticket by number
      const response = await helpdeskAPI.getTickets({ ticket_number: targetTicketNumber.trim() });
      const tickets = response.data.tickets || response.data || [];
      
      if (tickets.length === 0) {
        setSearchError('Ticket not found');
      } else if (tickets.length > 1) {
        setSearchError('Multiple tickets found. Please be more specific.');
      } else {
        const foundTicket = tickets[0];
        if (foundTicket.id === sourceTicket.id) {
          setSearchError('Cannot merge ticket into itself');
        } else {
          setTargetTicket(foundTicket);
        }
      }
    } catch (err: any) {
      setSearchError(err.response?.data?.detail || 'Failed to search for ticket');
    } finally {
      setLoading(false);
    }
  };

  const handleMerge = async () => {
    if (!targetTicket) {
      setError('Please search and select a target ticket first');
      return;
    }

    setMerging(true);
    setError(null);

    try {
      await helpdeskAPI.mergeTicket(sourceTicket.id, targetTicket.id);
      onMergeSuccess();
      onClose();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to merge tickets');
    } finally {
      setMerging(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <MergeIcon color="primary" />
          <Typography variant="h6">Merge Ticket</Typography>
        </Box>
      </DialogTitle>
      <DialogContent>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        <Alert severity="warning" sx={{ mb: 3 }}>
          <Typography variant="body2" fontWeight="medium" gutterBottom>
            What happens when you merge:
          </Typography>
          <Typography variant="body2" component="div">
            • The source ticket will be closed and marked as merged
            <br />
            • All comments, attachments, and history will be preserved
            <br />
            • Both tickets will be linked together
            <br />
            • This action cannot be undone
          </Typography>
        </Alert>

        <Box sx={{ mb: 3 }}>
          <Typography variant="subtitle2" gutterBottom>
            Source Ticket (will be merged):
          </Typography>
          <Paper variant="outlined" sx={{ p: 2, bgcolor: 'action.hover' }}>
            <Typography variant="body1" fontWeight="medium">
              {sourceTicket.ticket_number}: {sourceTicket.subject}
            </Typography>
            <Box sx={{ display: 'flex', gap: 1, mt: 1 }}>
              <Chip label={sourceTicket.status} size="small" />
              <Chip label={sourceTicket.priority} size="small" />
            </Box>
          </Paper>
        </Box>

        <Divider sx={{ my: 3 }} />

        <Box sx={{ mb: 2 }}>
          <Typography variant="subtitle2" gutterBottom>
            Target Ticket (merge into):
          </Typography>
          <Box sx={{ display: 'flex', gap: 1, mb: 2 }}>
            <TextField
              fullWidth
              label="Ticket Number"
              value={targetTicketNumber}
              onChange={(e) => setTargetTicketNumber(e.target.value)}
              placeholder="e.g., TKT-202501-00001"
              onKeyPress={(e) => {
                if (e.key === 'Enter') {
                  handleSearchTicket();
                }
              }}
              error={!!searchError}
              helperText={searchError}
            />
            <Button
              variant="outlined"
              onClick={handleSearchTicket}
              disabled={loading || !targetTicketNumber.trim()}
              sx={{ minWidth: 100 }}
            >
              {loading ? <CircularProgress size={20} /> : 'Search'}
            </Button>
          </Box>

          {targetTicket && (
            <Paper variant="outlined" sx={{ p: 2, bgcolor: 'success.light', color: 'success.contrastText' }}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                <CheckCircleIcon />
                <Typography variant="body1" fontWeight="medium">
                  Ticket Found
                </Typography>
              </Box>
              <Typography variant="body1">
                {targetTicket.ticket_number}: {targetTicket.subject}
              </Typography>
              <Box sx={{ display: 'flex', gap: 1, mt: 1 }}>
                <Chip label={targetTicket.status} size="small" sx={{ bgcolor: 'rgba(255,255,255,0.2)' }} />
                <Chip label={targetTicket.priority} size="small" sx={{ bgcolor: 'rgba(255,255,255,0.2)' }} />
              </Box>
            </Paper>
          )}
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} disabled={merging}>
          Cancel
        </Button>
        <Button
          onClick={handleMerge}
          variant="contained"
          color="warning"
          startIcon={<MergeIcon />}
          disabled={!targetTicket || merging}
        >
          {merging ? 'Merging...' : 'Merge Tickets'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default TicketMergeDialog;

