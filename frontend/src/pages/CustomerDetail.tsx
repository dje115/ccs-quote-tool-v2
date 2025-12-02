import React, { useEffect, useState, useCallback } from 'react';
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
  Checkbox,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Tooltip
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
  GetApp as GetAppIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Info as InfoIcon,
  Lightbulb as LightbulbIcon,
  AutoAwesome as SparkleIcon,
  Support as SupportIcon,
  Work as WorkIcon,
  Visibility as ViewIcon
} from '@mui/icons-material';
import { useNavigate, useParams } from 'react-router-dom';
import { customerAPI, contactAPI, quoteAPI, helpdeskAPI, opportunityAPI } from '../services/api';
import { useAbortController } from '../hooks/useAbortController';
import axios from 'axios';

// Get API base URL (works in both React and Vite)
const getApiBaseUrl = () => {
  // Try Vite env first
  if (typeof import.meta !== 'undefined' && import.meta.env?.VITE_API_URL) {
    return import.meta.env.VITE_API_URL;
  }
  // Try React env
  if (typeof process !== 'undefined' && process.env?.REACT_APP_API_URL) {
    return process.env.REACT_APP_API_URL;
  }
  // Fallback to window location for same-origin requests
  return window.location.origin.replace(':3000', ':8000');
};
import api from '../services/api';
import { useWebSocketContext } from '../contexts/WebSocketContext';
import CustomerOverviewTab from '../components/CustomerOverviewTab';
import ActivityCenter from '../components/ActivityCenter';
import CustomerTimeline from '../components/CustomerTimeline';
import ContactDialog from '../components/ContactDialog';
import CustomerContractsTab from '../components/CustomerContractsTab';

const CustomerDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [customer, setCustomer] = useState<any>(null);
  const [contacts, setContacts] = useState<any[]>([]);
  const [quotes, setQuotes] = useState<any[]>([]);
  const [tickets, setTickets] = useState<any[]>([]);
  const [opportunities, setOpportunities] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [addContactOpen, setAddContactOpen] = useState(false);
  const [editingContact, setEditingContact] = useState<any>(null);
  const [aiAnalysisLoading, setAiAnalysisLoading] = useState(false);
  const [aiAnalysisError, setAiAnalysisError] = useState<string | null>(null);
  const [aiAnalysisSuccess, setAiAnalysisSuccess] = useState<string | null>(null);
  const [aiAnalysisDialogOpen, setAiAnalysisDialogOpen] = useState(false);
  const [updateFinancialData, setUpdateFinancialData] = useState(false);
  const [updateAddresses, setUpdateAddresses] = useState(false);
  const [createTicketDialogOpen, setCreateTicketDialogOpen] = useState(false);
  const [newTicket, setNewTicket] = useState({ subject: '', description: '', priority: 'medium' });
  const [currentTab, setCurrentTab] = useState(() => {
    // Restore tab from localStorage on component mount
    const savedTab = localStorage.getItem('customerDetailTab');
    return savedTab ? parseInt(savedTab) : 0;
  });

  // Subscribe to WebSocket events for AI analysis and customer updates
  const { subscribe, isConnected } = useWebSocketContext();

  // Define loadCustomerData using useCallback to avoid dependency issues
  const loadCustomerData = useCallback(async (signal?: AbortSignal) => {
    if (!id) return;
    
    try {
      setLoading(true);
      
      // Abort all requests if signal is already aborted
      if (signal?.aborted) {
        return;
      }
      
      const [customerRes, contactsRes, quotesRes, ticketsRes, opportunitiesRes] = await Promise.all([
        customerAPI.get(id, { signal }),
        contactAPI.list(id, { signal }),
        quoteAPI.list({ customer_id: id }, { signal }),
        helpdeskAPI.getTickets({ customer_id: id }, { signal }),
        opportunityAPI.getCustomerOpportunities(id).catch(() => ({ data: [] })) // Load opportunities, ignore errors
      ]);

      // Check if request was cancelled before updating state
      if (signal?.aborted) {
        return;
      }

      setCustomer(customerRes.data);
      setContacts(contactsRes.data);
      // Handle both old format (array) and new format (paginated response)
      const quotesData = quotesRes.data;
      if (Array.isArray(quotesData)) {
        setQuotes(quotesData);
      } else if (quotesData?.items) {
        setQuotes(quotesData.items || []);
      } else {
        setQuotes([]);
      }
      // Handle tickets response - it can be {tickets: [...]} or just [...]
      const ticketsData = ticketsRes.data?.tickets || ticketsRes.data || [];
      setTickets(Array.isArray(ticketsData) ? ticketsData : []);
      // Handle opportunities response
      setOpportunities(opportunitiesRes.data || []);
    } catch (error: any) {
      // Ignore cancellation errors
      if (axios.isCancel(error) || error.name === 'CanceledError' || error.code === 'ERR_CANCELED') {
        return;
      }
      console.error('Error loading customer data:', error);
      // Set error state so UI can show appropriate message
      if (error.response?.status === 404) {
        // Customer not found - this is handled by the UI showing "Customer not found"
      }
    } finally {
      // Only update loading state if not cancelled
      if (!signal?.aborted) {
        setLoading(false);
      }
    }
  }, [id]);

  // Load customer data on mount or when id changes
  useEffect(() => {
    if (!id) return;
    
    const abortController = new AbortController();
    loadCustomerData(abortController.signal);
    
    // Cleanup: abort requests when component unmounts or id changes
    return () => {
      abortController.abort();
    };
  }, [id, loadCustomerData]);
  
  // Subscribe to WebSocket events
  useEffect(() => {
    if (!id || !isConnected) return;

    // Subscribe to ai_analysis.started for this customer (updates status from 'queued' to 'running')
    const unsubscribeStarted = subscribe('ai_analysis.started', (event) => {
      if (event.data.customer_id === id) {
        console.log('AI analysis started! Updating status to running...');
        loadCustomerData(); // Reload to show 'running' status
      }
    });

    // Subscribe to ai_analysis.completed for this customer
    const unsubscribeCompleted = subscribe('ai_analysis.completed', (event) => {
      if (event.data.customer_id === id) {
        console.log('AI analysis completed! Reloading data...');
        setAiAnalysisSuccess('AI analysis completed successfully!');
        loadCustomerData();
        setTimeout(() => setAiAnalysisSuccess(null), 5000);
      }
    });

    // Subscribe to ai_analysis.failed for this customer
    const unsubscribeFailed = subscribe('ai_analysis.failed', (event) => {
      if (event.data.customer_id === id) {
        console.log('AI analysis failed.');
        setAiAnalysisError('AI analysis failed. Please try again.');
        loadCustomerData();
        setTimeout(() => setAiAnalysisError(null), 5000);
      }
    });

    // Subscribe to customer.updated for this customer
    const unsubscribeUpdated = subscribe('customer.updated', (event) => {
      if (event.data.customer_id === id) {
        console.log('Customer updated via WebSocket, reloading...');
        loadCustomerData();
      }
    });

    return () => {
      unsubscribeStarted();
      unsubscribeCompleted();
      unsubscribeFailed();
      unsubscribeUpdated();
    };
  }, [id, isConnected, subscribe, loadCustomerData]); // Removed 'customer' from dependencies to prevent unnecessary re-subscriptions

  const handleOpenAiAnalysisDialog = () => {
    // Set defaults based on existing data
    // Default to OFF (false) if data exists, ON (true) if no data
    const hasFinancialData = customer?.companies_house_data && 
      typeof customer.companies_house_data === 'object' && 
      Object.keys(customer.companies_house_data).length > 0;
    
    const hasAddressData = customer?.google_maps_data && 
      typeof customer.google_maps_data === 'object' &&
      customer.google_maps_data.locations && 
      Array.isArray(customer.google_maps_data.locations) &&
      customer.google_maps_data.locations.length > 0;
    
    // Debug logging
    console.log('AI Analysis Dialog - Data Check:', {
      hasFinancialData,
      hasAddressData,
      companiesHouseData: customer?.companies_house_data,
      googleMapsData: customer?.google_maps_data,
      locationsCount: customer?.google_maps_data?.locations?.length
    });
    
    // Set checkboxes: false (unchecked) when data exists, true (checked) when no data
    setUpdateFinancialData(!hasFinancialData);
    setUpdateAddresses(!hasAddressData);
    setAiAnalysisDialogOpen(true);
  };

  const handleCloseAiAnalysisDialog = () => {
    setAiAnalysisDialogOpen(false);
  };

  const runAiAnalysis = async () => {
    try {
      setAiAnalysisLoading(true);
      setAiAnalysisError(null);
      setAiAnalysisSuccess(null);
      setAiAnalysisDialogOpen(false);

      // Queue the background task with options
      const response = await customerAPI.runAiAnalysis(id!, {
        update_financial_data: updateFinancialData,
        update_addresses: updateAddresses
      });
      
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

  const handleLifecycleAutoManagedChange = async (enabled: boolean) => {
    // Optimistic update
    setCustomer((prev: any) => ({
      ...prev,
      lifecycle_auto_managed: enabled
    }));
    
    try {
      await customerAPI.update(id!, { lifecycle_auto_managed: enabled });
      setAiAnalysisSuccess(enabled ? 'Lifecycle automation enabled' : 'Lifecycle automation disabled');
      setTimeout(() => setAiAnalysisSuccess(null), 3000);
      await loadCustomerData();
    } catch (error) {
      console.error('Failed to update lifecycle automation:', error);
      // Revert optimistic update on error
      setCustomer((prev: any) => ({
        ...prev,
        lifecycle_auto_managed: !enabled
      }));
      setAiAnalysisError('Failed to update lifecycle automation');
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
          onClick={handleOpenAiAnalysisDialog}
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
      {/* AI Analysis Options Dialog */}
      <Dialog 
        open={aiAnalysisDialogOpen} 
        onClose={handleCloseAiAnalysisDialog}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <AiIcon />
            <Typography variant="h6">AI Analysis Options</Typography>
          </Box>
        </DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Choose which data sources to include in the AI analysis. Uncheck any section to exclude it and save API quota.
          </Typography>
          
          {/* Financial Data Section */}
          <Card 
            variant="outlined" 
            sx={{ 
              mb: 2, 
              p: 2,
              border: updateFinancialData ? '2px solid' : '1px solid',
              borderColor: updateFinancialData ? 'primary.main' : 'divider',
              backgroundColor: updateFinancialData ? 'action.selected' : 'background.paper',
              cursor: 'pointer',
              '&:hover': {
                backgroundColor: 'action.hover'
              }
            }}
            onClick={() => setUpdateFinancialData(!updateFinancialData)}
          >
            <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
              <Checkbox
                checked={updateFinancialData}
                onChange={(e) => {
                  e.stopPropagation();
                  setUpdateFinancialData(e.target.checked);
                }}
                color="primary"
                sx={{ 
                  '& .MuiSvgIcon-root': { 
                    fontSize: 32 
                  },
                  mt: -0.5
                }}
              />
              <Box sx={{ flex: 1 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                  <Typography variant="h6" sx={{ fontWeight: 600 }}>
                    Financial Data (Companies House)
                  </Typography>
                  <Chip 
                    label={updateFinancialData ? "INCLUDED" : "EXCLUDED"} 
                    color={updateFinancialData ? "primary" : "default"}
                    size="small"
                    sx={{ fontWeight: 600 }}
                  />
                </Box>
                <Typography variant="body2" color="text.secondary">
                  {customer?.companies_house_data && 
                   typeof customer.companies_house_data === 'object' &&
                   Object.keys(customer.companies_house_data).length > 0
                    ? `✓ Financial data exists (${Object.keys(customer.companies_house_data).length} fields) - ${updateFinancialData ? 'will be refreshed' : 'will be skipped'}`
                    : `⚠ No financial data - ${updateFinancialData ? 'will be fetched' : 'will be skipped'}`}
                </Typography>
              </Box>
            </Box>
          </Card>
          
          {/* Address Data Section */}
          <Card 
            variant="outlined" 
            sx={{ 
              mb: 2, 
              p: 2,
              border: updateAddresses ? '2px solid' : '1px solid',
              borderColor: updateAddresses ? 'primary.main' : 'divider',
              backgroundColor: updateAddresses ? 'action.selected' : 'background.paper',
              cursor: 'pointer',
              '&:hover': {
                backgroundColor: 'action.hover'
              }
            }}
            onClick={() => setUpdateAddresses(!updateAddresses)}
          >
            <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
              <Checkbox
                checked={updateAddresses}
                onChange={(e) => {
                  e.stopPropagation();
                  setUpdateAddresses(e.target.checked);
                }}
                color="primary"
                sx={{ 
                  '& .MuiSvgIcon-root': { 
                    fontSize: 32 
                  },
                  mt: -0.5
                }}
              />
              <Box sx={{ flex: 1 }}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
                  <Typography variant="h6" sx={{ fontWeight: 600 }}>
                    Address Data (Google Maps)
                  </Typography>
                  <Chip 
                    label={updateAddresses ? "INCLUDED" : "EXCLUDED"} 
                    color={updateAddresses ? "primary" : "default"}
                    size="small"
                    sx={{ fontWeight: 600 }}
                  />
                </Box>
                <Typography variant="body2" color="text.secondary">
                  {customer?.google_maps_data && 
                   typeof customer.google_maps_data === 'object' &&
                   customer.google_maps_data.locations && 
                   Array.isArray(customer.google_maps_data.locations) &&
                   customer.google_maps_data.locations.length > 0
                    ? `✓ ${customer.google_maps_data.locations.length} location(s) exist - ${updateAddresses ? 'will be refreshed' : 'will be skipped'}`
                    : `⚠ No address data - ${updateAddresses ? 'will be fetched' : 'will be skipped'}`}
                </Typography>
              </Box>
            </Box>
          </Card>
          
          {/* Summary Box */}
          <Alert 
            severity="info" 
            sx={{ mt: 2 }}
            icon={false}
          >
            <Typography variant="body2" sx={{ fontWeight: 500, mb: 0.5 }}>
              Summary:
            </Typography>
            <Typography variant="body2">
              {updateFinancialData && updateAddresses 
                ? 'Both data sources will be updated'
                : updateFinancialData 
                  ? 'Only Financial Data will be updated (Addresses excluded)'
                  : updateAddresses
                    ? 'Only Address Data will be updated (Financial Data excluded)'
                    : '⚠️ No data sources selected - only AI analysis will run'}
            </Typography>
          </Alert>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseAiAnalysisDialog} color="inherit">
            Cancel
          </Button>
          <Button 
            onClick={runAiAnalysis} 
            variant="contained" 
            color="primary"
            disabled={aiAnalysisLoading}
            startIcon={aiAnalysisLoading ? <CircularProgress size={20} /> : <AiIcon />}
          >
            {aiAnalysisLoading ? 'Starting...' : 'Run Analysis'}
          </Button>
        </DialogActions>
      </Dialog>

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
          value={currentTab >= 7 ? false : currentTab} 
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
          value={currentTab >= 7 && currentTab <= 11 ? currentTab - 7 : false}
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
          <Tab icon={<WorkIcon />} iconPosition="start" label="Opportunities" />
          <Tab icon={<SupportIcon />} iconPosition="start" label="Tickets" />
          <Tab icon={<DescriptionIcon />} iconPosition="start" label="Contracts" />
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
          onLifecycleAutoManagedChange={handleLifecycleAutoManagedChange}
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

              {/* New Discovery AI Analysis Format - Opportunity Summary */}
              {customer.ai_analysis_raw.opportunity_summary && (
                <Box sx={{ mb: 3, p: 2, bgcolor: '#e3f2fd', borderRadius: 2, border: '1px solid #2196f3' }}>
                  <Typography variant="subtitle2" color="primary" gutterBottom sx={{ fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: 1 }}>
                    <InfoIcon /> Opportunity Summary
                  </Typography>
                  <Typography variant="body2" sx={{ whiteSpace: 'pre-line', lineHeight: 1.6 }}>
                    {customer.ai_analysis_raw.opportunity_summary}
                  </Typography>
                </Box>
              )}

              {/* Risk Assessment (array format) */}
              {customer.ai_analysis_raw.risk_assessment && Array.isArray(customer.ai_analysis_raw.risk_assessment) && customer.ai_analysis_raw.risk_assessment.length > 0 && (
                <Box sx={{ mb: 3, p: 2, bgcolor: '#ffebee', borderRadius: 2, border: '1px solid #f44336' }}>
                  <Typography variant="subtitle2" color="error.main" gutterBottom sx={{ fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: 1 }}>
                    <WarningIcon /> Risk Assessment
                  </Typography>
                  <Box component="ul" sx={{ pl: 2, m: 0 }}>
                    {customer.ai_analysis_raw.risk_assessment.map((risk: string, idx: number) => (
                      <Box component="li" key={idx} sx={{ mb: 1 }}>
                        <Typography variant="body2">{risk}</Typography>
                      </Box>
                    ))}
                  </Box>
                </Box>
              )}

              {/* Recommendations (array format) */}
              {customer.ai_analysis_raw.recommendations && Array.isArray(customer.ai_analysis_raw.recommendations) && customer.ai_analysis_raw.recommendations.length > 0 && (
                <Box sx={{ mb: 3, p: 2, bgcolor: '#e8f5e9', borderRadius: 2, border: '2px solid #4caf50' }}>
                  <Typography variant="subtitle2" color="success.dark" gutterBottom sx={{ fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: 1 }}>
                    <LightbulbIcon /> Recommendations
                  </Typography>
                  <Typography variant="caption" color="text.secondary" sx={{ mb: 2, display: 'block' }}>
                    Strategic recommendations based on AI analysis
                  </Typography>
                  <Box component="ol" sx={{ pl: 2, m: 0 }}>
                    {customer.ai_analysis_raw.recommendations.map((rec: string, idx: number) => (
                      <Box component="li" key={idx} sx={{ mb: 1 }}>
                        <Typography variant="body2">{rec}</Typography>
                      </Box>
                    ))}
                  </Box>
                </Box>
              )}

              {/* Next Steps (array format) */}
              {customer.ai_analysis_raw.next_steps && Array.isArray(customer.ai_analysis_raw.next_steps) && customer.ai_analysis_raw.next_steps.length > 0 && (
                <Box sx={{ mb: 3, p: 2, bgcolor: '#fff3e0', borderRadius: 2, border: '2px solid #ff9800' }}>
                  <Typography variant="subtitle2" color="warning.dark" gutterBottom sx={{ fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: 1 }}>
                    <CheckCircleIcon /> Next Steps
                  </Typography>
                  <Typography variant="caption" color="text.secondary" sx={{ mb: 2, display: 'block' }}>
                    Recommended actions to move forward with this opportunity
                  </Typography>
                  <Box component="ol" sx={{ pl: 2, m: 0 }}>
                    {customer.ai_analysis_raw.next_steps.map((step: string, idx: number) => (
                      <Box component="li" key={idx} sx={{ mb: 1 }}>
                        <Typography variant="body2">{step}</Typography>
                      </Box>
                    ))}
                  </Box>
                </Box>
              )}

              {/* Conversion Probability and AI Confidence Score */}
              {(customer.ai_analysis_raw.conversion_probability !== undefined || customer.ai_analysis_raw.ai_confidence_score !== undefined) && (
                <Grid container spacing={2} sx={{ mb: 3 }}>
                  {customer.ai_analysis_raw.conversion_probability !== undefined && (
                    <Grid
                      size={{
                        xs: 12,
                        sm: 6
                      }}>
                      <Box sx={{ p: 2, bgcolor: '#f3f4f6', borderRadius: 2, border: '1px solid #e5e7eb' }}>
                        <Typography variant="caption" color="text.secondary">Conversion Probability</Typography>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 1 }}>
                          <Typography variant="h6" fontWeight="bold">
                            {customer.ai_analysis_raw.conversion_probability}%
                          </Typography>
                          <Chip 
                            label={
                              customer.ai_analysis_raw.conversion_probability >= 70 ? 'High' :
                              customer.ai_analysis_raw.conversion_probability >= 40 ? 'Medium' : 'Low'
                            }
                            color={
                              customer.ai_analysis_raw.conversion_probability >= 70 ? 'success' :
                              customer.ai_analysis_raw.conversion_probability >= 40 ? 'warning' : 'default'
                            }
                            size="small"
                          />
                        </Box>
                      </Box>
                    </Grid>
                  )}
                  {customer.ai_analysis_raw.ai_confidence_score !== undefined && (
                    <Grid
                      size={{
                        xs: 12,
                        sm: 6
                      }}>
                      <Box sx={{ p: 2, bgcolor: '#f3f4f6', borderRadius: 2, border: '1px solid #e5e7eb' }}>
                        <Typography variant="caption" color="text.secondary">AI Confidence Score</Typography>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 1 }}>
                          <Typography variant="h6" fontWeight="bold">
                            {Math.round((customer.ai_analysis_raw.ai_confidence_score || 0) * 100)}%
                          </Typography>
                          <Chip 
                            label={
                              (customer.ai_analysis_raw.ai_confidence_score || 0) >= 0.7 ? 'High' :
                              (customer.ai_analysis_raw.ai_confidence_score || 0) >= 0.4 ? 'Medium' : 'Low'
                            }
                            color={
                              (customer.ai_analysis_raw.ai_confidence_score || 0) >= 0.7 ? 'success' :
                              (customer.ai_analysis_raw.ai_confidence_score || 0) >= 0.4 ? 'warning' : 'default'
                            }
                            size="small"
                          />
                        </Box>
                      </Box>
                    </Grid>
                  )}
                </Grid>
              )}

              {/* Qualification Reason */}
              {customer.ai_analysis_raw.qualification_reason && (
                <Box sx={{ mb: 2, p: 2, bgcolor: '#f1f8e9', borderRadius: 2, border: '1px solid #8bc34a' }}>
                  <Typography variant="subtitle2" color="success.dark" gutterBottom sx={{ fontWeight: 'bold', display: 'flex', alignItems: 'center', gap: 1 }}>
                    <CheckCircleIcon /> Qualification Reason
                  </Typography>
                  <Typography variant="body2" sx={{ whiteSpace: 'pre-line', lineHeight: 1.6 }}>
                    {customer.ai_analysis_raw.qualification_reason}
                  </Typography>
                </Box>
              )}

              {/* Analyzed At Timestamp */}
              {customer.ai_analysis_raw.analyzed_at && (
                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 2, fontStyle: 'italic' }}>
                  Analysis generated: {new Date(customer.ai_analysis_raw.analyzed_at).toLocaleString()}
                </Typography>
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
                        {customer.companies_house_data.accounts_detail.detailed_financials.map((yearData: any, index: number) => (
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

              {/* Accounts Documents Section */}
              {customer.companies_house_data?.accounts_documents && 
               Array.isArray(customer.companies_house_data.accounts_documents) && 
               customer.companies_house_data.accounts_documents.length > 0 && (
                <Box sx={{ mt: 4 }}>
                  <Typography variant="h6" color="primary" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    📄 Accounts Documents
                  </Typography>
                  <Alert severity="info" sx={{ mb: 2 }}>
                    <Typography variant="body2">
                      View original accounts documents stored in MinIO. These documents are available for reference and can be shared with accountants.
                    </Typography>
                  </Alert>
                  <TableContainer component={Paper} variant="outlined">
                    <Table>
                      <TableHead>
                        <TableRow>
                          <TableCell><strong>Year</strong></TableCell>
                          <TableCell><strong>Filing Date</strong></TableCell>
                          <TableCell><strong>Description</strong></TableCell>
                          <TableCell><strong>Size</strong></TableCell>
                          <TableCell><strong>Actions</strong></TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {customer.companies_house_data.accounts_documents.map((doc: any, index: number) => (
                          <TableRow key={index} sx={{ '&:nth-of-type(odd)': { bgcolor: '#fafafa' } }}>
                            <TableCell>
                              <strong>{doc.year || 'Unknown'}</strong>
                            </TableCell>
                            <TableCell>
                              {doc.filing_date ? new Date(doc.filing_date).toLocaleDateString() : 'N/A'}
                            </TableCell>
                            <TableCell>
                              {doc.description || 'Annual Accounts'}
                            </TableCell>
                            <TableCell>
                              {doc.size_bytes ? `${(doc.size_bytes / 1024).toFixed(1)} KB` : 'N/A'}
                            </TableCell>
                            <TableCell>
                              <Button
                                variant="outlined"
                                size="small"
                                startIcon={<DescriptionIcon />}
                                onClick={async () => {
                                  if (doc.transaction_id) {
                                    try {
                                      const token = localStorage.getItem('access_token') || localStorage.getItem('token');
                                      const apiUrl = getApiBaseUrl();
                                      const response = await fetch(`${apiUrl}/api/v1/customers/${id}/accounts-documents/${doc.transaction_id}/view`, {
                                        headers: {
                                          'Authorization': `Bearer ${token}`
                                        }
                                      });
                                      if (response.ok) {
                                        const blob = await response.blob();
                                        const url = window.URL.createObjectURL(blob);
                                        window.open(url, '_blank');
                                      } else {
                                        console.error('Error viewing document:', response.status, response.statusText);
                                      }
                                    } catch (error) {
                                      console.error('Error viewing document:', error);
                                    }
                                  }
                                }}
                                sx={{ mr: 1 }}
                              >
                                View
                              </Button>
                              <Button
                                variant="outlined"
                                size="small"
                                startIcon={<GetAppIcon />}
                                onClick={async () => {
                                  if (doc.transaction_id) {
                                    try {
                                      const token = localStorage.getItem('access_token') || localStorage.getItem('token');
                                      const apiUrl = getApiBaseUrl();
                                      const response = await fetch(`${apiUrl}/api/v1/customers/${id}/accounts-documents/${doc.transaction_id}/download-url?expires_hours=24`, {
                                        headers: {
                                          'Authorization': `Bearer ${token}`
                                        }
                                      });
                                      if (response.ok) {
                                        const data = await response.json();
                                        if (data.presigned_url) {
                                          window.open(data.presigned_url, '_blank');
                                        }
                                      } else {
                                        console.error('Error getting download URL:', response.status, response.statusText);
                                      }
                                    } catch (error) {
                                      console.error('Error getting download URL:', error);
                                    }
                                  }
                                }}
                              >
                                Download
                              </Button>
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </Box>
              )}
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
                  .filter((place: any, index: number) => {
                    const excludedAddresses = customer.excluded_addresses || [];
                    // Use same key generation logic as in map function
                    const locationId = place.place_id 
                      ? place.place_id 
                      : `${place.name?.replace(/\s+/g, '_').replace(/\./g, '_').replace(/,/g, '_') || 'unnamed'}_${place.formatted_address?.replace(/\s+/g, '_').replace(/\./g, '_').replace(/,/g, '_').replace(/\//g, '_') || index}_${index}`;
                    return !excludedAddresses.includes(locationId);
                  })
                  .map((place: any, index: number) => {
                    // Create unique key: use place_id if available, otherwise combine name + address + index
                    const locationId = place.place_id 
                      ? place.place_id 
                      : `${place.name?.replace(/\s+/g, '_').replace(/\./g, '_').replace(/,/g, '_') || 'unnamed'}_${place.formatted_address?.replace(/\s+/g, '_').replace(/\./g, '_').replace(/,/g, '_').replace(/\//g, '_') || index}_${index}`;
                    
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
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
          <ActivityCenter customerId={customer.id} />
          <Box sx={{ width: '100%' }}>
            <CustomerTimeline customerId={customer.id} limit={30} />
          </Box>
        </Box>
      )}
      {/* Tab Panel 8: Quotes */}
      {currentTab === 8 && (
        <Paper sx={{ p: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
            <Typography variant="h5" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <DescriptionIcon /> Quotes
            </Typography>
            <Box sx={{ display: 'flex', gap: 1 }}>
              <Button 
                variant="outlined" 
                startIcon={<AddIcon />}
                onClick={() => navigate(`/quotes/new?customer=${id}`)}
              >
                Create AI Quote
              </Button>
              <Button 
                variant="contained" 
                startIcon={<AddIcon />}
                onClick={() => navigate(`/quotes/new/legacy?customer=${id}`)}
              >
                Create Manual Quote
              </Button>
            </Box>
          </Box>
          
          {quotes.length === 0 ? (
            <Alert severity="info">
              No quotes found for this customer. Create a new quote to get started.
            </Alert>
          ) : (
            <TableContainer component={Paper} variant="outlined">
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell><strong>Quote #</strong></TableCell>
                    <TableCell><strong>Title</strong></TableCell>
                    <TableCell><strong>Status</strong></TableCell>
                    <TableCell><strong>Total</strong></TableCell>
                    <TableCell><strong>Created</strong></TableCell>
                    <TableCell><strong>Actions</strong></TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {quotes.map((quote: any) => (
                    <TableRow key={quote.id} hover>
                      <TableCell>{quote.quote_number}</TableCell>
                      <TableCell>{quote.title}</TableCell>
                      <TableCell>
                        <Chip 
                          label={quote.status} 
                          size="small"
                          color={
                            quote.status === 'accepted' ? 'success' :
                            quote.status === 'sent' ? 'info' :
                            quote.status === 'draft' ? 'default' :
                            quote.status === 'rejected' ? 'error' : 'default'
                          }
                        />
                      </TableCell>
                      <TableCell>£{parseFloat(quote.total_amount || 0).toLocaleString('en-GB', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</TableCell>
                      <TableCell>{new Date(quote.created_at).toLocaleDateString()}</TableCell>
                      <TableCell>
                        <Button
                          size="small"
                          onClick={() => navigate(`/quotes/${quote.id}`)}
                        >
                          View
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </Paper>
      )}
      
      {/* Tab Panel 9: Opportunities */}
      {currentTab === 9 && (
        <Paper sx={{ p: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
            <Typography variant="h5" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <WorkIcon /> Opportunities
            </Typography>
            <Button 
              variant="contained" 
              startIcon={<AddIcon />}
              onClick={() => {
                // Navigate to opportunities page with customer pre-selected
                navigate(`/opportunities?customer_id=${id}`);
              }}
            >
              Create New Opportunity
            </Button>
          </Box>
          
          {opportunities.length === 0 ? (
            <Alert severity="info">
              No opportunities found for this customer. Create a new opportunity to track deals.
            </Alert>
          ) : (
            <TableContainer component={Paper} variant="outlined">
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell><strong>Title</strong></TableCell>
                    <TableCell><strong>Stage</strong></TableCell>
                    <TableCell><strong>Probability</strong></TableCell>
                    <TableCell><strong>Value</strong></TableCell>
                    <TableCell><strong>Deal Date</strong></TableCell>
                    <TableCell><strong>Created</strong></TableCell>
                    <TableCell><strong>Actions</strong></TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {opportunities.map((opp: any) => (
                    <TableRow key={opp.id} hover>
                      <TableCell>
                        <Typography variant="body2" fontWeight="medium">
                          {opp.title}
                        </Typography>
                        {opp.description && (
                          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>
                            {opp.description.substring(0, 60)}...
                          </Typography>
                        )}
                      </TableCell>
                      <TableCell>
                        <Chip
                          label={opp.stage === 'qualified' ? 'Qualified' :
                                 opp.stage === 'scoping' ? 'Scoping' :
                                 opp.stage === 'proposal_sent' ? 'Proposal Sent' :
                                 opp.stage === 'negotiation' ? 'Negotiation' :
                                 opp.stage === 'verbal_yes' ? 'Verbal Yes' :
                                 opp.stage === 'closed_won' ? 'Closed Won' :
                                 opp.stage === 'closed_lost' ? 'Closed Lost' : opp.stage}
                          size="small"
                          color={
                            opp.stage === 'qualified' ? 'info' :
                            opp.stage === 'scoping' ? 'primary' :
                            opp.stage === 'proposal_sent' ? 'warning' :
                            opp.stage === 'negotiation' ? 'warning' :
                            opp.stage === 'verbal_yes' ? 'success' :
                            opp.stage === 'closed_won' ? 'success' :
                            opp.stage === 'closed_lost' ? 'error' : 'default'
                          }
                        />
                      </TableCell>
                      <TableCell>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <Typography variant="body2">{opp.conversion_probability}%</Typography>
                          <Box
                            sx={{
                              width: 50,
                              height: 8,
                              bgcolor: 'grey.200',
                              borderRadius: 1,
                              overflow: 'hidden'
                            }}
                          >
                            <Box
                              sx={{
                                width: `${opp.conversion_probability}%`,
                                height: '100%',
                                bgcolor: opp.conversion_probability > 70 ? 'success.main' : 
                                         opp.conversion_probability > 40 ? 'warning.main' : 'error.main'
                              }}
                            />
                          </Box>
                        </Box>
                      </TableCell>
                      <TableCell>
                        {opp.estimated_value ? (
                          <Typography variant="body2" fontWeight="medium">
                            £{opp.estimated_value.toLocaleString()}
                          </Typography>
                        ) : (
                          <Typography variant="body2" color="text.secondary">
                            Not set
                          </Typography>
                        )}
                      </TableCell>
                      <TableCell>
                        {opp.potential_deal_date ? (
                          <Typography variant="body2">
                            {new Date(opp.potential_deal_date).toLocaleDateString()}
                          </Typography>
                        ) : (
                          <Typography variant="body2" color="text.secondary">
                            Not set
                          </Typography>
                        )}
                      </TableCell>
                      <TableCell>
                        <Typography variant="body2">
                          {new Date(opp.created_at).toLocaleDateString()}
                        </Typography>
                      </TableCell>
                      <TableCell>
                        <IconButton
                          size="small"
                          onClick={() => navigate(`/opportunities/${opp.id}`)}
                        >
                          <ViewIcon />
                        </IconButton>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </Paper>
      )}
      
      {/* Tab Panel 10: Tickets */}
      {currentTab === 10 && (
        <Box>
          <Paper sx={{ p: 3, mb: 3 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
              <Typography variant="h5" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <SupportIcon /> Support Tickets
              </Typography>
              <Button 
                variant="contained" 
                startIcon={<AddIcon />}
                onClick={() => setCreateTicketDialogOpen(true)}
              >
                Create New Ticket
              </Button>
            </Box>
            
            {tickets.length === 0 ? (
              <Alert severity="info">
                No tickets found for this customer. Create a new ticket to get started.
              </Alert>
            ) : (
              <TableContainer component={Paper} variant="outlined">
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell><strong>Ticket #</strong></TableCell>
                      <TableCell><strong>Subject</strong></TableCell>
                      <TableCell><strong>Status</strong></TableCell>
                      <TableCell><strong>Priority</strong></TableCell>
                      <TableCell><strong>SLA Status</strong></TableCell>
                      <TableCell><strong>Created</strong></TableCell>
                      <TableCell><strong>Actions</strong></TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {tickets.map((ticket: any) => {
                      const hasSLA = ticket.sla_policy_id;
                      const hasBreach = ticket.sla_first_response_breached || ticket.sla_resolution_breached;
                      const slaStatus = hasSLA ? (hasBreach ? 'breached' : 'compliant') : 'no_sla';
                      
                      return (
                        <TableRow key={ticket.id} hover>
                          <TableCell>{ticket.ticket_number}</TableCell>
                          <TableCell>{ticket.subject}</TableCell>
                          <TableCell>
                            <Chip 
                              label={ticket.status} 
                              size="small"
                              color={
                                ticket.status === 'open' ? 'error' :
                                ticket.status === 'in_progress' ? 'warning' :
                                ticket.status === 'resolved' ? 'success' :
                                ticket.status === 'closed' ? 'default' : 'default'
                              }
                            />
                          </TableCell>
                          <TableCell>
                            <Chip 
                              label={ticket.priority} 
                              size="small"
                              color={
                                ticket.priority === 'urgent' ? 'error' :
                                ticket.priority === 'high' ? 'warning' :
                                ticket.priority === 'medium' ? 'info' : 'default'
                              }
                            />
                          </TableCell>
                          <TableCell>
                            {hasSLA ? (
                              <Tooltip title={
                                hasBreach 
                                  ? `SLA Breached: ${ticket.sla_first_response_breached ? 'First Response' : ''}${ticket.sla_first_response_breached && ticket.sla_resolution_breached ? ' & ' : ''}${ticket.sla_resolution_breached ? 'Resolution' : ''}`
                                  : 'SLA Compliant'
                              }>
                                <Chip
                                  icon={hasBreach ? <ErrorIcon /> : <CheckCircleIcon />}
                                  label={hasBreach ? 'Breached' : 'Compliant'}
                                  size="small"
                                  color={hasBreach ? 'error' : 'success'}
                                />
                              </Tooltip>
                            ) : (
                              <Chip
                                label="No SLA"
                                size="small"
                                color="default"
                                variant="outlined"
                              />
                            )}
                          </TableCell>
                          <TableCell>{new Date(ticket.created_at).toLocaleDateString()}</TableCell>
                          <TableCell>
                            <Button
                              size="small"
                              onClick={() => navigate(`/helpdesk/${ticket.id}`)}
                            >
                              View
                            </Button>
                          </TableCell>
                        </TableRow>
                      );
                    })}
                  </TableBody>
                </Table>
              </TableContainer>
            )}
          </Paper>

          {/* SLA Compliance History */}
          {customer?.id && (
            <Box sx={{ mb: 3 }}>
              <CustomerSLAHistory customerId={customer.id} />
            </Box>
          )}
        </Box>
      )}
      {/* Contact Dialog */}
      <ContactDialog
        open={addContactOpen}
        onClose={handleCloseContactDialog}
        onSave={handleSaveContact}
        contact={editingContact}
        customerId={id!}
      />
      
      {/* Create Ticket Dialog */}
      <Dialog open={createTicketDialogOpen} onClose={() => setCreateTicketDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Create New Ticket</DialogTitle>
        <DialogContent>
          <Box sx={{ pt: 2 }}>
            <TextField
              fullWidth
              label="Subject"
              value={newTicket.subject}
              onChange={(e) => setNewTicket({ ...newTicket, subject: e.target.value })}
              margin="normal"
              required
            />
            <TextField
              fullWidth
              label="Description"
              value={newTicket.description}
              onChange={(e) => setNewTicket({ ...newTicket, description: e.target.value })}
              margin="normal"
              multiline
              rows={6}
              required
              helperText="AI will improve this description and suggest next actions"
            />
            <FormControl fullWidth margin="normal">
              <InputLabel>Priority</InputLabel>
              <Select
                value={newTicket.priority}
                label="Priority"
                onChange={(e) => setNewTicket({ ...newTicket, priority: e.target.value })}
              >
                <MenuItem value="low">Low</MenuItem>
                <MenuItem value="medium">Medium</MenuItem>
                <MenuItem value="high">High</MenuItem>
                <MenuItem value="urgent">Urgent</MenuItem>
              </Select>
            </FormControl>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateTicketDialogOpen(false)}>Cancel</Button>
          <Button
            onClick={async () => {
              try {
                await helpdeskAPI.createTicket({
                  subject: newTicket.subject,
                  description: newTicket.description,
                  priority: newTicket.priority,
                  customer_id: id
                });
                setCreateTicketDialogOpen(false);
                setNewTicket({ subject: '', description: '', priority: 'medium' });
                await loadCustomerData();
                setAiAnalysisSuccess('Ticket created successfully! AI is analyzing and improving the description.');
                setTimeout(() => setAiAnalysisSuccess(null), 5000);
              } catch (error: any) {
                setAiAnalysisError(error.response?.data?.detail || 'Failed to create ticket');
                setTimeout(() => setAiAnalysisError(null), 5000);
              }
            }}
            variant="contained"
            disabled={!newTicket.subject || !newTicket.description}
          >
            Create
          </Button>
        </DialogActions>
      </Dialog>
      
      {/* Tab Panel 11: Contracts */}
      {currentTab === 11 && customer && (
        <CustomerContractsTab customerId={customer.id} />
      )}
    </Container>
  );
};

export default CustomerDetail;

