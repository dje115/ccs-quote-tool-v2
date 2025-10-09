import React from 'react';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import Container from '@mui/material/Container';
import Typography from '@mui/material/Typography';
import Box from '@mui/material/Box';

const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
});

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Container maxWidth="lg">
        <Box sx={{ my: 4 }}>
          <Typography variant="h2" component="h1" gutterBottom>
            CCS Quote Tool v2
          </Typography>
          <Typography variant="h5" component="h2" gutterBottom>
            Multi-tenant SaaS CRM and Quoting Platform
          </Typography>
          <Typography variant="body1">
            Welcome to CCS Quote Tool v2! The application is starting up...
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
            Version 2.0.0 - Development
          </Typography>
        </Box>
      </Container>
    </ThemeProvider>
  );
}

export default App;

