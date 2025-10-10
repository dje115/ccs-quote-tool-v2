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
  TextField
} from '@mui/material';
import {
  ArrowBack as BackIcon,
  Edit as EditIcon,
  Add as AddIcon,
  Phone as PhoneIcon,
  Email as EmailIcon,
  Language as WebsiteIcon,
  Business as BusinessIcon
} from '@mui/icons-material';
import { useNavigate, useParams } from 'react-router-dom';
import { customerAPI, contactAPI, quoteAPI } from '../services/api';

const CustomerDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [customer, setCustomer] = useState<any>(null);
  const [contacts, setContacts] = useState<any[]>([]);
  const [quotes, setQuotes] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [addContactOpen, setAddContactOpen] = useState(false);

  useEffect(() => {
    if (id) {
      loadCustomerData();
    }
  }, [id]);

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

  if (loading) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <Typography>Loading...</Typography>
      </Container>
    );
  }

  if (!customer) {
    return (
      <Container maxWidth="lg" sx={{ mt: 4 }}>
        <Typography>Customer not found</Typography>
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
          {customer.company_name}
        </Typography>
        <Button
          variant="outlined"
          startIcon={<EditIcon />}
          onClick={() => navigate(`/customers/${id}/edit`)}
        >
          Edit
        </Button>
      </Box>

      <Grid container spacing={3}>
        {/* Customer Information */}
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
                      Business Type
                    </Typography>
                    <Typography>{customer.business_type || 'N/A'}</Typography>
                  </Box>
                </Box>
              </Grid>

              <Grid item xs={12} sm={6}>
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                  <BusinessIcon color="action" />
                  <Box>
                    <Typography variant="caption" color="text.secondary">
                      Business Sector
                    </Typography>
                    <Typography>{customer.business_sector || 'N/A'}</Typography>
                  </Box>
                </Box>
              </Grid>

              {customer.website && (
                <Grid item xs={12}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                    <WebsiteIcon color="action" />
                    <Box>
                      <Typography variant="caption" color="text.secondary">
                        Website
                      </Typography>
                      <Typography>
                        <a href={customer.website} target="_blank" rel="noopener noreferrer">
                          {customer.website}
                        </a>
                      </Typography>
                    </Box>
                  </Box>
                </Grid>
              )}

              {customer.contact_email && (
                <Grid item xs={12} sm={6}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                    <EmailIcon color="action" />
                    <Box>
                      <Typography variant="caption" color="text.secondary">
                        Email
                      </Typography>
                      <Typography>{customer.contact_email}</Typography>
                    </Box>
                  </Box>
                </Grid>
              )}

              {customer.contact_phone && (
                <Grid item xs={12} sm={6}>
                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                    <PhoneIcon color="action" />
                    <Box>
                      <Typography variant="caption" color="text.secondary">
                        Phone
                      </Typography>
                      <Typography>{customer.contact_phone}</Typography>
                    </Box>
                  </Box>
                </Grid>
              )}

              {customer.employee_count_estimate && (
                <Grid item xs={12} sm={6}>
                  <Typography variant="caption" color="text.secondary">
                    Employees (Estimate)
                  </Typography>
                  <Typography>{customer.employee_count_estimate}</Typography>
                </Grid>
              )}

              {customer.annual_revenue_estimate && (
                <Grid item xs={12} sm={6}>
                  <Typography variant="caption" color="text.secondary">
                    Annual Revenue (Estimate)
                  </Typography>
                  <Typography>£{customer.annual_revenue_estimate?.toLocaleString()}</Typography>
                </Grid>
              )}
            </Grid>

            {customer.notes && (
              <Box sx={{ mt: 3 }}>
                <Typography variant="caption" color="text.secondary">
                  Notes
                </Typography>
                <Typography>{customer.notes}</Typography>
              </Box>
            )}
          </Paper>

          {/* Contacts */}
          <Paper sx={{ p: 3, mb: 3 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">
                Contacts ({contacts.length})
              </Typography>
              <Button
                size="small"
                startIcon={<AddIcon />}
                onClick={() => setAddContactOpen(true)}
              >
                Add Contact
              </Button>
            </Box>
            <Divider sx={{ mb: 2 }} />

            {contacts.length === 0 ? (
              <Typography color="text.secondary">No contacts yet</Typography>
            ) : (
              <List>
                {contacts.map((contact) => (
                  <ListItem key={contact.id}>
                    <ListItemText
                      primary={`${contact.first_name} ${contact.last_name}`}
                      secondary={
                        <>
                          {contact.job_title && <>{contact.job_title}<br /></>}
                          {contact.email && <>{contact.email}<br /></>}
                          {contact.phone && <>{contact.phone}</>}
                        </>
                      }
                    />
                    {contact.is_primary && (
                      <Chip label="Primary" size="small" color="primary" />
                    )}
                  </ListItem>
                ))}
              </List>
            )}
          </Paper>

          {/* Quotes */}
          <Paper sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">
                Quotes ({quotes.length})
              </Typography>
              <Button
                size="small"
                startIcon={<AddIcon />}
                onClick={() => navigate(`/quotes/new?customer=${id}`)}
              >
                Create Quote
              </Button>
            </Box>
            <Divider sx={{ mb: 2 }} />

            {quotes.length === 0 ? (
              <Typography color="text.secondary">No quotes yet</Typography>
            ) : (
              <List>
                {quotes.map((quote) => (
                  <ListItem
                    key={quote.id}
                    button
                    onClick={() => navigate(`/quotes/${quote.id}`)}
                  >
                    <ListItemText
                      primary={quote.title}
                      secondary={`${quote.quote_number} - £${quote.total_amount?.toLocaleString()}`}
                    />
                    <Chip label={quote.status} size="small" />
                  </ListItem>
                ))}
              </List>
            )}
          </Paper>
        </Grid>

        {/* Sidebar */}
        <Grid item xs={12} md={4}>
          <Card sx={{ mb: 3 }}>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Status
              </Typography>
              <Chip
                label={customer.status}
                color={customer.status === 'active' ? 'success' : 'default'}
                sx={{ mb: 2 }}
              />

              <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
                Lead Score
              </Typography>
              <Chip label={customer.lead_score || 0} color="primary" />

              <Typography variant="caption" display="block" sx={{ mt: 2 }} color="text.secondary">
                Created: {new Date(customer.created_at).toLocaleDateString()}
              </Typography>
            </CardContent>
          </Card>

          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Quick Actions
              </Typography>
              <Button
                fullWidth
                variant="outlined"
                sx={{ mb: 1 }}
                onClick={() => navigate(`/quotes/new?customer=${id}`)}
              >
                Create Quote
              </Button>
              <Button
                fullWidth
                variant="outlined"
                sx={{ mb: 1 }}
                onClick={() => setAddContactOpen(true)}
              >
                Add Contact
              </Button>
              <Button
                fullWidth
                variant="outlined"
                onClick={() => navigate(`/customers/${id}/edit`)}
              >
                Edit Customer
              </Button>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Container>
  );
};

export default CustomerDetail;

