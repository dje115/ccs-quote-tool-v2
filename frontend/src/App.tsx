import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';

// Initialize i18n
import './i18n';

// Components
import Layout from './components/Layout';
import GlobalAIMonitor from './components/GlobalAIMonitor';
import { WebSocketProvider } from './contexts/WebSocketContext';

// Pages
import Login from './pages/Login';
import Signup from './pages/Signup';
import Dashboard from './pages/Dashboard';
import Customers from './pages/Customers';
import Competitors from './pages/Competitors';
import CustomerDetail from './pages/CustomerDetail';
import CustomerEdit from './pages/CustomerEdit';
import CustomerNew from './pages/CustomerNew';
import CustomerAnalysis from './pages/CustomerAnalysis';
import Leads from './pages/Leads';
import LeadDetail from './pages/LeadDetail';
import Campaigns from './pages/Campaigns';
import PlanningApplications from './pages/PlanningApplications';
import CampaignCreate from './pages/CampaignCreate';
import DynamicBusinessSearch from './pages/DynamicBusinessSearch';
import CompanyListImportCampaign from './pages/CompanyListImportCampaign';
import CampaignDetail from './pages/CampaignDetail';
import Quotes from './pages/Quotes';
import QuoteNew from './pages/QuoteNew';
import QuoteDetail from './pages/QuoteDetail';
import Users from './pages/Users';
import Settings from './pages/Settings';
import Suppliers from './pages/Suppliers';

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

// Protected route wrapper with layout
const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const token = localStorage.getItem('access_token');
  return token ? <Layout>{children}</Layout> : <Navigate to="/login" />;
};

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <WebSocketProvider>
        <BrowserRouter>
          <GlobalAIMonitor />
          <Routes>
          <Route path="/login" element={<Login />} />
          <Route path="/signup" element={<Signup />} />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <Dashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/customers"
            element={
              <ProtectedRoute>
                <Customers />
              </ProtectedRoute>
            }
          />
          <Route
            path="/customers/new"
            element={
              <ProtectedRoute>
                <CustomerNew />
              </ProtectedRoute>
            }
          />
          <Route
            path="/customers/:id/edit"
            element={
              <ProtectedRoute>
                <CustomerEdit />
              </ProtectedRoute>
            }
          />
          <Route
            path="/competitors"
            element={
              <ProtectedRoute>
                <Competitors />
              </ProtectedRoute>
            }
          />
          <Route
            path="/customers/:id"
            element={
              <ProtectedRoute>
                <CustomerDetail />
              </ProtectedRoute>
            }
          />
          <Route
            path="/customers/:id/analysis"
            element={
              <ProtectedRoute>
                <CustomerAnalysis />
              </ProtectedRoute>
            }
          />
          <Route
            path="/leads"
            element={
              <ProtectedRoute>
                <Leads />
              </ProtectedRoute>
            }
          />
          <Route
            path="/leads/:id"
            element={
              <ProtectedRoute>
                <LeadDetail />
              </ProtectedRoute>
            }
          />
          <Route
            path="/campaigns"
            element={
              <ProtectedRoute>
                <Campaigns />
              </ProtectedRoute>
            }
          />
          <Route
            path="/campaigns/create"
            element={
              <ProtectedRoute>
                <CampaignCreate />
              </ProtectedRoute>
            }
          />
          <Route
            path="/campaigns/new"
            element={
              <ProtectedRoute>
                <DynamicBusinessSearch />
              </ProtectedRoute>
            }
          />
          <Route
            path="/campaigns/import"
            element={
              <ProtectedRoute>
                <CompanyListImportCampaign />
              </ProtectedRoute>
            }
          />
          <Route
            path="/campaigns/:campaignId"
            element={
              <ProtectedRoute>
                <CampaignDetail />
              </ProtectedRoute>
            }
          />
          <Route
            path="/planning-applications"
            element={
              <ProtectedRoute>
                <PlanningApplications />
              </ProtectedRoute>
            }
          />
          <Route
            path="/quotes"
            element={
              <ProtectedRoute>
                <Quotes />
              </ProtectedRoute>
            }
          />
          <Route
            path="/quotes/new"
            element={
              <ProtectedRoute>
                <QuoteNew />
              </ProtectedRoute>
            }
          />
          <Route
            path="/quotes/:id"
            element={
              <ProtectedRoute>
                <QuoteDetail />
              </ProtectedRoute>
            }
          />
          <Route
            path="/users"
            element={
              <ProtectedRoute>
                <Users />
              </ProtectedRoute>
            }
          />
          <Route
            path="/settings"
            element={
              <ProtectedRoute>
                <Settings />
              </ProtectedRoute>
            }
          />
          <Route
            path="/suppliers"
            element={
              <ProtectedRoute>
                <Suppliers />
              </ProtectedRoute>
            }
          />
          <Route path="/" element={<Navigate to="/dashboard" />}           />
          </Routes>
        </BrowserRouter>
      </WebSocketProvider>
    </ThemeProvider>
  );
}

export default App;

