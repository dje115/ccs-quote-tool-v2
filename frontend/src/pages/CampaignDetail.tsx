import React, { useEffect, useState } from 'react';
import {
  Container,
  Paper,
  Typography,
  Box,
  Button,
  Grid,
  Card,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  IconButton,
  LinearProgress,
  Alert,
  Divider
} from '@mui/material';
import {
  ArrowBack as BackIcon,
  Stop as StopIcon,
  Delete as DeleteIcon,
  Refresh as RefreshIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  PersonAdd as PersonAddIcon
} from '@mui/icons-material';
import { useNavigate, useParams } from 'react-router-dom';
import { campaignAPI } from '../services/api';

const CampaignDetail: React.FC = () => {
  const { campaignId } = useParams<{ campaignId: string }>();
  const navigate = useNavigate();
  const [campaign, setCampaign] = useState<any>(null);
  const [leads, setLeads] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (campaignId) {
      loadCampaign();
      loadLeads();
      
      // Auto-refresh if running
      const interval = setInterval(() => {
        if (campaign?.status === 'running') {
          loadCampaign();
          loadLeads();
        }
      }, 10000);
      
      return () => clearInterval(interval);
    }
  }, [campaignId]);

  const loadCampaign = async () => {
    try {
      if (!campaignId) return;
      const response = await campaignAPI.get(campaignId);
      setCampaign(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Error loading campaign:', error);
      setLoading(false);
    }
  };

  const loadLeads = async () => {
    try {
      if (!campaignId) return;
      const response = await campaignAPI.getLeads(campaignId);
      setLeads(response.data || []);
    } catch (error) {
      console.error('Error loading leads:', error);
    }
  };

  const handleStop = async () => {
    if (!campaignId || !window.confirm('Stop this campaign?')) return;
    
    try {
      await campaignAPI.stop(campaignId);
      loadCampaign();
    } catch (error) {
      alert('Failed to stop campaign');
    }
  };

  const handleDelete = async () => {
    if (!campaignId || !window.confirm('Delete this campaign? This cannot be undone.')) return;
    
    try {
      await campaignAPI.delete(campaignId);
      navigate('/campaigns');
    } catch (error) {
      alert('Failed to delete campaign');
    }
  };

  const handleConvertLead = async (leadId: string) => {
    try {
      await campaignAPI.convertLead(leadId);
      alert('Lead converted to customer successfully!');
      loadLeads();
    } catch (error) {
      alert('Failed to convert lead');
    }
  };

  if (loading) {
    return (
      <Container maxWidth="xl" sx={{ mt: 4 }}>
        <LinearProgress />
      </Container>
    );
  }

  if (!campaign) {
    return (
      <Container maxWidth="xl" sx={{ mt: 4 }}>
        <Alert severity="error">Campaign not found</Alert>
      </Container>
    );
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running': return 'info';
      case 'completed': return 'success';
      case 'failed': return 'error';
      case 'cancelled': return 'warning';
      default: return 'default';
    }
  };

  return (
    <Container maxWidth="xl" sx={{ mt: 2, mb: 4 }}>
      {/* Header */}
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <IconButton onClick={() => navigate('/campaigns')}>
            <BackIcon />
          </IconButton>
          <div>
            <Typography variant="h4" fontWeight="600">
              {campaign.name}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Created {new Date(campaign.created_at).toLocaleDateString()}
            </Typography>
          </div>
        </Box>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button startIcon={<RefreshIcon />} onClick={loadCampaign} variant="outlined">
            Refresh
          </Button>
          {campaign.status === 'running' && (
            <Button startIcon={<StopIcon />} onClick={handleStop} variant="outlined" color="warning">
              Stop
            </Button>
          )}
          {(campaign.status === 'completed' || campaign.status === 'failed' || campaign.status === 'cancelled') && (
            <Button startIcon={<DeleteIcon />} onClick={handleDelete} variant="outlined" color="error">
              Delete
            </Button>
          )}
        </Box>
      </Box>

      {/* Status Alert */}
      {campaign.status === 'running' && (
        <Alert severity="info" sx={{ mb: 3 }}>
          Campaign is currently running. This page will auto-refresh every 10 seconds.
        </Alert>
      )}

      {/* Statistics Cards */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ borderRadius: 2 }}>
            <CardContent>
              <Typography color="text.secondary" variant="overline">
                Status
              </Typography>
              <Box sx={{ mt: 1 }}>
                <Chip
                  label={campaign.status.toUpperCase()}
                  color={getStatusColor(campaign.status)}
                  icon={campaign.status === 'completed' ? <CheckCircleIcon /> : campaign.status === 'failed' ? <ErrorIcon /> : undefined}
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ borderRadius: 2 }}>
            <CardContent>
              <Typography color="text.secondary" variant="overline">
                Total Found
              </Typography>
              <Typography variant="h4" fontWeight="600">
                {campaign.total_found}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ borderRadius: 2 }}>
            <CardContent>
              <Typography color="text.secondary" variant="overline">
                Leads Created
              </Typography>
              <Typography variant="h4" fontWeight="600" color="primary">
                {campaign.leads_created}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card sx={{ borderRadius: 2 }}>
            <CardContent>
              <Typography color="text.secondary" variant="overline">
                Duplicates
              </Typography>
              <Typography variant="h4" fontWeight="600" color="text.secondary">
                {campaign.duplicates_found}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Campaign Details */}
      <Paper sx={{ p: 3, mb: 3, borderRadius: 2 }}>
        <Typography variant="h6" fontWeight="600" gutterBottom>
          Campaign Details
        </Typography>
        <Divider sx={{ mb: 2 }} />
        <Grid container spacing={2}>
          <Grid item xs={12} sm={6}>
            <Typography variant="body2" color="text.secondary">
              Postcode:
            </Typography>
            <Typography variant="body1" fontWeight="500">
              {campaign.postcode}
            </Typography>
          </Grid>
          <Grid item xs={12} sm={6}>
            <Typography variant="body2" color="text.secondary">
              Distance:
            </Typography>
            <Typography variant="body1" fontWeight="500">
              {campaign.distance_miles} miles
            </Typography>
          </Grid>
          <Grid item xs={12} sm={6}>
            <Typography variant="body2" color="text.secondary">
              Campaign Type:
            </Typography>
            <Typography variant="body1" fontWeight="500">
              {campaign.prompt_type.replace(/_/g, ' ').toUpperCase()}
            </Typography>
          </Grid>
          <Grid item xs={12} sm={6}>
            <Typography variant="body2" color="text.secondary">
              Max Results:
            </Typography>
            <Typography variant="body1" fontWeight="500">
              {campaign.max_results}
            </Typography>
          </Grid>
          {campaign.description && (
            <Grid item xs={12}>
              <Typography variant="body2" color="text.secondary">
                Description:
              </Typography>
              <Typography variant="body1">
                {campaign.description}
              </Typography>
            </Grid>
          )}
        </Grid>
      </Paper>

      {/* Leads Table */}
      <Paper sx={{ borderRadius: 2 }}>
        <Box sx={{ p: 2, borderBottom: '1px solid #e0e0e0' }}>
          <Typography variant="h6" fontWeight="600">
            Leads ({leads.length})
          </Typography>
        </Box>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow sx={{ backgroundColor: '#f5f5f5' }}>
                <TableCell><strong>Company</strong></TableCell>
                <TableCell><strong>Website</strong></TableCell>
                <TableCell><strong>Sector</strong></TableCell>
                <TableCell align="right"><strong>Score</strong></TableCell>
                <TableCell><strong>Status</strong></TableCell>
                <TableCell align="right"><strong>Actions</strong></TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {leads.length === 0 ? (
                <TableRow>
                  <TableCell colSpan={6} align="center" sx={{ py: 6 }}>
                    <Typography color="text.secondary">
                      {campaign.status === 'running' 
                        ? 'Leads are being generated...'
                        : 'No leads found for this campaign'
                      }
                    </Typography>
                  </TableCell>
                </TableRow>
              ) : (
                leads.map((lead) => (
                  <TableRow key={lead.id} hover>
                    <TableCell>
                      <Typography variant="body2" fontWeight="500">
                        {lead.company_name}
                      </Typography>
                      {lead.postcode && (
                        <Typography variant="caption" color="text.secondary">
                          {lead.postcode}
                        </Typography>
                      )}
                    </TableCell>
                    <TableCell>
                      {lead.website ? (
                        <a href={lead.website} target="_blank" rel="noopener noreferrer">
                          <Typography variant="body2" color="primary">
                            {lead.website.replace(/https?:\/\//, '')}
                          </Typography>
                        </a>
                      ) : (
                        <Typography variant="body2" color="text.secondary">
                          N/A
                        </Typography>
                      )}
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={lead.business_sector || 'Unknown'}
                        size="small"
                        variant="outlined"
                      />
                    </TableCell>
                    <TableCell align="right">
                      <Chip
                        label={lead.lead_score}
                        size="small"
                        color={lead.lead_score >= 70 ? 'success' : lead.lead_score >= 50 ? 'warning' : 'default'}
                      />
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={lead.status}
                        size="small"
                        color={lead.status === 'converted' ? 'success' : 'default'}
                      />
                    </TableCell>
                    <TableCell align="right">
                      {lead.status !== 'converted' && (
                        <Button
                          size="small"
                          startIcon={<PersonAddIcon />}
                          onClick={() => handleConvertLead(lead.id)}
                          variant="outlined"
                        >
                          Convert
                        </Button>
                      )}
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

export default CampaignDetail;

