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
  Divider,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField
} from '@mui/material';
import {
  ArrowBack as BackIcon,
  Stop as StopIcon,
  Delete as DeleteIcon,
  Refresh as RefreshIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  PersonAdd as PersonAddIcon,
  Edit as EditIcon
} from '@mui/icons-material';
import { useNavigate, useParams } from 'react-router-dom';
import { campaignAPI } from '../services/api';

const CampaignDetail: React.FC = () => {
  const { campaignId } = useParams<{ campaignId: string }>();
  const navigate = useNavigate();
  const [campaign, setCampaign] = useState<any>(null);
  const [leads, setLeads] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [editDialogOpen, setEditDialogOpen] = useState(false);
  const [editFormData, setEditFormData] = useState({
    name: '',
    description: '',
    company_names: [] as string[]
  });

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
      // Ensure leads is always an array
      const leadsData = response.data?.data || response.data || [];
      setLeads(Array.isArray(leadsData) ? leadsData : []);
    } catch (error) {
      console.error('Error loading leads:', error);
      // Set empty array on error to prevent map errors
      setLeads([]);
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
      console.error('Delete error:', error);
      alert('Failed to delete campaign');
    }
  };

  const handleOpenEdit = () => {
    if (campaign) {
      setEditFormData({
        name: campaign.name || '',
        description: campaign.description || '',
        company_names: campaign.company_names || []
      });
      setEditDialogOpen(true);
    }
  };

  const handleSaveEdit = async () => {
    if (!campaignId) return;
    
    try {
      await campaignAPI.update(campaignId, {
        name: editFormData.name,
        description: editFormData.description
      });
      
      setEditDialogOpen(false);
      loadCampaign();
    } catch (error) {
      alert('Failed to update campaign');
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

  // Calculate accurate totals
  const leadsCreated = campaign.leads_created || campaign.leads_created_count || leads.length || 0;
  const duplicatesFound = campaign.duplicates_found || campaign.duplicates_count || 0;
  const totalFound = campaign.total_found || campaign.total_found_count || (leadsCreated + duplicatesFound) || 0;

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
          {campaign.status === 'draft' && (
            <Button startIcon={<EditIcon />} onClick={handleOpenEdit} variant="outlined" color="primary">
              Edit
            </Button>
          )}
          {campaign.status === 'running' && (
            <Button startIcon={<StopIcon />} onClick={handleStop} variant="outlined" color="warning">
              Stop
            </Button>
          )}
          <Button startIcon={<DeleteIcon />} onClick={handleDelete} variant="outlined" color="error">
            Delete
          </Button>
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
        <Grid
          size={{
            xs: 12,
            sm: 6,
            md: 3
          }}>
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

        <Grid
          size={{
            xs: 12,
            sm: 6,
            md: 3
          }}>
          <Card sx={{ borderRadius: 2 }}>
            <CardContent>
              <Typography color="text.secondary" variant="overline">
                Total Found
              </Typography>
              <Typography variant="h4" fontWeight="600">
                {totalFound}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid
          size={{
            xs: 12,
            sm: 6,
            md: 3
          }}>
          <Card sx={{ borderRadius: 2 }}>
            <CardContent>
              <Typography color="text.secondary" variant="overline">
                Leads Created
              </Typography>
              <Typography variant="h4" fontWeight="600" color="primary">
                {leadsCreated}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

        <Grid
          size={{
            xs: 12,
            sm: 6,
            md: 3
          }}>
          <Card sx={{ borderRadius: 2 }}>
            <CardContent>
              <Typography color="text.secondary" variant="overline">
                Duplicates
              </Typography>
              <Typography variant="h4" fontWeight="600" color="text.secondary">
                {duplicatesFound}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
      {/* Campaign Details */}
      <Paper sx={{ p: 3, mb: 3, borderRadius: 2, backgroundColor: '#fafafa' }}>
        <Typography variant="h6" fontWeight="600" gutterBottom sx={{ color: 'primary.main' }}>
          Campaign Details
        </Typography>
        <Divider sx={{ mb: 3, borderColor: 'primary.main' }} />
        <Grid container spacing={3}>
          <Grid
            size={{
              xs: 12,
              sm: 6,
              md: 4
            }}>
            <Box sx={{ p: 2, backgroundColor: 'white', borderRadius: 2, border: '1px solid #e0e0e0' }}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Campaign Type
              </Typography>
              <Typography variant="body1" fontWeight="600" sx={{ color: 'primary.main' }}>
                {campaign.prompt_type?.replace(/_/g, ' ').toUpperCase() || 'Not specified'}
              </Typography>
            </Box>
          </Grid>
          
          <Grid
            size={{
              xs: 12,
              sm: 6,
              md: 4
            }}>
            <Box sx={{ p: 2, backgroundColor: 'white', borderRadius: 2, border: '1px solid #e0e0e0' }}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Target Sector
              </Typography>
              <Typography variant="body1" fontWeight="600" sx={{ color: 'success.main' }}>
                🎯 {campaign.sector_name || 'Not specified'}
              </Typography>
            </Box>
          </Grid>

          <Grid
            size={{
              xs: 12,
              sm: 6,
              md: 4
            }}>
            <Box sx={{ p: 2, backgroundColor: 'white', borderRadius: 2, border: '1px solid #e0e0e0' }}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Max Results
              </Typography>
              <Typography variant="body1" fontWeight="600" sx={{ color: 'info.main' }}>
                {campaign.max_results || 'Not specified'}
              </Typography>
            </Box>
          </Grid>

          {campaign.postcode && (
            <Grid
              size={{
                xs: 12,
                sm: 6,
                md: 4
              }}>
              <Box sx={{ p: 2, backgroundColor: 'white', borderRadius: 2, border: '1px solid #e0e0e0' }}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Postcode
                </Typography>
                <Typography variant="body1" fontWeight="600" sx={{ color: 'warning.main' }}>
                  📍 {campaign.postcode}
                </Typography>
              </Box>
            </Grid>
          )}

          {campaign.distance_miles && (
            <Grid
              size={{
                xs: 12,
                sm: 6,
                md: 4
              }}>
              <Box sx={{ p: 2, backgroundColor: 'white', borderRadius: 2, border: '1px solid #e0e0e0' }}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Distance
                </Typography>
                <Typography variant="body1" fontWeight="600" sx={{ color: 'secondary.main' }}>
                  📏 {campaign.distance_miles} miles
                </Typography>
              </Box>
            </Grid>
          )}

          <Grid
            size={{
              xs: 12,
              sm: 6,
              md: 4
            }}>
            <Box sx={{ p: 2, backgroundColor: 'white', borderRadius: 2, border: '1px solid #e0e0e0' }}>
              <Typography variant="body2" color="text.secondary" gutterBottom>
                Created
              </Typography>
              <Typography variant="body1" fontWeight="600">
                📅 {new Date(campaign.created_at).toLocaleString()}
              </Typography>
            </Box>
          </Grid>

          {campaign.completed_at && (
            <Grid
              size={{
                xs: 12,
                sm: 6,
                md: 4
              }}>
              <Box sx={{ p: 2, backgroundColor: 'white', borderRadius: 2, border: '1px solid #e0e0e0' }}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Completed
                </Typography>
                <Typography variant="body1" fontWeight="600" sx={{ color: 'success.main' }}>
                  ✅ {new Date(campaign.completed_at).toLocaleString()}
                </Typography>
              </Box>
            </Grid>
          )}

          {campaign.custom_prompt && (
            <Grid size={12}>
              <Box sx={{ p: 2, backgroundColor: 'white', borderRadius: 2, border: '1px solid #e0e0e0' }}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Search Prompt
                </Typography>
                <Typography variant="body1" sx={{ 
                  backgroundColor: '#f8f9fa', 
                  p: 2, 
                  borderRadius: 1, 
                  border: '1px solid #e9ecef',
                  fontStyle: 'italic',
                  color: 'text.secondary'
                }}>
                  "{campaign.custom_prompt}"
                </Typography>
              </Box>
            </Grid>
          )}

          {campaign.company_names && campaign.company_names.length > 0 && (
            <Grid size={12}>
              <Box sx={{ p: 2, backgroundColor: 'white', borderRadius: 2, border: '1px solid #e0e0e0' }}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Target Companies ({campaign.company_names.length})
                </Typography>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mt: 1 }}>
                  {campaign.company_names.map((name: string, index: number) => (
                    <Chip 
                      key={index} 
                      label={name} 
                      size="small" 
                      variant="outlined" 
                      sx={{ 
                        backgroundColor: '#e3f2fd',
                        borderColor: '#2196f3',
                        color: '#1976d2'
                      }}
                    />
                  ))}
                </Box>
              </Box>
            </Grid>
          )}

          {campaign.description && (
            <Grid size={12}>
              <Box sx={{ p: 2, backgroundColor: 'white', borderRadius: 2, border: '1px solid #e0e0e0' }}>
                <Typography variant="body2" color="text.secondary" gutterBottom>
                  Description
                </Typography>
                <Typography variant="body1" sx={{ color: 'text.primary' }}>
                  {campaign.description}
                </Typography>
              </Box>
            </Grid>
          )}
        </Grid>
      </Paper>
      {/* AI Analysis Summary */}
      {campaign.ai_analysis_summary && (
        <Paper sx={{ p: 3, mb: 3, borderRadius: 2 }}>
          <Typography variant="h6" fontWeight="600" gutterBottom>
            AI Analysis Summary
          </Typography>
          <Divider sx={{ mb: 2 }} />
          <Typography variant="body2" sx={{ 
            backgroundColor: '#f8f9fa', 
            p: 2, 
            borderRadius: 1, 
            border: '1px solid #e9ecef',
            whiteSpace: 'pre-wrap',
            fontFamily: 'monospace',
            fontSize: '0.875rem'
          }}>
            {typeof campaign.ai_analysis_summary === 'string' 
              ? campaign.ai_analysis_summary 
              : JSON.stringify(campaign.ai_analysis_summary, null, 2)
            }
          </Typography>
        </Paper>
      )}
      {/* Leads Table */}
      <Paper sx={{ borderRadius: 2 }}>
        <Box sx={{ p: 2, borderBottom: '1px solid #e0e0e0' }}>
          <Typography variant="h6" fontWeight="600">
            Leads ({(leads || []).length})
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
              {(leads || []).length === 0 ? (
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
                (leads || []).map((lead) => (
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
      {/* Edit Dialog */}
      <Dialog open={editDialogOpen} onClose={() => setEditDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Edit Campaign</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2, display: 'flex', flexDirection: 'column', gap: 2 }}>
            <TextField
              label="Campaign Name"
              fullWidth
              value={editFormData.name}
              onChange={(e) => setEditFormData({ ...editFormData, name: e.target.value })}
            />
            <TextField
              label="Description"
              fullWidth
              multiline
              rows={3}
              value={editFormData.description}
              onChange={(e) => setEditFormData({ ...editFormData, description: e.target.value })}
            />
            {editFormData.company_names.length > 0 && (
              <Box>
                <Typography variant="subtitle2" gutterBottom>
                  Companies ({editFormData.company_names.length}):
                </Typography>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mt: 1 }}>
                  {editFormData.company_names.map((name, index) => (
                    <Chip key={index} label={name} size="small" />
                  ))}
                </Box>
                <Typography variant="caption" color="text.secondary" sx={{ mt: 1, display: 'block' }}>
                  Note: Company list cannot be edited after creation
                </Typography>
              </Box>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditDialogOpen(false)}>Cancel</Button>
          <Button onClick={handleSaveEdit} variant="contained" color="primary">
            Save Changes
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default CampaignDetail;

