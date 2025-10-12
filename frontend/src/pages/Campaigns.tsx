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
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  CircularProgress,
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
  TrendingUp as TrendingUpIcon,
  Business as BusinessIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon
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

interface CampaignStats {
  total_campaigns: number;
  running_campaigns: number;
  total_leads_generated: number;
  avg_conversion_rate: number;
}

const Campaigns: React.FC = () => {
  const navigate = useNavigate();
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [filteredCampaigns, setFilteredCampaigns] = useState<Campaign[]>([]);
  const [loading, setLoading] = useState(true);
  const [stats, setStats] = useState<CampaignStats | null>(null);
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [activeTab, setActiveTab] = useState(0);

  useEffect(() => {
    loadCampaigns();
    const interval = setInterval(loadCampaigns, 10000); // Refresh every 10 seconds
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    // Filter campaigns based on status
    if (statusFilter === 'all') {
      setFilteredCampaigns(campaigns);
    } else {
      setFilteredCampaigns(campaigns.filter(c => c.status === statusFilter));
    }
  }, [campaigns, statusFilter]);

  const loadCampaigns = async () => {
    try {
      const response = await campaignAPI.list();
      setCampaigns(response.data);
      
      // Calculate stats
      const totalCampaigns = response.data.length;
      const runningCampaigns = response.data.filter((c: Campaign) => c.status === 'running').length;
      const totalLeads = response.data.reduce((sum: number, c: Campaign) => sum + c.leads_created, 0);
      
      setStats({
        total_campaigns: totalCampaigns,
        running_campaigns: runningCampaigns,
        total_leads_generated: totalLeads,
        avg_conversion_rate: 0 // Can be calculated with more data
      });
      
      setLoading(false);
    } catch (error) {
      console.error('Error loading campaigns:', error);
      setLoading(false);
    }
  };

  const handleStopCampaign = async (campaignId: string) => {
    if (!window.confirm('Are you sure you want to stop this campaign?')) {
      return;
    }
    
    try {
      await campaignAPI.stop(campaignId);
      loadCampaigns();
    } catch (error) {
      console.error('Error stopping campaign:', error);
      alert('Failed to stop campaign');
    }
  };

  const handleDeleteCampaign = async (campaignId: string) => {
    if (!window.confirm('Are you sure you want to delete this campaign? This cannot be undone.')) {
      return;
    }
    
    try {
      await campaignAPI.delete(campaignId);
      loadCampaigns();
    } catch (error) {
      console.error('Error deleting campaign:', error);
      alert('Failed to delete campaign');
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running':
        return 'info';
      case 'completed':
        return 'success';
      case 'failed':
        return 'error';
      case 'cancelled':
        return 'warning';
      case 'draft':
        return 'default';
      default:
        return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running':
        return <CircularProgress size={16} />;
      case 'completed':
        return <CheckCircleIcon fontSize="small" />;
      case 'failed':
        return <ErrorIcon fontSize="small" />;
      default:
        return null;
    }
  };

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleString();
  };

  const formatDuration = (started?: string, completed?: string) => {
    if (!started || !completed) return 'N/A';
    const start = new Date(started).getTime();
    const end = new Date(completed).getTime();
    const durationMinutes = Math.round((end - start) / 60000);
    return `${durationMinutes} min`;
  };

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 4 }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <CampaignIcon sx={{ fontSize: 40, color: 'primary.main' }} />
          <div>
            <Typography variant="h4" component="h1" gutterBottom sx={{ mb: 0 }}>
              Lead Generation Campaigns
            </Typography>
            <Typography variant="body2" color="text.secondary">
              AI-powered campaigns to find potential customers
            </Typography>
          </div>
        </Box>
        <Box sx={{ display: 'flex', gap: 2 }}>
          <Tooltip title="Refresh campaigns">
            <IconButton onClick={loadCampaigns} disabled={loading}>
              <RefreshIcon />
            </IconButton>
          </Tooltip>
          <Button
            variant="contained"
            size="large"
            startIcon={<AddIcon />}
            onClick={() => navigate('/campaigns/new')}
            sx={{
              background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
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
      {stats && (
        <Grid container spacing={3} sx={{ mb: 4 }}>
          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <div>
                    <Typography color="text.secondary" gutterBottom variant="overline">
                      Total Campaigns
                    </Typography>
                    <Typography variant="h4">
                      {stats.total_campaigns}
                    </Typography>
                  </div>
                  <CampaignIcon sx={{ fontSize: 48, color: 'primary.main', opacity: 0.3 }} />
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <div>
                    <Typography color="text.secondary" gutterBottom variant="overline">
                      Running Now
                    </Typography>
                    <Typography variant="h4">
                      {stats.running_campaigns}
                    </Typography>
                  </div>
                  <CircularProgress size={48} sx={{ opacity: 0.3 }} />
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <div>
                    <Typography color="text.secondary" gutterBottom variant="overline">
                      Leads Generated
                    </Typography>
                    <Typography variant="h4">
                      {stats.total_leads_generated}
                    </Typography>
                  </div>
                  <BusinessIcon sx={{ fontSize: 48, color: 'success.main', opacity: 0.3 }} />
                </Box>
              </CardContent>
            </Card>
          </Grid>

          <Grid item xs={12} sm={6} md={3}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <div>
                    <Typography color="text.secondary" gutterBottom variant="overline">
                      Avg. Success Rate
                    </Typography>
                    <Typography variant="h4">
                      {stats.total_campaigns > 0 
                        ? Math.round((campaigns.filter(c => c.status === 'completed').length / stats.total_campaigns) * 100)
                        : 0}%
                    </Typography>
                  </div>
                  <TrendingUpIcon sx={{ fontSize: 48, color: 'info.main', opacity: 0.3 }} />
                </Box>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      )}

      {/* Filter Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs
          value={activeTab}
          onChange={(e, newValue) => {
            setActiveTab(newValue);
            const statuses = ['all', 'running', 'completed', 'failed', 'draft'];
            setStatusFilter(statuses[newValue]);
          }}
          indicatorColor="primary"
          textColor="primary"
        >
          <Tab label={`All (${campaigns.length})`} />
          <Tab label={`Running (${campaigns.filter(c => c.status === 'running').length})`} />
          <Tab label={`Completed (${campaigns.filter(c => c.status === 'completed').length})`} />
          <Tab label={`Failed (${campaigns.filter(c => c.status === 'failed').length})`} />
          <Tab label={`Draft (${campaigns.filter(c => c.status === 'draft').length})`} />
        </Tabs>
      </Paper>

      {/* Alert for running campaigns */}
      {stats && stats.running_campaigns > 0 && (
        <Alert severity="info" sx={{ mb: 3 }}>
          {stats.running_campaigns} campaign{stats.running_campaigns > 1 ? 's' : ''} currently running. 
          Campaigns typically take 3-10 minutes depending on the number of results and data enrichment.
        </Alert>
      )}

      {/* Campaigns Table */}
      <TableContainer component={Paper}>
        {loading && <LinearProgress />}
        <Table>
          <TableHead>
            <TableRow sx={{ backgroundColor: 'grey.50' }}>
              <TableCell><strong>Campaign Name</strong></TableCell>
              <TableCell><strong>Type</strong></TableCell>
              <TableCell><strong>Location</strong></TableCell>
              <TableCell align="center"><strong>Status</strong></TableCell>
              <TableCell align="right"><strong>Found</strong></TableCell>
              <TableCell align="right"><strong>Created</strong></TableCell>
              <TableCell align="right"><strong>Duplicates</strong></TableCell>
              <TableCell><strong>Duration</strong></TableCell>
              <TableCell><strong>Created At</strong></TableCell>
              <TableCell align="right"><strong>Actions</strong></TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {filteredCampaigns.length === 0 ? (
              <TableRow>
                <TableCell colSpan={10} align="center" sx={{ py: 6 }}>
                  <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 2 }}>
                    <CampaignIcon sx={{ fontSize: 64, color: 'text.disabled' }} />
                    <Typography variant="h6" color="text.secondary">
                      No campaigns found
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {statusFilter === 'all' 
                        ? 'Create your first campaign to start generating leads'
                        : `No ${statusFilter} campaigns`
                      }
                    </Typography>
                    {statusFilter === 'all' && (
                      <Button
                        variant="contained"
                        startIcon={<AddIcon />}
                        onClick={() => navigate('/campaigns/new')}
                      >
                        Create Campaign
                      </Button>
                    )}
                  </Box>
                </TableCell>
              </TableRow>
            ) : (
              filteredCampaigns.map((campaign) => (
                <TableRow 
                  key={campaign.id}
                  hover
                  sx={{ 
                    '&:hover': { 
                      backgroundColor: 'action.hover',
                      cursor: 'pointer'
                    }
                  }}
                  onClick={() => navigate(`/campaigns/${campaign.id}`)}
                >
                  <TableCell>
                    <Typography variant="body1" fontWeight="medium">
                      {campaign.name}
                    </Typography>
                    {campaign.description && (
                      <Typography variant="caption" color="text.secondary" display="block">
                        {campaign.description.substring(0, 60)}
                        {campaign.description.length > 60 ? '...' : ''}
                      </Typography>
                    )}
                  </TableCell>
                  <TableCell>
                    <Chip 
                      label={campaign.prompt_type.replace('_', ' ')} 
                      size="small" 
                      variant="outlined"
                    />
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">
                      {campaign.postcode}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      ±{campaign.distance_miles} miles
                    </Typography>
                  </TableCell>
                  <TableCell align="center">
                    <Chip
                      icon={getStatusIcon(campaign.status)}
                      label={campaign.status.toUpperCase()}
                      color={getStatusColor(campaign.status)}
                      size="small"
                    />
                  </TableCell>
                  <TableCell align="right">
                    <Typography variant="body2">
                      {campaign.total_found}
                    </Typography>
                  </TableCell>
                  <TableCell align="right">
                    <Typography 
                      variant="body2" 
                      fontWeight="medium" 
                      color="success.main"
                    >
                      {campaign.leads_created}
                    </Typography>
                  </TableCell>
                  <TableCell align="right">
                    <Typography variant="body2" color="text.secondary">
                      {campaign.duplicates_found}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">
                      {formatDuration(campaign.started_at, campaign.completed_at)}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Typography variant="caption">
                      {formatDate(campaign.created_at)}
                    </Typography>
                  </TableCell>
                  <TableCell align="right" onClick={(e) => e.stopPropagation()}>
                    <Box sx={{ display: 'flex', gap: 1, justifyContent: 'flex-end' }}>
                      <Tooltip title="View campaign details">
                        <IconButton
                          size="small"
                          color="primary"
                          onClick={(e) => {
                            e.stopPropagation();
                            navigate(`/campaigns/${campaign.id}`);
                          }}
                        >
                          <ViewIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                      
                      {campaign.status === 'running' && (
                        <Tooltip title="Stop campaign">
                          <IconButton
                            size="small"
                            color="warning"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleStopCampaign(campaign.id);
                            }}
                          >
                            <StopIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      )}
                      
                      {(campaign.status === 'completed' || campaign.status === 'failed' || campaign.status === 'cancelled') && (
                        <Tooltip title="Delete campaign">
                          <IconButton
                            size="small"
                            color="error"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleDeleteCampaign(campaign.id);
                            }}
                          >
                            <DeleteIcon fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      )}
                    </Box>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Help Text */}
      <Box sx={{ mt: 3 }}>
        <Alert severity="info" variant="outlined">
          <Typography variant="body2">
            <strong>💡 Pro Tip:</strong> Campaigns use GPT-5-mini with web search to find real UK businesses. 
            They automatically enrich data with Google Maps (locations), Companies House (financials), and LinkedIn. 
            All leads are deduplicated against existing customers and leads in your system.
          </Typography>
        </Alert>
      </Box>
    </Container>
  );
};

export default Campaigns;
