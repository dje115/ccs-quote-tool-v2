import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Grid,
  Card,
  CardContent,
  Chip,
  IconButton,
  Tooltip,
  Alert,
  CircularProgress,
  Fab,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  LinearProgress
} from '@mui/material';
import {
  Add as AddIcon,
  Business as BusinessIcon,
  LocationOn as LocationIcon,
  Speed as SpeedIcon,
  GpsFixed as TargetIcon,
  PlayArrow as PlayIcon,
  Pause as PauseIcon,
  Stop as StopIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Refresh as RefreshIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Schedule as ScheduleIcon,
  TrendingUp as TrendingUpIcon,
  Public as PublicIcon,
  RestartAlt as RestartIcon,
  PlayCircleOutline as StartIcon
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import { useApi } from '../hooks/useApi';

interface Campaign {
  id: number;
  name: string;
  description: string;
  sector_name: string;
  postcode: string;
  distance_miles: number;
  max_results: number;
  status: string;
  created_at: string;
  completed_at?: string;
  total_leads: number;
  ai_analysis_summary: string;
}

const CampaignsList: React.FC = () => {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const api = useApi();
  
  const [campaigns, setCampaigns] = useState<Campaign[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedCampaign, setSelectedCampaign] = useState<Campaign | null>(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [actionLoading, setActionLoading] = useState<number | null>(null);

  useEffect(() => {
    loadCampaigns();
  }, []);

  const loadCampaigns = async () => {
    setLoading(true);
    try {
      const response = await api.get('/campaigns/');
      setCampaigns(response.data);
    } catch (err: any) {
      console.error('Failed to load campaigns:', err);
      setError(err.response?.data?.detail || t('campaigns.loadError', 'Failed to load campaigns'));
    } finally {
      setLoading(false);
    }
  };

  const handleStartCampaign = async (campaignId: number) => {
    setActionLoading(campaignId);
    try {
      // API call to start campaign
      await api.post(`/campaigns/${campaignId}/start`);
      await loadCampaigns();
    } catch (err) {
      console.error('Failed to start campaign:', err);
    } finally {
      setActionLoading(null);
    }
  };

  const handleStopCampaign = async (campaignId: number) => {
    setActionLoading(campaignId);
    try {
      await api.post(`/campaigns/${campaignId}/stop`);
      await loadCampaigns();
    } catch (err) {
      console.error('Failed to stop campaign:', err);
    } finally {
      setActionLoading(null);
    }
  };

  const handlePauseCampaign = async (campaignId: number) => {
    setActionLoading(campaignId);
    try {
      await api.post(`/campaigns/${campaignId}/pause`);
      await loadCampaigns();
    } catch (err) {
      console.error('Failed to pause campaign:', err);
    } finally {
      setActionLoading(null);
    }
  };

  const handleRestartCampaign = async (campaignId: number) => {
    setActionLoading(campaignId);
    try {
      await api.post(`/campaigns/${campaignId}/restart`);
      await loadCampaigns();
    } catch (err) {
      console.error('Failed to restart campaign:', err);
    } finally {
      setActionLoading(null);
    }
  };

  const handleDeleteCampaign = async (campaignId: number) => {
    setActionLoading(campaignId);
    try {
      await api.delete(`/campaigns/${campaignId}`);
      await loadCampaigns();
      setDeleteDialogOpen(false);
    } catch (err) {
      console.error('Failed to delete campaign:', err);
    } finally {
      setActionLoading(null);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'completed': return 'success';
      case 'running': return 'primary';
      case 'failed': return 'error';
      case 'queued': return 'warning';
      case 'paused': return 'default';
      default: return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case 'completed': return <CheckCircleIcon />;
      case 'running': return <PlayIcon />;
      case 'failed': return <ErrorIcon />;
      case 'queued': return <ScheduleIcon />;
      case 'paused': return <PauseIcon />;
      default: return <BusinessIcon />;
    }
  };

  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString('en-GB', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ maxWidth: 1400, mx: 'auto', p: 3 }}>
      {/* Header */}
      <Paper elevation={2} sx={{ p: 3, mb: 3 }}>
        <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
          <Box display="flex" alignItems="center">
            <BusinessIcon sx={{ mr: 2, color: 'primary.main', fontSize: 32 }} />
            <Box>
              <Typography variant="h4" component="h1" gutterBottom>
                {t('campaigns.title', 'Lead Generation Campaigns')}
              </Typography>
              <Typography variant="body1" color="text.secondary">
                {t('campaigns.subtitle', 'Manage your AI-powered lead generation campaigns')}
              </Typography>
            </Box>
          </Box>
          <Box display="flex" gap={2}>
            <Tooltip title={t('campaigns.refresh', 'Refresh campaigns')}>
              <IconButton onClick={loadCampaigns} disabled={loading}>
                <RefreshIcon />
              </IconButton>
            </Tooltip>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => navigate('/campaigns/create')}
            >
              {t('campaigns.createNew', 'Create New Campaign')}
            </Button>
          </Box>
        </Box>

        {/* Stats */}
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6} md={3}>
            <Card variant="outlined">
              <CardContent sx={{ textAlign: 'center' }}>
                <Typography variant="h4" color="primary">
                  {campaigns.length}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {t('campaigns.totalCampaigns', 'Total Campaigns')}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card variant="outlined">
              <CardContent sx={{ textAlign: 'center' }}>
                <Typography variant="h4" color="success.main">
                  {campaigns.filter(c => c.status === 'completed').length}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {t('campaigns.completed', 'Completed')}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card variant="outlined">
              <CardContent sx={{ textAlign: 'center' }}>
                <Typography variant="h4" color="warning.main">
                  {campaigns.filter(c => c.status === 'running').length}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {t('campaigns.running', 'Running')}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
          <Grid item xs={12} sm={6} md={3}>
            <Card variant="outlined">
              <CardContent sx={{ textAlign: 'center' }}>
                <Typography variant="h4" color="info.main">
                  {campaigns.reduce((sum, c) => sum + c.total_leads, 0)}
                </Typography>
                <Typography variant="body2" color="text.secondary">
                  {t('campaigns.totalLeads', 'Total Leads')}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        </Grid>
      </Paper>

      {/* Error Message */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Campaigns Table */}
      <Paper elevation={2}>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>{t('campaigns.name', 'Campaign Name')}</TableCell>
                <TableCell>{t('campaigns.sector', 'Sector')}</TableCell>
                <TableCell>{t('campaigns.location', 'Location')}</TableCell>
                <TableCell>{t('campaigns.status', 'Status')}</TableCell>
                <TableCell>{t('campaigns.results', 'Results')}</TableCell>
                <TableCell>{t('campaigns.created', 'Created')}</TableCell>
                <TableCell>{t('campaigns.actions', 'Actions')}</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {campaigns.map((campaign) => (
                <TableRow key={campaign.id} hover>
                  <TableCell>
                    <Box>
                      <Typography variant="body1" fontWeight="medium">
                        {campaign.name}
                      </Typography>
                      {campaign.description && (
                        <Typography variant="caption" color="text.secondary">
                          {campaign.description}
                        </Typography>
                      )}
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Box display="flex" alignItems="center">
                      <PublicIcon sx={{ mr: 1, fontSize: 16, color: 'action.active' }} />
                      <Typography variant="body2">
                        {campaign.sector_name.length > 30 
                          ? `${campaign.sector_name.substring(0, 30)}...`
                          : campaign.sector_name
                        }
                      </Typography>
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Box display="flex" alignItems="center">
                      <LocationIcon sx={{ mr: 1, fontSize: 16, color: 'action.active' }} />
                      <Box>
                        <Typography variant="body2">{campaign.postcode}</Typography>
                        <Typography variant="caption" color="text.secondary">
                          {campaign.distance_miles} miles
                        </Typography>
                      </Box>
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Chip
                      icon={getStatusIcon(campaign.status)}
                      label={t(`campaigns.status.${campaign.status}`, campaign.status)}
                      color={getStatusColor(campaign.status) as any}
                      size="small"
                    />
                  </TableCell>
                  <TableCell>
                    <Box display="flex" alignItems="center">
                      <TargetIcon sx={{ mr: 1, fontSize: 16, color: 'action.active' }} />
                      <Box>
                        <Typography variant="body2">
                          {campaign.total_leads} / {campaign.max_results}
                        </Typography>
                        <LinearProgress
                          variant="determinate"
                          value={(campaign.total_leads / campaign.max_results) * 100}
                          sx={{ width: 60, height: 4 }}
                        />
                      </Box>
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">
                      {formatDate(campaign.created_at)}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Box display="flex" gap={0.5} flexWrap="wrap">
                      {/* Start Button - for queued, paused, or failed campaigns */}
                      {(campaign.status === 'queued' || campaign.status === 'paused' || campaign.status === 'failed') && (
                        <Tooltip title={t('campaigns.start', 'Start campaign')}>
                          <span>
                            <IconButton
                              size="small"
                              onClick={() => handleStartCampaign(campaign.id)}
                              disabled={actionLoading === campaign.id}
                              color="success"
                            >
                              {actionLoading === campaign.id ? 
                                <CircularProgress size={16} /> : 
                                <StartIcon />
                              }
                            </IconButton>
                          </span>
                        </Tooltip>
                      )}
                      
                      {/* Stop Button - for running campaigns */}
                      {campaign.status === 'running' && (
                        <Tooltip title={t('campaigns.stop', 'Stop campaign')}>
                          <span>
                            <IconButton
                              size="small"
                              onClick={() => handleStopCampaign(campaign.id)}
                              disabled={actionLoading === campaign.id}
                              color="error"
                            >
                              {actionLoading === campaign.id ? 
                                <CircularProgress size={16} /> : 
                                <StopIcon />
                              }
                            </IconButton>
                          </span>
                        </Tooltip>
                      )}
                      
                      {/* Pause Button - for running campaigns */}
                      {campaign.status === 'running' && (
                        <Tooltip title={t('campaigns.pause', 'Pause campaign')}>
                          <span>
                            <IconButton
                              size="small"
                              onClick={() => handlePauseCampaign(campaign.id)}
                              disabled={actionLoading === campaign.id}
                              color="warning"
                            >
                              {actionLoading === campaign.id ? 
                                <CircularProgress size={16} /> : 
                                <PauseIcon />
                              }
                            </IconButton>
                          </span>
                        </Tooltip>
                      )}
                      
                      {/* Restart Button - for paused, failed, or completed campaigns */}
                      {(campaign.status === 'paused' || campaign.status === 'failed' || campaign.status === 'completed') && (
                        <Tooltip title={t('campaigns.restart', 'Restart campaign')}>
                          <span>
                            <IconButton
                              size="small"
                              onClick={() => handleRestartCampaign(campaign.id)}
                              disabled={actionLoading === campaign.id}
                              color="info"
                            >
                              {actionLoading === campaign.id ? 
                                <CircularProgress size={16} /> : 
                                <RestartIcon />
                              }
                            </IconButton>
                          </span>
                        </Tooltip>
                      )}
                      
                      {/* View Details Button - always available */}
                      <Tooltip title={t('campaigns.view', 'View details')}>
                        <IconButton
                          size="small"
                          onClick={() => navigate(`/campaigns/${campaign.id}`)}
                          color="primary"
                        >
                          <TrendingUpIcon />
                        </IconButton>
                      </Tooltip>
                      
                      {/* Edit Button - for non-running campaigns */}
                      {campaign.status !== 'running' && (
                        <Tooltip title={t('campaigns.edit', 'Edit campaign')}>
                          <IconButton
                            size="small"
                            onClick={() => navigate(`/campaigns/${campaign.id}/edit`)}
                            color="default"
                          >
                            <EditIcon />
                          </IconButton>
                        </Tooltip>
                      )}
                      
                      {/* Delete Button - for non-running campaigns */}
                      {campaign.status !== 'running' && (
                        <Tooltip title={t('campaigns.delete', 'Delete campaign')}>
                          <IconButton
                            size="small"
                            onClick={() => {
                              setSelectedCampaign(campaign);
                              setDeleteDialogOpen(true);
                            }}
                            color="error"
                          >
                            <DeleteIcon />
                          </IconButton>
                        </Tooltip>
                      )}
                    </Box>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      </Paper>

      {/* Floating Action Button */}
      <Fab
        color="primary"
        aria-label="add campaign"
        sx={{ position: 'fixed', bottom: 16, right: 16 }}
        onClick={() => navigate('/campaigns/create')}
      >
        <AddIcon />
      </Fab>

      {/* Delete Confirmation Dialog */}
      <Dialog open={deleteDialogOpen} onClose={() => setDeleteDialogOpen(false)}>
        <DialogTitle>
          {t('campaigns.deleteConfirm', 'Delete Campaign')}
        </DialogTitle>
        <DialogContent>
          <Typography>
            {t('campaigns.deleteMessage', 'Are you sure you want to delete')} "{selectedCampaign?.name}"?
            {t('campaigns.deleteWarning', ' This action cannot be undone.')}
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteDialogOpen(false)}>
            {t('common.cancel', 'Cancel')}
          </Button>
          <Button
            onClick={() => selectedCampaign && handleDeleteCampaign(selectedCampaign.id)}
            color="error"
            disabled={actionLoading === selectedCampaign?.id}
          >
            {actionLoading === selectedCampaign?.id ? 
              <CircularProgress size={16} /> : 
              t('common.delete', 'Delete')
            }
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default CampaignsList;
