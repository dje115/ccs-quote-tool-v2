import React, { useState, useEffect } from 'react';
import {
  Container,
  Paper,
  Typography,
  Box,
  Grid,
  TextField,
  Button,
  Divider,
  Alert,
  Card,
  CardContent,
  Switch,
  FormControlLabel,
  Chip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  CircularProgress,
  Tabs,
  Tab
} from '@mui/material';
import {
  Save as SaveIcon,
  Key as KeyIcon,
  Business as BusinessIcon,
  Notifications as NotificationsIcon,
  CheckCircle as CheckCircleIcon,
  Cancel as CancelIcon,
  Science as ScienceIcon,
  Person as PersonIcon,
  Work as WorkIcon
} from '@mui/icons-material';
import CompanyProfile from '../components/CompanyProfile';

const Settings: React.FC = () => {
  const [currentTab, setCurrentTab] = useState(0);
  const [success, setSuccess] = useState('');
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);

  // API Status
  const [apiStatus, setApiStatus] = useState({
    openai: { configured: false, status: 'not_configured', source: 'none' },
    google_maps: { configured: false, status: 'not_configured', source: 'none' },
    companies_house: { configured: false, status: 'not_configured', source: 'none' }
  });

  // Test Modal
  const [testModalOpen, setTestModalOpen] = useState(false);
  const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null);
  const [testing, setTesting] = useState(false);

  // Profile settings
  const [profileData, setProfileData] = useState({
    first_name: '',
    last_name: '',
    email: '',
    phone: '',
    company_name: ''
  });

  // API settings
  const [apiData, setApiData] = useState({
    openai_key: '',
    companies_house_key: '',
    google_maps_key: ''
  });

  // API keys for saving (matching the form fields)
  const [apiKeys, setApiKeys] = useState({
    openai: '',
    companiesHouse: '',
    googleMaps: ''
  });

  // Notification settings
  const [notifications, setNotifications] = useState({
    email_on_new_lead: true,
    email_on_quote_accepted: true,
    email_on_campaign_complete: true,
    daily_summary: false
  });

  // Load API status and profile data on component mount
  useEffect(() => {
    loadApiStatus();
    loadProfileData();
  }, []);

  const loadApiStatus = async () => {
    try {
      const token = localStorage.getItem('access_token');
      // Use direct API call like the admin portal instead of proxy
      const response = await fetch('http://localhost:8000/api/v1/settings/api-status', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const status = await response.json();
        setApiStatus(status);
      }
    } catch (error) {
      console.error('Error loading API status:', error);
    }
  };

  const loadProfileData = async () => {
    try {
      // Get user data from localStorage (set during login)
      const userData = JSON.parse(localStorage.getItem('user') || '{}');
      
      // Get company name from company profile
      const token = localStorage.getItem('access_token');
      const companyResponse = await fetch('http://localhost:8000/api/v1/settings/company-profile', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      let companyName = '';
      if (companyResponse.ok) {
        const companyData = await companyResponse.json();
        companyName = companyData.company_name || '';
      }
      
      // Set profile data from user data
      setProfileData({
        first_name: userData.first_name || '',
        last_name: userData.last_name || '',
        email: userData.email || '',
        phone: userData.phone || '',
        company_name: companyName
      });
    } catch (error) {
      console.error('Error loading profile data:', error);
    }
  };

  const handleSaveProfile = async () => {
    setSaving(true);
    setError('');
    setSuccess('');
    
    try {
      const token = localStorage.getItem('access_token');
      
      // Update company name via company profile API
      await fetch('http://localhost:8000/api/v1/settings/company-profile', {
        method: 'PUT',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          company_name: profileData.company_name
        })
      });
      
      setSuccess('Profile updated successfully!');
      // Reload to ensure we have latest data
      loadProfileData();
    } catch (err) {
      setError('Failed to update profile');
    } finally {
      setSaving(false);
    }
  };

  const handleSaveAPI = async () => {
    setSaving(true);
    setError('');
    setSuccess('');
    
    try {
      const token = localStorage.getItem('access_token');
      // Use direct API call like the admin portal instead of proxy
      const response = await fetch('http://localhost:8000/api/v1/settings/api-keys', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          openai_api_key: apiKeys.openai,
          companies_house_api_key: apiKeys.companiesHouse,
          google_maps_api_key: apiKeys.googleMaps
        })
      });
      
      if (response.ok) {
        setSuccess('API settings updated successfully!');
        // Reload API status after saving
        loadApiStatus();
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Failed to update API settings');
      }
    } catch (err) {
      setError('Failed to update API settings');
    } finally {
      setSaving(false);
    }
  };

  const testAPI = async (apiType: string) => {
    setTesting(true);
    setTestModalOpen(true);
    setTestResult(null);
    
    try {
      const token = localStorage.getItem('access_token');
      // Use direct API call like the admin portal instead of proxy
      const response = await fetch(`http://localhost:8000/api/v1/settings/test-${apiType}`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        }
      });
      
      // Clone the response to avoid "body stream already read" error
      const responseClone = response.clone();
      const contentType = response.headers.get('content-type');
      
      let result;
      if (contentType && contentType.includes('application/json')) {
        try {
          result = await response.json();
        } catch (jsonError) {
          // Fallback to text if JSON parsing fails
          const textResponse = await responseClone.text();
          result = {
            success: false,
            message: `Invalid JSON response: ${textResponse.substring(0, 200)}...`
          };
        }
      } else {
        // Handle non-JSON responses (proxy errors, HTML pages, etc.)
        const textResponse = await responseClone.text();
        result = {
          success: false,
          message: `Server returned non-JSON response. This may indicate a proxy or network issue. Response: ${textResponse.substring(0, 200)}...`
        };
      }
      
      setTestResult(result);
      
      // Reload API status after test
      loadApiStatus();
    } catch (error) {
      console.error('API Test Error:', error);
      setTestResult({
        success: false,
        message: `Network error: ${error}. Please check your internet connection and try again.`
      });
    } finally {
      setTesting(false);
    }
  };

  const closeTestModal = () => {
    setTestModalOpen(false);
    setTestResult(null);
  };

  const handleSaveNotifications = async () => {
    setSaving(true);
    setError('');
    setSuccess('');
    
    try {
      // API call to save notifications
      await new Promise(resolve => setTimeout(resolve, 1000)); // Simulated delay
      setSuccess('Notification settings updated successfully!');
    } catch (err) {
      setError('Failed to update notification settings');
    } finally {
      setSaving(false);
    }
  };

  return (
    <Container maxWidth="lg">
      <Typography variant="h4" component="h1" gutterBottom>
        Settings
      </Typography>

      {success && (
        <Alert severity="success" sx={{ mb: 3 }} onClose={() => setSuccess('')}>
          {success}
        </Alert>
      )}

      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError('')}>
          {error}
        </Alert>
      )}

      {/* Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs 
          value={currentTab} 
          onChange={(e, newValue) => setCurrentTab(newValue)}
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
          }}
        >
          <Tab icon={<PersonIcon />} iconPosition="start" label="Profile" />
          <Tab icon={<KeyIcon />} iconPosition="start" label="API Keys" />
          <Tab icon={<WorkIcon />} iconPosition="start" label="Company Profile" />
          <Tab icon={<NotificationsIcon />} iconPosition="start" label="Notifications" />
        </Tabs>
      </Paper>

      {/* Tab 0: Profile Settings */}
      {currentTab === 0 && (
      <Grid container spacing={3}>
        {/* Company Settings */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 3 }}>
                <BusinessIcon color="primary" />
                <Typography variant="h6">Company Settings</Typography>
              </Box>

              <Grid container spacing={2}>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Company Name"
                    value={profileData.company_name}
                    onChange={(e) => setProfileData({ ...profileData, company_name: e.target.value })}
                    helperText="Your legal company name - used throughout the system and in AI analysis"
                  />
                </Grid>
                <Grid item xs={12}>
                  <Button
                    variant="contained"
                    startIcon={<SaveIcon />}
                    onClick={handleSaveProfile}
                    disabled={saving}
                  >
                    Save Company Name
                  </Button>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>
        
        {/* Profile Settings */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 3 }}>
                <PersonIcon color="primary" />
                <Typography variant="h6">User Profile</Typography>
              </Box>

              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="First Name"
                    value={profileData.first_name}
                    onChange={(e) => setProfileData({ ...profileData, first_name: e.target.value })}
                    disabled
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Last Name"
                    value={profileData.last_name}
                    onChange={(e) => setProfileData({ ...profileData, last_name: e.target.value })}
                    disabled
                  />
                </Grid>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Email"
                    type="email"
                    value={profileData.email}
                    onChange={(e) => setProfileData({ ...profileData, email: e.target.value })}
                    disabled
                  />
                </Grid>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Phone"
                    value={profileData.phone}
                    onChange={(e) => setProfileData({ ...profileData, phone: e.target.value })}
                    disabled
                  />
                </Grid>
                <Grid item xs={12}>
                  <Alert severity="info">
                    User profile fields are managed by your administrator. Please contact support to update these fields.
                  </Alert>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

      </Grid>
      )}

      {/* Tab 1: API Keys */}
      {currentTab === 1 && (
      <Grid container spacing={3}>
        {/* API Keys will go here */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 3 }}>
                <KeyIcon color="primary" />
                <Typography variant="h6">API Keys Settings</Typography>
              </Box>

              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={notifications.email_on_new_lead}
                      onChange={(e) =>
                        setNotifications({ ...notifications, email_on_new_lead: e.target.checked })
                      }
                    />
                  }
                  label="Email on new lead"
                />
                <FormControlLabel
                  control={
                    <Switch
                      checked={notifications.email_on_quote_accepted}
                      onChange={(e) =>
                        setNotifications({
                          ...notifications,
                          email_on_quote_accepted: e.target.checked
                        })
                      }
                    />
                  }
                  label="Email on quote accepted"
                />
                <FormControlLabel
                  control={
                    <Switch
                      checked={notifications.email_on_campaign_complete}
                      onChange={(e) =>
                        setNotifications({
                          ...notifications,
                          email_on_campaign_complete: e.target.checked
                        })
                      }
                    />
                  }
                  label="Email on campaign complete"
                />
                <FormControlLabel
                  control={
                    <Switch
                      checked={notifications.daily_summary}
                      onChange={(e) =>
                        setNotifications({ ...notifications, daily_summary: e.target.checked })
                      }
                    />
                  }
                  label="Daily summary email"
                />

                <Button
                  variant="contained"
                  startIcon={<SaveIcon />}
                  onClick={handleSaveNotifications}
                  disabled={saving}
                  fullWidth
                  sx={{ mt: 2 }}
                >
                  Save Notifications
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* API Settings */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 3 }}>
                <KeyIcon color="primary" />
                <Typography variant="h6">API Keys</Typography>
              </Box>

              <Alert severity="info" sx={{ mb: 3 }}>
                API keys are encrypted and stored securely. Leave fields blank to use system-wide
                keys (if available).
              </Alert>

              <Grid container spacing={2}>
                <Grid item xs={12} md={4}>
                  <TextField
                    fullWidth
                    label="OpenAI API Key"
                    type="password"
                    value={apiKeys.openai}
                    onChange={(e) => setApiKeys({ ...apiKeys, openai: e.target.value })}
                    helperText="For AI-powered lead generation"
                  />
                </Grid>
                <Grid item xs={12} md={4}>
                  <TextField
                    fullWidth
                    label="Companies House API Key"
                    type="password"
                    value={apiKeys.companiesHouse}
                    onChange={(e) => setApiKeys({ ...apiKeys, companiesHouse: e.target.value })}
                    helperText="For UK company data"
                  />
                </Grid>
                <Grid item xs={12} md={4}>
                  <TextField
                    fullWidth
                    label="Google Maps API Key"
                    type="password"
                    value={apiKeys.googleMaps}
                    onChange={(e) => setApiKeys({ ...apiKeys, googleMaps: e.target.value })}
                    helperText="For location services"
                  />
                </Grid>
                <Grid item xs={12}>
                  <Button
                    variant="contained"
                    startIcon={<SaveIcon />}
                    onClick={handleSaveAPI}
                    disabled={saving}
                  >
                    Save API Keys
                  </Button>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* API Status */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 3 }}>
                <ScienceIcon color="primary" />
                <Typography variant="h6">API Status</Typography>
              </Box>

              <Grid container spacing={3}>
                <Grid item xs={12} md={4}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                    <Typography variant="body1">OpenAI API</Typography>
                    <Chip
                      icon={apiStatus.openai.configured ? <CheckCircleIcon /> : <CancelIcon />}
                      label={
                        apiStatus.openai.configured 
                          ? (apiStatus.openai.source === 'system_wide' ? 'Using System-wide Key' : 'Configured')
                          : 'Not Configured'
                      }
                      color={apiStatus.openai.configured ? 'success' : 'error'}
                      size="small"
                    />
                  </Box>
                  <Button
                    variant="outlined"
                    size="small"
                    startIcon={<ScienceIcon />}
                    onClick={() => testAPI('openai')}
                    fullWidth
                  >
                    Test Connection
                  </Button>
                </Grid>

                <Grid item xs={12} md={4}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                    <Typography variant="body1">Google Maps API</Typography>
                    <Chip
                      icon={apiStatus.google_maps.configured ? <CheckCircleIcon /> : <CancelIcon />}
                      label={
                        apiStatus.google_maps.configured 
                          ? (apiStatus.google_maps.source === 'system_wide' ? 'Using System-wide Key' : 'Configured')
                          : 'Not Configured'
                      }
                      color={apiStatus.google_maps.configured ? 'success' : 'error'}
                      size="small"
                    />
                  </Box>
                  <Button
                    variant="outlined"
                    size="small"
                    startIcon={<ScienceIcon />}
                    onClick={() => testAPI('google-maps')}
                    fullWidth
                  >
                    Test Connection
                  </Button>
                </Grid>

                <Grid item xs={12} md={4}>
                  <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
                    <Typography variant="body1">Companies House API</Typography>
                    <Chip
                      icon={apiStatus.companies_house.configured ? <CheckCircleIcon /> : <CancelIcon />}
                      label={
                        apiStatus.companies_house.configured 
                          ? (apiStatus.companies_house.source === 'system_wide' ? 'Using System-wide Key' : 'Configured')
                          : 'Not Configured'
                      }
                      color={apiStatus.companies_house.configured ? 'success' : 'error'}
                      size="small"
                    />
                  </Box>
                  <Button
                    variant="outlined"
                    size="small"
                    startIcon={<ScienceIcon />}
                    onClick={() => testAPI('companies-house')}
                    fullWidth
                  >
                    Test Connection
                  </Button>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* Password Change */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Change Password
              </Typography>
              <Divider sx={{ mb: 3 }} />

              <Grid container spacing={2}>
                <Grid item xs={12}>
                  <TextField fullWidth label="Current Password" type="password" />
                </Grid>
                <Grid item xs={12}>
                  <TextField fullWidth label="New Password" type="password" />
                </Grid>
                <Grid item xs={12}>
                  <TextField fullWidth label="Confirm New Password" type="password" />
                </Grid>
                <Grid item xs={12}>
                  <Button variant="contained" disabled={saving}>
                    Update Password
                  </Button>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

      </Grid>
      )}

      {/* Tab 2: Company Profile */}
      {currentTab === 2 && (
        <CompanyProfile />
      )}

      {/* Tab 3: Notifications */}
      {currentTab === 3 && (
      <Grid container spacing={3}>
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 3 }}>
                <NotificationsIcon color="primary" />
                <Typography variant="h6">Notification Settings</Typography>
              </Box>

              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={notifications.email_on_new_lead}
                      onChange={(e) => setNotifications({ ...notifications, email_on_new_lead: e.target.checked })}
                    />
                  }
                  label="Email me when a new lead is created"
                />
                <FormControlLabel
                  control={
                    <Switch
                      checked={notifications.email_on_quote_accepted}
                      onChange={(e) => setNotifications({ ...notifications, email_on_quote_accepted: e.target.checked })}
                    />
                  }
                  label="Email me when a quote is accepted"
                />
                <FormControlLabel
                  control={
                    <Switch
                      checked={notifications.email_on_campaign_complete}
                      onChange={(e) => setNotifications({ ...notifications, email_on_campaign_complete: e.target.checked })}
                    />
                  }
                  label="Email me when a lead generation campaign completes"
                />
                <FormControlLabel
                  control={
                    <Switch
                      checked={notifications.daily_summary}
                      onChange={(e) => setNotifications({ ...notifications, daily_summary: e.target.checked })}
                    />
                  }
                  label="Send me a daily summary email"
                />
              </Box>

              <Button
                variant="contained"
                startIcon={<SaveIcon />}
                onClick={handleSaveNotifications}
                disabled={saving}
                sx={{ mt: 3 }}
              >
                Save Notifications
              </Button>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
      )}

      {/* Test Results Modal */}
      <Dialog open={testModalOpen} onClose={closeTestModal} maxWidth="sm" fullWidth>
        <DialogTitle>API Test Results</DialogTitle>
        <DialogContent>
          {testing ? (
            <Box sx={{ display: 'flex', flexDirection: 'column', alignItems: 'center', py: 3 }}>
              <CircularProgress size={40} sx={{ mb: 2 }} />
              <Typography variant="body1">Testing API connection...</Typography>
            </Box>
          ) : testResult ? (
            <Alert 
              severity={testResult.success ? 'success' : 'error'}
              sx={{ mt: 2 }}
            >
              <Typography variant="h6" gutterBottom>
                {testResult.success ? 'API Test Successful!' : 'API Test Failed'}
              </Typography>
              <Typography variant="body2">
                {testResult.message}
              </Typography>
            </Alert>
          ) : null}
        </DialogContent>
        <DialogActions>
          <Button onClick={closeTestModal}>
            Close
          </Button>
        </DialogActions>
      </Dialog>
    </Container>
  );
};

export default Settings;

