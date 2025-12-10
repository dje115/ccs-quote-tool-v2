import React, { useState, useEffect } from 'react';
import {
  Box,
  Tabs,
  Tab,
  Typography,
  Paper,
  Container,
  Alert,
  CircularProgress,
} from '@mui/material';
import SecurityDashboard from '../components/compliance/SecurityDashboard';
import GDPRCompliance from '../components/compliance/GDPRCompliance';
import ISOCompliance from '../components/compliance/ISOCompliance';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`compliance-tabpanel-${index}`}
      aria-labelledby={`compliance-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const Compliance: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom>
        Compliance & Security
      </Typography>
      <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
        Manage security monitoring, GDPR compliance, and ISO 27001/9001 certifications
      </Typography>

      {error && (
        <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      <Paper sx={{ width: '100%' }}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs
            value={tabValue}
            onChange={handleTabChange}
            aria-label="compliance tabs"
          >
            <Tab label="Security Dashboard" />
            <Tab label="GDPR Compliance" />
            <Tab label="ISO 27001" />
            <Tab label="ISO 9001" />
          </Tabs>
        </Box>

        <TabPanel value={tabValue} index={0}>
          <SecurityDashboard />
        </TabPanel>

        <TabPanel value={tabValue} index={1}>
          <GDPRCompliance />
        </TabPanel>

        <TabPanel value={tabValue} index={2}>
          <ISOCompliance standard="iso_27001" />
        </TabPanel>

        <TabPanel value={tabValue} index={3}>
          <ISOCompliance standard="iso_9001" />
        </TabPanel>
      </Paper>
    </Container>
  );
};

export default Compliance;

