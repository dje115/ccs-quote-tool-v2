import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Alert,
  CircularProgress,
  Link,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField
} from '@mui/material';
import {
  Assignment as AssignmentIcon,
  Warning as WarningIcon,
  Refresh as RefreshIcon,
  CheckCircle as CheckCircleIcon,
  Schedule as ScheduleIcon
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { helpdeskAPI } from '../services/api';

const NPADashboard: React.FC = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [overdueNPAs, setOverdueNPAs] = useState<any[]>([]);
  const [missingNPAs, setMissingNPAs] = useState<any[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [ensuring, setEnsuring] = useState(false);
  const [ensureDialogOpen, setEnsureDialogOpen] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const [overdueResponse, missingResponse] = await Promise.all([
        helpdeskAPI.getOverdueNPAs(),
        helpdeskAPI.getTicketsWithoutNPA()
      ]);

      // API returns { tickets: [...] } or { overdue_count: X, tickets: [...] }
      setOverdueNPAs(Array.isArray(overdueResponse.data?.tickets) ? overdueResponse.data.tickets : 
                     Array.isArray(overdueResponse.data) ? overdueResponse.data : []);
      setMissingNPAs(Array.isArray(missingResponse.data?.tickets) ? missingResponse.data.tickets : 
                     Array.isArray(missingResponse.data) ? missingResponse.data : []);
    } catch (error: any) {
      console.error('Error loading NPA data:', error);
      setError(error.response?.data?.detail || 'Failed to load NPA dashboard');
    } finally {
      setLoading(false);
    }
  };

  const handleEnsureAll = async () => {
    try {
      setEnsuring(true);
      setError(null);
      await helpdeskAPI.ensureAllTicketsHaveNPA();
      setEnsureDialogOpen(false);
      await loadData();
    } catch (error: any) {
      console.error('Error ensuring NPAs:', error);
      setError(error.response?.data?.detail || 'Failed to ensure all tickets have NPAs');
    } finally {
      setEnsuring(false);
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  const totalIssues = (Array.isArray(overdueNPAs) ? overdueNPAs.length : 0) + (Array.isArray(missingNPAs) ? missingNPAs.length : 0);

  return (
    <Box>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h5" component="h1">
          Next Point of Action Dashboard
        </Typography>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={loadData}
          >
            Refresh
          </Button>
          <Button
            variant="contained"
            startIcon={<AssignmentIcon />}
            onClick={() => setEnsureDialogOpen(true)}
            disabled={ensuring}
          >
            Ensure All Tickets Have NPA
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Summary Cards */}
      <Box sx={{ display: 'flex', gap: 2, mb: 3 }}>
        <Paper sx={{ p: 2, flex: 1, borderLeft: '4px solid', borderLeftColor: 'error.main' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
            <WarningIcon color="error" />
            <Typography variant="h6">Overdue NPAs</Typography>
          </Box>
          <Typography variant="h4" color="error.main">
            {overdueNPAs.length}
          </Typography>
        </Paper>
        <Paper sx={{ p: 2, flex: 1, borderLeft: '4px solid', borderLeftColor: 'warning.main' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
            <AssignmentIcon color="warning" />
            <Typography variant="h6">Missing NPAs</Typography>
          </Box>
          <Typography variant="h4" color="warning.main">
            {missingNPAs.length}
          </Typography>
        </Paper>
        <Paper sx={{ p: 2, flex: 1, borderLeft: '4px solid', borderLeftColor: 'info.main' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
            <ScheduleIcon color="info" />
            <Typography variant="h6">Total Issues</Typography>
          </Box>
          <Typography variant="h4" color="info.main">
            {totalIssues}
          </Typography>
        </Paper>
      </Box>

      {/* Overdue NPAs */}
      {overdueNPAs.length > 0 && (
        <Paper sx={{ mb: 3 }}>
          <Box sx={{ p: 2, borderBottom: '1px solid', borderColor: 'divider' }}>
            <Typography variant="h6" color="error">
              Overdue Next Points of Action
            </Typography>
          </Box>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Ticket</TableCell>
                  <TableCell>NPA</TableCell>
                  <TableCell>Due Date</TableCell>
                  <TableCell>Days Overdue</TableCell>
                  <TableCell>Assigned To</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {overdueNPAs.map((item: any) => {
                  const dueDate = item.due_date ? new Date(item.due_date) : null;
                  const now = new Date();
                  const daysOverdue = dueDate ? Math.floor((now.getTime() - dueDate.getTime()) / (1000 * 60 * 60 * 24)) : 0;
                  
                  return (
                    <TableRow key={item.ticket_id || item.id} hover>
                      <TableCell>
                        <Link
                          component="button"
                          variant="body2"
                          onClick={() => navigate(`/helpdesk/tickets/${item.ticket_id || item.id}`)}
                          sx={{ cursor: 'pointer' }}
                        >
                          #{item.ticket_number || item.id}
                        </Link>
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2" sx={{ maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                          {item.npa || item.next_point_of_action || 'N/A'}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        {dueDate ? dueDate.toLocaleDateString() : 'N/A'}
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={`${daysOverdue} days`}
                          color="error"
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        {item.assigned_to || item.assigned_to_name || 'Unassigned'}
                      </TableCell>
                      <TableCell>
                        <Chip label={item.status || 'N/A'} size="small" />
                      </TableCell>
                      <TableCell>
                        <Button
                          size="small"
                          onClick={() => navigate(`/helpdesk/tickets/${item.ticket_id || item.id}`)}
                        >
                          View
                        </Button>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      )}

      {/* Missing NPAs */}
      {missingNPAs.length > 0 && (
        <Paper>
          <Box sx={{ p: 2, borderBottom: '1px solid', borderColor: 'divider' }}>
            <Typography variant="h6" color="warning.main">
              Tickets Without Next Point of Action
            </Typography>
          </Box>
          <TableContainer>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Ticket</TableCell>
                  <TableCell>Subject</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Priority</TableCell>
                  <TableCell>Created</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {missingNPAs.map((ticket: any) => (
                  <TableRow key={ticket.id} hover>
                    <TableCell>
                      <Link
                        component="button"
                        variant="body2"
                        onClick={() => navigate(`/helpdesk/tickets/${ticket.id}`)}
                        sx={{ cursor: 'pointer' }}
                      >
                        #{ticket.ticket_number || ticket.id}
                      </Link>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2" sx={{ maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis' }}>
                        {ticket.subject || ticket.title || 'N/A'}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip label={ticket.status || 'N/A'} size="small" />
                    </TableCell>
                    <TableCell>
                      <Chip 
                        label={ticket.priority || 'N/A'} 
                        size="small" 
                        color={ticket.priority === 'urgent' || ticket.priority === 'URGENT' ? 'error' : 'default'} 
                      />
                    </TableCell>
                    <TableCell>
                      {ticket.created_at ? new Date(ticket.created_at).toLocaleDateString() : 'N/A'}
                    </TableCell>
                    <TableCell>
                      <Button
                        size="small"
                        onClick={() => navigate(`/helpdesk/tickets/${ticket.id}`)}
                      >
                        View
                      </Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </Paper>
      )}

      {overdueNPAs.length === 0 && missingNPAs.length === 0 && (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <CheckCircleIcon color="success" sx={{ fontSize: 48, mb: 2 }} />
          <Typography variant="h6" gutterBottom>
            All Good!
          </Typography>
          <Typography variant="body2" color="text.secondary">
            No overdue or missing Next Points of Action found.
          </Typography>
        </Paper>
      )}

      {/* Ensure All Dialog */}
      <Dialog open={ensureDialogOpen} onClose={() => setEnsureDialogOpen(false)}>
        <DialogTitle>Ensure All Tickets Have NPA</DialogTitle>
        <DialogContent>
          <Typography variant="body2" sx={{ mb: 2 }}>
            This will generate Next Points of Action for all tickets that are missing them. 
            This may take a few moments.
          </Typography>
          <Alert severity="info">
            Only tickets that are open and don't already have an NPA will be processed.
          </Alert>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEnsureDialogOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={handleEnsureAll}
            disabled={ensuring}
            startIcon={ensuring ? <CircularProgress size={16} /> : <AssignmentIcon />}
          >
            {ensuring ? 'Processing...' : 'Ensure All'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default NPADashboard;

