import React, { useEffect, useState } from 'react';
import {
  Container,
  Grid,
  Paper,
  Typography,
  Card,
  CardContent,
  Button,
  Box
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import {
  People as PeopleIcon,
  TrendingUp as LeadsIcon,
  Description as QuotesIcon,
  Campaign as CampaignIcon
} from '@mui/icons-material';
import { customerAPI, leadAPI, quoteAPI, campaignAPI } from '../services/api';

const Dashboard: React.FC = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState({
    customers: 0,
    leads: 0,
    quotes: 0,
    campaigns: 0
  });

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      const [customersRes, leadsRes, quotesRes, campaignsRes] = await Promise.all([
        customerAPI.list({ limit: 1 }),
        leadAPI.list({ limit: 1 }),
        quoteAPI.list({ limit: 1 }),
        campaignAPI.list()
      ]);

      setStats({
        customers: customersRes.data.length,
        leads: leadsRes.data.length,
        quotes: quotesRes.data.length,
        campaigns: campaignsRes.data.length
      });
    } catch (error) {
      console.error('Error loading stats:', error);
    }
  };

  const StatCard = ({ title, value, icon, color, onClick }: any) => (
    <Card sx={{ height: '100%', cursor: 'pointer', '&:hover': { boxShadow: 6 } }} onClick={onClick}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <Box>
            <Typography color="text.secondary" gutterBottom>
              {title}
            </Typography>
            <Typography variant="h3" component="div">
              {value}
            </Typography>
          </Box>
          <Box sx={{ color, fontSize: 48 }}>
            {icon}
          </Box>
        </Box>
      </CardContent>
    </Card>
  );

  return (
    <Container maxWidth="lg" sx={{ mt: 4, mb: 4 }}>
      <Typography variant="h4" gutterBottom>
        Dashboard
      </Typography>

      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Customers"
            value={stats.customers}
            icon={<PeopleIcon />}
            color="primary.main"
            onClick={() => navigate('/customers')}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Leads"
            value={stats.leads}
            icon={<LeadsIcon />}
            color="success.main"
            onClick={() => navigate('/leads')}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Quotes"
            value={stats.quotes}
            icon={<QuotesIcon />}
            color="warning.main"
            onClick={() => navigate('/quotes')}
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Campaigns"
            value={stats.campaigns}
            icon={<CampaignIcon />}
            color="info.main"
            onClick={() => navigate('/campaigns')}
          />
        </Grid>
      </Grid>

      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Quick Actions
            </Typography>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              <Button variant="contained" onClick={() => navigate('/customers/new')}>
                Add New Customer
              </Button>
              <Button variant="contained" color="success" onClick={() => navigate('/campaigns/new')}>
                Start Lead Generation Campaign
              </Button>
              <Button variant="contained" color="warning" onClick={() => navigate('/quotes/new')}>
                Create Quote
              </Button>
            </Box>
          </Paper>
        </Grid>

        <Grid item xs={12} md={6}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Recent Activity
            </Typography>
            <Typography color="text.secondary">
              No recent activity
            </Typography>
          </Paper>
        </Grid>
      </Grid>
    </Container>
  );
};

export default Dashboard;

