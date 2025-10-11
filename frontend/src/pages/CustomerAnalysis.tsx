import React, { useState, useEffect } from 'react';
import {
  Container,
  Paper,
  Typography,
  Box,
  Button,
  Grid,
  Card,
  CardContent,
  Chip,
  LinearProgress,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  Alert,
  CircularProgress,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  ArrowBack as ArrowBackIcon,
  Assessment as AssessmentIcon,
  TrendingUp as TrendingUpIcon,
  Business as BusinessIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  Refresh as RefreshIcon,
  Download as DownloadIcon
} from '@mui/icons-material';
import { useNavigate, useParams } from 'react-router-dom';
import { customerAPI } from '../services/api';
import AIAnalysisDashboard from '../components/AIAnalysisDashboard';

const CustomerAnalysis: React.FC = () => {
  const navigate = useNavigate();
  const { id } = useParams<{ id: string }>();
  const [customer, setCustomer] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    if (id) {
      loadCustomer();
    }
  }, [id]);

  const loadCustomer = async () => {
    try {
      setLoading(true);
      const response = await customerAPI.get(id!);
      setCustomer(response.data);
    } catch (err) {
      setError('Failed to load customer data');
      console.error('Error loading customer:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleAnalysisComplete = async (analysis: any) => {
    try {
      // Update customer with new analysis
      const updatedCustomer = {
        ...customer,
        ai_analysis: analysis,
        lead_score: analysis.analysis?.lead_score || customer.lead_score
      };
      
      await customerAPI.update(id!, updatedCustomer);
      setCustomer(updatedCustomer);
    } catch (err) {
      console.error('Error updating customer with analysis:', err);
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return '#4caf50';
    if (score >= 60) return '#ff9800';
    return '#f44336';
  };

  const getUrgencyColor = (urgency: string) => {
    switch (urgency?.toLowerCase()) {
      case 'high': return 'error';
      case 'medium': return 'warning';
      case 'low': return 'success';
      default: return 'default';
    }
  };

  const AnalysisCard: React.FC<{ title: string; children: React.ReactNode; icon?: React.ReactNode }> = ({
    title,
    children,
    icon
  }) => (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          {icon}
          <Typography variant="h6" sx={{ ml: icon ? 1 : 0 }}>
            {title}
          </Typography>
        </Box>
        {children}
      </CardContent>
    </Card>
  );

  const renderExistingAnalysis = () => {
    if (!customer?.ai_analysis) return null;

    const analysis = customer.ai_analysis.analysis || customer.ai_analysis;

    return (
      <Grid container spacing={3}>
        {/* Lead Score Overview */}
        <Grid item xs={12} md={6}>
          <AnalysisCard
            title="Lead Score"
            icon={<AssessmentIcon color="primary" />}
          >
            <Box sx={{ mb: 2 }}>
              <LinearProgress
                variant="determinate"
                value={analysis.lead_score || 0}
                sx={{
                  height: 20,
                  borderRadius: 10,
                  backgroundColor: '#e0e0e0',
                  '& .MuiLinearProgress-bar': {
                    backgroundColor: getScoreColor(analysis.lead_score || 0),
                    borderRadius: 10
                  }
                }}
              />
              <Typography variant="h4" sx={{ textAlign: 'center', mt: 1 }}>
                {analysis.lead_score || 0}/100
              </Typography>
            </Box>
            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', justifyContent: 'center' }}>
              <Chip
                label={analysis.urgency || 'Unknown'}
                color={getUrgencyColor(analysis.urgency || '')}
              />
              <Chip
                label={analysis.size_assessment || 'Unknown Size'}
                variant="outlined"
              />
            </Box>
          </AnalysisCard>
        </Grid>

        {/* Company Overview */}
        <Grid item xs={12} md={6}>
          <AnalysisCard
            title="Company Overview"
            icon={<BusinessIcon color="primary" />}
          >
            <Typography variant="body2" sx={{ mb: 2 }}>
              {analysis.company_overview || 'No overview available'}
            </Typography>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
              <Typography variant="body2">Industry:</Typography>
              <Typography variant="body2" fontWeight="bold">
                {analysis.industry_analysis || 'Unknown'}
              </Typography>
            </Box>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
              <Typography variant="body2">Growth Potential:</Typography>
              <Typography variant="body2" fontWeight="bold">
                {analysis.growth_potential || 'Unknown'}
              </Typography>
            </Box>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
              <Typography variant="body2">Budget Estimate:</Typography>
              <Typography variant="body2" fontWeight="bold">
                {analysis.budget_estimate || 'Unknown'}
              </Typography>
            </Box>
            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
              <Typography variant="body2">Timeline:</Typography>
              <Typography variant="body2" fontWeight="bold">
                {analysis.timeline || 'Unknown'}
              </Typography>
            </Box>
          </AnalysisCard>
        </Grid>

        {/* IT Infrastructure Needs */}
        <Grid item xs={12}>
          <AnalysisCard
            title="IT Infrastructure Assessment"
            icon={<TrendingUpIcon color="primary" />}
          >
            <Typography variant="body2">
              {analysis.it_needs_assessment || 'No assessment available'}
            </Typography>
          </AnalysisCard>
        </Grid>

        {/* Opportunities and Risks */}
        <Grid item xs={12} md={6}>
          <AnalysisCard
            title="Opportunities"
            icon={<CheckCircleIcon color="success" />}
          >
            {analysis.opportunities && analysis.opportunities.length > 0 ? (
              <List dense>
                {analysis.opportunities.map((opportunity: string, index: number) => (
                  <ListItem key={index} sx={{ py: 0.5 }}>
                    <ListItemIcon>
                      <CheckCircleIcon color="success" fontSize="small" />
                    </ListItemIcon>
                    <ListItemText primary={opportunity} />
                  </ListItem>
                ))}
              </List>
            ) : (
              <Typography variant="body2" color="text.secondary">
                No specific opportunities identified
              </Typography>
            )}
          </AnalysisCard>
        </Grid>

        <Grid item xs={12} md={6}>
          <AnalysisCard
            title="Risk Factors"
            icon={<WarningIcon color="warning" />}
          >
            {analysis.risk_factors && analysis.risk_factors.length > 0 ? (
              <List dense>
                {analysis.risk_factors.map((risk: string, index: number) => (
                  <ListItem key={index} sx={{ py: 0.5 }}>
                    <ListItemIcon>
                      <WarningIcon color="warning" fontSize="small" />
                    </ListItemIcon>
                    <ListItemText primary={risk} />
                  </ListItem>
                ))}
              </List>
            ) : (
              <Typography variant="body2" color="text.secondary">
                No significant risk factors identified
              </Typography>
            )}
          </AnalysisCard>
        </Grid>

        {/* Recommended Approach */}
        {analysis.recommended_approach && (
          <Grid item xs={12}>
            <AnalysisCard
              title="Recommended Approach"
              icon={<AssessmentIcon color="primary" />}
            >
              <Typography variant="body2">
                {analysis.recommended_approach}
              </Typography>
            </AnalysisCard>
          </Grid>
        )}

        {/* Decision Makers */}
        {analysis.decision_makers && analysis.decision_makers.length > 0 && (
          <Grid item xs={12} md={6}>
            <AnalysisCard
              title="Key Decision Makers"
              icon={<BusinessIcon color="primary" />}
            >
              <List dense>
                {analysis.decision_makers.map((maker: string, index: number) => (
                  <ListItem key={index}>
                    <ListItemText primary={maker} />
                  </ListItem>
                ))}
              </List>
            </AnalysisCard>
          </Grid>
        )}

        {/* Next Steps */}
        {analysis.next_steps && analysis.next_steps.length > 0 && (
          <Grid item xs={12} md={6}>
            <AnalysisCard
              title="Next Steps"
              icon={<TrendingUpIcon color="primary" />}
            >
              <List dense>
                {analysis.next_steps.map((step: string, index: number) => (
                  <ListItem key={index}>
                    <ListItemText primary={`${index + 1}. ${step}`} />
                  </ListItem>
                ))}
              </List>
            </AnalysisCard>
          </Grid>
        )}
      </Grid>
    );
  };

  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
          <CircularProgress />
          <Typography sx={{ ml: 2 }}>Loading customer analysis...</Typography>
        </Box>
      </Container>
    );
  }

  if (error || !customer) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
        <Alert severity="error" sx={{ mb: 2 }}>
          {error || 'Customer not found'}
        </Alert>
        <Button
          variant="contained"
          startIcon={<ArrowBackIcon />}
          onClick={() => navigate('/customers')}
        >
          Back to Customers
        </Button>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      {/* Header */}
      <Box sx={{ display: 'flex', alignItems: 'center', mb: 3 }}>
        <IconButton
          onClick={() => navigate('/customers')}
          sx={{ mr: 2 }}
        >
          <ArrowBackIcon />
        </IconButton>
        <Box sx={{ flexGrow: 1 }}>
          <Typography variant="h4" component="h1">
            AI Analysis: {customer.company_name}
          </Typography>
          <Typography variant="subtitle1" color="text.secondary">
            {customer.name} • {customer.email}
          </Typography>
        </Box>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Tooltip title="Refresh Analysis">
            <IconButton onClick={loadCustomer}>
              <RefreshIcon />
            </IconButton>
          </Tooltip>
          <Tooltip title="Download Report">
            <IconButton>
              <DownloadIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {/* Customer Info Card */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Grid container spacing={3}>
          <Grid item xs={12} md={6}>
            <Typography variant="h6" gutterBottom>Customer Information</Typography>
            <Typography variant="body2"><strong>Company:</strong> {customer.company_name}</Typography>
            <Typography variant="body2"><strong>Contact:</strong> {customer.name}</Typography>
            <Typography variant="body2"><strong>Email:</strong> {customer.email}</Typography>
            <Typography variant="body2"><strong>Phone:</strong> {customer.phone || 'Not provided'}</Typography>
          </Grid>
          <Grid item xs={12} md={6}>
            <Typography variant="h6" gutterBottom>Company Details</Typography>
            <Typography variant="body2"><strong>Industry:</strong> {customer.industry || 'Not specified'}</Typography>
            <Typography variant="body2"><strong>Website:</strong> {customer.website || 'Not provided'}</Typography>
            <Typography variant="body2"><strong>Address:</strong> {customer.address || 'Not provided'}</Typography>
            {customer.company_number && (
              <Typography variant="body2"><strong>Company Number:</strong> {customer.company_number}</Typography>
            )}
          </Grid>
        </Grid>
      </Paper>

      <Divider sx={{ mb: 3 }} />

      {/* Analysis Content */}
      {customer.ai_analysis ? (
        renderExistingAnalysis()
      ) : (
        <Box>
          <Alert severity="info" sx={{ mb: 3 }}>
            No AI analysis available for this customer. Run a new analysis to get insights.
          </Alert>
          
          {/* AI Analysis Dashboard for new analysis */}
          <AIAnalysisDashboard
            companyData={customer}
            onAnalysisComplete={handleAnalysisComplete}
          />
        </Box>
      )}
    </Container>
  );
};

export default CustomerAnalysis;


