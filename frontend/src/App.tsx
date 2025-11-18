import React, { Suspense, lazy } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import CssBaseline from '@mui/material/CssBaseline';
import { CircularProgress, Box } from '@mui/material';

// Initialize i18n
import './i18n';

// Components (keep as regular imports - needed immediately)
import Layout from './components/Layout';
import GlobalAIMonitor from './components/GlobalAIMonitor';
import { WebSocketProvider } from './contexts/WebSocketContext';

// Pages - Lazy load for code splitting (reduces initial bundle size)
const Login = lazy(() => import('./pages/Login'));
const Signup = lazy(() => import('./pages/Signup'));
const Dashboard = lazy(() => import('./pages/Dashboard'));
const Customers = lazy(() => import('./pages/Customers'));
const Competitors = lazy(() => import('./pages/Competitors'));
const CustomerDetail = lazy(() => import('./pages/CustomerDetail'));
const CustomerEdit = lazy(() => import('./pages/CustomerEdit'));
const CustomerNew = lazy(() => import('./pages/CustomerNew'));
const CustomerAnalysis = lazy(() => import('./pages/CustomerAnalysis'));
const Leads = lazy(() => import('./pages/Leads'));
const LeadDetail = lazy(() => import('./pages/LeadDetail'));
const Campaigns = lazy(() => import('./pages/Campaigns'));
const PlanningApplications = lazy(() => import('./pages/PlanningApplications'));
const CampaignCreate = lazy(() => import('./pages/CampaignCreate'));
const DynamicBusinessSearch = lazy(() => import('./pages/DynamicBusinessSearch'));
const CompanyListImportCampaign = lazy(() => import('./pages/CompanyListImportCampaign'));
const CampaignDetail = lazy(() => import('./pages/CampaignDetail'));
const Quotes = lazy(() => import('./pages/Quotes'));
const QuoteNew = lazy(() => import('./pages/QuoteNew'));
const QuoteDetail = lazy(() => import('./pages/QuoteDetail'));
const Users = lazy(() => import('./pages/Users'));
const Settings = lazy(() => import('./pages/Settings'));
const Suppliers = lazy(() => import('./pages/Suppliers'));
const PromptManagement = lazy(() => import('./pages/PromptManagement'));
const Helpdesk = lazy(() => import('./pages/Helpdesk'));
const TicketDetail = lazy(() => import('./pages/TicketDetail'));

// Loading fallback component
const LoadingFallback = () => (
  <Box
    sx={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      minHeight: '100vh',
    }}
  >
    <CircularProgress />
  </Box>
);

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
// SECURITY: HttpOnly cookies cannot be read by JavaScript, so we check auth status
// by verifying user object exists (stored in localStorage) or by making API call
const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const [isAuthenticated, setIsAuthenticated] = React.useState<boolean | null>(null);
  
  React.useEffect(() => {
    // SECURITY: Always validate auth via API call to check token validity
    // HttpOnly cookies can't be read by JavaScript, so we must verify via API
    // This ensures expired or invalid tokens don't grant access
    const checkAuth = async () => {
      try {
        const { authAPI } = await import('./services/api');
        const response = await authAPI.getCurrentUser();
        
        // Update localStorage with fresh user data
        if (response.data) {
          localStorage.setItem('user', JSON.stringify(response.data));
        }
        
        setIsAuthenticated(true);
      } catch (error: any) {
        // Auth failed - clear any stale data
        localStorage.removeItem('user');
        setIsAuthenticated(false);
      }
    };
    
    checkAuth();
  }, []);
  
  // Show loading spinner while checking authentication
  if (isAuthenticated === null) {
    return <LoadingFallback />;
  }
  
  return isAuthenticated ? <Layout>{children}</Layout> : <Navigate to="/login" />;
};

function App() {
  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <WebSocketProvider>
        <BrowserRouter>
          <GlobalAIMonitor />
          <Suspense fallback={<LoadingFallback />}>
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
          <Route
            path="/prompts"
            element={
              <ProtectedRoute>
                <PromptManagement />
              </ProtectedRoute>
            }
          />
          <Route
            path="/helpdesk/:id"
            element={
              <ProtectedRoute>
                <TicketDetail />
              </ProtectedRoute>
            }
          />
          <Route
            path="/helpdesk"
            element={
              <ProtectedRoute>
                <Helpdesk />
              </ProtectedRoute>
            }
          />
          <Route path="/" element={<Navigate to="/dashboard" />} />
            </Routes>
          </Suspense>
        </BrowserRouter>
      </WebSocketProvider>
    </ThemeProvider>
  );
}

export default App;

