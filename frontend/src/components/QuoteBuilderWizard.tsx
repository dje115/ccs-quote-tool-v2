import React, { useState, useEffect } from 'react';
import {
  Box,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  Button,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Paper,
  Typography,
  CircularProgress,
  Alert,
  Grid,
  Card,
  CardContent,
  Divider,
  Chip
} from '@mui/material';
import {
  ArrowBack as BackIcon,
  ArrowForward as ForwardIcon,
  Save as SaveIcon,
  Psychology as AiIcon,
  CheckCircle as CheckCircleIcon
} from '@mui/icons-material';
import { quoteAPI, customerAPI } from '../services/api';

interface QuoteBuilderWizardProps {
  onComplete: (quoteId: string) => void;
  onCancel: () => void;
  initialCustomerId?: string;
}

const QuoteBuilderWizard: React.FC<QuoteBuilderWizardProps> = ({
  onComplete,
  onCancel,
  initialCustomerId
}) => {
  const [activeStep, setActiveStep] = useState(0);
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Step 1: Customer/Project Selection
  const [customerId, setCustomerId] = useState<string>(initialCustomerId || '');
  const [quoteTitle, setQuoteTitle] = useState('');
  const [customers, setCustomers] = useState<any[]>([]);
  const [loadingCustomers, setLoadingCustomers] = useState(true);

  // Step 2: Requirements Description
  const [customerRequest, setCustomerRequest] = useState('');
  const [requiredDeadline, setRequiredDeadline] = useState('');
  const [location, setLocation] = useState('');
  const [quantity, setQuantity] = useState<number>(1);

  // Step 3: AI Generation (read-only)
  const [generationProgress, setGenerationProgress] = useState<string>('');
  const [generatedQuoteId, setGeneratedQuoteId] = useState<string | null>(null);

  // Step 4: Review & Edit Documents
  const [documents, setDocuments] = useState<any[]>([]);
  const [selectedDocumentType, setSelectedDocumentType] = useState<string>('');

  useEffect(() => {
    loadCustomers();
  }, []);

  // Update customerId when initialCustomerId changes (e.g., from URL param)
  useEffect(() => {
    if (initialCustomerId && initialCustomerId !== customerId) {
      setCustomerId(initialCustomerId);
    }
  }, [initialCustomerId]);

  // Set customerId after customers are loaded if initialCustomerId is provided
  useEffect(() => {
    if (initialCustomerId && customers.length > 0) {
      // Verify the customer exists in the list
      const customerExists = customers.some(c => c.id === initialCustomerId);
      if (customerExists) {
        setCustomerId(prev => {
          if (prev !== initialCustomerId) {
            console.log('Setting customerId from customers list:', initialCustomerId);
            return initialCustomerId;
          }
          return prev;
        });
      }
    }
  }, [customers, initialCustomerId]);

  const loadCustomers = async () => {
    try {
      setLoadingCustomers(true);
      // Include leads in the customer list for quote creation
      const response = await customerAPI.list({ limit: 1000, exclude_leads: false });
      const customersList = response.data?.items || response.data || [];
      setCustomers(customersList);
      
      // If initialCustomerId is provided and customer exists in the list, set it
      if (initialCustomerId && customersList.length > 0) {
        const customerExists = customersList.some((c: any) => c.id === initialCustomerId);
        if (customerExists) {
          console.log('Setting customerId from initialCustomerId:', initialCustomerId);
          setCustomerId(initialCustomerId);
        } else {
          console.warn('Customer not found in list:', initialCustomerId, 'Available customers:', customersList.map((c: any) => c.id));
        }
      }
    } catch (error) {
      console.error('Error loading customers:', error);
    } finally {
      setLoadingCustomers(false);
    }
  };

  const handleNext = () => {
    if (activeStep === 0) {
      // Validate step 1
      if (!customerId) {
        setError('Please select a customer');
        return;
      }
      if (!quoteTitle) {
        setError('Please enter a quote title');
        return;
      }
    } else if (activeStep === 1) {
      // Validate step 2
      if (!customerRequest.trim()) {
        setError('Please describe what the customer wants');
        return;
      }
      // Move to generation step
      handleGenerateQuote();
      return;
    }
    setError(null);
    setActiveStep((prev) => prev + 1);
  };

  const handleBack = () => {
    setError(null);
    setActiveStep((prev) => prev - 1);
  };

  const handleGenerateQuote = async () => {
    setGenerating(true);
    setError(null);
    setGenerationProgress('Generating quote with AI...');

    try {
      const response = await quoteAPI.generate({
        customer_id: customerId,
        customer_request: customerRequest,
        quote_title: quoteTitle,
        required_deadline: requiredDeadline || undefined,
        location: location || undefined,
        quantity: quantity || undefined
      });

      if (response.data?.success) {
        setGeneratedQuoteId(response.data.quote_id);
        setGenerationProgress('Quote generated successfully!');
        
        // Load documents
        await loadDocuments(response.data.quote_id);
        
        // Move to review step
        setActiveStep(3);
      } else {
        throw new Error(response.data?.error || 'Failed to generate quote');
      }
    } catch (error: any) {
      console.error('Error generating quote:', error);
      setError(error.response?.data?.detail || error.message || 'Failed to generate quote');
    } finally {
      setGenerating(false);
    }
  };

  const loadDocuments = async (quoteId: string) => {
    try {
      const response = await quoteAPI.getDocuments(quoteId);
      if (response.data?.documents) {
        setDocuments(response.data.documents);
      }
    } catch (error) {
      console.error('Error loading documents:', error);
    }
  };

  const handleFinish = () => {
    if (generatedQuoteId) {
      onComplete(generatedQuoteId);
    }
  };

  const handleViewEditDocument = (documentType: string) => {
    if (generatedQuoteId) {
      // Navigate to quote detail page with documents tab open and document ready to edit
      window.location.href = `/quotes/${generatedQuoteId}?tab=documents&edit=${documentType}`;
    }
  };

  const steps = [
    {
      label: 'Customer & Project',
      description: 'Select customer and enter project details'
    },
    {
      label: 'Requirements',
      description: 'Describe what the customer wants (plain English)'
    },
    {
      label: 'AI Generation',
      description: 'AI is generating your quote with all document types'
    },
    {
      label: 'Review & Edit',
      description: 'Review and edit the generated documents'
    }
  ];

  return (
    <Box sx={{ maxWidth: '100%' }}>
      {error && activeStep !== 0 && activeStep !== 1 && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}
      <Stepper activeStep={activeStep} orientation="vertical">
        {/* Step 1: Customer & Project Selection */}
        <Step>
          <StepLabel>
            <Typography variant="h6">{steps[0].label}</Typography>
            <Typography variant="body2" color="text.secondary">
              {steps[0].description}
            </Typography>
          </StepLabel>
          <StepContent>
            {error && (
              <Alert severity="error" sx={{ mb: 2 }}>
                {error}
              </Alert>
            )}
            <Grid container spacing={3} sx={{ mt: 1 }}>
              <Grid item xs={12}>
                <FormControl fullWidth size="medium" sx={{ mb: 2 }}>
                  <InputLabel id="customer-select-label">Customer *</InputLabel>
                  <Select
                    labelId="customer-select-label"
                    value={customerId}
                    label="Customer *"
                    onChange={(e) => setCustomerId(e.target.value)}
                    required
                    disabled={loadingCustomers}
                    sx={{ 
                      minHeight: '56px',
                      fontSize: '1rem',
                      '& .MuiSelect-select': {
                        padding: '16px 14px'
                      }
                    }}
                    MenuProps={{
                      PaperProps: {
                        style: {
                          maxHeight: 400,
                        },
                      },
                    }}
                  >
                    {loadingCustomers ? (
                      <MenuItem value="" disabled>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <CircularProgress size={20} />
                          <Typography>Loading customers...</Typography>
                        </Box>
                      </MenuItem>
                    ) : (
                      [
                        <MenuItem key="placeholder" value="" sx={{ py: 1.5 }}>
                          <em>Select a customer or lead...</em>
                        </MenuItem>,
                        ...customers.map((customer) => (
                          <MenuItem 
                            key={customer.id} 
                            value={customer.id} 
                            sx={{ 
                              fontSize: '1rem', 
                              py: 2,
                              minHeight: '48px',
                              display: 'flex',
                              alignItems: 'center'
                            }}
                          >
                            <Box>
                              <Typography variant="body1" fontWeight="medium">
                                {customer.company_name}
                              </Typography>
                              {customer.status && (
                                <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 0.5 }}>
                                  Status: {customer.status}
                                </Typography>
                              )}
                            </Box>
                          </MenuItem>
                        ))
                      ]
                    )}
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label="Quote Title *"
                  value={quoteTitle}
                  onChange={(e) => setQuoteTitle(e.target.value)}
                  required
                  helperText="Enter a descriptive title for this quote"
                  sx={{
                    '& .MuiInputBase-input': {
                      fontSize: '1rem',
                      padding: '14px 14px'
                    }
                  }}
                />
              </Grid>
            </Grid>
            <Box sx={{ mt: 3, display: 'flex', gap: 2 }}>
              <Button onClick={onCancel} startIcon={<BackIcon />}>
                Cancel
              </Button>
              <Button
                variant="contained"
                onClick={handleNext}
                endIcon={<ForwardIcon />}
                disabled={!customerId || !quoteTitle}
              >
                Next
              </Button>
            </Box>
          </StepContent>
        </Step>

        {/* Step 2: Requirements Description */}
        <Step>
          <StepLabel>
            <Typography variant="h6">{steps[1].label}</Typography>
            <Typography variant="body2" color="text.secondary">
              {steps[1].description}
            </Typography>
          </StepLabel>
          <StepContent>
            {error && (
              <Alert severity="error" sx={{ mb: 2 }}>
                {error}
              </Alert>
            )}
            <Grid container spacing={3} sx={{ mt: 1 }}>
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  multiline
                  rows={8}
                  label="Customer Request *"
                  placeholder="Describe what the customer wants in plain English. Be as detailed as possible. For example: 'We need 12 fibre cores installed between two cabinets' or 'Install Cat6 cabling for a new office building with 50 workstations'"
                  value={customerRequest}
                  onChange={(e) => setCustomerRequest(e.target.value)}
                  required
                  helperText="The AI will use this description to generate a complete quote with all document types. Include details about scope, requirements, and any specific needs."
                  sx={{ mb: 2 }}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Required Deadline (Optional)"
                  type="date"
                  value={requiredDeadline}
                  onChange={(e) => setRequiredDeadline(e.target.value)}
                  InputLabelProps={{ shrink: true }}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Project Location (Optional)"
                  value={location}
                  onChange={(e) => setLocation(e.target.value)}
                  placeholder="e.g., London, UK"
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Quantity (Optional)"
                  type="number"
                  value={quantity}
                  onChange={(e) => setQuantity(parseInt(e.target.value) || 1)}
                  inputProps={{ min: 1 }}
                  helperText="Number of units if applicable"
                />
              </Grid>
            </Grid>
            <Box sx={{ mt: 3, display: 'flex', gap: 2 }}>
              <Button onClick={handleBack} startIcon={<BackIcon />}>
                Back
              </Button>
              <Button
                variant="contained"
                onClick={handleNext}
                endIcon={<AiIcon />}
                disabled={!customerRequest.trim() || generating}
              >
                Generate Quote
              </Button>
            </Box>
          </StepContent>
        </Step>

        {/* Step 3: AI Generation */}
        <Step>
          <StepLabel>
            <Typography variant="h6">{steps[2].label}</Typography>
            <Typography variant="body2" color="text.secondary">
              {steps[2].description}
            </Typography>
          </StepLabel>
          <StepContent>
            <Box sx={{ mt: 2, textAlign: 'center', py: 4 }}>
              {generating ? (
                <>
                  <CircularProgress size={60} sx={{ mb: 2 }} />
                  <Typography variant="body1" sx={{ mt: 2 }}>
                    {generationProgress}
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                    This may take 30-60 seconds...
                  </Typography>
                </>
              ) : generatedQuoteId ? (
                <>
                  <CheckCircleIcon color="success" sx={{ fontSize: 60, mb: 2 }} />
                  <Typography variant="h6" color="success.main">
                    Quote Generated Successfully!
                  </Typography>
                  <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                    Quote ID: {generatedQuoteId}
                  </Typography>
                  <Button
                    variant="contained"
                    onClick={() => setActiveStep(3)}
                    sx={{ mt: 3 }}
                    endIcon={<ForwardIcon />}
                  >
                    Review Documents
                  </Button>
                </>
              ) : (
                <Alert severity="info">
                  Click "Generate Quote" in the previous step to start generation.
                </Alert>
              )}
            </Box>
          </StepContent>
        </Step>

        {/* Step 4: Review & Edit */}
        <Step>
          <StepLabel>
            <Typography variant="h6">{steps[3].label}</Typography>
            <Typography variant="body2" color="text.secondary">
              {steps[3].description}
            </Typography>
          </StepLabel>
          <StepContent>
            {error && (
              <Alert severity="error" sx={{ mb: 2 }}>
                {error}
              </Alert>
            )}

            {documents.length > 0 ? (
              <Grid container spacing={3} sx={{ mt: 1 }}>
                {documents.map((doc) => (
                  <Grid item xs={12} sm={6} md={3} key={doc.id}>
                    <Card sx={{ height: '100%', display: 'flex', flexDirection: 'column' }}>
                      <CardContent sx={{ flexGrow: 1, display: 'flex', flexDirection: 'column' }}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                          <Typography variant="h6" sx={{ fontSize: '1rem', fontWeight: 600 }}>
                            {doc.document_type.replace('_', ' ').replace(/\b\w/g, l => l.toUpperCase())}
                          </Typography>
                          <Chip label={`v${doc.version}`} size="small" color="primary" />
                        </Box>
                        <Typography variant="body2" color="text.secondary" sx={{ mb: 2, fontSize: '0.75rem', flexGrow: 1 }}>
                          Created: {new Date(doc.created_at).toLocaleDateString()}
                        </Typography>
                        <Button
                          variant="outlined"
                          size="small"
                          fullWidth
                          onClick={() => handleViewEditDocument(doc.document_type)}
                        >
                          View & Edit
                        </Button>
                      </CardContent>
                    </Card>
                  </Grid>
                ))}
              </Grid>
            ) : (
              <Alert severity="info" sx={{ mt: 2 }}>
                No documents found. Please generate the quote first.
              </Alert>
            )}

            <Box sx={{ mt: 3, display: 'flex', gap: 2 }}>
              <Button onClick={handleBack} startIcon={<BackIcon />}>
                Back
              </Button>
              <Button
                variant="contained"
                onClick={handleFinish}
                endIcon={<CheckCircleIcon />}
                disabled={!generatedQuoteId}
              >
                Complete
              </Button>
            </Box>
          </StepContent>
        </Step>
      </Stepper>
    </Box>
  );
};

export default QuoteBuilderWizard;

