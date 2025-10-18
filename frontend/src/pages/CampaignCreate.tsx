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
  Add as AddIcon,
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
  featured?: boolean;
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
      featured: true
    },
    {
      id: 'similar_business',
      title: 'Similar Business Lookup',
      description: 'Find businesses similar to a specific company',
      icon: <BusinessIcon sx={{ fontSize: 40 }} />,
      color: '#764ba2'
    },
    {
      id: 'planning_applications',
      title: 'Planning Applications',
      description: 'Find businesses with construction/renovation plans',
      icon: <MapIcon sx={{ fontSize: 40 }} />,
      color: '#f093fb'
    },
    {
      id: 'company_list_import',
      title: 'Company List Import',
      description: 'Import companies from CRM records and competitor lists',
      icon: <UploadIcon sx={{ fontSize: 40 }} />,
      color: '#f5576c'
    }
  ];

  const featuredTemplate = campaignTemplates.find(t => t.featured);
  const otherTemplates = campaignTemplates.filter(t => !t.featured);

  const handleSelectTemplate = (templateId: string) => {
    switch (templateId) {
      case 'dynamic_search':
        navigate('/campaigns/new/dynamic-search');
        break;
      case 'similar_business':
        navigate('/campaigns/new/similar-business');
        break;
      case 'planning_applications':
        navigate('/campaigns/new/planning-applications');
        break;
      case 'company_list_import':
        navigate('/campaigns/new/company-list-import');
        break;
      default:
        break;
    }
  };

  return (
    <Container maxWidth="xl" sx={{ py: 3, width: '100%', height: '100%' }}>
      {/* Header */}
      <Box sx={{ textAlign: 'center', mb: 4 }}>
        <Typography variant="h3" fontWeight="700" color="primary" gutterBottom>
          Create New Campaign
        </Typography>
        <Typography variant="h6" color="text.secondary" sx={{ mb: 3 }}>
          Choose a search prompt to get started
        </Typography>
      </Box>

      {/* Featured Template - Dynamic Business Search */}
      {featuredTemplate && (
        <Box sx={{ mb: 4 }}>
          <Paper
            sx={{
              p: 4,
              borderRadius: 3,
              background: `linear-gradient(135deg, ${featuredTemplate.color} 0%, #764ba2 100%)`,
              color: 'white',
              cursor: 'pointer',
              transition: 'all 0.3s ease',
              '&:hover': {
                transform: 'translateY(-4px)',
                boxShadow: 6
              }
            }}
            onClick={() => handleSelectTemplate(featuredTemplate.id)}
          >
            <Grid container spacing={3} alignItems="center">
              <Grid item xs={12} sm="auto">
                <Box sx={{ display: 'flex', justifyContent: 'center', fontSize: 60 }}>
                  {featuredTemplate.icon}
                </Box>
              </Grid>
              <Grid item xs={12} sm>
                <Typography variant="h5" sx={{ fontWeight: 700, mb: 1 }}>
                  ⭐ {featuredTemplate.title}
                </Typography>
                <Typography variant="body1" sx={{ opacity: 0.95, mb: 2 }}>
                  {featuredTemplate.description}
                </Typography>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <Typography variant="body2" sx={{ fontWeight: 600 }}>
                    Get Started
                  </Typography>
                  <ArrowForwardIcon sx={{ fontSize: 20 }} />
                </Box>
              </Grid>
            </Grid>
          </Paper>
        </Box>
      )}

      {/* Other Templates Grid */}
      <Box sx={{ mb: 4 }}>
        <Typography variant="h6" sx={{ fontWeight: 700, mb: 3, color: 'primary.main' }}>
          Other Search Options
        </Typography>
        <Grid container spacing={3}>
          {otherTemplates.map((template) => (
            <Grid item xs={12} sm={6} md={4} key={template.id}>
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
                onClick={() => handleSelectTemplate(template.id)}
              >
                <Box
                  sx={{
                    display: 'flex',
                    justifyContent: 'center',
                    mb: 2,
                    color: template.color,
                    fontSize: 40
                  }}
                >
                  {template.icon}
                </Box>
                <Typography variant="h6" sx={{ fontWeight: 700, mb: 1, textAlign: 'center' }}>
                  {template.title}
                </Typography>
                <Typography
                  variant="body2"
                  color="text.secondary"
                  sx={{ mb: 2, textAlign: 'center', flex: 1 }}
                >
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
                  }}
                >
                  Select
                </Button>
              </Paper>
            </Grid>
          ))}
        </Grid>
      </Box>

      {/* Quick Info Section */}
      <Paper sx={{ p: 3, backgroundColor: '#f5f5f5', borderRadius: 2 }}>
        <Typography variant="h6" sx={{ fontWeight: 700, mb: 2 }}>
          💡 Campaign Tips
        </Typography>
        <Box sx={{ display: 'grid', gridTemplateColumns: { xs: 1, sm: 2 }, gap: 2 }}>
          <Box>
            <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 0.5 }}>
              🎯 Be Specific
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Define clear target criteria for better lead quality
            </Typography>
          </Box>
          <Box>
            <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 0.5 }}>
              📍 Location Matters
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Use postcodes and distance for targeted local searches
            </Typography>
          </Box>
          <Box>
            <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 0.5 }}>
              ⏱️ Start Small
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Begin with 50-100 leads to test your approach
            </Typography>
          </Box>
          <Box>
            <Typography variant="subtitle2" sx={{ fontWeight: 600, mb: 0.5 }}>
              ✅ Track Results
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Monitor success rates to refine future campaigns
            </Typography>
          </Box>
        </Box>
      </Paper>
    </Container>
  );
};

export default CampaignCreate;
