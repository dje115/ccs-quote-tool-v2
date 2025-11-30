import React, { useEffect, useState } from 'react';
import {
  Container,
  Paper,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Button,
  Box,
  Chip,
  IconButton,
  TextField,
  InputAdornment,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Grid,
  Card,
  CardContent
} from '@mui/material';
import {
  Add as AddIcon,
  Visibility as ViewIcon,
  Search as SearchIcon,
  TrendingUp as TrendingUpIcon,
  ArrowUpward as ArrowUpwardIcon,
  ArrowDownward as ArrowDownwardIcon,
  CalendarToday as CalendarIcon
} from '@mui/icons-material';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { opportunityAPI, customerAPI } from '../services/api';

interface Opportunity {
  id: string;
  customer_id: string;
  title: string;
  description?: string;
  stage: string;
  conversion_probability: number;
  potential_deal_date?: string;
  estimated_value?: number;
  created_at: string;
  updated_at: string;
}

const Opportunities: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [opportunities, setOpportunities] = useState<Opportunity[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [stageFilter, setStageFilter] = useState<string>('all');
  const [sortBy, setSortBy] = useState<string>('created_at');
  const [sortOrder, setSortOrder] = useState<string>('desc');
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [customers, setCustomers] = useState<any[]>([]);
  const [newOpportunity, setNewOpportunity] = useState({
    customer_id: '',
    title: '',
    description: '',
    stage: 'qualified',
    conversion_probability: 20,
    estimated_value: ''
  });

  useEffect(() => {
    loadOpportunities();
    loadCustomers();
  }, [sortBy, sortOrder, stageFilter]);

  // Auto-open create dialog and set customer if customer_id is in URL (after customers are loaded)
  useEffect(() => {
    const customerId = searchParams.get('customer_id');
    if (customerId && customers.length > 0) {
      // Update customer_id in form if it's in URL
      setNewOpportunity(prev => ({ ...prev, customer_id: customerId }));
      setCreateDialogOpen(true);
    }
  }, [searchParams, customers]);

  const loadOpportunities = async () => {
    try {
      setLoading(true);
      const params: any = {
        sort_by: sortBy,
        sort_order: sortOrder
      };
      
      if (stageFilter !== 'all') {
        params.stage = stageFilter;
      }
      
      const response = await opportunityAPI.list(params);
      setOpportunities(response.data || []);
    } catch (error) {
      console.error('Error loading opportunities:', error);
      setOpportunities([]);
    } finally {
      setLoading(false);
    }
  };

  const loadCustomers = async () => {
    try {
      // Include leads in the customer list for opportunity creation
      const response = await customerAPI.list({ limit: 1000, exclude_leads: false });
      setCustomers(response.data || []);
    } catch (error) {
      console.error('Error loading customers:', error);
    }
  };

  const handleSort = (column: string) => {
    if (sortBy === column) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(column);
      setSortOrder('desc');
    }
  };

  const handleCreateOpportunity = async () => {
    try {
      await opportunityAPI.create({
        ...newOpportunity,
        estimated_value: newOpportunity.estimated_value ? parseFloat(newOpportunity.estimated_value) : null
      });
      setCreateDialogOpen(false);
      setNewOpportunity({
        customer_id: '',
        title: '',
        description: '',
        stage: 'qualified',
        conversion_probability: 20,
        estimated_value: ''
      });
      loadOpportunities();
    } catch (error) {
      console.error('Error creating opportunity:', error);
      alert('Failed to create opportunity');
    }
  };

  const getStageColor = (stage: string) => {
    const colors: Record<string, 'default' | 'primary' | 'success' | 'warning' | 'error' | 'info'> = {
      qualified: 'info',
      scoping: 'primary',
      proposal_sent: 'warning',
      negotiation: 'warning',
      verbal_yes: 'success',
      closed_won: 'success',
      closed_lost: 'error'
    };
    return colors[stage] || 'default';
  };

  const getStageLabel = (stage: string) => {
    const labels: Record<string, string> = {
      qualified: 'Qualified',
      scoping: 'Scoping',
      proposal_sent: 'Proposal Sent',
      negotiation: 'Negotiation',
      verbal_yes: 'Verbal Yes',
      closed_won: 'Closed Won',
      closed_lost: 'Closed Lost'
    };
    return labels[stage] || stage;
  };

  const filteredOpportunities = opportunities.filter(opp => {
    const matchesSearch = opp.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
                         (opp.description && opp.description.toLowerCase().includes(searchTerm.toLowerCase()));
    return matchesSearch;
  });

  // Calculate stats
  const stats = {
    total: opportunities.length,
    active: opportunities.filter(o => !['closed_won', 'closed_lost'].includes(o.stage)).length,
    totalValue: opportunities.reduce((sum, o) => sum + (o.estimated_value || 0), 0),
    avgProbability: opportunities.length > 0 
      ? Math.round(opportunities.reduce((sum, o) => sum + o.conversion_probability, 0) / opportunities.length)
      : 0
  };

  return (
    <Container maxWidth="xl" sx={{ py: 3 }}>
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h4" component="h1">
          Opportunities
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setCreateDialogOpen(true)}
        >
          New Opportunity
        </Button>
      </Box>

      {/* Stats Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                Total Opportunities
              </Typography>
              <Typography variant="h4">{stats.total}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                Active Opportunities
              </Typography>
              <Typography variant="h4" color="primary">{stats.active}</Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                Total Pipeline Value
              </Typography>
              <Typography variant="h4" color="success.main">
                £{stats.totalValue.toLocaleString()}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                Avg. Conversion Probability
              </Typography>
              <Typography variant="h4">{stats.avgProbability}%</Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Filters */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
          <TextField
            placeholder="Search opportunities..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              ),
            }}
            sx={{ flexGrow: 1, minWidth: 200 }}
          />
          <FormControl sx={{ minWidth: 200 }}>
            <InputLabel>Stage</InputLabel>
            <Select
              value={stageFilter}
              label="Stage"
              onChange={(e) => setStageFilter(e.target.value)}
            >
              <MenuItem value="all">All Stages</MenuItem>
              <MenuItem value="qualified">Qualified</MenuItem>
              <MenuItem value="scoping">Scoping</MenuItem>
              <MenuItem value="proposal_sent">Proposal Sent</MenuItem>
              <MenuItem value="negotiation">Negotiation</MenuItem>
              <MenuItem value="verbal_yes">Verbal Yes</MenuItem>
              <MenuItem value="closed_won">Closed Won</MenuItem>
              <MenuItem value="closed_lost">Closed Lost</MenuItem>
            </Select>
          </FormControl>
        </Box>
      </Paper>

      {/* Opportunities Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell 
                sx={{ cursor: 'pointer', userSelect: 'none' }} 
                onClick={() => handleSort('title')}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  Title
                  {sortBy === 'title' && (
                    sortOrder === 'asc' ? <ArrowUpwardIcon fontSize="small" /> : <ArrowDownwardIcon fontSize="small" />
                  )}
                </Box>
              </TableCell>
              <TableCell>Customer</TableCell>
              <TableCell 
                sx={{ cursor: 'pointer', userSelect: 'none' }} 
                onClick={() => handleSort('stage')}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  Stage
                  {sortBy === 'stage' && (
                    sortOrder === 'asc' ? <ArrowUpwardIcon fontSize="small" /> : <ArrowDownwardIcon fontSize="small" />
                  )}
                </Box>
              </TableCell>
              <TableCell>Probability</TableCell>
              <TableCell 
                sx={{ cursor: 'pointer', userSelect: 'none' }} 
                onClick={() => handleSort('estimated_value')}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  Value
                  {sortBy === 'estimated_value' && (
                    sortOrder === 'asc' ? <ArrowUpwardIcon fontSize="small" /> : <ArrowDownwardIcon fontSize="small" />
                  )}
                </Box>
              </TableCell>
              <TableCell>Deal Date</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={7} align="center">
                  <CircularProgress />
                </TableCell>
              </TableRow>
            ) : filteredOpportunities.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} align="center">
                  <Typography variant="body2" color="text.secondary" sx={{ py: 3 }}>
                    No opportunities found
                  </Typography>
                </TableCell>
              </TableRow>
            ) : (
              filteredOpportunities.map((opp) => (
                <TableRow key={opp.id} hover>
                  <TableCell>
                    <Typography variant="body2" fontWeight="medium">
                      {opp.title}
                    </Typography>
                    {opp.description && (
                      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>
                        {opp.description.substring(0, 50)}...
                      </Typography>
                    )}
                  </TableCell>
                  <TableCell>
                    <Button
                      size="small"
                      onClick={() => navigate(`/customers/${opp.customer_id}`)}
                    >
                      View Customer
                    </Button>
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={getStageLabel(opp.stage)}
                      color={getStageColor(opp.stage)}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <Typography variant="body2">{opp.conversion_probability}%</Typography>
                      <Box
                        sx={{
                          width: 60,
                          height: 8,
                          bgcolor: 'grey.200',
                          borderRadius: 1,
                          overflow: 'hidden'
                        }}
                      >
                        <Box
                          sx={{
                            width: `${opp.conversion_probability}%`,
                            height: '100%',
                            bgcolor: opp.conversion_probability > 70 ? 'success.main' : 
                                     opp.conversion_probability > 40 ? 'warning.main' : 'error.main'
                          }}
                        />
                      </Box>
                    </Box>
                  </TableCell>
                  <TableCell>
                    {opp.estimated_value ? (
                      <Typography variant="body2" fontWeight="medium">
                        £{opp.estimated_value.toLocaleString()}
                      </Typography>
                    ) : (
                      <Typography variant="body2" color="text.secondary">
                        Not set
                      </Typography>
                    )}
                  </TableCell>
                  <TableCell>
                    {opp.potential_deal_date ? (
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                        <CalendarIcon fontSize="small" />
                        <Typography variant="body2">
                          {new Date(opp.potential_deal_date).toLocaleDateString()}
                        </Typography>
                      </Box>
                    ) : (
                      <Typography variant="body2" color="text.secondary">
                        Not set
                      </Typography>
                    )}
                  </TableCell>
                  <TableCell align="right">
                    <IconButton
                      size="small"
                      onClick={() => navigate(`/opportunities/${opp.id}`)}
                    >
                      <ViewIcon />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Create Opportunity Dialog */}
      <Dialog open={createDialogOpen} onClose={() => setCreateDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Create New Opportunity</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2, display: 'flex', flexDirection: 'column', gap: 2 }}>
            <FormControl fullWidth sx={{ mb: 1 }}>
              <InputLabel>Customer *</InputLabel>
              <Select
                value={newOpportunity.customer_id}
                label="Customer *"
                onChange={(e) => setNewOpportunity({ ...newOpportunity, customer_id: e.target.value })}
                sx={{ 
                  minHeight: '56px',
                  '& .MuiSelect-select': {
                    padding: '16px 14px'
                  }
                }}
                MenuProps={{
                  PaperProps: {
                    style: {
                      maxHeight: 400,
                    },
                  },
                }}
              >
                <MenuItem value="" sx={{ py: 1.5 }}>
                  <em>Select a customer or lead...</em>
                </MenuItem>
                {customers.map((customer) => (
                  <MenuItem 
                    key={customer.id} 
                    value={customer.id}
                    sx={{ 
                      py: 2,
                      minHeight: '48px',
                      display: 'flex',
                      alignItems: 'center'
                    }}
                  >
                    <Box>
                      <Typography variant="body1" fontWeight="medium">
                        {customer.company_name}
                      </Typography>
                      {customer.status && (
                        <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>
                          Status: {customer.status}
                        </Typography>
                      )}
                    </Box>
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <TextField
              label="Title *"
              fullWidth
              value={newOpportunity.title}
              onChange={(e) => setNewOpportunity({ ...newOpportunity, title: e.target.value })}
            />
            <TextField
              label="Description"
              fullWidth
              multiline
              rows={3}
              value={newOpportunity.description}
              onChange={(e) => setNewOpportunity({ ...newOpportunity, description: e.target.value })}
            />
            <FormControl fullWidth>
              <InputLabel>Stage</InputLabel>
              <Select
                value={newOpportunity.stage}
                label="Stage"
                onChange={(e) => setNewOpportunity({ ...newOpportunity, stage: e.target.value })}
              >
                <MenuItem value="qualified">Qualified</MenuItem>
                <MenuItem value="scoping">Scoping</MenuItem>
                <MenuItem value="proposal_sent">Proposal Sent</MenuItem>
                <MenuItem value="negotiation">Negotiation</MenuItem>
                <MenuItem value="verbal_yes">Verbal Yes</MenuItem>
              </Select>
            </FormControl>
            <TextField
              label="Conversion Probability (%)"
              type="number"
              fullWidth
              value={newOpportunity.conversion_probability}
              onChange={(e) => setNewOpportunity({ ...newOpportunity, conversion_probability: parseInt(e.target.value) || 0 })}
              inputProps={{ min: 0, max: 100 }}
            />
            <TextField
              label="Estimated Value"
              type="number"
              fullWidth
              value={newOpportunity.estimated_value}
              onChange={(e) => setNewOpportunity({ ...newOpportunity, estimated_value: e.target.value })}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={handleCreateOpportunity}
            variant="contained"
            disabled={!newOpportunity.customer_id || !newOpportunity.title}
          >
            Create
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default Opportunities;

