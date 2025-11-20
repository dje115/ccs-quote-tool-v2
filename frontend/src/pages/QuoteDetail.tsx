import React, { useEffect, useState } from 'react';
import {
  Container,
  Paper,
  Typography,
  Box,
  Button,
  Chip,
  Divider,
  Grid,
  Card,
  CardContent,
  CircularProgress,
  Alert,
  Tabs,
  Tab,
  List,
  ListItem,
  ListItemText
} from '@mui/material';
import {
  ArrowBack as BackIcon,
  Edit as EditIcon,
  Download as DownloadIcon,
  Send as SendIcon
} from '@mui/icons-material';
import { useNavigate, useParams, useSearchParams } from 'react-router-dom';
import { quoteAPI } from '../services/api';
import QuoteAICopilot from '../components/QuoteAICopilot';
import QuoteDocumentViewer from '../components/QuoteDocumentViewer';
import QuoteDocumentEditor from '../components/QuoteDocumentEditor';
import QuotePromptManager from '../components/QuotePromptManager';

const QuoteDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const [quote, setQuote] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [currentTab, setCurrentTab] = useState(0);
  const [editingDocument, setEditingDocument] = useState<string | null>(null);

  useEffect(() => {
    if (id) {
      loadQuote();
      
      // Check URL params for tab and edit document
      const tabParam = searchParams.get('tab');
      const editParam = searchParams.get('edit');
      
      if (tabParam === 'documents') {
        setCurrentTab(2); // Documents tab is index 2
      }
      
      if (editParam) {
        setEditingDocument(editParam);
      }
    }
  }, [id, searchParams]);

  const loadQuote = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await quoteAPI.get(id!);
      setQuote(response.data);
    } catch (error: any) {
      console.error('Error loading quote:', error);
      setError(error.response?.data?.detail || 'Failed to load quote');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ py: 3, display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '50vh' }}>
        <CircularProgress />
      </Container>
    );
  }

  if (error || !quote) {
    return (
      <Container maxWidth="lg" sx={{ py: 3 }}>
        <Alert severity="error">{error || 'Quote not found'}</Alert>
        <Button startIcon={<BackIcon />} onClick={() => navigate('/quotes')} sx={{ mt: 2 }}>
          Back to Quotes
        </Button>
      </Container>
    );
  }

  return (
    <Container maxWidth="lg" sx={{ py: 3 }}>
      <Box sx={{ mb: 3, display: 'flex', alignItems: 'center', gap: 2 }}>
        <Button startIcon={<BackIcon />} onClick={() => navigate('/quotes')}>
          Back
        </Button>
        <Typography variant="h4" component="h1">
          Quote: {quote.quote_number || quote.title}
        </Typography>
        <Chip
          label={quote.status || 'DRAFT'}
          color={quote.status === 'accepted' ? 'success' : quote.status === 'rejected' ? 'error' : 'default'}
          sx={{ ml: 'auto' }}
        />
      </Box>

      <Paper sx={{ p: 3 }}>
        <Tabs value={currentTab} onChange={(e, newValue) => setCurrentTab(newValue)} sx={{ mb: 3 }}>
          <Tab label="Overview" />
          <Tab label="Project Details" />
          <Tab label="Documents" />
          <Tab label="AI Analysis" />
          <Tab label="Pricing" />
          <Tab label="AI Prompt" />
        </Tabs>

        {currentTab === 0 && (
          <Box>
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <Typography variant="h6" gutterBottom>
                  Quote Information
                </Typography>
                <List>
                  <ListItem>
                    <ListItemText primary="Quote Number" secondary={quote.quote_number || 'N/A'} />
                  </ListItem>
                  <ListItem>
                    <ListItemText primary="Title" secondary={quote.title || 'N/A'} />
                  </ListItem>
                  <ListItem>
                    <ListItemText primary="Status" secondary={quote.status || 'DRAFT'} />
                  </ListItem>
                  <ListItem>
                    <ListItemText primary="Total Amount" secondary={quote.total_amount ? `£${parseFloat(quote.total_amount).toFixed(2)}` : 'N/A'} />
                  </ListItem>
                </List>
              </Grid>
              <Grid item xs={12} md={6}>
                <Typography variant="h6" gutterBottom>
                  Dates
                </Typography>
                <List>
                  <ListItem>
                    <ListItemText primary="Created" secondary={quote.created_at ? new Date(quote.created_at).toLocaleDateString() : 'N/A'} />
                  </ListItem>
                  {quote.valid_until && (
                    <ListItem>
                      <ListItemText primary="Valid Until" secondary={new Date(quote.valid_until).toLocaleDateString()} />
                    </ListItem>
                  )}
                </List>
              </Grid>
            </Grid>

            <Divider sx={{ my: 3 }} />

            <Box sx={{ display: 'flex', gap: 2 }}>
              <Button variant="outlined" startIcon={<EditIcon />}>
                Edit Quote
              </Button>
              <Button variant="outlined" startIcon={<DownloadIcon />}>
                Download PDF
              </Button>
              <Button variant="outlined" startIcon={<SendIcon />}>
                Send Quote
              </Button>
            </Box>
          </Box>
        )}

        {currentTab === 1 && (
          <Box>
            <Typography variant="h6" gutterBottom>
              Project Details
            </Typography>
            <Grid container spacing={2} sx={{ mt: 1 }}>
              {quote.project_title && (
                <Grid item xs={12}>
                  <Typography variant="subtitle2">Project Title</Typography>
                  <Typography variant="body2" color="text.secondary">{quote.project_title}</Typography>
                </Grid>
              )}
              {quote.site_address && (
                <Grid item xs={12}>
                  <Typography variant="subtitle2">Site Address</Typography>
                  <Typography variant="body2" color="text.secondary">{quote.site_address}</Typography>
                </Grid>
              )}
              {quote.building_type && (
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2">Building Type</Typography>
                  <Typography variant="body2" color="text.secondary">{quote.building_type}</Typography>
                </Grid>
              )}
              {quote.building_size && (
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2">Building Size</Typography>
                  <Typography variant="body2" color="text.secondary">{quote.building_size} sqm</Typography>
                </Grid>
              )}
              {quote.number_of_floors && (
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2">Number of Floors</Typography>
                  <Typography variant="body2" color="text.secondary">{quote.number_of_floors}</Typography>
                </Grid>
              )}
              {quote.number_of_rooms && (
                <Grid item xs={12} sm={6}>
                  <Typography variant="subtitle2">Number of Rooms</Typography>
                  <Typography variant="body2" color="text.secondary">{quote.number_of_rooms}</Typography>
                </Grid>
              )}
              {quote.description && (
                <Grid item xs={12}>
                  <Typography variant="subtitle2">Description</Typography>
                  <Typography variant="body2" color="text.secondary">{quote.description}</Typography>
                </Grid>
              )}
            </Grid>
          </Box>
        )}

        {currentTab === 2 && (
          <Box>
            {editingDocument ? (
              <QuoteDocumentEditor
                quoteId={quote.id}
                documentType={editingDocument}
                onSave={() => {
                  setEditingDocument(null);
                  loadQuote();
                }}
                onCancel={() => setEditingDocument(null)}
              />
            ) : (
              <QuoteDocumentViewer
                quoteId={quote.id}
                onEdit={(documentType) => setEditingDocument(documentType)}
              />
            )}
          </Box>
        )}

        {currentTab === 3 && (
          <Grid container spacing={3}>
            <Grid item xs={12} md={8}>
              <Box>
                <Typography variant="h6" gutterBottom>
                  AI Analysis
                </Typography>
                {quote.ai_analysis ? (
                  <Card sx={{ mt: 2 }}>
                    <CardContent>
                      <Typography variant="body2" style={{ whiteSpace: 'pre-wrap' }}>
                        {typeof quote.ai_analysis === 'string' ? quote.ai_analysis : JSON.stringify(quote.ai_analysis, null, 2)}
                      </Typography>
                    </CardContent>
                  </Card>
                ) : (
                  <Alert severity="info" sx={{ mt: 2 }}>No AI analysis available for this quote.</Alert>
                )}
              </Box>
            </Grid>
            <Grid item xs={12} md={4}>
              <QuoteAICopilot quoteId={quote.id} compact={true} />
            </Grid>
          </Grid>
        )}

        {currentTab === 4 && (
          <Box>
            <Typography variant="h6" gutterBottom>
              Pricing Breakdown
            </Typography>
            <Grid container spacing={2} sx={{ mt: 1 }}>
              <Grid item xs={12} sm={6}>
                <Typography variant="subtitle2">Subtotal</Typography>
                <Typography variant="h6">£{quote.subtotal ? parseFloat(quote.subtotal).toFixed(2) : '0.00'}</Typography>
              </Grid>
              <Grid item xs={12} sm={6}>
                <Typography variant="subtitle2">Tax ({quote.tax_rate ? (quote.tax_rate * 100).toFixed(0) : 20}%)</Typography>
                <Typography variant="h6">£{quote.tax_amount ? parseFloat(quote.tax_amount).toFixed(2) : '0.00'}</Typography>
              </Grid>
              <Grid item xs={12}>
                <Divider sx={{ my: 2 }} />
                <Typography variant="subtitle2">Total Amount</Typography>
                <Typography variant="h4" color="primary">£{quote.total_amount ? parseFloat(quote.total_amount).toFixed(2) : '0.00'}</Typography>
              </Grid>
            </Grid>
          </Box>
        )}

        {currentTab === 5 && (
          <Box>
            <QuotePromptManager quoteId={quote.id} />
          </Box>
        )}
      </Paper>
    </Container>
  );
};

export default QuoteDetail;

