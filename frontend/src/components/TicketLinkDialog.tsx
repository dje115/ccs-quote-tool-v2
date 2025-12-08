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
  Chip,
  Divider,
  FormControl,
  InputLabel,
  Select,
  MenuItem
} from '@mui/material';
import {
  Link as LinkIcon,
  Close as CloseIcon,
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

interface TicketLinkDialogProps {
  open: boolean;
  onClose: () => void;
  sourceTicket: Ticket;
  onLinkSuccess: () => void;
}

const LINK_TYPES = [
  { value: 'related', label: 'Related', description: 'Tickets are related to each other' },
  { value: 'duplicate', label: 'Duplicate', description: 'Tickets are duplicates of each other' },
  { value: 'blocks', label: 'Blocks', description: 'This ticket blocks the other ticket' },
  { value: 'blocked_by', label: 'Blocked By', description: 'This ticket is blocked by the other ticket' },
  { value: 'follows', label: 'Follows', description: 'This ticket follows from the other ticket' },
  { value: 'followed_by', label: 'Followed By', description: 'This ticket is followed by the other ticket' }
];

const TicketLinkDialog: React.FC<TicketLinkDialogProps> = ({
  open,
  onClose,
  sourceTicket,
  onLinkSuccess
}) => {
  const [targetTicketNumber, setTargetTicketNumber] = useState('');
  const [targetTicket, setTargetTicket] = useState<Ticket | null>(null);
  const [linkType, setLinkType] = useState('related');
  const [loading, setLoading] = useState(false);
  const [linking, setLinking] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [searchError, setSearchError] = useState<string | null>(null);

  useEffect(() => {
    if (!open) {
      // Reset state when dialog closes
      setTargetTicketNumber('');
      setTargetTicket(null);
      setLinkType('related');
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
          setSearchError('Cannot link ticket to itself');
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

  const handleLink = async () => {
    if (!targetTicket) {
      setError('Please search and select a target ticket first');
      return;
    }

    setLinking(true);
    setError(null);

    try {
      await helpdeskAPI.linkTicket(sourceTicket.id, targetTicket.id, linkType);
      onLinkSuccess();
      onClose();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to link tickets');
    } finally {
      setLinking(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
          <LinkIcon color="primary" />
          <Typography variant="h6">Link Ticket</Typography>
        </Box>
      </DialogTitle>
      <DialogContent>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}

        <Box sx={{ mb: 3 }}>
          <Typography variant="subtitle2" gutterBottom>
            Source Ticket:
          </Typography>
          <Box sx={{ p: 2, bgcolor: 'action.hover', borderRadius: 1 }}>
            <Typography variant="body1" fontWeight="medium">
              {sourceTicket.ticket_number}: {sourceTicket.subject}
            </Typography>
            <Box sx={{ display: 'flex', gap: 1, mt: 1 }}>
              <Chip label={sourceTicket.status} size="small" />
              <Chip label={sourceTicket.priority} size="small" />
            </Box>
          </Box>
        </Box>

        <Divider sx={{ my: 3 }} />

        <Box sx={{ mb: 2 }}>
          <Typography variant="subtitle2" gutterBottom>
            Target Ticket (link to):
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
            <Box sx={{ p: 2, bgcolor: 'success.light', color: 'success.contrastText', borderRadius: 1, mb: 2 }}>
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
            </Box>
          )}

          <FormControl fullWidth sx={{ mt: 2 }}>
            <InputLabel>Link Type</InputLabel>
            <Select
              value={linkType}
              label="Link Type"
              onChange={(e) => setLinkType(e.target.value)}
            >
              {LINK_TYPES.map((type) => (
                <MenuItem key={type.value} value={type.value}>
                  <Box>
                    <Typography variant="body2" fontWeight="medium">
                      {type.label}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {type.description}
                    </Typography>
                  </Box>
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose} disabled={linking}>
          Cancel
        </Button>
        <Button
          onClick={handleLink}
          variant="contained"
          color="primary"
          startIcon={<LinkIcon />}
          disabled={!targetTicket || linking}
        >
          {linking ? 'Linking...' : 'Link Tickets'}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default TicketLinkDialog;

