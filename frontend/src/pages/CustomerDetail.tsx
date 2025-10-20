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
  List,
  ListItem,
  ListItemText,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Alert,
  CircularProgress,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tabs,
  Tab,
  FormControlLabel,
  Checkbox
} from '@mui/material';
import {
  ArrowBack as BackIcon,
  Edit as EditIcon,
  Add as AddIcon,
  Phone as PhoneIcon,
  Email as EmailIcon,
  Language as WebsiteIcon,
  Language as LanguageIcon,
  Business as BusinessIcon,
  Psychology as AiIcon,
  ExpandMore as ExpandMoreIcon,
  Place as PlaceIcon,
  Assessment as AssessmentIcon,
  AccountBalance as AccountBalanceIcon,
  People as PeopleIcon,
  CompareArrows as CompareArrowsIcon,
  Description as DescriptionIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Info as InfoIcon,
  Lightbulb as LightbulbIcon,
  AutoAwesome as SparkleIcon
} from '@mui/icons-material';
import { useNavigate, useParams } from 'react-router-dom';
import { customerAPI, contactAPI, quoteAPI } from '../services/api';
import api from '../services/api';
import CustomerOverviewTab from '../components/CustomerOverviewTab';
import ActivityCenter from '../components/ActivityCenter';
import ContactDialog from '../components/ContactDialog';

const CustomerDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [customer, setCustomer] = useState<any>(null);
  const [contacts, setContacts] = useState<any[]>([]);
  const [quotes, setQuotes] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [addContactOpen, setAddContactOpen] = useState(false);
  const [editingContact, setEditingContact] = useState<any>(null);
  const [aiAnalysisLoading, setAiAnalysisLoading] = useState(false);
  const [aiAnalysisError, setAiAnalysisError] = useState<string | null>(null);
  const [aiAnalysisSuccess, setAiAnalysisSuccess] = useState<string | null>(null);
  const [currentTab, setCurrentTab] = useState(() => {
    // Restore tab from localStorage on component mount
    const savedTab = localStorage.getItem('customerDetailTab');
    return savedTab ? parseInt(savedTab) : 0;
  });

  useEffect(() => {
    if (id) {
      loadCustomerData();
    }
  }, [id]);

  // Poll for AI analysis completion (persists across navigation like campaigns)
  useEffect(() => {
    if (!customer) return;
    
    // Check if analysis is running or queued
    const isAnalysisActive = customer.ai_analysis_status === 'running' || customer.ai_analysis_status === 'queued';
    
    if (isAnalysisActive) {
      console.log(`AI analysis is ${customer.ai_analysis_status} for ${customer.company_name}, polling for completion...`);
      
      const pollInterval = setInterval(async () => {
        try {
          const customerRes = await customerAPI.get(id!);
          const updatedCustomer = customerRes.data;
          
          // Check if status changed to completed
          if (updatedCustomer.ai_analysis_status === 'completed') {
            console.log('AI analysis completed! Reloading data...');
            clearInterval(pollInterval);
            setAiAnalysisSuccess('AI analysis completed successfully!');
            await loadCustomerData();
            setTimeout(() => setAiAnalysisSuccess(null), 5000);
          } else if (updatedCustomer.ai_analysis_status === 'failed') {
            console.log('AI analysis failed.');
            clearInterval(pollInterval);
            setAiAnalysisError('AI analysis failed. Please try again.');
            await loadCustomerData();
            setTimeout(() => setAiAnalysisError(null), 5000);
          }
        } catch (pollError) {
          console.error('Error polling for analysis completion:', pollError);
        }
      }, 3000);
      
      // Cleanup on unmount or when customer changes
      return () => {
        clearInterval(pollInterval);
      };
    }
  }, [customer?.ai_analysis_status, id]);

  const loadCustomerData = async () => {
    try {
      setLoading(true);
      const [customerRes, contactsRes, quotesRes] = await Promise.all([
        customerAPI.get(id!),
        contactAPI.list(id!),
        quoteAPI.list({ customer_id: id })
      ]);

      setCustomer(customerRes.data);
      setContacts(contactsRes.data);
      setQuotes(quotesRes.data);
    } catch (error) {
      console.error('Error loading customer data:', error);
    } finally {
      setLoading(false);
    }
  };

  const runAiAnalysis = async () => {
    try {
      setAiAnalysisLoading(true);
      setAiAnalysisError(null);
      setAiAnalysisSuccess(null);

      // Queue the background task
      const response = await customerAPI.runAiAnalysis(id!);
      
      if (response.data.success) {
        setAiAnalysisSuccess('AI analysis running in background. You can navigate away - it will continue processing.');
        
        // Reload to show the 'queued' status
        await loadCustomerData();
        
        // Don't manage polling here - it will be handled by useEffect based on status
        setAiAnalysisLoading(false);
        
        // Clear success message after 5 seconds
        setTimeout(() => setAiAnalysisSuccess(null), 5000);
      } else {
        setAiAnalysisError(response.data.error || 'Failed to queue AI analysis');
        setAiAnalysisLoading(false);
      }
    } catch (error: any) {
      console.error('Error running AI analysis:', error);
      setAiAnalysisError(error.response?.data?.detail || 'Failed to run AI analysis');
      setAiAnalysisLoading(false);
    }
  };

  const handleConfirmRegistration = async (confirmed: boolean) => {
    try {
      await customerAPI.confirmRegistration(id!, confirmed);
      // Update local state
      setCustomer({ ...customer, registration_confirmed: confirmed });
    } catch (error: any) {
      console.error('Error updating registration confirmation:', error);
      setAiAnalysisError('Failed to update registration confirmation');
    }
  };

  const handleAddDirectorAsContact = async (director: any) => {
    try {
      // Parse name from Companies House format: "Surname, FirstNames MiddleNames"
      // We want: first_name = "FirstName" (just first name), last_name = "Surname"
      let firstName = '';
      let lastName = '';
      
      if (director.name.includes(',')) {
        // Format: "Barr, Christopher Ian Ernest" -> first: "Christopher", last: "Barr"
        const [surnameWithComma, ...restParts] = director.name.split(',');
        lastName = surnameWithComma.trim();
        
        // Get just the first name from "Christopher Ian Ernest"
        const firstNames = restParts.join(',').trim();
        const firstNameParts = firstNames.split(' ');
        firstName = firstNameParts[0] || ''; // Just take the first name
      } else {
        // Fallback: if no comma, assume "FirstName LastName" format
        const nameParts = director.name.split(' ');
        firstName = nameParts[0] || '';
        lastName = nameParts.slice(1).join(' ') || nameParts[0];
      }
      
      // Create contact from director
      const contactData = {
        customer_id: id!,
        first_name: firstName,
        last_name: lastName,
        job_title: director.officer_role || 'Director',
        role: 'other',  // Use lowercase with underscore to match the enum
        email: null,
        phone: null,
        is_primary: false,
        notes: `Added from Companies House. Appointed: ${director.appointed_on || 'Unknown'}. Nationality: ${director.nationality || 'Unknown'}.`
      };

      console.log('Sending contact data:', contactData);
      const response = await contactAPI.create(contactData);
      console.log('Contact created successfully:', response.data);
      
      await loadCustomerData(); // Reload to show new contact
      setAiAnalysisSuccess(`Added ${director.name} as a contact`);
      setTimeout(() => setAiAnalysisSuccess(null), 3000);
    } catch (error: any) {
      console.error('Full error:', error);
      console.error('Error response:', error.response);
      console.error('Error data:', error.response?.data);
      setAiAnalysisError(
        error.response?.data?.detail 
        ? (typeof error.response.data.detail === 'string' 
          ? error.response.data.detail 
          : JSON.stringify(error.response.data.detail))
        : 'Failed to add director as contact'
      );
      setTimeout(() => setAiAnalysisError(null), 5000);
    }
  };

  const handleSaveContact = async (contactData: any) => {
    if (editingContact) {
      // Update existing contact
      await contactAPI.update(editingContact.id, contactData);
    } else {
      // Create new contact
      await contactAPI.create(contactData);
    }
    await loadCustomerData(); // Reload contacts
    setAddContactOpen(false);
    setEditingContact(null);
  };

  const handleEditContact = (contact: any) => {
    setEditingContact(contact);
    setAddContactOpen(true);
  };

  const handleCloseContactDialog = () => {
    setAddContactOpen(false);
    setEditingContact(null);
  };

  const handleAddCompetitorsToCampaign = async (competitor?: string) => {
    // Determine which competitors to add
    const competitorsToAdd = competitor ? [competitor] : 
      (Array.isArray(customer?.ai_analysis_raw?.competitors) ? customer.ai_analysis_raw.competitors : []);
    
    if (competitorsToAdd.length === 0) {
      setAiAnalysisError('No competitors data available');
      setTimeout(() => setAiAnalysisError(null), 3000);
      return;
    }

    // Navigate to Company List Import page with competitors pre-filled
    navigate('/campaigns/import', {
      state: {
        companies: competitorsToAdd,
        source: `Competitors of ${customer?.company_name}`
      }
    });
  };

  const handleStatusChange = async (newStatus: string) => {
    try {
      await customerAPI.update(id!, { status: newStatus });
      setAiAnalysisSuccess(`Status updated to ${newStatus}`);
      setTimeout(() => setAiAnalysisSuccess(null), 3000);
      // Reload customer data to reflect new status
      await loadCustomerData();
    } catch (error) {
      console.error('Failed to update status:', error);
      setAiAnalysisError('Failed to update status');
      setTimeout(() => setAiAnalysisError(null), 5000);
    }
  };

  const handleCompetitorToggle = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const isCompetitor = event.target.checked;
    
    // Optimistic update - update local state immediately
    setCustomer((prev: any) => ({
      ...prev,
      is_competitor: isCompetitor
    }));
    
    try {
      await customerAPI.update(id!, { is_competitor: isCompetitor });
      setAiAnalysisSuccess(isCompetitor ? 'Marked as competitor' : 'Removed competitor flag');
      setTimeout(() => setAiAnalysisSuccess(null), 3000);
    } catch (error) {
      console.error('Failed to update competitor status:', error);
      // Revert optimistic update on error
      setCustomer((prev: any) => ({
        ...prev,
        is_competitor: !isCompetitor
      }));
      setAiAnalysisError('Failed to update competitor status');
      setTimeout(() => setAiAnalysisError(null), 5000);
    }
  };

  if (loading || !customer) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4, display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '400px' }}>
        <Box sx={{ textAlign: 'center' }}>
          {loading ? (
            <>
              <CircularProgress />
              <Typography sx={{ mt: 2 }}>Loading customer data...</Typography>
            </>
          ) : (
            <Typography>Customer not found</Typography>
          )}
        </Box>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg">
      <Box sx={{ mb: 3, display: 'flex', alignItems: 'center', gap: 2 }}>
        <IconButton onClick={() => navigate('/customers')}>
          <BackIcon />
        </IconButton>
        <Typography variant="h4" component="h1" sx={{ flexGrow: 1 }}>
          {customer?.company_name || 'Unknown Customer'}
        </Typography>
        <FormControlLabel
          control={
            <Checkbox
              checked={customer?.is_competitor || false}
              onChange={handleCompetitorToggle}
              color="warning"
            />
          }
          label={
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
              <BusinessIcon fontSize="small" />
              <Typography variant="body2">Competitor</Typography>
            </Box>
          }
        />
        <Button
          variant="contained"
          color="primary"
          startIcon={(aiAnalysisLoading || customer?.ai_analysis_status === 'running' || customer?.ai_analysis_status === 'queued') ? 
            <CircularProgress size={20} color="inherit" /> : <AiIcon />}
          onClick={runAiAnalysis}
          disabled={aiAnalysisLoading || customer?.ai_analysis_status === 'running' || customer?.ai_analysis_status === 'queued'}
        >
          {customer?.ai_analysis_status === 'running' ? 'Running...' : 
           customer?.ai_analysis_status === 'queued' ? 'Queued...' : 
           aiAnalysisLoading ? 'Analyzing...' : 'AI Analysis'}
        </Button>
        <Button
          variant="outlined"
          startIcon={<EditIcon />}
          onClick={() => navigate(`/customers/${id}/edit`)}
        >
          Edit
        </Button>
      </Box>
      {/* AI Analysis Alerts */}
      {aiAnalysisError && (
        <Alert severity="error" onClose={() => setAiAnalysisError(null)} sx={{ mb: 2 }}>
          {aiAnalysisError}
        </Alert>
      )}
      {aiAnalysisSuccess && (
        <Alert severity="success" onClose={() => setAiAnalysisSuccess(null)} sx={{ mb: 2 }}>
          {aiAnalysisSuccess}
        </Alert>
      )}
      {/* Modern Tabbed Interface */}
      <Paper sx={{ mb: 3 }}>
        {/* First Row of Tabs - Intelligence & Data */}
        <Tabs 
          value={currentTab > 6 ? false : currentTab} 
          onChange={(e, newValue) => {
            setCurrentTab(newValue);
            localStorage.setItem('customerDetailTab', String(newValue));
          }}
          variant="scrollable"
          scrollButtons="auto"
          sx={{
            borderBottom: 1,
            borderColor: 'divider',
            '& .MuiTab-root': {
              minHeight: 64,
              fontSize: '0.95rem',
              fontWeight: 500,
              textTransform: 'none',
            },
            '& .Mui-selected': {
              color: '#1976d2',
            },
          }}
        >
          <Tab icon={<BusinessIcon />} iconPosition="start" label="Overview" />
          <Tab icon={<LightbulbIcon />} iconPosition="start" label="Discovery Intelligence" />
          <Tab icon={<AssessmentIcon />} iconPosition="start" label="AI Analysis" />
          <Tab icon={<AccountBalanceIcon />} iconPosition="start" label="Financial Data" />
          <Tab icon={<PlaceIcon />} iconPosition="start" label="Addresses" />
          <Tab icon={<PeopleIcon />} iconPosition="start" label="Directors" />
          <Tab icon={<CompareArrowsIcon />} iconPosition="start" label="Business Intelligence" />
        </Tabs>
        
        {/* Second Row of Tabs - Activity & Documents */}
        <Tabs
          value={currentTab > 6 ? currentTab - 7 : false}
          onChange={(e, newValue) => {
            const tabIndex = newValue + 7;
            setCurrentTab(tabIndex);
            localStorage.setItem('customerDetailTab', String(tabIndex));
          }}
          variant="scrollable"
          scrollButtons="auto"
          sx={{
            borderBottom: 1,
            borderColor: 'divider',
            bgcolor: '#f5f5f5',
            '& .MuiTab-root': {
              minHeight: 56,
              fontSize: '0.9rem',
              fontWeight: 500,
              textTransform: 'none',
            },
            '& .Mui-selected': {
              color: '#1976d2',
              bgcolor: '#fff',
            },
          }}
        >
          <Tab icon={<PhoneIcon />} iconPosition="start" label="Activity" />
          <Tab icon={<DescriptionIcon />} iconPosition="start" label="Quotes" />
        </Tabs>
      </Paper>
      {/* Tab Panel 0: Overview - World-Class AI-Powered CRM */}
      {currentTab === 0 && customer && (
        <CustomerOverviewTab
          customer={customer}
          contacts={contacts}
          onAddContact={() => setAddContactOpen(true)}
          onEditContact={handleEditContact}
          onConfirmRegistration={handleConfirmRegistration}
          onStatusChange={handleStatusChange}
        />
      )}
      {/* Tab Panel 1: Discovery Intelligence - Data from Campaign Phase */}
      {currentTab === 1 && customer && (
        <Box>
          {/* Quick Telesales Summary */}
          {customer.description && (
            <Paper sx={{ p: 3, mb: 3, bgcolor: 'success.light', border: '2px solid', borderColor: 'success.main' }}>
              <Typography variant="h6" gutterBottom sx={{ color: 'success.dark', fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: 1 }}>
                <PhoneIcon /> Quick Telesales Summary
              </Typography>
              <Divider sx={{ mb: 2, borderColor: 'success.main' }} />
              <Typography 
                variant="body2" 
                sx={{ 
                  whiteSpace: 'pre-line',
                  '& strong': { fontWeight: 'bold', color: 'success.dark' }
                }}
                dangerouslySetInnerHTML={{
                  __html: customer.description.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
                }}
              />
            </Paper>
          )}

          {/* Discovery AI Analysis */}
          {customer.ai_analysis_raw && typeof customer.ai_analysis_raw === 'object' && (
            <Paper sx={{ p: 3, mb: 3 }}>
              <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <AiIcon /> Discovery AI Analysis
              </Typography>
              <Divider sx={{ mb: 2 }} />
              <Typography variant="caption" color="text.secondary" sx={{ mb: 2, display: 'block' }}>
                {customer.ai_analysis_raw.light_analysis ? 
                  'Generated during campaign discovery phase (Light Analysis)' : 
                  'Generated during campaign discovery phase'}
              </Typography>

              {/* Light Analysis (from campaign execution) */}
              {customer.ai_analysis_raw.light_analysis && (
                <Box sx={{ mb: 3, p: 2, bgcolor: '#f3f4f6', borderRadius: 2, border: '1px solid #e5e7eb' }}>
                  <Typography variant="subtitle2" color="primary" gutterBottom sx={{ fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: 1 }}>
                    <SparkleIcon /> Quick Business Analysis
                  </Typography>
                  <Typography variant="caption" color="text.secondary" sx={{ mb: 2, display: 'block' }}>
                    Light analysis generated during campaign execution for quick insights
                  </Typography>
                  <Typography variant="body2" sx={{ whiteSpace: 'pre-line', lineHeight: 1.6 }}>
                    {customer.ai_analysis_raw.light_analysis.light_analysis || customer.ai_analysis_raw.light_analysis}
                  </Typography>
                </Box>
              )}

              {/* Company Profile */}
              {customer.ai_analysis_raw.company_profile && (
                <Box sx={{ mb: 3 }}>
                  <Typography variant="subtitle2" color="primary" gutterBottom>
                    Company Profile
                  </Typography>
                  <Typography variant="body2" paragraph>
                    {customer.ai_analysis_raw.company_profile}
                  </Typography>
                </Box>
              )}

              {/* Key Metrics Grid */}
              <Grid container spacing={2} sx={{ mb: 3 }}>
                {customer.ai_analysis_raw.business_sector && (
                  <Grid
                    size={{
                      xs: 12,
                      sm: 6
                    }}>
                    <Typography variant="caption" color="text.secondary">Business Sector</Typography>
                    <Typography variant="body2">{customer.ai_analysis_raw.business_sector}</Typography>
                  </Grid>
                )}
                {customer.ai_analysis_raw.business_size_category && (
                  <Grid
                    size={{
                      xs: 12,
                      sm: 6
                    }}>
                    <Typography variant="caption" color="text.secondary">Company Size</Typography>
                    <Typography variant="body2">{customer.ai_analysis_raw.business_size_category}</Typography>
                  </Grid>
                )}
                {customer.ai_analysis_raw.estimated_employees && (
                  <Grid
                    size={{
                      xs: 12,
                      sm: 6
                    }}>
                    <Typography variant="caption" color="text.secondary">Estimated Employees</Typography>
                    <Typography variant="body2">{customer.ai_analysis_raw.estimated_employees}</Typography>
                  </Grid>
                )}
                {customer.ai_analysis_raw.estimated_revenue && (
                  <Grid
                    size={{
                      xs: 12,
                      sm: 6
                    }}>
                    <Typography variant="caption" color="text.secondary">Estimated Revenue</Typography>
                    <Typography variant="body2">{customer.ai_analysis_raw.estimated_revenue}</Typography>
                  </Grid>
                )}
                {customer.ai_analysis_raw.technology_maturity && (
                  <Grid
                    size={{
                      xs: 12,
                      sm: 6
                    }}>
                    <Typography variant="caption" color="text.secondary">Technology Maturity</Typography>
                    <Typography variant="body2">{customer.ai_analysis_raw.technology_maturity}</Typography>
                  </Grid>
                )}
                {(customer.ai_analysis_raw.service_budget_estimate || customer.ai_analysis_raw.it_budget_estimate) && (
                  <Grid
                    size={{
                      xs: 12,
                      sm: 6
                    }}>
                    <Typography variant="caption" color="text.secondary">Budget Estimate</Typography>
                    <Typography variant="body2">{customer.ai_analysis_raw.service_budget_estimate || customer.ai_analysis_raw.it_budget_estimate}</Typography>
                  </Grid>
                )}
                {customer.ai_analysis_raw.growth_potential && (
                  <Grid
                    size={{
                      xs: 12,
                      sm: 6
                    }}>
                    <Typography variant="caption" color="text.secondary">Growth Potential</Typography>
                    <Chip 
                      label={customer.ai_analysis_raw.growth_potential} 
                      color={
                        customer.ai_analysis_raw.growth_potential === 'High' ? 'success' : 
                        customer.ai_analysis_raw.growth_potential === 'Medium' ? 'warning' : 'default'
                      }
                      size="small"
                    />
                  </Grid>
                )}
              </Grid>

              {/* Detailed Sections */}
              {customer.ai_analysis_raw.primary_business_activities && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" color="primary" gutterBottom>
                    Primary Business Activities
                  </Typography>
                  <Typography variant="body2">{customer.ai_analysis_raw.primary_business_activities}</Typography>
                </Box>
              )}

              {customer.ai_analysis_raw.financial_health_analysis && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" color="primary" gutterBottom>
                    Financial Health Analysis
                  </Typography>
                  <Typography variant="body2">{customer.ai_analysis_raw.financial_health_analysis}</Typography>
                </Box>
              )}

              {customer.ai_analysis_raw.technology_needs && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" color="primary" gutterBottom>
                    Needs Assessment
                  </Typography>
                  <Typography variant="body2">{customer.ai_analysis_raw.technology_needs}</Typography>
                </Box>
              )}

              {customer.ai_analysis_raw.actionable_recommendations && Array.isArray(customer.ai_analysis_raw.actionable_recommendations) && customer.ai_analysis_raw.actionable_recommendations.length > 0 && (
                <Box sx={{ mb: 3, p: 2, bgcolor: '#e8f5e9', borderRadius: 2, border: '2px solid #4caf50' }}>
                  <Typography variant="subtitle2" color="success.dark" gutterBottom sx={{ fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: 1 }}>
                    <LightbulbIcon /> How We Can Help This Customer
                  </Typography>
                  <Typography variant="caption" color="text.secondary" sx={{ mb: 2, display: 'block' }}>
                    Actionable recommendations based on our products/services and their needs
                  </Typography>
                  <Box component="ol" sx={{ pl: 2, m: 0 }}>
                    {customer.ai_analysis_raw.actionable_recommendations.map((rec: string, idx: number) => (
                      <Box component="li" key={idx} sx={{ mb: 1 }}>
                        <Typography variant="body2">{rec}</Typography>
                      </Box>
                    ))}
                  </Box>
                </Box>
              )}

              {customer.ai_analysis_raw.opportunities && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" color="success.main" gutterBottom>
                    Business Opportunities
                  </Typography>
                  <Typography variant="body2">{customer.ai_analysis_raw.opportunities}</Typography>
                </Box>
              )}

              {customer.ai_analysis_raw.competitors && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" color="primary" gutterBottom>
                    Competitive Landscape
                  </Typography>
                  <Typography variant="body2">{customer.ai_analysis_raw.competitors}</Typography>
                </Box>
              )}

              {customer.ai_analysis_raw.risks && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" color="error.main" gutterBottom>
                    Risk Factors
                  </Typography>
                  <Typography variant="body2">{customer.ai_analysis_raw.risks}</Typography>
                </Box>
              )}
            </Paper>
          )}

          {/* No Discovery Data */}
          {!customer.description && (!customer.ai_analysis_raw || Object.keys(customer.ai_analysis_raw).length === 0) && (
            <Paper sx={{ p: 3 }}>
              <Alert severity="info">
                No discovery intelligence data available. This customer was not created from a campaign discovery.
              </Alert>
            </Paper>
          )}
        </Box>
      )}
      {/* Tab Panel 2: AI Analysis */}
      {currentTab === 2 && (
        <Box>
          {/* Known Facts Section */}
          <Paper sx={{ p: 3, mb: 3, bgcolor: '#fff8e1', border: '2px solid #ffd54f' }}>
            <Typography variant="h6" gutterBottom sx={{ color: '#f57c00', display: 'flex', alignItems: 'center', gap: 1 }}>
              <InfoIcon /> Known Facts (User-Verified Information)
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
              Add known facts about this company to help improve AI analysis accuracy. These facts will be used in future AI analyses to provide more accurate insights.
            </Typography>
            <TextField
              fullWidth
              multiline
              rows={4}
              value={customer?.known_facts || ''}
              onChange={(e) => {
                // Update local state immediately for better UX
                setCustomer((prev: any) => ({
                  ...prev,
                  known_facts: e.target.value
                }));
              }}
              placeholder="Example:&#10;- Does not have an Irish office (Google Maps incorrect match)&#10;- Main office relocated from London to Manchester in 2023&#10;- Currently migrating to Azure cloud&#10;- Prefers Cisco networking equipment"
              variant="outlined"
              sx={{ bgcolor: 'white' }}
            />
            <Box sx={{ mt: 2, display: 'flex', gap: 2, alignItems: 'center' }}>
              <Button
                variant="contained"
                color="primary"
                onClick={async () => {
                  try {
                    // Send the value, converting empty string to empty to allow clearing
                    const knownFactsValue = customer?.known_facts?.trim() || '';
                    await customerAPI.update(id!, { known_facts: knownFactsValue });
                    setAiAnalysisSuccess('Known facts saved successfully');
                    
                    // Reload customer data to ensure we have the latest
                    const customerRes = await customerAPI.get(id!);
                    setCustomer(customerRes.data);
                    
                    setTimeout(() => setAiAnalysisSuccess(null), 3000);
                  } catch (error) {
                    console.error('Error saving known facts:', error);
                    setAiAnalysisError('Failed to save known facts');
                    setTimeout(() => setAiAnalysisError(null), 5000);
                  }
                }}
              >
                Save Known Facts
              </Button>
              <Alert severity="info" sx={{ flex: 1 }}>
                <strong>Tip:</strong> These facts will be included in the AI prompt the next time you run an analysis.
              </Alert>
            </Box>
          </Paper>

          {/* Business Intelligence */}
          {customer?.ai_analysis_raw && typeof customer.ai_analysis_raw === 'object' ? (
            <Paper sx={{ p: 3, mb: 3 }}>
              <Typography variant="h5" gutterBottom sx={{ color: '#1976d2', display: 'flex', alignItems: 'center', gap: 1 }}>
                <AssessmentIcon /> Business Intelligence
              </Typography>
              <Divider sx={{ mb: 3 }} />
              
              <Grid container spacing={3}>
                <Grid
                  size={{
                    xs: 12,
                    md: 6
                  }}>
                  {customer.ai_analysis_raw.business_sector && (
                    <Box sx={{ mb: 3 }}>
                      <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600 }}>Business Sector</Typography>
                      <br />
                      <Chip label={customer.ai_analysis_raw.business_sector} color="primary" sx={{ mt: 1 }} />
                    </Box>
                  )}
                  {customer.ai_analysis_raw.business_size_category && (
                    <Box sx={{ mb: 3 }}>
                      <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600 }}>Company Size</Typography>
                      <Typography variant="body1" sx={{ mt: 0.5 }}>{customer.ai_analysis_raw.business_size_category}</Typography>
                    </Box>
                  )}
                  {customer.ai_analysis_raw.technology_maturity && (
                    <Box sx={{ mb: 3 }}>
                      <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600 }}>Technology Maturity</Typography>
                      <Typography variant="body1" sx={{ mt: 0.5 }}>{customer.ai_analysis_raw.technology_maturity}</Typography>
                    </Box>
                  )}
                </Grid>
                <Grid
                  size={{
                    xs: 12,
                    md: 6
                  }}>
                  {(customer.ai_analysis_raw.service_budget_estimate || customer.ai_analysis_raw.it_budget_estimate) && (
                    <Box sx={{ mb: 3 }}>
                      <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600 }}>Service Budget Estimate</Typography>
                      <Typography variant="body1" sx={{ mt: 0.5 }}>{customer.ai_analysis_raw.service_budget_estimate || customer.ai_analysis_raw.it_budget_estimate}</Typography>
                    </Box>
                  )}
                  {customer.ai_analysis_raw.growth_potential && (
                    <Box sx={{ mb: 3 }}>
                      <Typography variant="caption" color="text.secondary" sx={{ fontWeight: 600 }}>Growth Potential</Typography>
                      <br />
                      <Chip 
                        label={customer.ai_analysis_raw.growth_potential} 
                        color={
                          String(customer.ai_analysis_raw.growth_potential).toLowerCase() === 'high' ? 'success' :
                          String(customer.ai_analysis_raw.growth_potential).toLowerCase() === 'medium' ? 'warning' : 'default'
                        }
                        sx={{ mt: 1 }}
                      />
                    </Box>
                  )}
                </Grid>
              </Grid>

              {/* AI Company Profile */}
              {customer.ai_analysis_raw.company_profile && (
                <Box sx={{ mt: 4, p: 3, bgcolor: 'grey.50', borderRadius: 2 }}>
                  <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <BusinessIcon color="primary" />
                    AI Company Profile
                  </Typography>
                  <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap', lineHeight: 1.8 }}>
                    {customer.ai_analysis_raw.company_profile}
                  </Typography>
                </Box>
              )}

              {/* Technology Needs */}
              {customer.ai_analysis_raw.technology_needs && (
                <Box sx={{ mt: 3, p: 3, bgcolor: 'primary.50', borderRadius: 2, borderLeft: 4, borderColor: 'primary.main' }}>
                  <Typography variant="h6" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    💻 Technology Needs
                  </Typography>
                  <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap', lineHeight: 1.8 }}>
                    {customer.ai_analysis_raw.technology_needs}
                  </Typography>
                </Box>
              )}
            </Paper>
          ) : (
            <Paper sx={{ p: 3 }}>
              <Alert severity="info">
                No AI analysis data available yet. Click the "AI Analysis" button to generate insights.
              </Alert>
            </Paper>
          )}
        </Box>
      )}
      {/* Tab Panel 3: Financial Data */}
      {currentTab === 3 && (
        <Box>
          {/* Financial Data from Companies House */}
          {customer?.companies_house_data?.accounts_detail && (
            <Paper sx={{ p: 3, mb: 3 }}>
              <Typography variant="h5" gutterBottom sx={{ color: '#1976d2', display: 'flex', alignItems: 'center', gap: 1 }}>
                <AccountBalanceIcon />
                Financial Data (Companies House)
              </Typography>
              <Divider sx={{ mb: 3 }} />
              
              <Grid container spacing={3}>
                {/* Current Financial Position */}
                <Grid
                  size={{
                    xs: 12,
                    md: 6
                  }}>
                  <Card sx={{ p: 2, bgcolor: '#e3f2fd' }}>
                    <Typography variant="h6" color="primary" gutterBottom>
                      💰 Current Financial Position
                    </Typography>
                    {customer.companies_house_data.accounts_detail.shareholders_funds && (
                      <Box sx={{ mb: 2 }}>
                        <Typography variant="body2" color="text.secondary">Shareholders' Funds</Typography>
                        <Typography variant="h6">{String(customer.companies_house_data.accounts_detail.shareholders_funds)}</Typography>
                      </Box>
                    )}
                    {customer.companies_house_data.accounts_detail.cash_at_bank && (
                      <Box sx={{ mb: 2 }}>
                        <Typography variant="body2" color="text.secondary">Cash at Bank</Typography>
                        <Typography variant="h6">{String(customer.companies_house_data.accounts_detail.cash_at_bank)}</Typography>
                      </Box>
                    )}
                    {customer.companies_house_data.accounts_detail.turnover && (
                      <Box sx={{ mb: 2 }}>
                        <Typography variant="body2" color="text.secondary">Turnover</Typography>
                        <Typography variant="h6">{String(customer.companies_house_data.accounts_detail.turnover)}</Typography>
                      </Box>
                    )}
                    {customer.companies_house_data.accounts_detail.employees && (
                      <Box sx={{ mb: 2 }}>
                        <Typography variant="body2" color="text.secondary">Estimated Employees</Typography>
                        <Typography variant="h6">{String(customer.companies_house_data.accounts_detail.employees)}</Typography>
                      </Box>
                    )}
                  </Card>
                </Grid>
                
                {/* Financial Trends */}
                <Grid
                  size={{
                    xs: 12,
                    md: 6
                  }}>
                  <Card sx={{ p: 2, bgcolor: '#f3e5f5' }}>
                    <Typography variant="h6" color="secondary" gutterBottom>
                      📈 Financial Trends
                    </Typography>
                    {customer.companies_house_data.accounts_detail.revenue_growth && (
                      <Box sx={{ mb: 2 }}>
                        <Typography variant="body2" color="text.secondary">Revenue Growth</Typography>
                        <Chip 
                          label={String(customer.companies_house_data.accounts_detail.revenue_growth)} 
                          size="medium"
                          color={String(customer.companies_house_data.accounts_detail.revenue_growth).startsWith('+') ? 'success' : 
                                 String(customer.companies_house_data.accounts_detail.revenue_growth).startsWith('-') ? 'error' : 'default'}
                        />
                      </Box>
                    )}
                    {customer.companies_house_data.accounts_detail.profitability_trend && (
                      <Box sx={{ mb: 2 }}>
                        <Typography variant="body2" color="text.secondary">Profitability Trend</Typography>
                        <Chip 
                          label={String(customer.companies_house_data.accounts_detail.profitability_trend)} 
                          size="medium"
                          color={customer.companies_house_data.accounts_detail.profitability_trend === 'Growing' ? 'success' :
                                 customer.companies_house_data.accounts_detail.profitability_trend === 'Stable' ? 'warning' : 'error'}
                        />
                      </Box>
                    )}
                    {customer.companies_house_data.accounts_detail.financial_health_score !== undefined && (
                      <Box sx={{ mb: 2 }}>
                        <Typography variant="body2" color="text.secondary">Financial Health Score</Typography>
                        <Chip 
                          label={`${customer.companies_house_data.accounts_detail.financial_health_score}/100`} 
                          size="medium"
                          color={customer.companies_house_data.accounts_detail.financial_health_score >= 70 ? 'success' :
                                 customer.companies_house_data.accounts_detail.financial_health_score >= 40 ? 'warning' : 'error'}
                        />
                      </Box>
                    )}
                    {customer.companies_house_data.accounts_detail.years_of_data && (
                      <Box sx={{ mb: 2 }}>
                        <Typography variant="body2" color="text.secondary">Years of Data Available</Typography>
                        <Typography variant="h6">{String(customer.companies_house_data.accounts_detail.years_of_data)} years</Typography>
                      </Box>
                    )}
                  </Card>
                </Grid>
              </Grid>

              {/* Multi-year Financial History Table */}
              {customer.companies_house_data.accounts_detail.detailed_financials && 
               Array.isArray(customer.companies_house_data.accounts_detail.detailed_financials) && 
               customer.companies_house_data.accounts_detail.detailed_financials.length > 0 && (
                <Box sx={{ mt: 3 }}>
                  <Typography variant="h6" color="primary" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    📊 Financial History
                  </Typography>
                  <TableContainer component={Paper}>
                    <Table size="small">
                      <TableHead sx={{ bgcolor: '#f5f5f5' }}>
                        <TableRow>
                          <TableCell><strong>Year</strong></TableCell>
                          <TableCell><strong>Turnover</strong></TableCell>
                          <TableCell><strong>Shareholders' Funds</strong></TableCell>
                          <TableCell><strong>Cash at Bank</strong></TableCell>
                          <TableCell><strong>Profit Before Tax</strong></TableCell>
                          <TableCell><strong>Employees</strong></TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {customer.companies_house_data.accounts_detail.detailed_financials.slice(0, 5).map((yearData: any, index: number) => (
                          <TableRow key={index} sx={{ '&:nth-of-type(odd)': { bgcolor: '#fafafa' } }}>
                            <TableCell>
                              <strong>
                                {yearData.financial_year || 
                                 (yearData.period_end && yearData.period_end.substring(0, 4)) ||
                                 (yearData.reporting_date && yearData.reporting_date.substring(0, 4)) ||
                                 (yearData.filing_date && yearData.filing_date.substring(0, 4)) ||
                                 'Unknown'}
                              </strong>
                            </TableCell>
                            <TableCell>
                              {yearData.turnover ? 
                                (typeof yearData.turnover === 'number' ? 
                                  `£${yearData.turnover.toLocaleString()}` : yearData.turnover) : 
                                'N/A'}
                            </TableCell>
                            <TableCell>
                              {yearData.shareholders_funds ? 
                                (typeof yearData.shareholders_funds === 'number' ? 
                                  `£${yearData.shareholders_funds.toLocaleString()}` : yearData.shareholders_funds) : 
                                'N/A'}
                            </TableCell>
                            <TableCell>
                              {yearData.cash_at_bank ? 
                                (typeof yearData.cash_at_bank === 'number' ? 
                                  `£${yearData.cash_at_bank.toLocaleString()}` : yearData.cash_at_bank) : 
                                'N/A'}
                            </TableCell>
                            <TableCell sx={{ 
                              color: yearData.profit_before_tax && typeof yearData.profit_before_tax === 'number' && yearData.profit_before_tax < 0 ? 'error.main' : 'success.main'
                            }}>
                              {yearData.profit_before_tax ? 
                                (typeof yearData.profit_before_tax === 'number' ? 
                                  `£${yearData.profit_before_tax.toLocaleString()}` : yearData.profit_before_tax) : 
                                'N/A'}
                            </TableCell>
                            <TableCell>
                              {yearData.employees || 'N/A'}
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </Box>
              )}

              {/* AI Analysis Summary (from v1) */}
              <Box sx={{ mt: 3 }}>
                <Typography variant="h6" color="primary" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  🎯 Analysis Summary
                </Typography>
                
                {/* Financial Health Analysis */}
                {customer.companies_house_data.accounts_detail.financial_health_score !== undefined && (
                  <Alert 
                    severity={
                      customer.companies_house_data.accounts_detail.financial_health_score >= 70 ? 'success' :
                      customer.companies_house_data.accounts_detail.financial_health_score >= 40 ? 'warning' : 'error'
                    }
                    icon={
                      customer.companies_house_data.accounts_detail.financial_health_score >= 70 ? <CheckCircleIcon /> :
                      customer.companies_house_data.accounts_detail.financial_health_score >= 40 ? <WarningIcon /> : <ErrorIcon />
                    }
                    sx={{ mb: 2 }}
                  >
                    <Typography variant="body1" fontWeight="bold">
                      {customer.companies_house_data.accounts_detail.financial_health_score >= 70 ? 'Strong Financial Health' :
                       customer.companies_house_data.accounts_detail.financial_health_score >= 40 ? 'Moderate Financial Health' : 'Weak Financial Health'}
                    </Typography>
                    <Typography variant="body2">
                      {customer.companies_house_data.accounts_detail.financial_health_score >= 70 ? 
                        'This company shows good financial stability and growth potential.' :
                       customer.companies_house_data.accounts_detail.financial_health_score >= 40 ? 
                        'This company has average financial stability.' :
                        'This company may have financial challenges.'}
                    </Typography>
                  </Alert>
                )}

                {/* Profitability Trend Analysis */}
                {customer.companies_house_data.accounts_detail.profitability_trend && (
                  <Alert 
                    severity={
                      customer.companies_house_data.accounts_detail.profitability_trend === 'Growing' ? 'success' :
                      customer.companies_house_data.accounts_detail.profitability_trend === 'Declining' ? 'error' : 'info'
                    }
                    icon={
                      customer.companies_house_data.accounts_detail.profitability_trend === 'Growing' ? <TrendingUpIcon /> :
                      customer.companies_house_data.accounts_detail.profitability_trend === 'Declining' ? <TrendingDownIcon /> : <InfoIcon />
                    }
                    sx={{ mb: 2 }}
                  >
                    <Typography variant="body1" fontWeight="bold">
                      {customer.companies_house_data.accounts_detail.profitability_trend === 'Growing' ? 'Growing Profitability' :
                       customer.companies_house_data.accounts_detail.profitability_trend === 'Declining' ? 'Declining Profitability' : 'Stable Profitability'}
                    </Typography>
                    <Typography variant="body2">
                      {customer.companies_house_data.accounts_detail.profitability_trend === 'Growing' ? 
                        'The company is showing positive financial trends.' :
                       customer.companies_house_data.accounts_detail.profitability_trend === 'Declining' ? 
                        'The company may be facing financial challenges.' :
                        'The company is maintaining stable financial performance.'}
                    </Typography>
                  </Alert>
                )}

                {/* Revenue Growth Insight */}
                {customer.companies_house_data.accounts_detail.revenue_growth && (
                  <Alert 
                    severity={
                      String(customer.companies_house_data.accounts_detail.revenue_growth).startsWith('+') ? 'success' :
                      String(customer.companies_house_data.accounts_detail.revenue_growth).startsWith('-') ? 'warning' : 'info'
                    }
                    sx={{ mb: 2 }}
                  >
                    <Typography variant="body2">
                      <strong>Revenue Trend:</strong> {customer.companies_house_data.accounts_detail.revenue_growth} year-over-year change
                    </Typography>
                  </Alert>
                )}
              </Box>
            </Paper>
          )}

          {!customer?.companies_house_data?.accounts_detail && (
            <Paper sx={{ p: 3 }}>
              <Alert severity="info">
                No financial data available. Run AI Analysis to fetch Companies House financial data.
              </Alert>
            </Paper>
          )}
        </Box>
      )}
      {/* Tab Panel 4: Addresses */}
      {currentTab === 4 && (
        <Box>
          {customer?.google_maps_data && Array.isArray(customer.google_maps_data.locations) && customer.google_maps_data.locations.length > 0 ? (
            <>
              <Paper sx={{ p: 3, mb: 3 }}>
                <Typography variant="h5" gutterBottom sx={{ color: '#1976d2', display: 'flex', alignItems: 'center', gap: 1 }}>
                  <PlaceIcon /> Google Maps Locations ({customer.google_maps_data.total_results || customer.google_maps_data.locations.length})
                </Typography>
                <Divider sx={{ mb: 3 }} />
                
                <Alert severity="info" sx={{ mb: 3 }}>
                  <Typography variant="body2">
                    📍 <strong>Address Selection</strong><br />
                    Select interesting addresses to create targeted lead generation campaigns. Mark irrelevant locations as "Not this business" to hide them.
                  </Typography>
                </Alert>
                
                {customer.google_maps_data.locations
                  .filter((place: any) => {
                    const excludedAddresses = customer.excluded_addresses || [];
                    const locationId = place.name?.replace(/\s+/g, '_').replace(/\./g, '_').replace(/,/g, '_');
                    return !excludedAddresses.includes(locationId);
                  })
                  .map((place: any) => {
                    const locationId = place.name?.replace(/\s+/g, '_').replace(/\./g, '_').replace(/,/g, '_');
                    
                    return (
                      <Card key={locationId} id={`address_${locationId}`} variant="outlined" sx={{ mb: 2, p: 2, '&:hover': { boxShadow: 3 }, transition: 'box-shadow 0.3s' }}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                          <Box sx={{ flexGrow: 1 }}>
                            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                              <input 
                                type="checkbox" 
                                style={{ cursor: 'pointer' }}
                                onChange={(e) => {
                                  console.log('Select address for lead generation:', place.name);
                                }}
                              />
                              <Typography variant="subtitle1" fontWeight="bold">
                                {place.name || 'Unnamed location'}
                              </Typography>
                              {place.business_status && (
                                <Chip 
                                  label={place.business_status} 
                                  size="small" 
                                  color={place.business_status === 'OPERATIONAL' ? 'success' : 'default'} 
                                />
                              )}
                            </Box>
                            
                            {place.formatted_address && (
                              <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
                                📍 {place.formatted_address}
                              </Typography>
                            )}
                            {place.formatted_phone_number && (
                              <Typography variant="body2" color="text.secondary" sx={{ mb: 0.5 }}>
                                📞 {place.formatted_phone_number}
                              </Typography>
                            )}
                            {place.rating && (
                              <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                                ⭐ Rating: {place.rating}/5 {place.user_ratings_total && `(${place.user_ratings_total} reviews)`}
                              </Typography>
                            )}
                            
                            <Button
                              variant="outlined"
                              size="small"
                              startIcon={<PlaceIcon />}
                              href={`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(place.formatted_address || place.name)}`}
                              target="_blank"
                              rel="noopener noreferrer"
                              sx={{ mt: 1 }}
                            >
                              Open in Google Maps
                            </Button>
                          </Box>
                          
                          <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                            <input 
                              type="checkbox" 
                              id={`exclude_${locationId}`}
                              style={{ cursor: 'pointer' }}
                              onChange={async (e) => {
                                try {
                                  // Hide element immediately for smooth UX (v1 approach)
                                  const addressElement = document.getElementById(`address_${locationId}`);
                                  if (addressElement) {
                                    addressElement.style.display = 'none';
                                  }
                                  
                                  await customerAPI.excludeAddress(id!, locationId);
                                  
                                  // Reload page to update the display
                                  window.location.reload();
                                } catch (error: any) {
                                  console.error('Error excluding address:', error);
                                  alert('Error excluding address: ' + (error.response?.data?.detail || error.message || 'Please try again'));
                                  // Reset checkbox and show element again
                                  e.target.checked = false;
                                  const addressElement = document.getElementById(`address_${locationId}`);
                                  if (addressElement) {
                                    addressElement.style.display = '';
                                  }
                                }
                              }}
                            />
                            <Typography variant="caption" color="text.secondary" component="label" htmlFor={`exclude_${locationId}`} sx={{ cursor: 'pointer' }}>
                              Not this business
                            </Typography>
                          </Box>
                        </Box>
                      </Card>
                    );
                  })}
                
                {/* Excluded Addresses Section */}
                {customer.excluded_addresses && customer.excluded_addresses.length > 0 && (
                  <Box sx={{ mt: 3 }}>
                    <Accordion>
                      <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                        <Typography>
                          👁️ Show Excluded Addresses ({customer.excluded_addresses.length})
                        </Typography>
                      </AccordionSummary>
                      <AccordionDetails>
                        {customer.google_maps_data.locations
                          .filter((place: any) => {
                            const locationId = place.name?.replace(/\s+/g, '_').replace(/\./g, '_').replace(/,/g, '_');
                            return customer.excluded_addresses?.includes(locationId);
                          })
                          .map((place: any) => {
                            const locationId = place.name?.replace(/\s+/g, '_').replace(/\./g, '_').replace(/,/g, '_');
                            
                            return (
                              <Card key={`excluded_${locationId}`} variant="outlined" sx={{ mb: 2, p: 2, bgcolor: 'grey.100' }}>
                                <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                  <Box>
                                    <Typography variant="subtitle2" color="text.secondary" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                                      🚫 {place.name}
                                    </Typography>
                                    <Typography variant="body2" color="text.secondary">
                                      {place.formatted_address}
                                    </Typography>
                                    <Typography variant="caption" color="text.secondary">
                                      Excluded from display
                                    </Typography>
                                  </Box>
                                  <Button
                                    variant="outlined"
                                    size="small"
                                    color="success"
                                    onClick={async () => {
                                      try {
                                        const response = await fetch(`/api/v1/customers/${id}/addresses/include`, {
                                          method: 'POST',
                                          headers: {
                                            'Content-Type': 'application/json',
                                            'Authorization': `Bearer ${localStorage.getItem('access_token')}`
                                          },
                                          body: JSON.stringify({ location_id: locationId })
                                        });
                                        
                                        if (response.ok) {
                                          // Wait for database commit and reload
                                          await new Promise(resolve => setTimeout(resolve, 500));
                                          window.location.reload();
                                        } else if (response.status === 401) {
                                          alert('Session expired. Please log in again.');
                                          window.location.href = '/login';
                                        } else {
                                          const errorData = await response.json();
                                          alert('Failed to restore address: ' + (errorData.detail || 'Unknown error'));
                                        }
                                      } catch (error) {
                                        console.error('Error restoring address:', error);
                                        alert('Error restoring address. Please try again.');
                                      }
                                    }}
                                  >
                                    ↺ Restore
                                  </Button>
                                </Box>
                              </Card>
                            );
                          })}
                      </AccordionDetails>
                    </Accordion>
                  </Box>
                )}
              </Paper>
            </>
          ) : (
            <Paper sx={{ p: 3 }}>
              <Alert severity="info">
                No address data available. Run AI Analysis to discover company locations.
              </Alert>
            </Paper>
          )}
        </Box>
      )}
      {/* Tab Panel 5: Directors */}
      {currentTab === 5 && (
        <Box>
          {customer?.companies_house_data?.accounts_detail?.active_directors && 
           customer.companies_house_data.accounts_detail.active_directors.length > 0 ? (
            <Paper sx={{ p: 3 }}>
              <Typography variant="h5" gutterBottom sx={{ color: '#1976d2', display: 'flex', alignItems: 'center', gap: 1 }}>
                <PeopleIcon /> Active Directors & Officers ({customer.companies_house_data.accounts_detail.total_active_directors || customer.companies_house_data.accounts_detail.active_directors.length})
              </Typography>
              <Divider sx={{ mb: 3 }} />
              
              <Grid container spacing={3}>
                {customer.companies_house_data.accounts_detail.active_directors.map((director: any, index: number) => (
                  <Grid
                    key={index}
                    size={{
                      xs: 12,
                      sm: 6,
                      md: 4
                    }}>
                    <Card variant="outlined" sx={{ height: '100%', '&:hover': { boxShadow: 3 }, transition: 'box-shadow 0.3s' }}>
                      <CardContent>
                        <Typography variant="h6" fontWeight="bold" gutterBottom sx={{ color: '#1976d2' }}>
                          {String(director.name || 'Unknown')}
                        </Typography>
                        <Chip 
                          label={String(director.role || director.officer_role || 'Director')} 
                          size="small" 
                          color="primary" 
                          sx={{ mb: 2 }} 
                        />
                        {director.appointed_on && (
                          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                            📅 Appointed: {new Date(director.appointed_on).toLocaleDateString()}
                          </Typography>
                        )}
                        {director.nationality && (
                          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                            🌍 Nationality: {String(director.nationality)}
                          </Typography>
                        )}
                        {director.occupation && (
                          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                            💼 Occupation: {String(director.occupation)}
                          </Typography>
                        )}
                        {director.address && typeof director.address === 'string' && (
                          <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 2, p: 1, bgcolor: 'grey.50', borderRadius: 1 }}>
                            📍 {director.address}
                          </Typography>
                        )}
                        {director.address && typeof director.address === 'object' && (
                          <Typography variant="caption" color="text.secondary" display="block" sx={{ mt: 2, p: 1, bgcolor: 'grey.50', borderRadius: 1 }}>
                            📍 {[director.address.premises, director.address.address_line_1, director.address.locality, director.address.postal_code].filter(Boolean).join(', ')}
                          </Typography>
                        )}
                        <Button 
                          variant="contained" 
                          size="small" 
                          fullWidth 
                          sx={{ mt: 2 }}
                          startIcon={<AddIcon />}
                          onClick={() => handleAddDirectorAsContact(director)}
                        >
                          Add as Contact
                        </Button>
                      </CardContent>
                    </Card>
                  </Grid>
                ))}
              </Grid>
            </Paper>
          ) : (
            <Paper sx={{ p: 3 }}>
              <Alert severity="info">
                No director information available. Run AI Analysis to fetch Companies House data.
              </Alert>
            </Paper>
          )}
        </Box>
      )}
      {/* Tab Panel 6: Business Intelligence - Opportunities, Competitors, Risks */}
      {currentTab === 6 && (
        <Box>
          {/* Website Intelligence Section */}
          {customer?.website_data && (
            <Paper sx={{ p: 3, mb: 3 }}>
              <Typography variant="h5" gutterBottom sx={{ color: '#2196f3', display: 'flex', alignItems: 'center', gap: 1 }}>
                <LanguageIcon /> Website Intelligence
              </Typography>
              <Divider sx={{ mb: 3 }} />
              
              <Grid container spacing={2}>
                {/* Website Title & Description */}
                {customer.website_data.website_title && (
                  <Grid size={12}>
                    <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                      Website Title
                    </Typography>
                    <Typography variant="body1" gutterBottom>
                      {customer.website_data.website_title}
                    </Typography>
                  </Grid>
                )}
                
                {customer.website_data.website_description && (
                  <Grid size={12}>
                    <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                      Description
                    </Typography>
                    <Typography variant="body1" gutterBottom>
                      {customer.website_data.website_description}
                    </Typography>
                  </Grid>
                )}
                
                {/* Keywords/Key Phrases */}
                {customer.website_data.key_phrases && customer.website_data.key_phrases.length > 0 && (
                  <Grid size={12}>
                    <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                      Key Topics & Keywords
                    </Typography>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mt: 1 }}>
                      {customer.website_data.key_phrases.slice(0, 15).map((phrase: any, index: number) => (
                        <Chip 
                          key={index}
                          label={typeof phrase === 'string' ? phrase : phrase[0]}
                          color="primary"
                          variant="outlined"
                          size="small"
                        />
                      ))}
                    </Box>
                  </Grid>
                )}
                
                {/* Contact Information from Website */}
                {customer.website_data.contact_info && customer.website_data.contact_info.length > 0 && (
                  <Grid size={12}>
                    <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                      Contact Information Found
                    </Typography>
                    <Box sx={{ mt: 1 }}>
                      {customer.website_data.contact_info.slice(0, 5).map((contact: string, index: number) => (
                        <Chip 
                          key={index}
                          label={contact}
                          icon={<PhoneIcon />}
                          sx={{ mr: 1, mb: 1 }}
                          size="small"
                        />
                      ))}
                    </Box>
                  </Grid>
                )}
                
                {/* Locations Mentioned */}
                {customer.website_data.locations && customer.website_data.locations.length > 0 && (
                  <Grid size={12}>
                    <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                      Locations Mentioned
                    </Typography>
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 1, mt: 1 }}>
                      {customer.website_data.locations.slice(0, 10).map((location: string, index: number) => (
                        <Chip 
                          key={index}
                          label={location}
                          icon={<PlaceIcon />}
                          color="secondary"
                          variant="outlined"
                          size="small"
                        />
                      ))}
                    </Box>
                  </Grid>
                )}
              </Grid>
            </Paper>
          )}

          {/* Opportunities Section */}
          {customer?.ai_analysis_raw?.opportunities && (
            <Paper sx={{ p: 3, mb: 3 }}>
              <Typography variant="h5" gutterBottom sx={{ color: '#4caf50', display: 'flex', alignItems: 'center', gap: 1 }}>
                <LightbulbIcon /> Opportunities
              </Typography>
              <Divider sx={{ mb: 3 }} />
              <Typography variant="body1" sx={{ whiteSpace: 'pre-line', lineHeight: 1.8 }}>
                {customer.ai_analysis_raw.opportunities}
              </Typography>
            </Paper>
          )}

          {/* Competitors Section */}
          {customer?.ai_analysis_raw?.competitors && (
            <Paper sx={{ p: 3, mb: 3 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                <Typography variant="h5" sx={{ color: '#ff9800', display: 'flex', alignItems: 'center', gap: 1 }}>
                  <CompareArrowsIcon /> Competitors
                </Typography>
                <Button 
                  variant="outlined" 
                  color="primary" 
                  size="small"
                  startIcon={<AddIcon />}
                  onClick={() => handleAddCompetitorsToCampaign()}
                >
                  Add All to Lead Campaign
                </Button>
              </Box>
              <Divider sx={{ mb: 3 }} />
              {Array.isArray(customer.ai_analysis_raw.competitors) ? (
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                  {customer.ai_analysis_raw.competitors.map((competitor: string, index: number) => (
                    <Box 
                      key={index} 
                      sx={{ 
                        display: 'flex', 
                        justifyContent: 'space-between', 
                        alignItems: 'center',
                        p: 2,
                        backgroundColor: '#fff3e0',
                        borderRadius: 1,
                        '&:hover': { backgroundColor: '#ffe0b2' }
                      }}
                    >
                      <Typography variant="body1">{competitor}</Typography>
                      <Button
                        variant="outlined"
                        size="small"
                        color="primary"
                        startIcon={<AddIcon />}
                        onClick={() => handleAddCompetitorsToCampaign(competitor)}
                      >
                        Add to Campaign
                      </Button>
                    </Box>
                  ))}
                </Box>
              ) : (
                <Typography variant="body1" sx={{ whiteSpace: 'pre-line', lineHeight: 1.8 }}>
                  {customer.ai_analysis_raw.competitors}
                </Typography>
              )}
            </Paper>
          )}

          {/* Risk Factors Section */}
          {customer?.ai_analysis_raw?.risks && (
            <Paper sx={{ p: 3, mb: 3 }}>
              <Typography variant="h5" gutterBottom sx={{ color: '#f44336', display: 'flex', alignItems: 'center', gap: 1 }}>
                <WarningIcon /> Risk Factors
              </Typography>
              <Divider sx={{ mb: 3 }} />
              <Typography variant="body1" sx={{ whiteSpace: 'pre-line', lineHeight: 1.8 }}>
                {customer.ai_analysis_raw.risks}
              </Typography>
            </Paper>
          )}

          {/* No data message */}
          {!customer?.ai_analysis_raw?.opportunities && !customer?.ai_analysis_raw?.competitors && !customer?.ai_analysis_raw?.risks && (
            <Paper sx={{ p: 3 }}>
              <Alert severity="info">
                No business intelligence data available. Run AI Analysis to generate opportunities, competitors analysis, and risk factors.
              </Alert>
            </Paper>
          )}
        </Box>
      )}
      {/* Tab Panel 7: Activity - AI-Powered Activity Center */}
      {currentTab === 7 && customer && (
        <Paper sx={{ p: 0 }}>
          <ActivityCenter customerId={customer.id} />
        </Paper>
      )}
      {/* Tab Panel 8: Quotes */}
      {currentTab === 8 && (
        <Paper sx={{ p: 3 }}>
          <Typography variant="h5" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <DescriptionIcon /> Quotes
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Create, manage, and track quotes for this customer.
          </Typography>
          
          <Alert severity="info" sx={{ mb: 3 }}>
            <Typography variant="body2">
              Quote management system coming soon. Features will include:
            </Typography>
            <Box component="ul" sx={{ mt: 1, mb: 0 }}>
              <li>AI-powered quote generation</li>
              <li>Product/service catalog integration</li>
              <li>Quote templates</li>
              <li>Version control</li>
              <li>Approval workflows</li>
              <li>PDF generation and email delivery</li>
              <li>Quote status tracking</li>
              <li>Win/loss analysis</li>
            </Box>
          </Alert>

          <Button variant="outlined" startIcon={<AddIcon />} disabled>
            Create New Quote
          </Button>
        </Paper>
      )}
      {/* Contact Dialog */}
      <ContactDialog
        open={addContactOpen}
        onClose={handleCloseContactDialog}
        onSave={handleSaveContact}
        contact={editingContact}
        customerId={id!}
      />
    </Container>
  );
};

export default CustomerDetail;



