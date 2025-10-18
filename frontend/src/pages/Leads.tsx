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
  CircularProgress,
  FormControlLabel,
  Checkbox
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
  CheckBoxOutlineBlank as CheckBoxOutlineBlankIcon,
  FilterList as FilterListIcon,
  ArrowUpward as ArrowUpwardIcon,
  ArrowDownward as ArrowDownwardIcon
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
  qualification_reason?: string;
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
  const [showConverted, setShowConverted] = useState(false);
  const [sortBy, setSortBy] = useState<string>('lead_score');
  const [sortOrder, setSortOrder] = useState<string>('desc');

  useEffect(() => {
    loadLeads();
  }, []);

  useEffect(() => {
    loadLeads();
  }, [sortBy, sortOrder]);

  const loadLeads = async () => {
    try {
      setLoading(true);
      // Fetch all campaign leads (discoveries) with sorting
      const params = {
        sort_by: sortBy,
        sort_order: sortOrder
      };
      const response = await campaignAPI.listAllLeads(params);
      setLeads(response.data?.data || []);
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
    
    const matchesStatus = filterStatus === 'all' || lead.status.toUpperCase() === filterStatus.toUpperCase();
    
    // Hide converted discoveries by default (when showConverted is FALSE)
    // Only show converted when showConverted is TRUE
    const matchesConvertedFilter = showConverted ? true : lead.status.toUpperCase() !== 'CONVERTED';
    
    return matchesSearch && matchesStatus && matchesConvertedFilter;
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

  const handleSort = (column: string) => {
    if (sortBy === column) {
      // Toggle sort order if same column
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      // Set new column and default to descending
      setSortBy(column);
      setSortOrder('desc');
    }
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

  // Calculate stats from ALL leads (not filtered)
  const leadStats = {
    total: leads.length,
    new: leads.filter(l => l.status.toUpperCase() === 'NEW').length,
    qualified: leads.filter(l => l.status.toUpperCase() === 'QUALIFIED').length,
    converted: leads.filter(l => l.status.toUpperCase() === 'CONVERTED').length,
    highScore: leads.filter(l => l.lead_score >= 80).length
  };

  return (
    <Container maxWidth="xl" sx={{ py: 3, width: '100%', height: '100%' }}>
      {/* Clean Centered Header */}
      <Box sx={{ textAlign: 'center', mb: 4 }}>
        <Typography variant="h3" fontWeight="700" color="primary" gutterBottom>
          Discoveries
        </Typography>
        <Typography variant="h6" color="text.secondary" sx={{ mb: 3 }}>
          AI-Generated Lead Intelligence & Management
        </Typography>
        <Box sx={{ display: 'flex', justifyContent: 'center', gap: 2 }}>
          {selectedLeads.length > 0 && (
            <Button
              variant="contained"
              color="success"
              startIcon={<CheckCircleIcon />}
              onClick={handleBulkConvert}
              disabled={converting}
              sx={{ 
                borderRadius: 2,
                px: 3,
                py: 1.5,
                fontWeight: 600,
                textTransform: 'none'
              }}
            >
              {converting ? 'Converting...' : `Convert ${selectedLeads.length} to CRM`}
            </Button>
          )}
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => navigate('/campaigns')}
            sx={{ 
              borderRadius: 2,
              px: 3,
              py: 1.5,
              fontWeight: 600,
              textTransform: 'none'
            }}
          >
            View All Campaigns
          </Button>
        </Box>
      </Box>
      {/* Stats Cards */}
      <Grid container spacing={3} sx={{ mb: 3, justifyContent: 'center' }}>
        <Grid
          size={{
            xs: 12,
            sm: 6,
            md: 3
          }}>
          <Tooltip title="Total number of discoveries generated from all campaigns" arrow>
            <div>
              <LeadStatsCard
                title="Total Discoveries"
                value={leadStats.total}
                color="#1976d2"
                icon={<BusinessIcon />}
              />
            </div>
          </Tooltip>
        </Grid>
        <Grid
          size={{
            xs: 12,
            sm: 6,
            md: 3
          }}>
          <Tooltip title="Discoveries that are new and haven't been contacted yet" arrow>
            <div>
              <LeadStatsCard
                title="New Discoveries"
                value={leadStats.new}
                color="#ff9800"
                icon={<TrendingUpIcon />}
              />
            </div>
          </Tooltip>
        </Grid>
        <Grid
          size={{
            xs: 12,
            sm: 6,
            md: 3
          }}>
          <Tooltip title="Discoveries that have been successfully converted to CRM leads for follow-up" arrow>
            <div>
              <LeadStatsCard
                title="Converted to CRM"
                value={leadStats.converted}
                color="#4caf50"
                icon={<CheckCircleIcon />}
              />
            </div>
          </Tooltip>
        </Grid>
        <Grid
          size={{
            xs: 12,
            sm: 6,
            md: 3
          }}>
          <Tooltip title="Discoveries with a lead score of 80 or higher - these are high-quality prospects based on AI analysis" arrow>
            <div>
              <LeadStatsCard
                title="High Score (80+)"
                value={leadStats.highScore}
                color="#e91e63"
                icon={<AssessmentIcon />}
              />
            </div>
          </Tooltip>
        </Grid>
      </Grid>
      {/* Filters */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Grid container spacing={2} alignItems="center">
          <Grid
            size={{
              xs: 12,
              md: 6
            }}>
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
          <Grid
            size={{
              xs: 12,
              md: 4
            }}>
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
          <Grid
            size={{
              xs: 12,
              md: 2
            }}>
            <FormControlLabel
              control={
                <Checkbox
                  checked={showConverted}
                  onChange={(e) => setShowConverted(e.target.checked)}
                  color="primary"
                />
              }
              label="Show Converted"
            />
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
              <TableCell 
                sx={{ cursor: 'pointer', userSelect: 'none' }} 
                onClick={() => handleSort('company_name')}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  Company
                  {sortBy === 'company_name' && (
                    sortOrder === 'asc' ? <ArrowUpwardIcon fontSize="small" /> : <ArrowDownwardIcon fontSize="small" />
                  )}
                </Box>
              </TableCell>
              <TableCell>Contact</TableCell>
              <TableCell 
                sx={{ cursor: 'pointer', userSelect: 'none' }} 
                onClick={() => handleSort('postcode')}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  Location
                  {sortBy === 'postcode' && (
                    sortOrder === 'asc' ? <ArrowUpwardIcon fontSize="small" /> : <ArrowDownwardIcon fontSize="small" />
                  )}
                </Box>
              </TableCell>
              <TableCell>Status</TableCell>
              <TableCell 
                sx={{ cursor: 'pointer', userSelect: 'none' }} 
                onClick={() => handleSort('lead_score')}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  Lead Score
                  {sortBy === 'lead_score' && (
                    sortOrder === 'asc' ? <ArrowUpwardIcon fontSize="small" /> : <ArrowDownwardIcon fontSize="small" />
                  )}
                </Box>
              </TableCell>
              <TableCell>Campaign</TableCell>
              <TableCell 
                sx={{ cursor: 'pointer', userSelect: 'none' }} 
                onClick={() => handleSort('created_at')}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  Created
                  {sortBy === 'created_at' && (
                    sortOrder === 'asc' ? <ArrowUpwardIcon fontSize="small" /> : <ArrowDownwardIcon fontSize="small" />
                  )}
                </Box>
              </TableCell>
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
                        <Typography 
                          variant="caption" 
                          display="block" 
                          color="primary"
                          sx={{ 
                            cursor: 'pointer',
                            textDecoration: 'underline',
                            '&:hover': { textDecoration: 'none' }
                          }}
                          onClick={(e) => {
                            e.stopPropagation();
                            window.open(`tel:${lead.contact_phone}`, '_self');
                          }}
                        >
                          📞 {lead.contact_phone}
                        </Typography>
                      )}
                      {lead.website && (
                        <Typography 
                          variant="caption" 
                          display="block" 
                          color="primary"
                          sx={{ 
                            cursor: 'pointer',
                            textDecoration: 'underline',
                            '&:hover': { textDecoration: 'none' }
                          }}
                          onClick={(e) => {
                            e.stopPropagation();
                            const url = lead.website?.startsWith('http') ? lead.website : `https://${lead.website}`;
                            window.open(url, '_blank');
                          }}
                        >
                          🌐 {lead.website}
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
