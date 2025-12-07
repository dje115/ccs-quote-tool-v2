import React, { useState } from 'react';
import {
  Box,
  Paper,
  Button,
  ButtonGroup,
  Menu,
  MenuItem,
  Typography,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  TextField,
  Chip,
  Stack,
  Alert
} from '@mui/material';
import {
  Assignment as AssignIcon,
  CheckCircle as StatusIcon,
  Flag as PriorityIcon,
  Label as TagIcon,
  Close as CloseIcon,
  CheckCircle as ResolveIcon,
  Delete as DeleteIcon
} from '@mui/icons-material';
import { helpdeskAPI, userAPI } from '../services/api';

interface TicketBulkActionsProps {
  selectedTicketIds: string[];
  onSuccess: () => void;
  onError: (error: string) => void;
}

const TicketBulkActions: React.FC<TicketBulkActionsProps> = ({
  selectedTicketIds,
  onSuccess,
  onError
}) => {
  const [assignMenuAnchor, setAssignMenuAnchor] = useState<HTMLElement | null>(null);
  const [statusMenuAnchor, setStatusMenuAnchor] = useState<HTMLElement | null>(null);
  const [priorityMenuAnchor, setPriorityMenuAnchor] = useState<HTMLElement | null>(null);
  const [tagDialogOpen, setTagDialogOpen] = useState(false);
  const [closeDialogOpen, setCloseDialogOpen] = useState(false);
  const [users, setUsers] = useState<any[]>([]);
  const [loadingUsers, setLoadingUsers] = useState(false);
  const [selectedUserId, setSelectedUserId] = useState('');
  const [selectedStatus, setSelectedStatus] = useState('');
  const [selectedPriority, setSelectedPriority] = useState('');
  const [tagsInput, setTagsInput] = useState('');
  const [closeStatus, setCloseStatus] = useState<'closed' | 'resolved'>('closed');
  const [processing, setProcessing] = useState(false);

  const handleAssignClick = async (event: React.MouseEvent<HTMLElement>) => {
    setAssignMenuAnchor(event.currentTarget);
    if (users.length === 0) {
      await loadUsers();
    }
  };

  const loadUsers = async () => {
    try {
      setLoadingUsers(true);
      const response = await userAPI.list();
      setUsers(response.data || []);
    } catch (err: any) {
      onError('Failed to load users');
    } finally {
      setLoadingUsers(false);
    }
  };

  const handleBulkAssign = async (userId: string) => {
    setAssignMenuAnchor(null);
    setProcessing(true);
    try {
      await helpdeskAPI.bulkAssignTickets(selectedTicketIds, userId);
      onSuccess();
    } catch (err: any) {
      onError(err.response?.data?.detail || 'Failed to assign tickets');
    } finally {
      setProcessing(false);
    }
  };

  const handleBulkUpdateStatus = async (status: string) => {
    setStatusMenuAnchor(null);
    setProcessing(true);
    try {
      await helpdeskAPI.bulkUpdateTickets({
        ticket_ids: selectedTicketIds,
        action: 'update_status',
        status
      });
      onSuccess();
    } catch (err: any) {
      onError(err.response?.data?.detail || 'Failed to update status');
    } finally {
      setProcessing(false);
    }
  };

  const handleBulkUpdatePriority = async (priority: string) => {
    setPriorityMenuAnchor(null);
    setProcessing(true);
    try {
      await helpdeskAPI.bulkUpdateTickets({
        ticket_ids: selectedTicketIds,
        action: 'update_priority',
        priority
      });
      onSuccess();
    } catch (err: any) {
      onError(err.response?.data?.detail || 'Failed to update priority');
    } finally {
      setProcessing(false);
    }
  };

  const handleBulkUpdateTags = async () => {
    setProcessing(true);
    try {
      const tags = tagsInput.split(',').map(t => t.trim()).filter(Boolean);
      await helpdeskAPI.bulkUpdateTickets({
        ticket_ids: selectedTicketIds,
        action: 'update_tags',
        tags
      });
      setTagDialogOpen(false);
      setTagsInput('');
      onSuccess();
    } catch (err: any) {
      onError(err.response?.data?.detail || 'Failed to update tags');
    } finally {
      setProcessing(false);
    }
  };

  const handleBulkClose = async () => {
    setProcessing(true);
    try {
      await helpdeskAPI.bulkCloseTickets(selectedTicketIds, closeStatus);
      setCloseDialogOpen(false);
      onSuccess();
    } catch (err: any) {
      onError(err.response?.data?.detail || 'Failed to close tickets');
    } finally {
      setProcessing(false);
    }
  };

  if (selectedTicketIds.length === 0) {
    return null;
  }

  return (
    <>
      <Paper
        sx={{
          p: 2,
          mb: 2,
          bgcolor: 'primary.light',
          color: 'primary.contrastText',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}
      >
        <Typography variant="body1" fontWeight="medium">
          {selectedTicketIds.length} ticket(s) selected
        </Typography>
        <ButtonGroup variant="contained" color="inherit" disabled={processing}>
          <Button
            startIcon={<AssignIcon />}
            onClick={handleAssignClick}
          >
            Assign
          </Button>
          <Button
            startIcon={<StatusIcon />}
            onClick={(e) => setStatusMenuAnchor(e.currentTarget)}
          >
            Status
          </Button>
          <Button
            startIcon={<PriorityIcon />}
            onClick={(e) => setPriorityMenuAnchor(e.currentTarget)}
          >
            Priority
          </Button>
          <Button
            startIcon={<TagIcon />}
            onClick={() => setTagDialogOpen(true)}
          >
            Tags
          </Button>
          <Button
            startIcon={<ResolveIcon />}
            onClick={() => setCloseDialogOpen(true)}
          >
            Close/Resolve
          </Button>
        </ButtonGroup>
      </Paper>

      {/* Assign Menu */}
      <Menu
        anchorEl={assignMenuAnchor}
        open={Boolean(assignMenuAnchor)}
        onClose={() => setAssignMenuAnchor(null)}
      >
        {loadingUsers ? (
          <MenuItem disabled>Loading users...</MenuItem>
        ) : users.length === 0 ? (
          <MenuItem disabled>No users available</MenuItem>
        ) : (
          users.map((user) => (
            <MenuItem
              key={user.id}
              onClick={() => handleBulkAssign(user.id)}
            >
              {user.name || user.email}
            </MenuItem>
          ))
        )}
      </Menu>

      {/* Status Menu */}
      <Menu
        anchorEl={statusMenuAnchor}
        open={Boolean(statusMenuAnchor)}
        onClose={() => setStatusMenuAnchor(null)}
      >
        <MenuItem onClick={() => handleBulkUpdateStatus('open')}>Open</MenuItem>
        <MenuItem onClick={() => handleBulkUpdateStatus('in_progress')}>In Progress</MenuItem>
        <MenuItem onClick={() => handleBulkUpdateStatus('waiting_customer')}>Waiting for Customer</MenuItem>
        <MenuItem onClick={() => handleBulkUpdateStatus('resolved')}>Resolved</MenuItem>
        <MenuItem onClick={() => handleBulkUpdateStatus('closed')}>Closed</MenuItem>
      </Menu>

      {/* Priority Menu */}
      <Menu
        anchorEl={priorityMenuAnchor}
        open={Boolean(priorityMenuAnchor)}
        onClose={() => setPriorityMenuAnchor(null)}
      >
        <MenuItem onClick={() => handleBulkUpdatePriority('urgent')}>Urgent</MenuItem>
        <MenuItem onClick={() => handleBulkUpdatePriority('high')}>High</MenuItem>
        <MenuItem onClick={() => handleBulkUpdatePriority('medium')}>Medium</MenuItem>
        <MenuItem onClick={() => handleBulkUpdatePriority('low')}>Low</MenuItem>
      </Menu>

      {/* Tags Dialog */}
      <Dialog open={tagDialogOpen} onClose={() => setTagDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Update Tags</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Tags (comma-separated)"
            value={tagsInput}
            onChange={(e) => setTagsInput(e.target.value)}
            placeholder="tag1, tag2, tag3"
            sx={{ mt: 1 }}
            helperText="Enter tags separated by commas. This will replace all existing tags."
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setTagDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleBulkUpdateTags}
            variant="contained"
            disabled={!tagsInput.trim() || processing}
          >
            Update Tags
          </Button>
        </DialogActions>
      </Dialog>

      {/* Close/Resolve Dialog */}
      <Dialog open={closeDialogOpen} onClose={() => setCloseDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Close/Resolve Tickets</DialogTitle>
        <DialogContent>
          <FormControl fullWidth sx={{ mt: 2 }}>
            <InputLabel>Action</InputLabel>
            <Select
              value={closeStatus}
              label="Action"
              onChange={(e) => setCloseStatus(e.target.value as 'closed' | 'resolved')}
            >
              <MenuItem value="resolved">Resolve</MenuItem>
              <MenuItem value="closed">Close</MenuItem>
            </Select>
          </FormControl>
          <Alert severity="warning" sx={{ mt: 2 }}>
            This will {closeStatus === 'closed' ? 'close' : 'resolve'} {selectedTicketIds.length} ticket(s).
          </Alert>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCloseDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleBulkClose}
            variant="contained"
            color={closeStatus === 'closed' ? 'error' : 'success'}
            disabled={processing}
          >
            {closeStatus === 'closed' ? 'Close' : 'Resolve'} Tickets
          </Button>
        </DialogActions>
      </Dialog>
    </>
  );
};

export default TicketBulkActions;

