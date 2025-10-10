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
  LinearProgress
} from '@mui/material';
import {
  Add as AddIcon,
  Visibility as ViewIcon,
  Stop as StopIcon
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { campaignAPI } from '../services/api';

const Campaigns: React.FC = () => {
  const navigate = useNavigate();
  const [campaigns, setCampaigns] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadCampaigns();
    const interval = setInterval(loadCampaigns, 5000); // Refresh every 5 seconds
    return () => clearInterval(interval);
  }, []);

  const loadCampaigns = async () => {
    try {
      const response = await campaignAPI.list();
      setCampaigns(response.data);
      setLoading(false);
    } catch (error) {
      console.error('Error loading campaigns:', error);
      setLoading(false);
    }
  };

  const handleStopCampaign = async (campaignId: string) => {
    try {
      await campaignAPI.stop(campaignId);
      loadCampaigns();
    } catch (error) {
      console.error('Error stopping campaign:', error);
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
      default:
        return 'default';
    }
  };

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Lead Generation Campaigns
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => navigate('/campaigns/new')}
        >
          New Campaign
        </Button>
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Campaign Name</TableCell>
              <TableCell>Location</TableCell>
              <TableCell>Status</TableCell>
              <TableCell align="right">Found</TableCell>
              <TableCell align="right">Created</TableCell>
              <TableCell align="right">Duplicates</TableCell>
              <TableCell>Created At</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={8} align="center">
                  Loading...
                </TableCell>
              </TableRow>
            ) : campaigns.length === 0 ? (
              <TableRow>
                <TableCell colSpan={8} align="center">
                  No campaigns yet. Create your first campaign!
                </TableCell>
              </TableRow>
            ) : (
              campaigns.map((campaign) => (
                <TableRow key={campaign.id} hover>
                  <TableCell>{campaign.name}</TableCell>
                  <TableCell>
                    {campaign.postcode}
                    {campaign.distance_miles && ` (${campaign.distance_miles}mi)`}
                  </TableCell>
                  <TableCell>
                    <Chip
                      label={campaign.status}
                      color={getStatusColor(campaign.status)}
                      size="small"
                    />
                    {campaign.status === 'running' && (
                      <LinearProgress sx={{ mt: 1 }} />
                    )}
                  </TableCell>
                  <TableCell align="right">{campaign.total_found || 0}</TableCell>
                  <TableCell align="right">{campaign.leads_created || 0}</TableCell>
                  <TableCell align="right">{campaign.duplicates_found || 0}</TableCell>
                  <TableCell>
                    {new Date(campaign.created_at).toLocaleDateString()}
                  </TableCell>
                  <TableCell align="right">
                    <IconButton
                      size="small"
                      onClick={() => navigate(`/campaigns/${campaign.id}`)}
                    >
                      <ViewIcon />
                    </IconButton>
                    {campaign.status === 'running' && (
                      <IconButton
                        size="small"
                        color="error"
                        onClick={() => handleStopCampaign(campaign.id)}
                      >
                        <StopIcon />
                      </IconButton>
                    )}
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>

      <Box sx={{ mt: 2 }}>
        <Typography variant="body2" color="text.secondary">
          Total: {campaigns.length} campaigns
        </Typography>
      </Box>
    </Container>
  );
};

export default Campaigns;

