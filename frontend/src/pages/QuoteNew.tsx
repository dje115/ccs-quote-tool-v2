import React, { useState, useEffect } from 'react';
import {
  Container,
  Paper,
  Typography,
  Box,
  Grid,
  TextField,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  FormControlLabel,
  Checkbox,
  Alert,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Stepper,
  Step,
  StepLabel,
  Card,
  CardContent,
  Divider,
  List,
  ListItem,
  ListItemText,
  Chip
} from '@mui/material';
import {
  ArrowBack as BackIcon,
  Save as SaveIcon,
  Psychology as AiIcon,
  Add as AddIcon,
  CheckCircle as CheckCircleIcon
} from '@mui/icons-material';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { customerAPI, quoteAPI } from '../services/api';
import api from '../services/api';

const QuoteNew: React.FC = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const customerIdParam = searchParams.get('customer');

  // Form state
  const [formData, setFormData] = useState({
    customer_id: customerIdParam || '',
    quote_type: 'cabling', // Default to cabling
    project_title: '',
    project_description: '',
    site_address: '',
    building_type: '',
    building_size: '',
    number_of_floors: '1',
    number_of_rooms: '1',
    cabling_type: '',
    wifi_requirements: false,
    cctv_requirements: false,
    door_entry_requirements: false,
    special_requirements: ''
  });

  // UI state
  const [customers, setCustomers] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [aiAnalyzing, setAiAnalyzing] = useState(false);
  const [aiAnalysis, setAiAnalysis] = useState<any>(null);
  const [clarifications, setClarifications] = useState<string[]>([]);
  const [clarificationAnswers, setClarificationAnswers] = useState<Record<string, string>>({});
  const [showClarificationDialog, setShowClarificationDialog] = useState(false);
  const [createCustomerOpen, setCreateCustomerOpen] = useState(false);
  const [newCustomer, setNewCustomer] = useState({
    company_name: '',
    main_email: '',
    main_phone: '',
    website: ''
  });

  // Load customers on mount
  useEffect(() => {
    loadCustomers();
  }, []);

  const loadCustomers = async () => {
    try {
      const response = await customerAPI.list({ limit: 1000 });
      setCustomers(response.data || []);
    } catch (error) {
      console.error('Error loading customers:', error);
    }
  };

  const handleInputChange = (field: string, value: any) => {
    setFormData(prev => ({ ...prev, [field]: value }));
  };

  const handleAnalyzeRequirements = async (questionsOnly: boolean = false) => {
    if (!formData.project_title || !formData.site_address) {
      alert('Please fill in Project Title and Site Address before analyzing.');
      return;
    }

    setAiAnalyzing(true);
    try {
      const response = await api.post('/quotes/analyze', {
        // Don't send quote_id - we're analyzing before creation
        quote_type: formData.quote_type,
        project_title: formData.project_title,
        project_description: formData.project_description,
        site_address: formData.site_address,
        building_type: formData.building_type,
        building_size: formData.building_size ? parseFloat(formData.building_size) : null,
        number_of_floors: formData.number_of_floors ? parseInt(formData.number_of_floors) : 1,
        number_of_rooms: formData.number_of_rooms ? parseInt(formData.number_of_rooms) : 1,
        cabling_type: formData.cabling_type,
        wifi_requirements: formData.wifi_requirements,
        cctv_requirements: formData.cctv_requirements,
        door_entry_requirements: formData.door_entry_requirements,
        special_requirements: formData.special_requirements,
        clarification_answers: Object.keys(clarificationAnswers).length > 0 
          ? Object.entries(clarificationAnswers).map(([question, answer]) => ({ question, answer }))
          : undefined,
        questions_only: questionsOnly
      });

      if (response.data && response.data.success !== false) {
        const analysis = response.data.data || response.data;

        if (questionsOnly && analysis.clarifications && analysis.clarifications.length > 0) {
          setClarifications(analysis.clarifications);
          setShowClarificationDialog(true);
        } else {
          setAiAnalysis(analysis);
          if (analysis.clarifications && analysis.clarifications.length > 0) {
            setClarifications(analysis.clarifications);
          }
        }
      } else {
        alert('AI Analysis failed: ' + (response.data.error || 'Unknown error'));
      }
    } catch (error: any) {
      console.error('Error analyzing requirements:', error);
      alert('Error analyzing requirements: ' + (error.response?.data?.detail || error.message));
    } finally {
      setAiAnalyzing(false);
    }
  };

  const handleSubmitClarifications = async () => {
    setShowClarificationDialog(false);
    const answers = clarifications.map(q => ({
      question: q,
      answer: clarificationAnswers[q] || ''
    }));
    setClarificationAnswers({});
    
    // Re-run analysis with clarifications
    await handleAnalyzeRequirements(false);
  };

  const handleCreateCustomer = async () => {
    try {
      const response = await customerAPI.create(newCustomer);
      if (response.data) {
        await loadCustomers();
        setFormData(prev => ({ ...prev, customer_id: response.data.id }));
        setCreateCustomerOpen(false);
        setNewCustomer({ company_name: '', main_email: '', main_phone: '', website: '' });
      }
    } catch (error: any) {
      alert('Error creating customer: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleSubmit = async () => {
    if (!formData.customer_id) {
      alert('Please select or create a customer.');
      return;
    }

    if (!formData.project_title || !formData.site_address) {
      alert('Please fill in required fields: Project Title and Site Address.');
      return;
    }

    setLoading(true);
    try {
      const quoteData = {
        customer_id: formData.customer_id,
        title: formData.project_title,
        description: formData.project_description,
        quote_type: formData.quote_type,
        project_title: formData.project_title,
        project_description: formData.project_description,
        site_address: formData.site_address,
        building_type: formData.building_type || null,
        building_size: formData.building_size ? parseFloat(formData.building_size) : null,
        number_of_floors: formData.number_of_floors ? parseInt(formData.number_of_floors) : 1,
        number_of_rooms: formData.number_of_rooms ? parseInt(formData.number_of_rooms) : 1,
        cabling_type: formData.cabling_type || null,
        wifi_requirements: formData.wifi_requirements,
        cctv_requirements: formData.cctv_requirements,
        door_entry_requirements: formData.door_entry_requirements,
        special_requirements: formData.special_requirements || null
      };

      const response = await quoteAPI.create(quoteData);
      if (response.data) {
        // If we have AI analysis, update the quote with it
        if (aiAnalysis) {
          try {
            await api.post('/quotes/analyze', {
              quote_id: response.data.id,
              clarification_answers: clarifications.map(q => ({
                question: q,
                answer: clarificationAnswers[q] || ''
              }))
            });
          } catch (error) {
            console.error('Error updating quote with AI analysis:', error);
            // Continue anyway - quote was created successfully
          }
        }
        navigate(`/quotes/${response.data.id}`);
      }
    } catch (error: any) {
      console.error('Error creating quote:', error);
      alert('Error creating quote: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="lg" sx={{ py: 3 }}>
      <Box sx={{ mb: 3, display: 'flex', alignItems: 'center', gap: 2 }}>
        <Button
          startIcon={<BackIcon />}
          onClick={() => navigate('/quotes')}
        >
          Back
        </Button>
        <Typography variant="h4" component="h1">
          Create New Quote
        </Typography>
      </Box>

      <Grid container spacing={3}>
        {/* Main Form */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Project Information
            </Typography>
            <Divider sx={{ mb: 3 }} />

            {/* Customer Selection */}
            <Box sx={{ mb: 3 }}>
              <FormControl fullWidth>
                <InputLabel>Customer *</InputLabel>
                <Select
                  value={formData.customer_id}
                  label="Customer *"
                  onChange={(e) => handleInputChange('customer_id', e.target.value)}
                >
                  <MenuItem value="">
                    <em>Select existing customer or create new...</em>
                  </MenuItem>
                  {customers.map((customer) => (
                    <MenuItem key={customer.id} value={customer.id}>
                      {customer.company_name} ({customer.status})
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
              <Button
                startIcon={<AddIcon />}
                onClick={() => setCreateCustomerOpen(true)}
                sx={{ mt: 1 }}
                variant="outlined"
              >
                Create New Customer
              </Button>
            </Box>

            {/* Quote Type Selection */}
            <Box sx={{ mb: 3 }}>
              <FormControl fullWidth>
                <InputLabel>Quote Type *</InputLabel>
                <Select
                  value={formData.quote_type}
                  label="Quote Type *"
                  onChange={(e) => handleInputChange('quote_type', e.target.value)}
                >
                  <MenuItem value="cabling">Structured Cabling</MenuItem>
                  <MenuItem value="network_build">Network Infrastructure Build</MenuItem>
                  <MenuItem value="server_build">Server Infrastructure Build</MenuItem>
                  <MenuItem value="software_dev">Software Development</MenuItem>
                  <MenuItem value="testing">Testing Services</MenuItem>
                  <MenuItem value="design">Design Services</MenuItem>
                </Select>
              </FormControl>
              <Typography variant="caption" color="text.secondary" sx={{ mt: 0.5, display: 'block' }}>
                Select the type of quote to use the appropriate AI analysis prompt
              </Typography>
            </Box>

            {/* Project Title */}
            <TextField
              fullWidth
              label="Project Title *"
              value={formData.project_title}
              onChange={(e) => handleInputChange('project_title', e.target.value)}
              sx={{ mb: 2 }}
              required
            />

            {/* Site Address */}
            <TextField
              fullWidth
              label="Site Address *"
              value={formData.site_address}
              onChange={(e) => handleInputChange('site_address', e.target.value)}
              multiline
              rows={2}
              sx={{ mb: 2 }}
              required
            />

            {/* Building Details */}
            <Grid container spacing={2} sx={{ mb: 2 }}>
              <Grid item xs={12} sm={4}>
                <FormControl fullWidth>
                  <InputLabel>Building Type</InputLabel>
                  <Select
                    value={formData.building_type}
                    label="Building Type"
                    onChange={(e) => handleInputChange('building_type', e.target.value)}
                  >
                    <MenuItem value="">Select Type</MenuItem>
                    <MenuItem value="residential">Residential</MenuItem>
                    <MenuItem value="commercial">Commercial</MenuItem>
                    <MenuItem value="retail">Retail</MenuItem>
                    <MenuItem value="industrial">Industrial</MenuItem>
                    <MenuItem value="educational">Educational</MenuItem>
                    <MenuItem value="healthcare">Healthcare</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} sm={4}>
                <TextField
                  fullWidth
                  label="Building Size (sqm)"
                  type="number"
                  value={formData.building_size}
                  onChange={(e) => handleInputChange('building_size', e.target.value)}
                />
              </Grid>
              <Grid item xs={12} sm={4}>
                <TextField
                  fullWidth
                  label="Number of Floors"
                  type="number"
                  value={formData.number_of_floors}
                  onChange={(e) => handleInputChange('number_of_floors', e.target.value)}
                />
              </Grid>
            </Grid>

            <Grid container spacing={2} sx={{ mb: 2 }}>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Number of Rooms/Areas"
                  type="number"
                  value={formData.number_of_rooms}
                  onChange={(e) => handleInputChange('number_of_rooms', e.target.value)}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <FormControl fullWidth>
                  <InputLabel>Cabling Type</InputLabel>
                  <Select
                    value={formData.cabling_type}
                    label="Cabling Type"
                    onChange={(e) => handleInputChange('cabling_type', e.target.value)}
                  >
                    <MenuItem value="">Select Type</MenuItem>
                    <MenuItem value="cat5e">Cat5e</MenuItem>
                    <MenuItem value="cat6">Cat6</MenuItem>
                    <MenuItem value="cat6a">Cat6a</MenuItem>
                    <MenuItem value="fiber">Fiber</MenuItem>
                    <MenuItem value="mixed">Mixed (Multiple Types)</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
            </Grid>

            {/* Requirements */}
            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle2" gutterBottom>
                Requirements
              </Typography>
              <FormControlLabel
                control={
                  <Checkbox
                    checked={formData.wifi_requirements}
                    onChange={(e) => handleInputChange('wifi_requirements', e.target.checked)}
                  />
                }
                label="WiFi Installation (UniFi)"
              />
              <FormControlLabel
                control={
                  <Checkbox
                    checked={formData.cctv_requirements}
                    onChange={(e) => handleInputChange('cctv_requirements', e.target.checked)}
                  />
                }
                label="CCTV System (UniFi)"
              />
              <FormControlLabel
                control={
                  <Checkbox
                    checked={formData.door_entry_requirements}
                    onChange={(e) => handleInputChange('door_entry_requirements', e.target.checked)}
                  />
                }
                label="Door Entry System (Paxton Net2/UniFi)"
              />
            </Box>

            {/* Project Description */}
            <TextField
              fullWidth
              label="Project Description"
              value={formData.project_description}
              onChange={(e) => handleInputChange('project_description', e.target.value)}
              multiline
              rows={3}
              sx={{ mb: 2 }}
              placeholder="Describe the project requirements, special considerations, etc."
            />

            {/* Special Requirements */}
            <TextField
              fullWidth
              label="Special Requirements"
              value={formData.special_requirements}
              onChange={(e) => handleInputChange('special_requirements', e.target.value)}
              multiline
              rows={2}
              sx={{ mb: 2 }}
              placeholder="Any special requirements, constraints, or additional services needed..."
            />

            {/* Actions */}
            <Box sx={{ display: 'flex', gap: 2, justifyContent: 'flex-end', mt: 3 }}>
              <Button
                variant="outlined"
                startIcon={aiAnalyzing ? <CircularProgress size={20} /> : <AiIcon />}
                onClick={() => handleAnalyzeRequirements(true)}
                disabled={aiAnalyzing}
              >
                AI Analysis
              </Button>
              <Button
                variant="contained"
                startIcon={loading ? <CircularProgress size={20} /> : <SaveIcon />}
                onClick={handleSubmit}
                disabled={loading}
              >
                Create Quote
              </Button>
            </Box>
          </Paper>

          {/* AI Analysis Results */}
          {aiAnalysis && (
            <Paper sx={{ p: 3, mt: 3 }}>
              <Typography variant="h6" gutterBottom>
                AI Analysis Results
              </Typography>
              <Divider sx={{ mb: 2 }} />
              
              {aiAnalysis.analysis && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Analysis Summary
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    {aiAnalysis.analysis}
                  </Typography>
                </Box>
              )}

              {aiAnalysis.products && aiAnalysis.products.length > 0 && (
                <Box sx={{ mb: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Recommended Products
                  </Typography>
                  <List dense>
                    {aiAnalysis.products.map((product: any, idx: number) => (
                      <ListItem key={idx}>
                        <ListItemText
                          primary={product.item || product.name}
                          secondary={`Qty: ${product.quantity || 1} | Unit Price: £${product.unit_price || 0} | Total: £${product.total_price || 0}`}
                        />
                      </ListItem>
                    ))}
                  </List>
                </Box>
              )}

              {clarifications.length > 0 && (
                <Alert severity="info" sx={{ mt: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Clarifications Needed:
                  </Typography>
                  <List dense>
                    {clarifications.map((q, idx) => (
                      <ListItem key={idx}>
                        <ListItemText primary={q} />
                      </ListItem>
                    ))}
                  </List>
                </Alert>
              )}
            </Paper>
          )}
        </Grid>

        {/* Sidebar */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2, position: 'sticky', top: 20 }}>
            <Typography variant="h6" gutterBottom>
              Quick Actions
            </Typography>
            <Button
              fullWidth
              variant="outlined"
              startIcon={<AiIcon />}
              onClick={() => handleAnalyzeRequirements(false)}
              disabled={aiAnalyzing}
              sx={{ mb: 1 }}
            >
              {aiAnalyzing ? 'Analyzing...' : 'Run Full AI Analysis'}
            </Button>
          </Paper>
        </Grid>
      </Grid>

      {/* Clarification Dialog */}
      <Dialog
        open={showClarificationDialog}
        onClose={() => setShowClarificationDialog(false)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>AI Clarification Questions</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            Please answer these questions to help AI provide a more accurate quote:
          </Typography>
          {clarifications.map((question, idx) => (
            <TextField
              key={idx}
              fullWidth
              label={question}
              multiline
              rows={2}
              value={clarificationAnswers[question] || ''}
              onChange={(e) =>
                setClarificationAnswers(prev => ({
                  ...prev,
                  [question]: e.target.value
                }))
              }
              sx={{ mb: 2 }}
            />
          ))}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowClarificationDialog(false)}>
            Skip
          </Button>
          <Button variant="contained" onClick={handleSubmitClarifications}>
            Submit & Analyze
          </Button>
        </DialogActions>
      </Dialog>

      {/* Create Customer Dialog */}
      <Dialog
        open={createCustomerOpen}
        onClose={() => setCreateCustomerOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Create New Customer</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Company Name *"
            value={newCustomer.company_name}
            onChange={(e) => setNewCustomer(prev => ({ ...prev, company_name: e.target.value }))}
            sx={{ mb: 2, mt: 1 }}
            required
          />
          <TextField
            fullWidth
            label="Email"
            type="email"
            value={newCustomer.main_email}
            onChange={(e) => setNewCustomer(prev => ({ ...prev, main_email: e.target.value }))}
            sx={{ mb: 2 }}
          />
          <TextField
            fullWidth
            label="Phone"
            value={newCustomer.main_phone}
            onChange={(e) => setNewCustomer(prev => ({ ...prev, main_phone: e.target.value }))}
            sx={{ mb: 2 }}
          />
          <TextField
            fullWidth
            label="Website"
            value={newCustomer.website}
            onChange={(e) => setNewCustomer(prev => ({ ...prev, website: e.target.value }))}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateCustomerOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={handleCreateCustomer}
            disabled={!newCustomer.company_name}
          >
            Create
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default QuoteNew;

