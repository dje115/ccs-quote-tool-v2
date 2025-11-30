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
  LinearProgress,
  Tooltip,
  Card,
  CardContent,
  Grid
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Visibility as ViewIcon,
  Search as SearchIcon,
  Assessment as AssessmentIcon,
  TrendingUp as TrendingUpIcon,
  Phone as PhoneIcon,
  Email as EmailIcon,
  Schedule as ScheduleIcon,
  ArrowUpward as ArrowUpwardIcon,
  ArrowDownward as ArrowDownwardIcon,
  Flag as FlagIcon
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { customerAPI } from '../services/api';

const LeadsCRM: React.FC = () => {
  const navigate = useNavigate();
  const [leads, setLeads] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [sortBy, setSortBy] = useState<string>('company_name');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('asc');

  useEffect(() => {
    loadLeads();
  }, []);

  const loadLeads = async () => {
    try {
      setLoading(true);
      const response = await customerAPI.listLeads();
      setLeads(response.data || []);
    } catch (error) {
      console.error('Error loading CRM leads:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredLeads = leads.filter(lead =>
    lead.company_name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    (lead.website && lead.website.toLowerCase().includes(searchTerm.toLowerCase())) ||
    (lead.main_email && lead.main_email.toLowerCase().includes(searchTerm.toLowerCase()))
  );

  const handleSort = (column: string) => {
    if (sortBy === column) {
      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
    } else {
      setSortBy(column);
      setSortOrder('asc');
    }
  };

  const sortedLeads = [...filteredLeads].sort((a, b) => {
    let aVal: any;
    let bVal: any;

    switch (sortBy) {
      case 'company_name':
        aVal = a.company_name?.toLowerCase() || '';
        bVal = b.company_name?.toLowerCase() || '';
        break;
      case 'lead_score':
        aVal = a.lead_score || 0;
        bVal = b.lead_score || 0;
        break;
      case 'last_contact_date':
        aVal = a.last_contact_date ? new Date(a.last_contact_date).getTime() : 0;
        bVal = b.last_contact_date ? new Date(b.last_contact_date).getTime() : 0;
        break;
      case 'next_scheduled_contact':
        aVal = a.next_scheduled_contact ? new Date(a.next_scheduled_contact).getTime() : 0;
        bVal = b.next_scheduled_contact ? new Date(b.next_scheduled_contact).getTime() : 0;
        break;
      case 'business_sector':
        aVal = a.business_sector?.toLowerCase() || '';
        bVal = b.business_sector?.toLowerCase() || '';
        break;
      default:
        return 0;
    }

    if (aVal < bVal) return sortOrder === 'asc' ? -1 : 1;
    if (aVal > bVal) return sortOrder === 'asc' ? 1 : -1;
    return 0;
  });

  const getScoreColor = (score: number | null | undefined) => {
    if (!score) return '#9e9e9e';
    if (score >= 80) return '#4caf50';
    if (score >= 60) return '#ff9800';
    return '#f44336';
  };

  // Calculate stats
  const stats = {
    total: leads.length,
    highScore: leads.filter(l => (l.lead_score || 0) >= 80).length,
    contacted: leads.filter(l => l.last_contact_date).length,
    conversionProbability: leads.reduce((sum, l) => sum + (l.conversion_probability || 0), 0) / (leads.length || 1)
  };

  return (
    <Container maxWidth="xl" sx={{ py: 3 }}>
      {/* Header */}
      <Box sx={{ textAlign: 'center', mb: 4 }}>
        <Typography variant="h3" fontWeight="700" color="primary" gutterBottom>
          CRM Leads
        </Typography>
        <Typography variant="h6" color="text.secondary" sx={{ mb: 3 }}>
          Qualified leads ready for follow-up and conversion
        </Typography>
      </Box>

      {/* Stats Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="center">
                <Box>
                  <Typography variant="h4" fontWeight="bold">{stats.total}</Typography>
                  <Typography variant="body2" color="text.secondary">Total Leads</Typography>
                </Box>
                <TrendingUpIcon sx={{ fontSize: 40, color: 'primary.main', opacity: 0.7 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="center">
                <Box>
                  <Typography variant="h4" fontWeight="bold">{stats.highScore}</Typography>
                  <Typography variant="body2" color="text.secondary">High Score (80+)</Typography>
                </Box>
                <AssessmentIcon sx={{ fontSize: 40, color: 'success.main', opacity: 0.7 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="center">
                <Box>
                  <Typography variant="h4" fontWeight="bold">{stats.contacted}</Typography>
                  <Typography variant="body2" color="text.secondary">Contacted</Typography>
                </Box>
                <PhoneIcon sx={{ fontSize: 40, color: 'info.main', opacity: 0.7 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
        <Grid size={{ xs: 12, sm: 6, md: 3 }}>
          <Card>
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="center">
                <Box>
                  <Typography variant="h4" fontWeight="bold">
                    {Math.round(stats.conversionProbability)}%
                  </Typography>
                  <Typography variant="body2" color="text.secondary">Avg Conversion Prob</Typography>
                </Box>
                <ScheduleIcon sx={{ fontSize: 40, color: 'warning.main', opacity: 0.7 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Search */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <TextField
          fullWidth
          placeholder="Search leads by company name, website, or email..."
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
      </Paper>

      {/* Leads Table */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow sx={{ backgroundColor: '#f5f5f5' }}>
              <TableCell><strong>SLA</strong></TableCell>
              <TableCell 
                sx={{ cursor: 'pointer', userSelect: 'none' }} 
                onClick={() => handleSort('company_name')}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <strong>Company</strong>
                  {sortBy === 'company_name' && (
                    sortOrder === 'asc' ? <ArrowUpwardIcon fontSize="small" /> : <ArrowDownwardIcon fontSize="small" />
                  )}
                </Box>
              </TableCell>
              <TableCell><strong>Contact</strong></TableCell>
              <TableCell 
                sx={{ cursor: 'pointer', userSelect: 'none' }} 
                onClick={() => handleSort('lead_score')}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <strong>Lead Score</strong>
                  {sortBy === 'lead_score' && (
                    sortOrder === 'asc' ? <ArrowUpwardIcon fontSize="small" /> : <ArrowDownwardIcon fontSize="small" />
                  )}
                </Box>
              </TableCell>
              <TableCell><strong>Conversion Probability</strong></TableCell>
              <TableCell 
                sx={{ cursor: 'pointer', userSelect: 'none' }} 
                onClick={() => handleSort('last_contact_date')}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <strong>Last Contact</strong>
                  {sortBy === 'last_contact_date' && (
                    sortOrder === 'asc' ? <ArrowUpwardIcon fontSize="small" /> : <ArrowDownwardIcon fontSize="small" />
                  )}
                </Box>
              </TableCell>
              <TableCell 
                sx={{ cursor: 'pointer', userSelect: 'none' }} 
                onClick={() => handleSort('next_scheduled_contact')}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <strong>Next Action</strong>
                  {sortBy === 'next_scheduled_contact' && (
                    sortOrder === 'asc' ? <ArrowUpwardIcon fontSize="small" /> : <ArrowDownwardIcon fontSize="small" />
                  )}
                </Box>
              </TableCell>
              <TableCell align="right"><strong>Actions</strong></TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={8} align="center">
                  <LinearProgress />
                </TableCell>
              </TableRow>
            ) : filteredLeads.length === 0 ? (
              <TableRow>
                <TableCell colSpan={7} align="center" sx={{ py: 6 }}>
                  <Typography color="text.secondary">
                    {searchTerm ? 'No leads found matching your search' : 'No CRM leads found'}
                  </Typography>
                </TableCell>
              </TableRow>
            ) : (
              sortedLeads.map((lead) => {
                const hasScheduledContact = lead.next_scheduled_contact && new Date(lead.next_scheduled_contact) > new Date();
                const isUpcoming = hasScheduledContact && new Date(lead.next_scheduled_contact) <= new Date(Date.now() + 7 * 24 * 60 * 60 * 1000); // Within 7 days
                
                return (
                <TableRow 
                  key={lead.id} 
                  hover 
                  sx={{ 
                    cursor: 'pointer',
                    backgroundColor: hasScheduledContact ? (isUpcoming ? 'rgba(255, 193, 7, 0.1)' : 'rgba(76, 175, 80, 0.05)') : 'inherit'
                  }}
                  onClick={() => navigate(`/customers/${lead.id}`)}
                >
                  <TableCell>
                    <Tooltip title={
                      lead.sla_breach_status === 'critical' ? 'Critical SLA breach' :
                      lead.sla_breach_status === 'warning' ? 'SLA warning' :
                      'No SLA breaches'
                    }>
                      <FlagIcon 
                        sx={{ 
                          color: lead.sla_breach_status === 'critical' ? '#f44336' :
                                 lead.sla_breach_status === 'warning' ? '#ff9800' :
                                 '#4caf50',
                          fontSize: 20
                        }} 
                      />
                    </Tooltip>
                  </TableCell>
                  <TableCell>
                    <Typography variant="subtitle2" fontWeight="500">
                      {lead.company_name}
                    </Typography>
                    {lead.website && (
                      <Typography variant="caption" color="text.secondary" display="block">
                        {lead.website}
                      </Typography>
                    )}
                  </TableCell>
                  <TableCell>
                    {lead.main_email && (
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5, mb: 0.5 }}>
                        <EmailIcon fontSize="small" color="action" />
                        <Typography variant="body2">{lead.main_email}</Typography>
                      </Box>
                    )}
                    {lead.main_phone && (
                      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                        <PhoneIcon fontSize="small" color="action" />
                        <Typography variant="body2">{lead.main_phone}</Typography>
                      </Box>
                    )}
                    {!lead.main_email && !lead.main_phone && (
                      <Typography variant="body2" color="text.secondary">No contact info</Typography>
                    )}
                  </TableCell>
                  <TableCell>
                    <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                      <LinearProgress
                        variant="determinate"
                        value={lead.lead_score || 0}
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
                        {lead.lead_score || 'N/A'}
                      </Typography>
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={`${lead.conversion_probability || 0}%`}
                      size="small"
                      color={lead.conversion_probability && lead.conversion_probability >= 70 ? 'success' : 
                             lead.conversion_probability && lead.conversion_probability >= 40 ? 'warning' : 'default'}
                    />
                  </TableCell>
                  <TableCell>
                    {lead.last_contact_date ? (
                      <Typography variant="body2">
                        {new Date(lead.last_contact_date).toLocaleDateString()}
                      </Typography>
                    ) : (
                      <Typography variant="body2" color="text.secondary">Never</Typography>
                    )}
                  </TableCell>
                  <TableCell>
                    {lead.next_scheduled_contact ? (
                      <Box>
                        <Chip
                          label={new Date(lead.next_scheduled_contact).toLocaleDateString()}
                          size="small"
                          color={isUpcoming ? 'warning' : 'success'}
                          icon={<ScheduleIcon fontSize="small" />}
                        />
                        {isUpcoming && (
                          <Typography variant="caption" color="warning.main" sx={{ display: 'block', mt: 0.5 }}>
                            Upcoming
                          </Typography>
                        )}
                      </Box>
                    ) : (
                      <Typography variant="body2" color="text.secondary">None scheduled</Typography>
                    )}
                  </TableCell>
                  <TableCell align="right" onClick={(e) => e.stopPropagation()}>
                    <Box sx={{ display: 'flex', gap: 1, justifyContent: 'flex-end' }}>
                      <Tooltip title="View Details">
                        <IconButton
                          size="small"
                          onClick={() => navigate(`/customers/${lead.id}`)}
                        >
                          <ViewIcon />
                        </IconButton>
                      </Tooltip>
                      <Button
                        size="small"
                        variant="outlined"
                        startIcon={<TrendingUpIcon />}
                        onClick={() => navigate(`/customers/${lead.id}`)}
                      >
                        Convert to Prospect
                      </Button>
                    </Box>
                  </TableCell>
                </TableRow>
                );
              })
            )}
          </TableBody>
        </Table>
      </TableContainer>
    </Container>
  );
};

export default LeadsCRM;

