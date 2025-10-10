import React, { useState } from 'react';
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
  FormControlLabel
} from '@mui/material';
import {
  Save as SaveIcon,
  Key as KeyIcon,
  Business as BusinessIcon,
  Notifications as NotificationsIcon
} from '@mui/icons-material';

const Settings: React.FC = () => {
  const [success, setSuccess] = useState('');
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);

  // Profile settings
  const [profileData, setProfileData] = useState({
    first_name: '',
    last_name: '',
    email: '',
    phone: ''
  });

  // API settings
  const [apiData, setApiData] = useState({
    openai_key: '',
    companies_house_key: '',
    google_maps_key: ''
  });

  // Notification settings
  const [notifications, setNotifications] = useState({
    email_on_new_lead: true,
    email_on_quote_accepted: true,
    email_on_campaign_complete: true,
    daily_summary: false
  });

  const handleSaveProfile = async () => {
    setSaving(true);
    setError('');
    setSuccess('');
    
    try {
      // API call to save profile
      await new Promise(resolve => setTimeout(resolve, 1000)); // Simulated delay
      setSuccess('Profile updated successfully!');
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
      // API call to save API keys
      await new Promise(resolve => setTimeout(resolve, 1000)); // Simulated delay
      setSuccess('API settings updated successfully!');
    } catch (err) {
      setError('Failed to update API settings');
    } finally {
      setSaving(false);
    }
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

      <Grid container spacing={3}>
        {/* Profile Settings */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 3 }}>
                <BusinessIcon color="primary" />
                <Typography variant="h6">Profile Settings</Typography>
              </Box>

              <Grid container spacing={2}>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="First Name"
                    value={profileData.first_name}
                    onChange={(e) => setProfileData({ ...profileData, first_name: e.target.value })}
                  />
                </Grid>
                <Grid item xs={12} sm={6}>
                  <TextField
                    fullWidth
                    label="Last Name"
                    value={profileData.last_name}
                    onChange={(e) => setProfileData({ ...profileData, last_name: e.target.value })}
                  />
                </Grid>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Email"
                    type="email"
                    value={profileData.email}
                    onChange={(e) => setProfileData({ ...profileData, email: e.target.value })}
                  />
                </Grid>
                <Grid item xs={12}>
                  <TextField
                    fullWidth
                    label="Phone"
                    value={profileData.phone}
                    onChange={(e) => setProfileData({ ...profileData, phone: e.target.value })}
                  />
                </Grid>
                <Grid item xs={12}>
                  <Button
                    variant="contained"
                    startIcon={<SaveIcon />}
                    onClick={handleSaveProfile}
                    disabled={saving}
                    fullWidth
                  >
                    Save Profile
                  </Button>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* Notification Settings */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 3 }}>
                <NotificationsIcon color="primary" />
                <Typography variant="h6">Notifications</Typography>
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
                    value={apiData.openai_key}
                    onChange={(e) => setApiData({ ...apiData, openai_key: e.target.value })}
                    helperText="For AI-powered lead generation"
                  />
                </Grid>
                <Grid item xs={12} md={4}>
                  <TextField
                    fullWidth
                    label="Companies House API Key"
                    type="password"
                    value={apiData.companies_house_key}
                    onChange={(e) =>
                      setApiData({ ...apiData, companies_house_key: e.target.value })
                    }
                    helperText="For UK company data"
                  />
                </Grid>
                <Grid item xs={12} md={4}>
                  <TextField
                    fullWidth
                    label="Google Maps API Key"
                    type="password"
                    value={apiData.google_maps_key}
                    onChange={(e) => setApiData({ ...apiData, google_maps_key: e.target.value })}
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

        {/* Danger Zone */}
        <Grid item xs={12} md={6}>
          <Card sx={{ borderColor: 'error.main', borderWidth: 1, borderStyle: 'solid' }}>
            <CardContent>
              <Typography variant="h6" color="error" gutterBottom>
                Danger Zone
              </Typography>
              <Divider sx={{ mb: 3 }} />

              <Typography variant="body2" color="text.secondary" gutterBottom>
                Once you delete your account, there is no going back. Please be certain.
              </Typography>

              <Button variant="outlined" color="error" sx={{ mt: 2 }}>
                Delete Account
              </Button>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Container>
  );
};

export default Settings;

