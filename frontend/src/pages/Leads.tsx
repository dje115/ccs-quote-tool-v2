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
  Email as EmailIcon,
  CheckBox as CheckBoxIcon,
  CheckBoxOutlineBlank as CheckBoxOutlineBlankIcon
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { campaignAPI } from '../services/api';

interface Lead {
  id: string;
  company_name: string;
  contact_name?: string;
  contact_email?: string;
  contact_phone?: string;
  website?: string;
  address?: string;
  postcode: string;
  business_sector?: string;
  company_size?: string;
  lead_score: number;
  status: string;
  source: string;
  campaign_id: string;
  campaign_name?: string;
  description?: string;
  project_value?: string;
  timeline?: string;
  created_at: string;
  external_data?: any;
  ai_analysis?: any;
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
  const [selectedLeads, setSelectedLeads] = useState<string[]>([]);
  const [converting, setConverting] = useState(false);

  useEffect(() => {
    loadLeads();
  }, []);

  const loadLeads = async () => {
    try {
      setLoading(true);
      // Fetch all campaign leads (discoveries)
      const response = await campaignAPI.listAllLeads();
      setLeads(response.data || []);
    } catch (error) {
      console.error('Error loading discoveries:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredLeads = leads.filter(lead => {
    const matchesSearch = 
      lead.company_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      (lead.contact_name && lead.contact_name.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (lead.contact_email && lead.contact_email.toLowerCase().includes(searchTerm.toLowerCase())) ||
      (lead.postcode && lead.postcode.toLowerCase().includes(searchTerm.toLowerCase()));
    
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
    { value: 'all', label: 'All Discoveries' },
    { value: 'new', label: 'New' },
    { value: 'contacted', label: 'Contacted' },
    { value: 'qualified', label: 'Qualified' },
    { value: 'converted', label: 'Converted' },
    { value: 'rejected', label: 'Rejected' },
    { value: 'duplicate', label: 'Duplicate' }
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

  const handleConvertToLead = async (leadId: string, event: React.MouseEvent) => {
    event.stopPropagation();
    if (!window.confirm('Convert this discovery to a CRM lead?')) return;
    
    try {
      await campaignAPI.convertLead(leadId);
      alert('Discovery converted to CRM lead successfully!');
      loadLeads(); // Refresh list
    } catch (error) {
      console.error('Error converting discovery:', error);
      alert('Failed to convert discovery');
    }
  };

  const handleSelectAll = () => {
    if (selectedLeads.length === filteredLeads.length) {
      setSelectedLeads([]);
    } else {
      setSelectedLeads(filteredLeads.map(lead => lead.id));
    }
  };

  const handleSelectLead = (leadId: string, event: React.MouseEvent) => {
    event.stopPropagation();
    setSelectedLeads(prev => {
      if (prev.includes(leadId)) {
        return prev.filter(id => id !== leadId);
      } else {
        return [...prev, leadId];
      }
    });
  };

  const handleBulkConvert = async () => {
    if (selectedLeads.length === 0) {
      alert('Please select discoveries to convert');
      return;
    }

    if (!window.confirm(`Convert ${selectedLeads.length} ${selectedLeads.length === 1 ? 'discovery' : 'discoveries'} to CRM leads?`)) {
      return;
    }

    setConverting(true);
    let successCount = 0;
    let failCount = 0;

    for (const leadId of selectedLeads) {
      try {
        await campaignAPI.convertLead(leadId);
        successCount++;
      } catch (error) {
        console.error(`Error converting discovery ${leadId}:`, error);
        failCount++;
      }
    }

    setConverting(false);
    setSelectedLeads([]);
    loadLeads();

    if (failCount === 0) {
      alert(`Successfully converted ${successCount} ${successCount === 1 ? 'discovery' : 'discoveries'} to CRM leads!`);
    } else {
      alert(`Converted ${successCount} discoveries. ${failCount} failed.`);
    }
  };

  const QuickActions: React.FC<{ lead: Lead }> = ({ lead }) => (
    <Box sx={{ display: 'flex', gap: 0.5 }}>
      <Tooltip title="View Details">
        <IconButton size="small" onClick={() => navigate(`/leads/${lead.id}`)}>
          <ViewIcon />
        </IconButton>
      </Tooltip>
      <Tooltip title="Convert to CRM Lead">
        <IconButton 
          size="small" 
          color="success"
          onClick={(e) => handleConvertToLead(lead.id, e)}
        >
          <CheckCircleIcon />
        </IconButton>
      </Tooltip>
      {lead.ai_analysis && (
        <Tooltip title="AI Analysis">
          <IconButton size="small">
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
          Discoveries
        </Typography>
        <Box sx={{ display: 'flex', gap: 2 }}>
          {selectedLeads.length > 0 && (
            <Button
              variant="contained"
              color="success"
              startIcon={<CheckCircleIcon />}
              onClick={handleBulkConvert}
              disabled={converting}
            >
              {converting ? 'Converting...' : `Convert ${selectedLeads.length} to CRM`}
            </Button>
          )}
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => navigate('/campaigns')}
          >
            View All Campaigns
          </Button>
        </Box>
      </Box>

      {/* Stats Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <LeadStatsCard
            title="Total Discoveries"
            value={leadStats.total}
            color="#1976d2"
            icon={<BusinessIcon />}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <LeadStatsCard
            title="New Discoveries"
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
              placeholder="Search discoveries..."
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

      {/* Discoveries Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell padding="checkbox">
                <IconButton size="small" onClick={handleSelectAll}>
                  {selectedLeads.length === filteredLeads.length && filteredLeads.length > 0 ? 
                    <CheckBoxIcon /> : <CheckBoxOutlineBlankIcon />
                  }
                </IconButton>
              </TableCell>
              <TableCell>Company</TableCell>
              <TableCell>Contact</TableCell>
              <TableCell>Location</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Lead Score</TableCell>
              <TableCell>Campaign</TableCell>
              <TableCell>Created</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={9} align="center">
                  <CircularProgress />
                </TableCell>
              </TableRow>
            ) : filteredLeads.length === 0 ? (
              <TableRow>
                <TableCell colSpan={9} align="center">
                  No discoveries found
                </TableCell>
              </TableRow>
            ) : (
              filteredLeads.map((lead) => (
                <TableRow 
                  key={lead.id} 
                  hover 
                  sx={{ 
                    cursor: 'pointer',
                    backgroundColor: selectedLeads.includes(lead.id) ? 'action.selected' : 'inherit'
                  }}
                  onClick={() => navigate(`/leads/${lead.id}`)}
                >
                  <TableCell padding="checkbox" onClick={(e) => e.stopPropagation()}>
                    <IconButton 
                      size="small" 
                      onClick={(e) => handleSelectLead(lead.id, e)}
                    >
                      {selectedLeads.includes(lead.id) ? 
                        <CheckBoxIcon color="primary" /> : <CheckBoxOutlineBlankIcon />
                      }
                    </IconButton>
                  </TableCell>
                  <TableCell>
                    <Box>
                      <Typography variant="subtitle2">{lead.company_name}</Typography>
                      {lead.business_sector && (
                        <Typography variant="caption" color="text.secondary">
                          {lead.business_sector}
                        </Typography>
                      )}
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Box>
                      {lead.contact_name && (
                        <Typography variant="subtitle2">{lead.contact_name}</Typography>
                      )}
                      {lead.contact_email && (
                        <Typography variant="caption" color="text.secondary" display="block">
                          {lead.contact_email}
                        </Typography>
                      )}
                      {lead.contact_phone && (
                        <Typography variant="caption" display="block" color="text.secondary">
                          {lead.contact_phone}
                        </Typography>
                      )}
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">{lead.postcode}</Typography>
                    {lead.company_size && (
                      <Typography variant="caption" color="text.secondary" display="block">
                        {lead.company_size}
                      </Typography>
                    )}
                  </TableCell>
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
                  <TableCell>
                    <Typography variant="body2">{lead.campaign_name || 'N/A'}</Typography>
                    <Typography variant="caption" color="text.secondary">
                      {lead.source}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    {new Date(lead.created_at).toLocaleDateString()}
                  </TableCell>
                  <TableCell align="right" onClick={(e) => e.stopPropagation()}>
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
          Showing {filteredLeads.length} of {leads.length} discoveries
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