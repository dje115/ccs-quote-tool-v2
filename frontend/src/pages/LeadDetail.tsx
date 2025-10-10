import React, { useEffect, useState } from 'react';
import {
  Container,
  Paper,
  Typography,
  Box,
  Grid,
  Chip,
  Button,
  Card,
  CardContent,
  Divider,
  IconButton,
  Alert
} from '@mui/material';
import {
  ArrowBack as BackIcon,
  Phone as PhoneIcon,
  Email as EmailIcon,
  Language as WebsiteIcon,
  Business as BusinessIcon,
  TrendingUp as ConvertIcon
} from '@mui/icons-material';
import { useNavigate, useParams } from 'react-router-dom';
import { leadAPI, customerAPI } from '../services/api';

const LeadDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [lead, setLead] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [converting, setConverting] = useState(false);

  useEffect(() => {
    if (id) {
      loadLead();
    }
  }, [id]);

  const loadLead = async () => {
    try {
      setLoading(true);
      const response = await leadAPI.get(id!);
      setLead(response.data);
    } catch (error) {
      console.error('Error loading lead:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleConvertToCustomer = async () => {
    if (!lead) return;

    setConverting(true);
    try {
      // Create customer from lead
      const customerData = {
        company_name: lead.company_name,
        website: lead.website,
        business_type: lead.business_type,
        business_sector: lead.business_sector,
        employee_count_estimate: lead.employee_count_estimate,
        annual_revenue_estimate: lead.annual_revenue_estimate,
        contact_email: lead.contact_email,
        contact_phone: lead.contact_phone,
        status: 'active',
        lead_score: lead.lead_score,
        notes: `Converted from lead: ${lead.notes || ''}`
      };

      const response = await customerAPI.create(customerData);
      
      // Update lead status
      await leadAPI.update(id!, { status: 'converted' });

      // Navigate to new customer
      navigate(`/customers/${response.data.id}`);
    } catch (error) {
      console.error('Error converting lead:', error);
      alert('Failed to convert lead to customer');
    } finally {
      setConverting(false);
    }
  };

  if (loading) {
    return (
      <Container maxWidth="lg">
        <Typography>Loading...</Typography>
      </Container>
    );
  }

  if (!lead) {
    return (
      <Container maxWidth="lg">
        <Typography>Lead not found</Typography>
      </Container>
    );
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'new':
        return 'info';
      case 'contacted':
        return 'warning';
      case 'qualified':
        return 'success';
      case 'converted':
        return 'success';
      case 'disqualified':
        return 'error';
      default:
        return 'default';
    }
  };

  return (
    <Container maxWidth="lg">
      <Box sx={{ mb: 3, display: 'flex', alignItems: 'center', gap: 2 }}>
        <IconButton onClick={() => navigate('/leads')}>
          <BackIcon />
        </IconButton>
        <Typography variant="h4" component="h1" sx={{ flexGrow: 1 }}>
          {lead.company_name}
        </Typography>
        {lead.status !== 'converted' && (
          <Button
            variant="contained"
            color="success"
            startIcon={<ConvertIcon />}
            onClick={handleConvertToCustomer}
            disabled={converting}
          >
            {converting ? 'Converting...' : 'Convert to Customer'}
          </Button>
        )}
      </Box>

      {lead.status === 'converted' && (
        <Alert severity="success" sx={{ mb: 3 }}>
          This lead has been converted to a customer
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* Lead Information */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 3, mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              Company Information
            </Typography>
            <Divider sx={{ mb: 2 }} />

            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                  <BusinessIcon color="action" />
                  <Box>
                    <Typography variant="caption" color="text.secondary">
                      Business Sector
                    </Typography>
                    <Typography>{lead.business_sector || 'N/A'}</Typography>
                  </Box>
                </Box>
              </Grid>

              <Grid item xs={12} sm={6}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                  <BusinessIcon color="action" />
                  <Box>
                    <Typography variant="caption" color="text.secondary">
                      Source
                    </Typography>
                    <Typography>{lead.source || 'N/A'}</Typography>
                  </Box>
                </Box>
              </Grid>

              {lead.website && (
                <Grid item xs={12}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                    <WebsiteIcon color="action" />
                    <Box>
                      <Typography variant="caption" color="text.secondary">
                        Website
                      </Typography>
                      <Typography>
                        <a href={lead.website} target="_blank" rel="noopener noreferrer">
                          {lead.website}
                        </a>
                      </Typography>
                    </Box>
                  </Box>
                </Grid>
              )}

              {lead.contact_email && (
                <Grid item xs={12} sm={6}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                    <EmailIcon color="action" />
                    <Box>
                      <Typography variant="caption" color="text.secondary">
                        Email
                      </Typography>
                      <Typography>{lead.contact_email}</Typography>
                    </Box>
                  </Box>
                </Grid>
              )}

              {lead.contact_phone && (
                <Grid item xs={12} sm={6}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                    <PhoneIcon color="action" />
                    <Box>
                      <Typography variant="caption" color="text.secondary">
                        Phone
                      </Typography>
                      <Typography>{lead.contact_phone}</Typography>
                    </Box>
                  </Box>
                </Grid>
              )}

              {lead.employee_count_estimate && (
                <Grid item xs={12} sm={6}>
                  <Typography variant="caption" color="text.secondary">
                    Employees (Estimate)
                  </Typography>
                  <Typography>{lead.employee_count_estimate}</Typography>
                </Grid>
              )}

              {lead.annual_revenue_estimate && (
                <Grid item xs={12} sm={6}>
                  <Typography variant="caption" color="text.secondary">
                    Annual Revenue (Estimate)
                  </Typography>
                  <Typography>£{lead.annual_revenue_estimate?.toLocaleString()}</Typography>
                </Grid>
              )}
            </Grid>

            {lead.notes && (
              <Box sx={{ mt: 3 }}>
                <Typography variant="caption" color="text.secondary">
                  Notes
                </Typography>
                <Typography>{lead.notes}</Typography>
              </Box>
            )}
          </Paper>

          {/* AI Analysis */}
          {lead.ai_analysis && (
            <Paper sx={{ p: 3 }}>
              <Typography variant="h6" gutterBottom>
                AI Analysis
              </Typography>
              <Divider sx={{ mb: 2 }} />
              <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>
                {lead.ai_analysis}
              </Typography>
            </Paper>
          )}
        </Grid>

        {/* Sidebar */}
        <Grid item xs={12} md={4}>
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Status
              </Typography>
              <Chip
                label={lead.status}
                color={getStatusColor(lead.status)}
                sx={{ mb: 2 }}
              />

              <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
                Lead Score
              </Typography>
              <Chip
                label={lead.lead_score || 0}
                color={lead.lead_score >= 70 ? 'success' : lead.lead_score >= 40 ? 'warning' : 'default'}
                size="large"
              />

              <Typography variant="caption" display="block" sx={{ mt: 2 }} color="text.secondary">
                Created: {new Date(lead.created_at).toLocaleDateString()}
              </Typography>
            </CardContent>
          </Card>

          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Quick Actions
              </Typography>
              {lead.status !== 'converted' && (
                <>
                  <Button
                    fullWidth
                    variant="contained"
                    color="success"
                    sx={{ mb: 1 }}
                    startIcon={<ConvertIcon />}
                    onClick={handleConvertToCustomer}
                    disabled={converting}
                  >
                    Convert to Customer
                  </Button>
                  <Button
                    fullWidth
                    variant="outlined"
                    sx={{ mb: 1 }}
                    onClick={() => leadAPI.update(id!, { status: 'contacted' })}
                  >
                    Mark as Contacted
                  </Button>
                  <Button
                    fullWidth
                    variant="outlined"
                    sx={{ mb: 1 }}
                    onClick={() => leadAPI.update(id!, { status: 'qualified' })}
                  >
                    Mark as Qualified
                  </Button>
                  <Button
                    fullWidth
                    variant="outlined"
                    color="error"
                    onClick={() => leadAPI.update(id!, { status: 'disqualified' })}
                  >
                    Disqualify
                  </Button>
                </>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Container>
  );
};

export default LeadDetail;

