import React, { useState, useEffect } from 'react';
import CrossCustomerPatternAnalysis from '../components/CrossCustomerPatternAnalysis';
import {
  Container,
  Box,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Button,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Alert,
  IconButton,
  Tooltip,
  Grid,
  Card,
  CardContent
} from '@mui/material';
import {
  Add as AddIcon,
  Refresh as RefreshIcon,
  FilterList as FilterIcon,
  Search as SearchIcon,
  Visibility as ViewIcon,
  Assessment as AssessmentIcon,
  TrendingUp as TrendingUpIcon
} from '@mui/icons-material';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { helpdeskAPI, customerAPI } from '../services/api';
import TicketComposer from '../components/TicketComposer';
import TicketBulkActions from '../components/TicketBulkActions';
import Checkbox from '@mui/material/Checkbox';

interface Ticket {
  id: string;
  ticket_number: string;
  subject: string;
  description: string;
  status: string;
  priority: string;
  category?: string;
  customer_id?: string;
  customer_name?: string;
  assigned_to_id?: string;
  assigned_to_name?: string;
  created_at: string;
  updated_at: string;
  resolved_at?: string;
  sla_response_due?: string;
  sla_resolution_due?: string;
}

const Helpdesk: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [tickets, setTickets] = useState<Ticket[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [filterPriority, setFilterPriority] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [customers, setCustomers] = useState<any[]>([]);
  const [loadingCustomers, setLoadingCustomers] = useState(false);
  const [newTicket, setNewTicket] = useState({
    subject: '',
    description: '',
    priority: 'medium',
    category: '',
    customer_id: searchParams.get('customer_id') || ''
  });
  const [stats, setStats] = useState({
    total: 0,
    open: 0,
    in_progress: 0,
    resolved: 0,
    closed: 0,
    urgent: 0,
    sla: {
      tickets_with_sla: 0,
      breached_count: 0,
      compliance_rate: 100,
      active_breach_alerts: 0
    }
  });
  const [selectedTicketIds, setSelectedTicketIds] = useState<Set<string>>(new Set());
  const [crossCustomerPatternOpen, setCrossCustomerPatternOpen] = useState(false);

  useEffect(() => {
    loadTickets();
    loadStats();
  }, [filterStatus, filterPriority]);

  useEffect(() => {
    if (createDialogOpen) {
      loadCustomers();
    }
  }, [createDialogOpen]);

  // Auto-open create dialog if customer_id is in URL (after customers are loaded)
  useEffect(() => {
    const customerId = searchParams.get('customer_id');
    if (customerId && customers.length > 0 && !createDialogOpen) {
      setNewTicket(prev => ({ ...prev, customer_id: customerId }));
      setCreateDialogOpen(true);
    }
  }, [searchParams, customers]);

  const loadCustomers = async () => {
    try {
      setLoadingCustomers(true);
      // Include leads in the customer list for ticket creation
      const response = await customerAPI.list({ limit: 1000, exclude_leads: false });
      setCustomers(response.data || []);
    } catch (err) {
      console.error('Error loading customers:', err);
    } finally {
      setLoadingCustomers(false);
    }
  };

  const loadTickets = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const params: any = {};
      if (filterStatus !== 'all') {
        params.status = filterStatus;
      }
      if (filterPriority !== 'all') {
        params.priority = filterPriority;
      }
      
      const response = await helpdeskAPI.getTickets(params);
      setTickets(response.data.tickets || response.data || []);
    } catch (err: any) {
      console.error('Error loading tickets:', err);
      setError(err.response?.data?.detail || 'Failed to load tickets');
    } finally {
      setLoading(false);
    }
  };

  const loadStats = async () => {
    try {
      const response = await helpdeskAPI.getTicketStats();
      setStats(response.data);
    } catch (err) {
      console.error('Error loading stats:', err);
    }
  };

  const handleCreateTicket = async () => {
    try {
      setError(null);
      await helpdeskAPI.createTicket({
        subject: newTicket.subject,
        description: newTicket.description,
        priority: newTicket.priority,
        category: newTicket.category || undefined,
        customer_id: newTicket.customer_id || undefined
      });
      
      setCreateDialogOpen(false);
      setNewTicket({ subject: '', description: '', priority: 'medium', category: '', customer_id: '' });
      loadTickets();
      loadStats();
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Failed to create ticket');
    }
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'open':
        return 'error';
      case 'in_progress':
        return 'warning';
      case 'resolved':
        return 'success';
      case 'closed':
        return 'default';
      default:
        return 'default';
    }
  };

  const getPriorityColor = (priority: string) => {
    switch (priority.toLowerCase()) {
      case 'urgent':
        return 'error';
      case 'high':
        return 'warning';
      case 'medium':
        return 'info';
      case 'low':
        return 'default';
      default:
        return 'default';
    }
  };

  const handleSelectTicket = (ticketId: string) => {
    setSelectedTicketIds(prev => {
      const newSet = new Set(prev);
      if (newSet.has(ticketId)) {
        newSet.delete(ticketId);
      } else {
        newSet.add(ticketId);
      }
      return newSet;
    });
  };

  const handleSelectAll = () => {
    if (selectedTicketIds.size === tickets.length) {
      setSelectedTicketIds(new Set());
    } else {
      setSelectedTicketIds(new Set(tickets.map(t => t.id)));
    }
  };

  const handleBulkActionSuccess = () => {
    setSelectedTicketIds(new Set());
    loadTickets();
    loadStats();
  };

  const handleBulkActionError = (error: string) => {
    setError(error);
  };

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Helpdesk & Customer Service
        </Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="outlined"
            startIcon={<TrendingUpIcon />}
            onClick={() => setCrossCustomerPatternOpen(true)}
          >
            Cross-Customer Patterns
          </Button>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => setCreateDialogOpen(true)}
          >
            New Ticket
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Stats Cards */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid size={{ xs: 12, sm: 6, md: 2.4 }}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Tickets
              </Typography>
              <Typography variant="h4">{stats.total}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 2.4 }}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Open
              </Typography>
              <Typography variant="h4" color="error">{stats.open}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 2.4 }}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                In Progress
              </Typography>
              <Typography variant="h4" color="warning.main">{stats.in_progress}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 2.4 }}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Resolved
              </Typography>
              <Typography variant="h4" color="success.main">{stats.resolved}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 2.4 }}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Closed
              </Typography>
              <Typography variant="h4">{stats.closed}</Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* SLA Metrics Cards */}
      {stats.sla && stats.sla.tickets_with_sla > 0 && (
        <Grid container spacing={2} sx={{ mb: 3 }}>
          <Grid size={{ xs: 12 }}>
            <Typography variant="h6" sx={{ mb: 1, display: 'flex', alignItems: 'center', gap: 1 }}>
              <AssessmentIcon color="primary" />
              SLA Metrics
            </Typography>
          </Grid>
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <Card sx={{ 
              background: stats.sla.compliance_rate >= 95 ? 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)' :
                          stats.sla.compliance_rate >= 80 ? 'linear-gradient(135deg, #ffc107 0%, #ff9800 100%)' :
                          'linear-gradient(135deg, #f44336 0%, #d32f2f 100%)',
              color: 'white'
            }}>
              <CardContent>
                <Typography variant="body2" sx={{ opacity: 0.9 }} gutterBottom>
                  SLA Compliance Rate
                </Typography>
                <Typography variant="h4" fontWeight="bold">{stats.sla.compliance_rate}%</Typography>
                <Typography variant="caption" sx={{ opacity: 0.8 }}>
                  {stats.sla.tickets_with_sla} tickets tracked
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <Card sx={{ 
              background: stats.sla.active_breach_alerts > 0 ? 'linear-gradient(135deg, #f44336 0%, #d32f2f 100%)' :
                          'linear-gradient(135deg, #2196f3 0%, #1976d2 100%)',
              color: 'white'
            }}>
              <CardContent>
                <Typography variant="body2" sx={{ opacity: 0.9 }} gutterBottom>
                  Active Breach Alerts
                </Typography>
                <Typography variant="h4" fontWeight="bold">{stats.sla.active_breach_alerts}</Typography>
                <Typography variant="caption" sx={{ opacity: 0.8 }}>
                  Unacknowledged breaches
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  Tickets with SLA
                </Typography>
                <Typography variant="h4">{stats.sla.tickets_with_sla}</Typography>
                <Typography variant="caption" color="textSecondary">
                  {stats.sla.tickets_with_sla > 0 ? 
                    `${Math.round((stats.sla.tickets_with_sla / stats.total) * 100)}% of total` : 
                    'No SLA policies applied'}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid size={{ xs: 12, sm: 6, md: 3 }}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  Breached Tickets
                </Typography>
                <Typography variant="h4" color={stats.sla.breached_count > 0 ? 'error' : 'success'}>
                  {stats.sla.breached_count}
                </Typography>
                <Typography variant="caption" color="textSecondary">
                  {stats.sla.tickets_with_sla > 0 ? 
                    `${Math.round((stats.sla.breached_count / stats.sla.tickets_with_sla) * 100)}% breach rate` : 
                    'N/A'}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Filters */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid size={{ xs: 12, md: 4 }}>
            <TextField
              fullWidth
              placeholder="Search tickets..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              InputProps={{
                startAdornment: <SearchIcon sx={{ mr: 1, color: 'text.secondary' }} />
              }}
            />
          </Grid>
          <Grid size={{ xs: 12, sm: 6, md: 2 }}>
            <FormControl fullWidth>
              <InputLabel>Status</InputLabel>
              <Select
                value={filterStatus}
                label="Status"
                onChange={(e) => setFilterStatus(e.target.value)}
              >
                <MenuItem value="all">All</MenuItem>
                <MenuItem value="open">Open</MenuItem>
                <MenuItem value="in_progress">In Progress</MenuItem>
                <MenuItem value="resolved">Resolved</MenuItem>
                <MenuItem value="closed">Closed</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid size={{ xs: 12, sm: 6, md: 2 }}>
            <FormControl fullWidth>
              <InputLabel>Priority</InputLabel>
              <Select
                value={filterPriority}
                label="Priority"
                onChange={(e) => setFilterPriority(e.target.value)}
              >
                <MenuItem value="all">All</MenuItem>
                <MenuItem value="urgent">Urgent</MenuItem>
                <MenuItem value="high">High</MenuItem>
                <MenuItem value="medium">Medium</MenuItem>
                <MenuItem value="low">Low</MenuItem>
              </Select>
            </FormControl>
          </Grid>
          <Grid size={{ xs: 12, md: 4 }}>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Button
                variant="outlined"
                startIcon={<RefreshIcon />}
                onClick={loadTickets}
              >
                Refresh
              </Button>
            </Box>
          </Grid>
        </Grid>
      </Paper>

      {/* Bulk Actions Toolbar */}
      <TicketBulkActions
        selectedTicketIds={Array.from(selectedTicketIds)}
        onSuccess={handleBulkActionSuccess}
        onError={handleBulkActionError}
      />

      {/* Tickets Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell padding="checkbox">
                <Checkbox
                  indeterminate={selectedTicketIds.size > 0 && selectedTicketIds.size < tickets.length}
                  checked={tickets.length > 0 && selectedTicketIds.size === tickets.length}
                  onChange={handleSelectAll}
                />
              </TableCell>
              <TableCell>Ticket #</TableCell>
              <TableCell>Subject</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Priority</TableCell>
              <TableCell>Customer</TableCell>
              <TableCell>Assigned To</TableCell>
              <TableCell>Created</TableCell>
              <TableCell>Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={9} align="center">
                  Loading tickets...
                </TableCell>
              </TableRow>
            ) : tickets.length === 0 ? (
              <TableRow>
                <TableCell colSpan={9} align="center">
                  No tickets found
                </TableCell>
              </TableRow>
            ) : (
              tickets.map((ticket) => (
                <TableRow key={ticket.id} hover>
                  <TableCell padding="checkbox">
                    <Checkbox
                      checked={selectedTicketIds.has(ticket.id)}
                      onChange={() => handleSelectTicket(ticket.id)}
                    />
                  </TableCell>
                  <TableCell>{ticket.ticket_number}</TableCell>
                  <TableCell>{ticket.subject}</TableCell>
                  <TableCell>
                    <Chip
                      label={ticket.status}
                      color={getStatusColor(ticket.status) as any}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={ticket.priority}
                      color={getPriorityColor(ticket.priority) as any}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>{ticket.customer_name || 'N/A'}</TableCell>
                  <TableCell>{ticket.assigned_to_name || 'Unassigned'}</TableCell>
                  <TableCell>
                    {new Date(ticket.created_at).toLocaleDateString()}
                  </TableCell>
                  <TableCell>
                    <Tooltip title="View Ticket">
                      <IconButton
                        size="small"
                        onClick={() => navigate(`/helpdesk/${ticket.id}`)}
                      >
                        <ViewIcon />
                      </IconButton>
                    </Tooltip>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* AI-Powered Ticket Composer */}
      <TicketComposer
        open={createDialogOpen}
        onClose={() => {
          setCreateDialogOpen(false);
          setNewTicket({ subject: '', description: '', priority: 'medium', category: '', customer_id: '' });
        }}
        onSave={(ticket) => {
          loadTickets();
          loadStats();
          setCreateDialogOpen(false);
        }}
      />

      {/* Cross-Customer Pattern Analysis Dialog */}
      <CrossCustomerPatternAnalysis
        open={crossCustomerPatternOpen}
        onClose={() => setCrossCustomerPatternOpen(false)}
      />
    </Container>
  );
};

export default Helpdesk;

