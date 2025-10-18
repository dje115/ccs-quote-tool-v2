import React from 'react';
import {
  Container,
  Paper,
  Typography,
  Box,
  Grid,
  Button
} from '@mui/material';
import {
  Search as SearchIcon,
  Business as BusinessIcon,
  Map as MapIcon,
  Upload as UploadIcon,
  ArrowForward as ArrowForwardIcon
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';

interface CampaignTemplate {
  id: string;
  title: string;
  description: string;
  icon: React.ReactNode;
  color: string;
  route: string;
}

const CampaignCreate: React.FC = () => {
  const navigate = useNavigate();

  const campaignTemplates: CampaignTemplate[] = [
    {
      id: 'dynamic_search',
      title: 'Dynamic Business Search',
      description: 'AI-powered search based on your company\'s services and target markets',
      icon: <SearchIcon sx={{ fontSize: 40 }} />,
      color: '#667eea',
      route: '/campaigns/new'
    },
    {
      id: 'similar_business',
      title: 'Similar Business Lookup',
      description: 'Find businesses similar to a specific company',
      icon: <BusinessIcon sx={{ fontSize: 40 }} />,
      color: '#764ba2',
      route: '/campaigns/new/similar-business'
    },
    {
      id: 'planning_applications',
      title: 'Planning Applications',
      description: 'Find businesses with construction/renovation plans',
      icon: <MapIcon sx={{ fontSize: 40 }} />,
      color: '#f093fb',
      route: '/campaigns/new/planning-applications'
    },
    {
      id: 'company_list_import',
      title: 'Company List Import',
      description: 'Import companies from CRM records and competitor lists',
      icon: <UploadIcon sx={{ fontSize: 40 }} />,
      color: '#f5576c',
      route: '/campaigns/import'
    }
  ];

  const handleSelectTemplate = (template: CampaignTemplate) => {
    navigate(template.route);
  };

  return (
    <Container maxWidth="xl" sx={{ py: 3, width: '100%', height: '100%' }}>
      {/* Header */}
      <Box sx={{ textAlign: 'center', mb: 4 }}>
        <Typography variant="h3" fontWeight="700" color="primary" gutterBottom>
          Create New Campaign
        </Typography>
        <Typography variant="h6" color="text.secondary" sx={{ mb: 3 }}>
          Choose a campaign type to get started
        </Typography>
      </Box>

      {/* Campaign Templates Grid */}
      <Grid container spacing={3} sx={{ mb: 4 }}>
        {campaignTemplates.map((template) => (
          <Grid
            key={template.id}
            size={{
              xs: 12,
              sm: 6,
              md: 6,
              lg: 3
            }}>
            <Paper
              sx={{
                p: 3,
                borderRadius: 2,
                cursor: 'pointer',
                transition: 'all 0.3s ease',
                border: '1px solid #e0e0e0',
                display: 'flex',
                flexDirection: 'column',
                height: '100%',
                '&:hover': {
                  transform: 'translateY(-4px)',
                  boxShadow: 3,
                  borderColor: 'primary.main'
                }
              }}
              onClick={() => handleSelectTemplate(template)}>
              <Box
                sx={{
                  display: 'flex',
                  justifyContent: 'center',
                  mb: 2,
                  color: template.color,
                  fontSize: 40
                }}>
                {template.icon}
              </Box>
              <Typography
                variant="h6"
                sx={{ fontWeight: 700, mb: 1, textAlign: 'center' }}>
                {template.title}
              </Typography>
              <Typography
                variant="body2"
                color="text.secondary"
                sx={{ mb: 2, textAlign: 'center', flex: 1 }}>
                {template.description}
              </Typography>
              <Button
                variant="outlined"
                endIcon={<ArrowForwardIcon />}
                fullWidth
                sx={{
                  borderColor: template.color,
                  color: template.color,
                  textTransform: 'none',
                  fontWeight: 600,
                  '&:hover': {
                    borderColor: template.color,
                    backgroundColor: 'transparent'
                  }
                }}>
                Select
              </Button>
            </Paper>
          </Grid>
        ))}
      </Grid>

      {/* Quick Info Section */}
      <Paper sx={{ p: 3, backgroundColor: '#f5f5f5', borderRadius: 2 }}>
        <Typography variant="h6" sx={{ fontWeight: 700, mb: 3 }}>
          💡 Campaign Tips
        </Typography>
        <Grid container spacing={3}>
          <Grid size={{ xs: 12, sm: 6 }}>
            <Box>
              <Typography variant="subtitle2" sx={{ fontWeight: 700, mb: 1, color: '#667eea' }}>
                🎯 Be Specific
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ lineHeight: 1.6 }}>
                Define clear target criteria for better lead quality
              </Typography>
            </Box>
          </Grid>
          <Grid size={{ xs: 12, sm: 6 }}>
            <Box>
              <Typography variant="subtitle2" sx={{ fontWeight: 700, mb: 1, color: '#667eea' }}>
                📍 Location Matters
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ lineHeight: 1.6 }}>
                Use postcodes and distance for targeted local searches
              </Typography>
            </Box>
          </Grid>
          <Grid size={{ xs: 12, sm: 6 }}>
            <Box>
              <Typography variant="subtitle2" sx={{ fontWeight: 700, mb: 1, color: '#667eea' }}>
                ⏱️ Start Small
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ lineHeight: 1.6 }}>
                Begin with 50-100 leads to test your approach
              </Typography>
            </Box>
          </Grid>
          <Grid size={{ xs: 12, sm: 6 }}>
            <Box>
              <Typography variant="subtitle2" sx={{ fontWeight: 700, mb: 1, color: '#667eea' }}>
                ✅ Track Results
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ lineHeight: 1.6 }}>
                Monitor success rates to refine future campaigns
              </Typography>
            </Box>
          </Grid>
        </Grid>
      </Paper>
    </Container>
  );
};

export default CampaignCreate;
