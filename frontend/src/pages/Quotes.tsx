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
  InputAdornment
} from '@mui/material';
import {
  Add as AddIcon,
  Visibility as ViewIcon,
  Search as SearchIcon
} from '@mui/icons-material';
import { useNavigate } from 'react-router-dom';
import { quoteAPI } from '../services/api';

const Quotes: React.FC = () => {
  const navigate = useNavigate();
  const [quotes, setQuotes] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

  useEffect(() => {
    loadQuotes();
  }, []);

  const loadQuotes = async () => {
    try {
      setLoading(true);
      const response = await quoteAPI.list();
      setQuotes(response.data);
    } catch (error) {
      console.error('Error loading quotes:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredQuotes = quotes.filter(quote =>
    quote.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    quote.quote_number.toLowerCase().includes(searchTerm.toLowerCase())
  );

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

  return (
    <Container maxWidth="lg">
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" component="h1">
          Quotes
        </Typography>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={() => navigate('/quotes/new')}
        >
          Create Quote
        </Button>
      </Box>

      <Paper sx={{ p: 2, mb: 3 }}>
        <TextField
          fullWidth
          placeholder="Search quotes..."
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          InputProps={{
            startAdornment: (
              <InputAdornment position="start">
                <SearchIcon />
              </InputAdornment>
            ),
          }}
        />
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
                  Loading...
                </TableCell>
              </TableRow>
            ) : filteredQuotes.length === 0 ? (
              <TableRow>
                <TableCell colSpan={8} align="center">
                  No quotes found. Create your first quote!
                </TableCell>
              </TableRow>
            ) : (
              filteredQuotes.map((quote) => (
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

      <Box sx={{ mt: 2 }}>
        <Typography variant="body2" color="text.secondary">
          Total: {filteredQuotes.length} quotes
        </Typography>
      </Box>
    </Container>
  );
};

export default Quotes;




