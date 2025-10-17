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
  Star as StarIcon,
  PlayArrow as PlayArrowIcon,
  Replay as ReplayIcon,
  Cancel as CancelIcon,
  Undo as UndoIcon
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { campaignAPI } from '../services/api';

interface Campaign {
  id: string;
  name: string;
  description?: string;
  sector_name: string;
  prompt_type: string;
  postcode: string;
  distance_miles: number;
  max_results: number;
  status: string;
  total_found: number;
  total_leads: number;  // Backend returns this as 'total_leads', not 'leads_created'
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
  const [sortBy, setSortBy] = useState<'created_at' | 'name' | 'status' | 'total_leads'>('created_at');
  const [sortOrder, setSortOrder] = useState<'asc' | 'desc'>('desc');

  // Calculate statistics
  const totalCampaigns = campaigns.length;
  const totalLeads = campaigns.reduce((sum, c) => sum + (c.total_leads || 0), 0);
  const newLeads = campaigns
    .filter(c => c.status === 'completed')
    .reduce((sum, c) => sum + (c.total_leads || 0), 0);
  const convertedLeads = 0; // TODO: Get from API

  useEffect(() => {
    loadCampaigns();
    const interval = setInterval(loadCampaigns, 10000); // Refresh every 10 seconds
    return () => clearInterval(interval);
  }, [sortBy, sortOrder]);

  const loadCampaigns = async () => {
    try {
      const response = await campaignAPI.list({
        sort_by: sortBy,
        sort_order: sortOrder
      });
      setCampaigns(response.data || []);
      setLoading(false);
    } catch (error) {
      console.error('Error loading campaigns:', error);
      setLoading(false);
    }
  };

  const handleStartCampaign = async (campaignId: string, event: React.MouseEvent) => {
    event.stopPropagation(); // Prevent row click
    try {
      await campaignAPI.start(campaignId);
      loadCampaigns(); // Refresh list
    } catch (error) {
      console.error('Error starting campaign:', error);
      alert('Failed to start campaign');
    }
  };

  const handleRestartCampaign = async (campaignId: string, event: React.MouseEvent) => {
    event.stopPropagation(); // Prevent row click
    try {
      await campaignAPI.restart(campaignId);
      loadCampaigns(); // Refresh list
    } catch (error) {
      console.error('Error restarting campaign:', error);
      alert('Failed to restart campaign');
    }
  };

  const handleDeleteCampaign = async (campaignId: string, event: React.MouseEvent) => {
    event.stopPropagation(); // Prevent row click
    
    const campaign = campaigns.find(c => c.id === campaignId);
    if (!campaign) return;
    
    const confirmed = window.confirm(
      `Are you sure you want to delete the draft campaign "${campaign.name}"?\n\nThis action cannot be undone.`
    );
    
    if (!confirmed) return;
    
    try {
      await campaignAPI.delete(campaignId);
      loadCampaigns(); // Refresh list
    } catch (error) {
      console.error('Error deleting campaign:', error);
      alert('Failed to delete campaign');
    }
  };

  const handleStopCampaign = async (campaignId: string, event: React.MouseEvent) => {
    event.stopPropagation(); // Prevent row click
    if (!window.confirm('Are you sure you want to stop this campaign?')) return;
    
    try {
      await campaignAPI.stop(campaignId);
      alert('Campaign stopped successfully');
      loadCampaigns(); // Refresh list
    } catch (error) {
      console.error('Error stopping campaign:', error);
      alert('Failed to stop campaign');
    }
  };

  const handleCancelQueuedCampaign = async (campaignId: string, event: React.MouseEvent) => {
    event.stopPropagation(); // Prevent row click
    if (!window.confirm('Are you sure you want to cancel this queued campaign?')) return;
    
    try {
      // For now, we'll use the stop endpoint which sets status to CANCELLED
      // This will prevent it from running when the worker picks it up
      await campaignAPI.stop(campaignId);
      loadCampaigns(); // Refresh list
    } catch (error) {
      console.error('Error cancelling campaign:', error);
      alert('Failed to cancel campaign');
    }
  };

  const handleResetToDraft = async (campaignId: string, event: React.MouseEvent) => {
    event.stopPropagation(); // Prevent row click
    if (!window.confirm('Reset this campaign back to draft status?')) return;
    
    try {
      await campaignAPI.resetToDraft(campaignId);
      loadCampaigns(); // Refresh list
    } catch (error) {
      console.error('Error resetting campaign to draft:', error);
      alert('Failed to reset campaign');
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'queued': return 'info';
      case 'running': return 'info';
      case 'completed': return 'success';
      case 'failed': return 'error';
      case 'cancelled': return 'warning';
      case 'draft': return 'default';
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
                <TableCell 
                  sx={{ cursor: 'pointer', userSelect: 'none' }}
                  onClick={() => {
                    if (sortBy === 'name') {
                      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
                    } else {
                      setSortBy('name');
                      setSortOrder('asc');
                    }
                  }}
                >
                  <strong>Campaign</strong>
                  {sortBy === 'name' && (sortOrder === 'asc' ? ' ↑' : ' ↓')}
                </TableCell>
                <TableCell 
                  sx={{ cursor: 'pointer', userSelect: 'none' }}
                  onClick={() => {
                    if (sortBy === 'status') {
                      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
                    } else {
                      setSortBy('status');
                      setSortOrder('asc');
                    }
                  }}
                >
                  <strong>Status</strong>
                  {sortBy === 'status' && (sortOrder === 'asc' ? ' ↑' : ' ↓')}
                </TableCell>
                <TableCell 
                  align="right"
                  sx={{ cursor: 'pointer', userSelect: 'none' }}
                  onClick={() => {
                    if (sortBy === 'total_leads') {
                      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
                    } else {
                      setSortBy('total_leads');
                      setSortOrder('desc');
                    }
                  }}
                >
                  <strong>Leads</strong>
                  {sortBy === 'total_leads' && (sortOrder === 'asc' ? ' ↑' : ' ↓')}
                </TableCell>
                <TableCell 
                  sx={{ cursor: 'pointer', userSelect: 'none' }}
                  onClick={() => {
                    if (sortBy === 'created_at') {
                      setSortOrder(sortOrder === 'asc' ? 'desc' : 'asc');
                    } else {
                      setSortBy('created_at');
                      setSortOrder('desc');
                    }
                  }}
                >
                  <strong>Created</strong>
                  {sortBy === 'created_at' && (sortOrder === 'asc' ? ' ↑' : ' ↓')}
                </TableCell>
                <TableCell align="center"><strong>Actions</strong></TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {filteredCampaigns.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={5} align="center" sx={{ py: 8 }}>
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
                      <Typography variant="caption" color="text.secondary" display="block">
                        🎯 {campaign.sector_name}
                      </Typography>
                      <Typography variant="caption" color="text.secondary" display="block">
                        📍 {campaign.postcode} • {campaign.distance_miles} miles • Max: {campaign.max_results}
                      </Typography>
                      {campaign.prompt_type === 'custom_search' && campaign.description && (
                        <Typography variant="caption" color="primary.main" display="block" sx={{ mt: 0.5 }}>
                          🔍 Custom: {campaign.description.substring(0, 50)}{campaign.description.length > 50 ? '...' : ''}
                        </Typography>
                      )}
                    </TableCell>
                    <TableCell>
                      <Chip
                        icon={getStatusIcon(campaign.status) || undefined}
                        label={campaign.status.charAt(0).toUpperCase() + campaign.status.slice(1)}
                        color={getStatusColor(campaign.status)}
                        size="small"
                        sx={{ fontWeight: 500 }}
                      />
                    </TableCell>
                    <TableCell align="right">
                      <Typography variant="body1" fontWeight="600" color="primary">
                        {campaign.total_leads || 0}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {formatDate(campaign.created_at)}
                      </Typography>
                    </TableCell>
                    <TableCell align="center" onClick={(e) => e.stopPropagation()}>
                      <Box sx={{ display: 'flex', gap: 1, justifyContent: 'center' }}>
                        {campaign.status === 'draft' && (
                          <>
                            <Tooltip title="Start Campaign">
                              <IconButton
                                size="small"
                                color="success"
                                onClick={(e) => handleStartCampaign(campaign.id, e)}
                                sx={{
                                  '&:hover': {
                                    backgroundColor: 'success.light',
                                    color: 'white'
                                  }
                                }}
                              >
                                <PlayArrowIcon />
                              </IconButton>
                            </Tooltip>
                            <Tooltip title="Delete Draft Campaign">
                              <IconButton
                                size="small"
                                color="error"
                                onClick={(e) => handleDeleteCampaign(campaign.id, e)}
                                sx={{
                                  '&:hover': {
                                    backgroundColor: 'error.light',
                                    color: 'white'
                                  }
                                }}
                              >
                                <DeleteIcon />
                              </IconButton>
                            </Tooltip>
                          </>
                        )}
                        {campaign.status === 'queued' && (
                          <>
                            <Tooltip title="Reset to Draft">
                              <IconButton
                                size="small"
                                color="primary"
                                onClick={(e) => handleResetToDraft(campaign.id, e)}
                                sx={{
                                  '&:hover': {
                                    backgroundColor: 'primary.light',
                                    color: 'white'
                                  }
                                }}
                              >
                                <UndoIcon />
                              </IconButton>
                            </Tooltip>
                            <Tooltip title="Cancel Campaign">
                              <IconButton
                                size="small"
                                color="error"
                                onClick={(e) => handleCancelQueuedCampaign(campaign.id, e)}
                                sx={{
                                  '&:hover': {
                                    backgroundColor: 'error.light',
                                    color: 'white'
                                  }
                                }}
                              >
                                <CancelIcon />
                              </IconButton>
                            </Tooltip>
                          </>
                        )}
                        {(campaign.status === 'failed' || campaign.status === 'cancelled' || campaign.status === 'completed') && (
                          <Tooltip title="Restart Campaign">
                            <IconButton
                              size="small"
                              color="primary"
                              onClick={(e) => handleRestartCampaign(campaign.id, e)}
                              sx={{
                                '&:hover': {
                                  backgroundColor: 'primary.light',
                                  color: 'white'
                                }
                              }}
                            >
                              <ReplayIcon />
                            </IconButton>
                          </Tooltip>
                        )}
                        {campaign.status === 'running' && (
                          <Tooltip title="Stop Campaign">
                            <IconButton
                              size="small"
                              color="error"
                              onClick={(e) => handleStopCampaign(campaign.id, e)}
                              sx={{
                                '&:hover': {
                                  backgroundColor: 'error.light',
                                  color: 'white'
                                }
                              }}
                            >
                              <StopIcon />
                            </IconButton>
                          </Tooltip>
                        )}
                        <Tooltip title="View Details">
                          <IconButton
                            size="small"
                            onClick={(e) => {
                              e.stopPropagation();
                              navigate(`/campaigns/${campaign.id}`);
                            }}
                          >
                            <ViewIcon />
                          </IconButton>
                        </Tooltip>
                      </Box>
                    </TableCell>
                  </TableRow>
                ))
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>

    </Container>
  );
};

export default Campaigns;
