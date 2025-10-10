import React, { useState } from 'react';
import {
  Container,
  Box,
  Paper,
  TextField,
  Button,
  Typography,
  Alert,
  Link,
  Grid,
  Stepper,
  Step,
  StepLabel
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import { tenantAPI } from '../services/api';

const Signup: React.FC = () => {
  const [activeStep, setActiveStep] = useState(0);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  // Form data
  const [formData, setFormData] = useState({
    name: '',
    slug: '',
    admin_email: '',
    admin_password: '',
    admin_first_name: '',
    admin_last_name: '',
  });

  const steps = ['Company Details', 'Admin Account', 'Confirm'];

  const handleChange = (field: string) => (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData({ ...formData, [field]: e.target.value });
    
    // Auto-generate slug from company name
    if (field === 'name') {
      const slug = e.target.value.toLowerCase().replace(/[^a-z0-9]+/g, '-').replace(/^-|-$/g, '');
      setFormData(prev => ({ ...prev, slug }));
    }
  };

  const handleNext = () => {
    setActiveStep((prevStep) => prevStep + 1);
  };

  const handleBack = () => {
    setActiveStep((prevStep) => prevStep - 1);
  };

  const handleSubmit = async () => {
    setError('');
    setLoading(true);

    try {
      await tenantAPI.signup(formData);
      
      // Success - redirect to login
      navigate('/login?signup=success');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Signup failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const renderStepContent = () => {
    switch (activeStep) {
      case 0:
        return (
          <>
            <TextField
              fullWidth
              label="Company Name"
              value={formData.name}
              onChange={handleChange('name')}
              required
              margin="normal"
              helperText="Your company or organization name"
            />
            <TextField
              fullWidth
              label="Company Slug"
              value={formData.slug}
              onChange={handleChange('slug')}
              required
              margin="normal"
              helperText="Used in URLs (e.g., yourcompany.ccsquote.com)"
            />
          </>
        );
      
      case 1:
        return (
          <>
            <Grid container spacing={2}>
              <Grid item xs={6}>
                <TextField
                  fullWidth
                  label="First Name"
                  value={formData.admin_first_name}
                  onChange={handleChange('admin_first_name')}
                  required
                  margin="normal"
                />
              </Grid>
              <Grid item xs={6}>
                <TextField
                  fullWidth
                  label="Last Name"
                  value={formData.admin_last_name}
                  onChange={handleChange('admin_last_name')}
                  required
                  margin="normal"
                />
              </Grid>
            </Grid>
            
            <TextField
              fullWidth
              label="Admin Email"
              type="email"
              value={formData.admin_email}
              onChange={handleChange('admin_email')}
              required
              margin="normal"
              helperText="This will be your login email"
            />
            
            <TextField
              fullWidth
              label="Password"
              type="password"
              value={formData.admin_password}
              onChange={handleChange('admin_password')}
              required
              margin="normal"
              helperText="Minimum 8 characters"
            />
          </>
        );
      
      case 2:
        return (
          <Box sx={{ mt: 2 }}>
            <Typography variant="h6" gutterBottom>
              Confirm Your Details
            </Typography>
            <Typography><strong>Company:</strong> {formData.name}</Typography>
            <Typography><strong>Slug:</strong> {formData.slug}</Typography>
            <Typography><strong>Admin:</strong> {formData.admin_first_name} {formData.admin_last_name}</Typography>
            <Typography><strong>Email:</strong> {formData.admin_email}</Typography>
            
            <Alert severity="info" sx={{ mt: 2 }}>
              You'll start with a 30-day free trial with access to all features!
            </Alert>
          </Box>
        );
      
      default:
        return null;
    }
  };

  return (
    <Container maxWidth="md">
      <Box sx={{ mt: 4, mb: 4 }}>
        <Paper elevation={3} sx={{ p: 4 }}>
          <Typography variant="h4" component="h1" gutterBottom align="center">
            Start Your Free Trial
          </Typography>
          <Typography variant="body1" align="center" color="text.secondary" sx={{ mb: 4 }}>
            Get started with CCS Quote Tool v2 - No credit card required
          </Typography>

          <Stepper activeStep={activeStep} sx={{ mb: 4 }}>
            {steps.map((label) => (
              <Step key={label}>
                <StepLabel>{label}</StepLabel>
              </Step>
            ))}
          </Stepper>

          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}

          {renderStepContent()}

          <Box sx={{ display: 'flex', justifyContent: 'space-between', mt: 4 }}>
            <Button
              disabled={activeStep === 0}
              onClick={handleBack}
            >
              Back
            </Button>

            {activeStep === steps.length - 1 ? (
              <Button
                variant="contained"
                onClick={handleSubmit}
                disabled={loading}
              >
                {loading ? 'Creating Account...' : 'Complete Signup'}
              </Button>
            ) : (
              <Button
                variant="contained"
                onClick={handleNext}
              >
                Next
              </Button>
            )}
          </Box>

          <Box sx={{ textAlign: 'center', mt: 3 }}>
            <Typography variant="body2">
              Already have an account?{' '}
              <Link href="/login" underline="hover">
                Log in
              </Link>
            </Typography>
          </Box>
        </Paper>
      </Box>
    </Container>
  );
};

export default Signup;

