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
  LinearProgress,
  Grid,
  Card,
  CardContent,
  Tooltip,
  Alert,
  Tabs,
  Tab
} from '@mui/material';
import {
  Add as AddIcon,
  Visibility as ViewIcon,
  Stop as StopIcon,
  Delete as DeleteIcon,
  Refresh as RefreshIcon,
  Campaign as CampaignIcon,
  Business as BusinessIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  People as PeopleIcon,
  Star as StarIcon
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { campaignAPI } from '../services/api';

interface Campaign {
  id: string;
  name: string;
  description?: string;
  prompt_type: string;
  postcode: string;
  distance_miles: number;
  max_results: number;
  status: string;
  total_found: number;
  leads_created: number;
  duplicates_found: number;
  errors_count: number;
  created_at: string;
  started_at?: string;
  completed_at?: string;
}

const Campaigns: React.FC = () => {
  const navigate = useNavigate();
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState(0);

  // Calculate statistics
  const totalCampaigns = campaigns.length;
  const totalLeads = campaigns.reduce((sum, c) => sum + c.leads_created, 0);
  const newLeads = campaigns
    .filter(c => c.status === 'completed')
    .reduce((sum, c) => sum + c.leads_created, 0);
  const convertedLeads = 0; // TODO: Get from API

  useEffect(() => {
    loadCampaigns();
    const interval = setInterval(loadCampaigns, 10000); // Refresh every 10 seconds
    return () => clearInterval(interval);
  }, []);

  const loadCampaigns = async () => {
    try {
      const response = await campaignAPI.list();
      setCampaigns(response.data || []);
      setLoading(false);
    } catch (error) {
      console.error('Error loading campaigns:', error);
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running': return 'info';
      case 'completed': return 'success';
      case 'failed': return 'error';
      case 'cancelled': return 'warning';
      default: return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return <CheckCircleIcon fontSize="small" />;
      case 'failed': return <ErrorIcon fontSize="small" />;
      default: return null;
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-GB');
  };

  const getFilteredCampaigns = () => {
    const statuses = ['all', 'running', 'completed', 'draft', 'cancelled'];
    const currentStatus = statuses[activeTab];
    
    if (currentStatus === 'all') return campaigns;
    return campaigns.filter(c => c.status === currentStatus);
  };

  const filteredCampaigns = getFilteredCampaigns();

  return (
    <Container maxWidth="xl" sx={{ mt: 2, mb: 4 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <Box
            sx={{
              width: 48,
              height: 48,
              borderRadius: '12px',
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}
          >
            <CampaignIcon sx={{ color: 'white', fontSize: 28 }} />
          </Box>
          <Typography variant="h4" component="h1" fontWeight="600">
            Lead Generation
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Button
            variant="outlined"
            startIcon={<PeopleIcon />}
            onClick={() => navigate('/leads')}
            sx={{ borderRadius: 2 }}
          >
            View All Leads
          </Button>
          <Button
            variant="contained"
            size="large"
            startIcon={<AddIcon />}
            onClick={() => navigate('/campaigns/new')}
            sx={{
              borderRadius: 2,
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              textTransform: 'none',
              fontSize: '16px',
              fontWeight: 600,
              px: 3,
              '&:hover': {
                background: 'linear-gradient(135deg, #764ba2 0%, #667eea 100%)',
              }
            }}
          >
            New Campaign
          </Button>
        </Box>
      </Box>

      {/* Statistics Cards */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card
            sx={{
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
              color: 'white',
              borderRadius: 3
            }}
          >
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <Box>
                  <Typography variant="h3" fontWeight="700" sx={{ mb: 0.5 }}>
                    {totalCampaigns}
                  </Typography>
                  <Typography variant="body2" sx={{ opacity: 0.9 }}>
                    Total Campaigns
                  </Typography>
                </Box>
                <BusinessIcon sx={{ fontSize: 40, opacity: 0.7 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card
            sx={{
              background: 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
              color: 'white',
              borderRadius: 3
            }}
          >
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <Box>
                  <Typography variant="h3" fontWeight="700" sx={{ mb: 0.5 }}>
                    {newLeads}
                  </Typography>
                  <Typography variant="body2" sx={{ opacity: 0.9 }}>
                    New Leads
                  </Typography>
                </Box>
                <StarIcon sx={{ fontSize: 40, opacity: 0.7 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card
            sx={{
              background: 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
              color: 'white',
              borderRadius: 3
            }}
          >
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <Box>
                  <Typography variant="h3" fontWeight="700" sx={{ mb: 0.5 }}>
                    {convertedLeads}
                  </Typography>
                  <Typography variant="body2" sx={{ opacity: 0.9 }}>
                    Converted
                  </Typography>
                </Box>
                <CheckCircleIcon sx={{ fontSize: 40, opacity: 0.7 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ borderRadius: 3, border: '2px solid #e0e0e0' }}>
            <CardContent>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <Box>
                  <Typography variant="h3" fontWeight="700" sx={{ mb: 0.5, color: 'text.primary' }}>
                    {totalLeads}
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    Total Leads
                  </Typography>
                </Box>
                <PeopleIcon sx={{ fontSize: 40, color: 'text.secondary', opacity: 0.5 }} />
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Recent Campaigns Section */}
      <Paper sx={{ borderRadius: 3, overflow: 'hidden' }}>
        <Box sx={{ p: 2, borderBottom: '1px solid #e0e0e0', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="h6" fontWeight="600">
            🚀 Recent Campaigns
          </Typography>
          <Tooltip title="Refresh">
            <IconButton size="small" onClick={loadCampaigns}>
              <RefreshIcon />
            </IconButton>
          </Tooltip>
        </Box>

        <Tabs
          value={activeTab}
          onChange={(e, newValue) => setActiveTab(newValue)}
          sx={{ borderBottom: '1px solid #e0e0e0', px: 2 }}
        >
          <Tab label={`All (${campaigns.length})`} />
          <Tab label={`Running (${campaigns.filter(c => c.status === 'running').length})`} />
          <Tab label={`Completed (${campaigns.filter(c => c.status === 'completed').length})`} />
          <Tab label={`Draft (${campaigns.filter(c => c.status === 'draft').length})`} />
          <Tab label={`Cancelled (${campaigns.filter(c => c.status === 'cancelled').length})`} />
        </Tabs>

        {loading && <LinearProgress />}

        <TableContainer>
          <Table>
            <TableHead>
              <TableRow sx={{ backgroundColor: '#f5f5f5' }}>
                <TableCell><strong>Campaign</strong></TableCell>
                <TableCell><strong>Status</strong></TableCell>
                <TableCell align="right"><strong>Leads</strong></TableCell>
                <TableCell><strong>Created</strong></TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filteredCampaigns.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={4} align="center" sx={{ py: 8 }}>
                    <CampaignIcon sx={{ fontSize: 64, color: 'text.disabled', mb: 2 }} />
                    <Typography variant="h6" color="text.secondary" gutterBottom>
                      No campaigns found
                    </Typography>
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
                      {activeTab === 0 
                        ? 'Create your first campaign to start generating leads'
                        : 'No campaigns in this status'
                      }
                    </Typography>
                    {activeTab === 0 && (
                      <Button
                        variant="contained"
                        startIcon={<AddIcon />}
                        onClick={() => navigate('/campaigns/new')}
                        sx={{
                          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
                          borderRadius: 2
                        }}
                      >
                        Create Campaign
                      </Button>
                    )}
                  </TableCell>
                </TableRow>
              ) : (
                filteredCampaigns.map((campaign) => (
                  <TableRow 
                    key={campaign.id}
                    hover
                    sx={{ 
                      cursor: 'pointer',
                      '&:hover': { backgroundColor: '#f9f9f9' }
                    }}
                    onClick={() => navigate(`/campaigns/${campaign.id}`)}
                  >
                    <TableCell>
                      <Typography variant="body1" fontWeight="500">
                        {campaign.name}
                      </Typography>
                      <Typography variant="caption" color="text.secondary">
                        {campaign.postcode} • {campaign.distance_miles} miles
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Chip
                        {...(getStatusIcon(campaign.status) && { icon: getStatusIcon(campaign.status) })}
                        label={campaign.status.charAt(0).toUpperCase() + campaign.status.slice(1)}
                        color={getStatusColor(campaign.status)}
                        size="small"
                        sx={{ fontWeight: 500 }}
                      />
                    </TableCell>
                    <TableCell align="right">
                      <Typography variant="body1" fontWeight="600" color="primary">
                        {campaign.leads_created}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {formatDate(campaign.created_at)}
                      </Typography>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>

      {/* Quick Actions */}
      <Grid container spacing={2} sx={{ mt: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Button
            fullWidth
            variant="outlined"
            startIcon={<AddIcon />}
            onClick={() => navigate('/campaigns/new')}
            sx={{ py: 1.5, borderRadius: 2, textTransform: 'none' }}
          >
            New Campaign
          </Button>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Button
            fullWidth
            variant="outlined"
            startIcon={<StarIcon />}
            onClick={() => navigate('/leads?status=new')}
            sx={{ py: 1.5, borderRadius: 2, textTransform: 'none' }}
          >
            New Leads
          </Button>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Button
            fullWidth
            variant="outlined"
            startIcon={<CheckCircleIcon />}
            onClick={() => navigate('/leads?status=qualified')}
            sx={{ py: 1.5, borderRadius: 2, textTransform: 'none' }}
          >
            Qualified Leads
          </Button>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Button
            fullWidth
            variant="outlined"
            startIcon={<CampaignIcon />}
            onClick={() => navigate('/campaigns')}
            sx={{ py: 1.5, borderRadius: 2, textTransform: 'none' }}
          >
            All Campaigns
          </Button>
        </Grid>
      </Grid>

      {/* Tips Section */}
      <Paper sx={{ mt: 3, p: 3, borderRadius: 3, background: '#f8f9fa' }}>
        <Typography variant="h6" gutterBottom fontWeight="600">
          💡 Lead Generation Tips
        </Typography>
        <Grid container spacing={2} sx={{ mt: 1 }}>
          <Grid item xs={12} md={6}>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Typography>📍</Typography>
              <Box>
                <Typography variant="subtitle2" fontWeight="600">Location Targeting</Typography>
                <Typography variant="body2" color="text.secondary">
                  Use specific postcodes and reasonable distances (10-30 miles) for better results. Target areas where you can easily travel for site visits.
                </Typography>
              </Box>
            </Box>
          </Grid>
          <Grid item xs={12} md={6}>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Typography>👥</Typography>
              <Box>
                <Typography variant="subtitle2" fontWeight="600">Follow Up Quickly</Typography>
                <Typography variant="body2" color="text.secondary">
                  Contact new leads within 24-48 hours while they're still warm. Set up follow-up reminders and track your contact attempts.
                </Typography>
              </Box>
            </Box>
          </Grid>
          <Grid item xs={12} md={6}>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Typography>🎯</Typography>
              <Box>
                <Typography variant="subtitle2" fontWeight="600">Quality Over Quantity</Typography>
                <Typography variant="body2" color="text.secondary">
                  Start with smaller, more focused campaigns (50-100 leads) and test your approach before running larger searches.
                </Typography>
              </Box>
            </Box>
          </Grid>
          <Grid item xs={12} md={6}>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Typography>📊</Typography>
              <Box>
                <Typography variant="subtitle2" fontWeight="600">Track Your Success</Typography>
                <Typography variant="body2" color="text.secondary">
                  Monitor which campaign types and prompts generate the best leads. Use this data to improve future campaigns.
                </Typography>
              </Box>
            </Box>
          </Grid>
        </Grid>
      </Paper>
    </Container>
  );
};

export default Campaigns;
