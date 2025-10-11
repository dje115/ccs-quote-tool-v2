import React, { useEffect, useState } from 'react';
import {
  Container,
  Paper,
  Typography,
  Box,
  TextField,
  Button,
  Grid,
  Alert,
  CircularProgress,
  IconButton
} from '@mui/material';
import {
  ArrowBack as BackIcon,
  Save as SaveIcon
} from '@mui/icons-material';
import { useNavigate, useParams } from 'react-router-dom';
import { customerAPI } from '../services/api';

const CustomerEdit: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [customer, setCustomer] = useState<any>(null);
  
  const [formData, setFormData] = useState({
    company_name: '',
    company_registration: '',
    website: '',
    main_email: '',
    main_phone: '',
    billing_address: '',
    billing_postcode: '',
    description: ''
  });

  useEffect(() => {
    loadCustomer();
  }, [id]);

  const loadCustomer = async () => {
    try {
      setLoading(true);
      const response = await customerAPI.get(id!);
      setCustomer(response.data);
      
      // Populate form with existing data
      setFormData({
        company_name: response.data.company_name || '',
        company_registration: response.data.company_registration || '',
        website: response.data.website || '',
        main_email: response.data.main_email || '',
        main_phone: response.data.main_phone || '',
        billing_address: response.data.billing_address || '',
        billing_postcode: response.data.billing_postcode || '',
        description: response.data.description || ''
      });
    } catch (error: any) {
      console.error('Error loading customer:', error);
      setError('Failed to load customer');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);
    setSaving(true);

    try {
      await customerAPI.update(id!, formData);
      setSuccess('Customer updated successfully!');
      setTimeout(() => {
        navigate(`/customers/${id}`);
      }, 1500);
    } catch (error: any) {
      console.error('Error updating customer:', error);
      setError(error.response?.data?.detail || 'Failed to update customer');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <Container maxWidth="md" sx={{ mt: 4, display: 'flex', justifyContent: 'center' }}>
        <CircularProgress />
      </Container>
    );
  }

  return (
    <Container maxWidth="md" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ mb: 3, display: 'flex', alignItems: 'center', gap: 2 }}>
        <IconButton onClick={() => navigate(`/customers/${id}`)}>
          <BackIcon />
        </IconButton>
        <Typography variant="h4" component="h1">
          Edit Customer
        </Typography>
      </Box>

      {error && (
        <Alert severity="error" onClose={() => setError(null)} sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" onClose={() => setSuccess(null)} sx={{ mb: 2 }}>
          {success}
        </Alert>
      )}

      <Paper sx={{ p: 4 }}>
        <form onSubmit={handleSubmit}>
          <Grid container spacing={3}>
            {/* Company Name */}
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Company Name"
                name="company_name"
                value={formData.company_name}
                onChange={handleChange}
                required
                variant="outlined"
              />
            </Grid>

            {/* Website */}
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Website"
                name="website"
                value={formData.website}
                onChange={handleChange}
                placeholder="https://example.com"
                variant="outlined"
              />
            </Grid>

            {/* Company Registration */}
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Company Registration Number"
                name="company_registration"
                value={formData.company_registration}
                onChange={handleChange}
                placeholder="e.g., 12345678"
                variant="outlined"
              />
            </Grid>

            {/* Email */}
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Main Email"
                name="main_email"
                type="email"
                value={formData.main_email}
                onChange={handleChange}
                placeholder="info@example.com"
                variant="outlined"
              />
            </Grid>

            {/* Phone */}
            <Grid item xs={12} sm={6}>
              <TextField
                fullWidth
                label="Main Phone"
                name="main_phone"
                value={formData.main_phone}
                onChange={handleChange}
                placeholder="01234 567890"
                variant="outlined"
              />
            </Grid>

            {/* Billing Address */}
            <Grid item xs={12} sm={8}>
              <TextField
                fullWidth
                label="Billing Address"
                name="billing_address"
                value={formData.billing_address}
                onChange={handleChange}
                multiline
                rows={2}
                variant="outlined"
              />
            </Grid>

            {/* Billing Postcode */}
            <Grid item xs={12} sm={4}>
              <TextField
                fullWidth
                label="Postcode"
                name="billing_postcode"
                value={formData.billing_postcode}
                onChange={handleChange}
                placeholder="SW1A 1AA"
                variant="outlined"
              />
            </Grid>

            {/* Description */}
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Description / Notes"
                name="description"
                value={formData.description}
                onChange={handleChange}
                multiline
                rows={4}
                variant="outlined"
                placeholder="Additional notes about this customer..."
              />
            </Grid>

            {/* Created & Updated Dates (Read-only) */}
            {customer && (
              <Grid item xs={12}>
                <Box sx={{ mt: 2, p: 2, bgcolor: '#f5f5f5', borderRadius: 1 }}>
                  <Typography variant="caption" color="text.secondary" display="block" gutterBottom>
                    Record Information
                  </Typography>
                  <Grid container spacing={2}>
                    <Grid item xs={12} sm={6}>
                      <Typography variant="body2">
                        <strong>Created:</strong> {new Date(customer.created_at).toLocaleString('en-GB', {
                          year: 'numeric',
                          month: 'short',
                          day: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit'
                        })}
                      </Typography>
                    </Grid>
                    <Grid item xs={12} sm={6}>
                      <Typography variant="body2">
                        <strong>Last Updated:</strong> {new Date(customer.updated_at).toLocaleString('en-GB', {
                          year: 'numeric',
                          month: 'short',
                          day: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit'
                        })}
                      </Typography>
                    </Grid>
                  </Grid>
                </Box>
              </Grid>
            )}
          </Grid>

          <Box sx={{ mt: 4, display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
            <Button
              variant="outlined"
              onClick={() => navigate(`/customers/${id}`)}
              disabled={saving}
            >
              Cancel
            </Button>
            <Button
              type="submit"
              variant="contained"
              startIcon={saving ? <CircularProgress size={20} color="inherit" /> : <SaveIcon />}
              disabled={saving}
            >
              {saving ? 'Saving...' : 'Save Changes'}
            </Button>
          </Box>
        </form>
      </Paper>
    </Container>
  );
};

export default CustomerEdit;

