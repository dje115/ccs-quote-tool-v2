import React, { useState, useEffect } from 'react';
import {
  Container,
  Box,
  Paper,
  TextField,
  Button,
  Typography,
  Alert,
  Link,
  Divider,
  Tabs,
  Tab
} from '@mui/material';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { authAPI, versionAPI } from '../services/api';

const Login: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [version, setVersion] = useState<string>('3.0.2');
  const [loginMethod, setLoginMethod] = useState<'password' | 'passwordless'>('password');
  const [passwordlessSent, setPasswordlessSent] = useState(false);
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  useEffect(() => {
    const fetchVersion = async () => {
      try {
        const response = await versionAPI.get();
        setVersion(response.data.version);
      } catch (error) {
        console.error('Failed to fetch version:', error);
      }
    };
    fetchVersion();
    
    // Check if we have a passwordless token in URL
    const token = searchParams.get('token');
    if (token) {
      handlePasswordlessVerify(token);
    }
  }, [searchParams]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      if (loginMethod === 'passwordless') {
        await authAPI.requestPasswordlessLogin(email);
        setPasswordlessSent(true);
      } else {
        const response = await authAPI.login(email, password);
        const { user } = response.data;

        // SECURITY: Tokens are stored in HttpOnly cookies (set by backend automatically)
        // Only store user info in localStorage (non-sensitive data)
        // Do NOT store tokens in localStorage - they're vulnerable to XSS attacks
        localStorage.setItem('user', JSON.stringify(user));
        
        // Tokens in response.data are ignored - we rely entirely on HttpOnly cookies
        // HttpOnly cookies are sent automatically by the browser and cannot be accessed by JavaScript

        // Redirect to dashboard for all users
        navigate('/dashboard');
      }
    } catch (err: any) {
      setError(err.response?.data?.detail || (loginMethod === 'passwordless' ? 'Failed to send login link.' : 'Login failed. Please check your credentials.'));
    } finally {
      setLoading(false);
    }
  };

  const handlePasswordlessVerify = async (token: string) => {
    setError('');
    setLoading(true);

    try {
      const response = await authAPI.verifyPasswordlessLogin(token);
      const { user } = response.data;

      localStorage.setItem('user', JSON.stringify(user));
      navigate('/dashboard');
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Invalid or expired login link.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="sm">
      <Box sx={{ mt: 8, display: 'flex', flexDirection: 'column', alignItems: 'center' }}>
        <Paper elevation={3} sx={{ p: 4, width: '100%' }}>
          <Typography variant="h4" component="h1" gutterBottom align="center">
            CCS Quote Tool v2
          </Typography>
          <Typography variant="h6" gutterBottom align="center" color="text.secondary">
            Multi-tenant CRM & Quoting Platform
          </Typography>

          {error && (
            <Alert severity="error" sx={{ mt: 2, mb: 2 }}>
              {error}
            </Alert>
          )}

          {passwordlessSent ? (
            <Alert severity="success" sx={{ mt: 2, mb: 2 }}>
              Check your email for a login link. The link will expire in 15 minutes.
            </Alert>
          ) : (
            <>
              <Tabs value={loginMethod === 'password' ? 0 : 1} onChange={(_, newValue) => {
                setLoginMethod(newValue === 0 ? 'password' : 'passwordless');
                setError('');
                setPasswordlessSent(false);
              }} sx={{ mb: 2 }}>
                <Tab label="Password" />
                <Tab label="Email Link" />
              </Tabs>

              <Box component="form" onSubmit={handleSubmit} sx={{ mt: 3 }}>
                <TextField
                  fullWidth
                  label="Email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                  margin="normal"
                  autoComplete="email"
                  autoFocus
                />

                {loginMethod === 'password' && (
                  <TextField
                    fullWidth
                    label="Password"
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    margin="normal"
                    autoComplete="current-password"
                  />
                )}

                <Button
                  type="submit"
                  fullWidth
                  variant="contained"
                  size="large"
                  disabled={loading}
                  sx={{ mt: 3, mb: 2 }}
                >
                  {loading 
                    ? (loginMethod === 'passwordless' ? 'Sending...' : 'Logging in...') 
                    : (loginMethod === 'passwordless' ? 'Send Login Link' : 'Login')
                  }
                </Button>
              </Box>
            </>
          )}

            <Box sx={{ textAlign: 'center', mt: 2 }}>
              <Typography variant="body2">
                Don't have an account?{' '}
                <Link href="/signup" underline="hover">
                  Sign up for free trial
                </Link>
              </Typography>
            </Box>
          </Box>
        </Paper>

        <Typography variant="body2" color="text.secondary" sx={{ mt: 4 }}>
          Version {version}
        </Typography>
      </Box>
    </Container>
  );
};

export default Login;



