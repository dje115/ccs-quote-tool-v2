import React, { useState, useEffect } from 'react';
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
  LinearProgress,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Grid,
  Card,
  CardContent,
  Alert,
  CircularProgress
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Visibility as ViewIcon,
  Search as SearchIcon,
  Assessment as AssessmentIcon,
  TrendingUp as TrendingUpIcon,
  Business as BusinessIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  Phone as PhoneIcon,
  Email as EmailIcon
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';

interface Lead {
  id: string;
  company_name: string;
  contact_name: string;
  email: string;
  phone?: string;
  industry: string;
  lead_score: number;
  status: 'new' | 'contacted' | 'qualified' | 'proposal' | 'closed_won' | 'closed_lost';
  source: string;
  created_at: string;
  last_contact: string;
  ai_analysis?: any;
  notes?: string;
}

const Leads: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const [leads, setLeads] = useState<Lead[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [showLeadForm, setShowLeadForm] = useState(false);
  const [editingLead, setEditingLead] = useState<Lead | null>(null);

  useEffect(() => {
    loadLeads();
  }, []);

  const loadLeads = async () => {
    try {
      setLoading(true);
      // Mock data for now - replace with actual API call
      const mockLeads: Lead[] = [
        {
          id: '1',
          company_name: 'TechCorp Solutions',
          contact_name: 'John Smith',
          email: 'john@techcorp.com',
          phone: '+44 20 7123 4567',
          industry: 'Technology',
          lead_score: 85,
          status: 'qualified',
          source: 'Website',
          created_at: '2024-01-15',
          last_contact: '2024-01-20',
          ai_analysis: {
            urgency: 'high',
            opportunities: ['Network upgrade needed', 'New office expansion'],
            risk_factors: ['Budget constraints']
          }
        },
        {
          id: '2',
          company_name: 'Manufacturing Ltd',
          contact_name: 'Sarah Johnson',
          email: 'sarah@manufacturing.co.uk',
          phone: '+44 161 234 5678',
          industry: 'Manufacturing',
          lead_score: 72,
          status: 'contacted',
          source: 'Referral',
          created_at: '2024-01-18',
          last_contact: '2024-01-19',
          ai_analysis: {
            urgency: 'medium',
            opportunities: ['Cabling infrastructure'],
            risk_factors: []
          }
        },
        {
          id: '3',
          company_name: 'Retail Chain UK',
          contact_name: 'Mike Wilson',
          email: 'mike@retailchain.co.uk',
          industry: 'Retail',
          lead_score: 45,
          status: 'new',
          source: 'Cold Outreach',
          created_at: '2024-01-20',
          last_contact: '',
          ai_analysis: {
            urgency: 'low',
            opportunities: ['Store network connectivity'],
            risk_factors: ['Long sales cycle']
          }
        }
      ];
      setLeads(mockLeads);
    } catch (error) {
      console.error('Error loading leads:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredLeads = leads.filter(lead => {
    const matchesSearch = 
      lead.company_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      lead.contact_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      lead.email.toLowerCase().includes(searchTerm.toLowerCase());
    
    const matchesStatus = filterStatus === 'all' || lead.status === filterStatus;
    
    return matchesSearch && matchesStatus;
  });

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'new':
        return 'default';
      case 'contacted':
        return 'primary';
      case 'qualified':
        return 'success';
      case 'proposal':
        return 'warning';
      case 'closed_won':
        return 'success';
      case 'closed_lost':
        return 'error';
      default:
        return 'default';
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return '#4caf50';
    if (score >= 60) return '#ff9800';
    return '#f44336';
  };

  const getUrgencyColor = (urgency: string) => {
    switch (urgency?.toLowerCase()) {
      case 'high': return 'error';
      case 'medium': return 'warning';
      case 'low': return 'success';
      default: return 'default';
    }
  };

  const statusOptions = [
    { value: 'all', label: 'All Leads' },
    { value: 'new', label: 'New' },
    { value: 'contacted', label: 'Contacted' },
    { value: 'qualified', label: 'Qualified' },
    { value: 'proposal', label: 'Proposal' },
    { value: 'closed_won', label: 'Closed Won' },
    { value: 'closed_lost', label: 'Closed Lost' }
  ];

  const LeadStatsCard: React.FC<{ title: string; value: number; color: string; icon: React.ReactNode }> = ({
    title,
    value,
    color,
    icon
  }) => (
    <Card>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box>
            <Typography color="text.secondary" gutterBottom variant="h6">
              {title}
            </Typography>
            <Typography variant="h4" sx={{ color }}>
              {value}
            </Typography>
          </Box>
          <Box sx={{ color, opacity: 0.7 }}>
            {icon}
          </Box>
        </Box>
      </CardContent>
    </Card>
  );

  const QuickActions: React.FC<{ lead: Lead }> = ({ lead }) => (
    <Box sx={{ display: 'flex', gap: 0.5 }}>
      <Tooltip title="Call">
        <IconButton size="small" color="primary">
          <PhoneIcon />
        </IconButton>
      </Tooltip>
      <Tooltip title="Email">
        <IconButton size="small" color="primary">
          <EmailIcon />
        </IconButton>
      </Tooltip>
      <Tooltip title="View Details">
        <IconButton size="small" onClick={() => navigate(`/leads/${lead.id}`)}>
          <ViewIcon />
        </IconButton>
      </Tooltip>
      {lead.ai_analysis && (
        <Tooltip title="AI Analysis">
          <IconButton size="small" onClick={() => navigate(`/leads/${lead.id}/analysis`)}>
            <AssessmentIcon />
          </IconButton>
        </Tooltip>
      )}
    </Box>
  );

  const leadStats = {
    total: leads.length,
    new: leads.filter(l => l.status === 'new').length,
    qualified: leads.filter(l => l.status === 'qualified').length,
    highScore: leads.filter(l => l.lead_score >= 80).length
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Leads
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => setShowLeadForm(true)}
        >
          Add Lead
        </Button>
      </Box>

      {/* Stats Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <LeadStatsCard
            title="Total Leads"
            value={leadStats.total}
            color="#1976d2"
            icon={<BusinessIcon />}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <LeadStatsCard
            title="New Leads"
            value={leadStats.new}
            color="#ff9800"
            icon={<TrendingUpIcon />}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <LeadStatsCard
            title="Qualified"
            value={leadStats.qualified}
            color="#4caf50"
            icon={<CheckCircleIcon />}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <LeadStatsCard
            title="High Score"
            value={leadStats.highScore}
            color="#e91e63"
            icon={<AssessmentIcon />}
          />
        </Grid>
      </Grid>

      {/* Filters */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              placeholder="Search leads..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              InputProps={{
                startAdornment: (
                  <InputAdornment position="start">
                    <SearchIcon />
                  </InputAdornment>
                ),
              }}
            />
          </Grid>
          <Grid item xs={12} md={6}>
            <TextField
              fullWidth
              select
              label="Filter by Status"
              value={filterStatus}
              onChange={(e) => setFilterStatus(e.target.value)}
              SelectProps={{ native: true }}
            >
              {statusOptions.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </TextField>
          </Grid>
        </Grid>
      </Paper>

      {/* Leads Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Company</TableCell>
              <TableCell>Contact</TableCell>
              <TableCell>Industry</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Lead Score</TableCell>
              <TableCell>Source</TableCell>
              <TableCell>Last Contact</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={8} align="center">
                  <CircularProgress />
                </TableCell>
              </TableRow>
            ) : filteredLeads.length === 0 ? (
              <TableRow>
                <TableCell colSpan={8} align="center">
                  No leads found
                </TableCell>
              </TableRow>
            ) : (
              filteredLeads.map((lead) => (
                <TableRow key={lead.id} hover>
                  <TableCell>
                    <Box>
                      <Typography variant="subtitle2">{lead.company_name}</Typography>
                      {lead.ai_analysis && (
                        <Chip
                          label={lead.ai_analysis.urgency || 'Unknown'}
                          color={getUrgencyColor(lead.ai_analysis.urgency || '')}
                          size="small"
                          sx={{ mt: 0.5 }}
                        />
                      )}
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Box>
                      <Typography variant="subtitle2">{lead.contact_name}</Typography>
                      <Typography variant="caption" color="text.secondary">
                        {lead.email}
                      </Typography>
                      {lead.phone && (
                        <Typography variant="caption" display="block" color="text.secondary">
                          {lead.phone}
                        </Typography>
                      )}
                    </Box>
                  </TableCell>
                  <TableCell>{lead.industry}</TableCell>
                  <TableCell>
                    <Chip
                      label={lead.status.replace('_', ' ').toUpperCase()}
                      color={getStatusColor(lead.status)}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <LinearProgress
                        variant="determinate"
                        value={lead.lead_score}
                        sx={{
                          width: 60,
                          height: 8,
                          borderRadius: 4,
                          backgroundColor: '#e0e0e0',
                          '& .MuiLinearProgress-bar': {
                            backgroundColor: getScoreColor(lead.lead_score),
                            borderRadius: 4
                          }
                        }}
                      />
                      <Typography variant="body2" sx={{ minWidth: 30 }}>
                        {lead.lead_score}
                      </Typography>
                    </Box>
                  </TableCell>
                  <TableCell>{lead.source}</TableCell>
                  <TableCell>
                    {lead.last_contact ? new Date(lead.last_contact).toLocaleDateString() : 'Never'}
                  </TableCell>
                  <TableCell align="right">
                    <QuickActions lead={lead} />
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Summary */}
      <Box sx={{ mt: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="body2" color="text.secondary">
          Showing {filteredLeads.length} of {leads.length} leads
        </Typography>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Chip
            label={`Avg Score: ${Math.round(leads.reduce((sum, lead) => sum + lead.lead_score, 0) / leads.length || 0)}`}
            variant="outlined"
          />
          <Chip
            label={`High Priority: ${leads.filter(l => l.ai_analysis?.urgency === 'high').length}`}
            color="error"
            variant="outlined"
          />
        </Box>
      </Box>
    </Container>
  );
};

export default Leads;