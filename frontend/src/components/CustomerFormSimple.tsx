import React, { useState } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Grid,
  Box,
  Typography,
  Alert
} from '@mui/material';

interface CustomerFormSimpleProps {
  open: boolean;
  onClose: () => void;
  onSave: (customer: any) => void;
}

const CustomerFormSimple: React.FC<CustomerFormSimpleProps> = ({ open, onClose, onSave }) => {
  const [formData, setFormData] = useState({
    company_name: '',
    website: '',
    email: '',
    phone: '',
    company_number: '',
    address: ''
  });
  const [error, setError] = useState('');

  const handleInputChange = (field: string) => (event: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({ ...formData, [field]: event.target.value });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!formData.company_name.trim()) {
      setError('Company name is required');
      return;
    }

    try {
      console.log('Submitting customer data:', formData);
      
      // Map to backend schema
      const customerData = {
        company_name: formData.company_name,
        website: formData.website || null,
        main_email: formData.email || null,
        main_phone: formData.phone || null,
        billing_address: formData.address || null
      };

      console.log('Calling onSave with:', customerData);
      await onSave(customerData);
      
      console.log('Customer saved successfully');
      
      // Reset form
      setFormData({
        company_name: '',
        website: '',
        email: '',
        phone: '',
        company_number: '',
        address: ''
      });
      setError('');
      onClose();
    } catch (err: any) {
      console.error('Error saving customer:', err);
      setError(err.message || 'Failed to create customer');
    }
  };

  const handleClose = () => {
    setFormData({
      company_name: '',
      website: '',
      email: '',
      phone: '',
      company_number: '',
      address: ''
    });
    setError('');
    onClose();
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
      <DialogTitle>Create New Customer</DialogTitle>
      <form onSubmit={handleSubmit}>
        <DialogContent>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}
          
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Enter basic customer information. After creating the customer, you can use the AI Analysis button on the customer detail page to automatically gather company intelligence, lead scoring, and opportunities.
          </Typography>

          <Grid container spacing={3}>
            <Grid size={12}>
              <TextField
                fullWidth
                required
                label="Company Name"
                value={formData.company_name}
                onChange={handleInputChange('company_name')}
                autoFocus
              />
            </Grid>

            <Grid
              size={{
                xs: 12,
                sm: 6
              }}>
              <TextField
                fullWidth
                label="Website"
                value={formData.website}
                onChange={handleInputChange('website')}
                placeholder="https://example.com"
              />
            </Grid>

            <Grid
              size={{
                xs: 12,
                sm: 6
              }}>
              <TextField
                fullWidth
                label="Company Registration Number"
                value={formData.company_number}
                onChange={handleInputChange('company_number')}
                placeholder="e.g., 12345678"
                helperText="Optional - AI can find this automatically"
              />
            </Grid>

            <Grid
              size={{
                xs: 12,
                sm: 6
              }}>
              <TextField
                fullWidth
                label="Email"
                type="email"
                value={formData.email}
                onChange={handleInputChange('email')}
              />
            </Grid>

            <Grid
              size={{
                xs: 12,
                sm: 6
              }}>
              <TextField
                fullWidth
                label="Phone"
                value={formData.phone}
                onChange={handleInputChange('phone')}
              />
            </Grid>

            <Grid size={12}>
              <TextField
                fullWidth
                label="Address"
                value={formData.address}
                onChange={handleInputChange('address')}
                multiline
                rows={3}
                placeholder="Company address"
              />
            </Grid>
          </Grid>
        </DialogContent>

        <DialogActions>
          <Button onClick={handleClose}>Cancel</Button>
          <Button type="submit" variant="contained" color="primary">
            Create Customer
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
};

export default CustomerFormSimple;


