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
  TextField,
  InputAdornment,
  Pagination,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  CircularProgress,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Stack,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ToggleButtonGroup,
  ToggleButton
} from '@mui/material';
import {
  Add as AddIcon,
  Visibility as ViewIcon,
  Search as SearchIcon,
  CheckCircle as CheckIcon
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { quoteAPI, customerAPI } from '../services/api';
import { Quote, PaginatedQuoteResponse } from '../types';

const Quotes: React.FC = () => {
  const navigate = useNavigate();
  const [quotes, setQuotes] = useState<Quote[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [total, setTotal] = useState(0);
  const [totalPages, setTotalPages] = useState(1);
  const [manualDialogOpen, setManualDialogOpen] = useState(false);
  const [manualCustomers, setManualCustomers] = useState<any[]>([]);
  const [manualLoading, setManualLoading] = useState(false);
  const [manualSaving, setManualSaving] = useState(false);
  const [manualForm, setManualForm] = useState({
    customer_id: '',
    title: '',
    description: ''
  });
  const [manualError, setManualError] = useState<string | null>(null);
  const [manualCustomerMode, setManualCustomerMode] = useState<'existing' | 'new'>('existing');
  const [newManualCustomer, setNewManualCustomer] = useState({
    company_name: '',
    main_email: '',
    main_phone: '',
    website: ''
  });

  useEffect(() => {
    loadQuotes();
  }, [page, pageSize, searchTerm]);

  const loadQuotes = async () => {
    try {
      setLoading(true);
      const skip = (page - 1) * pageSize;
      const response = await quoteAPI.list({
        skip,
        limit: pageSize,
        search: searchTerm || undefined
      });
      
      // Handle both old format (array) and new format (paginated response)
      if (Array.isArray(response.data)) {
        setQuotes(response.data as Quote[]);
        setTotal(response.data.length);
        setTotalPages(1);
      } else {
        const paginatedData = response.data as PaginatedQuoteResponse;
        setQuotes(paginatedData.items || []);
        setTotal(paginatedData.total || 0);
        setTotalPages(paginatedData.total_pages || 1);
      }
    } catch (error) {
      console.error('Error loading quotes:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSearchChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setSearchTerm(e.target.value);
    setPage(1); // Reset to first page on search
  };

  const handlePageChange = (_event: React.ChangeEvent<unknown>, value: number) => {
    setPage(value);
  };

  const handlePageSizeChange = (e: React.ChangeEvent<{ value: unknown }>) => {
    setPageSize(e.target.value as number);
    setPage(1); // Reset to first page when changing page size
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'draft':
        return 'default';
      case 'sent':
        return 'info';
      case 'accepted':
        return 'success';
      case 'rejected':
        return 'error';
      case 'expired':
        return 'warning';
      default:
        return 'default';
    }
  };

  const handleManualQuoteClick = () => {
    setManualDialogOpen(true);
    setManualError(null);
    setManualCustomerMode('existing');
    if (manualCustomers.length === 0) {
      loadManualCustomers();
    }
  };

  const loadManualCustomers = async () => {
    try {
      setManualLoading(true);
      // Include leads in the customer list for manual quote creation
      const response = await customerAPI.list({ limit: 100, exclude_leads: false });
      setManualCustomers(response.data || []);
    } catch (error) {
      console.error('Error loading customers for manual quote', error);
    } finally {
      setManualLoading(false);
    }
  };

  const handleManualCreate = async () => {
    if (!manualForm.title) {
      setManualError('Please enter a quote title.');
      return;
    }
    if (manualCustomerMode === 'existing' && !manualForm.customer_id) {
      setManualError('Please select a customer.');
      return;
    }
    if (manualCustomerMode === 'new' && !newManualCustomer.company_name) {
      setManualError('Please enter a company name for the new customer.');
      return;
    }

    try {
      setManualSaving(true);
      setManualError(null);
      let customerId = manualForm.customer_id;

      if (manualCustomerMode === 'new') {
        const createResponse = await customerAPI.create({
          company_name: newManualCustomer.company_name,
          main_email: newManualCustomer.main_email || undefined,
          main_phone: newManualCustomer.main_phone || undefined,
          website: newManualCustomer.website || undefined
        });
        customerId = createResponse.data?.id;
        if (!customerId) {
          throw new Error('Customer creation failed.');
        }
      }

      const response = await quoteAPI.create({
        customer_id: customerId,
        title: manualForm.title,
        description: manualForm.description || undefined
      });
      const newQuote = response.data;
      setManualDialogOpen(false);
      setManualForm({ customer_id: '', title: '', description: '' });
      setNewManualCustomer({ company_name: '', main_email: '', main_phone: '', website: '' });
      navigate(`/quotes/${newQuote.id}?tab=line-items`);
    } catch (error: any) {
      console.error('Failed to create manual quote', error);
      setManualError(error.response?.data?.detail || 'Unable to create quote. Please try again.');
    } finally {
      setManualSaving(false);
    }
  };

  return (
    <Container maxWidth="xl" sx={{ py: 3, width: '100%', height: '100%' }}>
      {/* Clean Centered Header */}
      <Box sx={{ textAlign: 'center', mb: 4 }}>
        <Typography variant="h3" fontWeight="700" color="primary" gutterBottom>
          Quotes
        </Typography>
        <Typography variant="h6" color="text.secondary" sx={{ mb: 3 }}>
          Professional Quote Management & Pricing
        </Typography>
        <Stack direction={{ xs: 'column', sm: 'row' }} justifyContent="center" spacing={2}>
          <Button
            variant="contained"
            startIcon={<AddIcon />}
            onClick={() => navigate('/quotes/new')}
            sx={{
              borderRadius: 2,
              px: 3,
              py: 1.5,
              fontWeight: 600,
              textTransform: 'none'
            }}
          >
            AI-Powered Quote
          </Button>
          <Button
            variant="outlined"
            startIcon={<AddIcon />}
            onClick={handleManualQuoteClick}
            sx={{
              borderRadius: 2,
              px: 3,
              py: 1.5,
              fontWeight: 600,
              textTransform: 'none'
            }}
          >
            Manual Quote
          </Button>
        </Stack>
      </Box>

      <Paper sx={{ p: 2, mb: 3 }}>
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          <TextField
            fullWidth
            placeholder="Search quotes by title, quote number, or project..."
            value={searchTerm}
            onChange={handleSearchChange}
            InputProps={{
              startAdornment: (
                <InputAdornment position="start">
                  <SearchIcon />
                </InputAdornment>
              ),
            }}
          />
          <FormControl sx={{ minWidth: 120 }}>
            <InputLabel>Page Size</InputLabel>
            <Select
              value={pageSize}
              label="Page Size"
              onChange={handlePageSizeChange}
            >
              <MenuItem value={10}>10</MenuItem>
              <MenuItem value={20}>20</MenuItem>
              <MenuItem value={50}>50</MenuItem>
              <MenuItem value={100}>100</MenuItem>
            </Select>
          </FormControl>
        </Box>
      </Paper>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Quote Number</TableCell>
              <TableCell>Title</TableCell>
              <TableCell>Customer</TableCell>
              <TableCell>Status</TableCell>
              <TableCell align="right">Total Amount</TableCell>
              <TableCell>Valid Until</TableCell>
              <TableCell>Created</TableCell>
              <TableCell align="right">Actions</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {loading ? (
              <TableRow>
                <TableCell colSpan={8} align="center">
                  <CircularProgress size={24} />
                </TableCell>
              </TableRow>
            ) : quotes.length === 0 ? (
              <TableRow>
                <TableCell colSpan={8} align="center">
                  No quotes found. Create your first quote!
                </TableCell>
              </TableRow>
            ) : (
              quotes.map((quote) => (
                <TableRow key={quote.id} hover>
                  <TableCell>{quote.quote_number}</TableCell>
                  <TableCell>{quote.title}</TableCell>
                  <TableCell>{quote.customer_id}</TableCell>
                  <TableCell>
                    <Chip
                      label={quote.status}
                      color={getStatusColor(quote.status)}
                      size="small"
                    />
                  </TableCell>
                  <TableCell align="right">
                    £{quote.total_amount?.toLocaleString() || '0.00'}
                  </TableCell>
                  <TableCell>
                    {quote.valid_until
                      ? new Date(quote.valid_until).toLocaleDateString()
                      : '-'}
                  </TableCell>
                  <TableCell>
                    {new Date(quote.created_at).toLocaleDateString()}
                  </TableCell>
                  <TableCell align="right">
                    <IconButton
                      size="small"
                      onClick={() => navigate(`/quotes/${quote.id}`)}
                    >
                      <ViewIcon />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))
            )}
          </TableBody>
        </Table>
      </TableContainer>

      <Box sx={{ mt: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="body2" color="text.secondary">
          Showing {quotes.length > 0 ? (page - 1) * pageSize + 1 : 0} - {Math.min(page * pageSize, total)} of {total} quotes
        </Typography>
        {totalPages > 1 && (
          <Pagination
            count={totalPages}
            page={page}
            onChange={handlePageChange}
            color="primary"
            showFirstButton
            showLastButton
          />
        )}
      </Box>

      <Dialog
        open={manualDialogOpen}
        onClose={() => setManualDialogOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Create Manual Quote</DialogTitle>
        <DialogContent dividers>
          <Typography variant="body2" color="text.secondary" gutterBottom>
            Build a quote line-by-line using the spreadsheet-style editor. Perfect for complex scopes, bundles, and supplier-specific pricing.
          </Typography>
          <List dense>
            {[
              'Section-based line items with optional & alternate toggles',
              'Live margin, tax, and total calculations',
              'Autosave-ready editing connected directly to the CRM'
            ].map((item, index) => (
              <ListItem key={index}>
                <ListItemIcon>
                  <CheckIcon color="success" />
                </ListItemIcon>
                <ListItemText primary={item} />
              </ListItem>
            ))}
          </List>
          <Box sx={{ mt: 2, display: 'flex', flexDirection: 'column', gap: 2 }}>
            <ToggleButtonGroup
              value={manualCustomerMode}
              exclusive
              onChange={(_event, value) => {
                if (value) {
                  setManualCustomerMode(value);
                  setManualError(null);
                }
              }}
            >
              <ToggleButton value="existing" sx={{ flex: 1 }}>
                Existing Customer
              </ToggleButton>
              <ToggleButton value="new" sx={{ flex: 1 }}>
                New Customer
              </ToggleButton>
            </ToggleButtonGroup>

            {manualCustomerMode === 'existing' ? (
              <FormControl fullWidth>
                <InputLabel id="manual-customer-label">Customer</InputLabel>
                <Select
                  labelId="manual-customer-label"
                  label="Customer"
                  value={manualForm.customer_id}
                  onChange={(event) =>
                    setManualForm((prev) => ({ ...prev, customer_id: event.target.value as string }))
                  }
                  disabled={manualLoading}
                >
                  {manualCustomers.map((customer) => (
                    <MenuItem key={customer.id} value={customer.id}>
                      {customer.company_name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            ) : (
              <>
                <TextField
                  label="Company Name"
                  required
                  value={newManualCustomer.company_name}
                  onChange={(event) =>
                    setNewManualCustomer((prev) => ({ ...prev, company_name: event.target.value }))
                  }
                />
                <TextField
                  label="Contact Email"
                  type="email"
                  value={newManualCustomer.main_email}
                  onChange={(event) =>
                    setNewManualCustomer((prev) => ({ ...prev, main_email: event.target.value }))
                  }
                />
                <TextField
                  label="Phone"
                  value={newManualCustomer.main_phone}
                  onChange={(event) =>
                    setNewManualCustomer((prev) => ({ ...prev, main_phone: event.target.value }))
                  }
                />
                <TextField
                  label="Website"
                  value={newManualCustomer.website}
                  onChange={(event) =>
                    setNewManualCustomer((prev) => ({ ...prev, website: event.target.value }))
                  }
                />
              </>
            )}
            <TextField
              label="Quote Title"
              fullWidth
              value={manualForm.title}
              onChange={(event) => setManualForm((prev) => ({ ...prev, title: event.target.value }))}
            />
            <TextField
              label="Overview / Notes"
              fullWidth
              multiline
              minRows={3}
              value={manualForm.description}
              onChange={(event) =>
                setManualForm((prev) => ({ ...prev, description: event.target.value }))
              }
            />
            {manualError && (
              <Typography variant="body2" color="error">
                {manualError}
              </Typography>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setManualDialogOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={handleManualCreate}
            disabled={manualSaving || !manualForm.customer_id || !manualForm.title}
          >
            {manualSaving ? 'Creating...' : 'Launch Manual Builder'}
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default Quotes;


