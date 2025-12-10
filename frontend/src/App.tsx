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
const LeadsCRM = lazy(() => import('./pages/LeadsCRM'));
const LeadDetail = lazy(() => import('./pages/LeadDetail'));
const Opportunities = lazy(() => import('./pages/Opportunities'));
const OpportunityDetail = lazy(() => import('./pages/OpportunityDetail'));
const Campaigns = lazy(() => import('./pages/Campaigns'));
const PlanningApplications = lazy(() => import('./pages/PlanningApplications'));
const CampaignCreate = lazy(() => import('./pages/CampaignCreate'));
const DynamicBusinessSearch = lazy(() => import('./pages/DynamicBusinessSearch'));
const SimilarBusinessCampaign = lazy(() => import('./pages/SimilarBusinessCampaign'));
const CompanyListImportCampaign = lazy(() => import('./pages/CompanyListImportCampaign'));
const CampaignDetail = lazy(() => import('./pages/CampaignDetail'));
const Quotes = lazy(() => import('./pages/Quotes'));
const QuoteNew = lazy(() => import('./pages/QuoteNew'));
const QuoteNewEnhanced = lazy(() => import('./pages/QuoteNewEnhanced'));
const QuoteDetail = lazy(() => import('./pages/QuoteDetail'));
const Users = lazy(() => import('./pages/Users'));
const Settings = lazy(() => import('./pages/Settings'));
const Suppliers = lazy(() => import('./pages/Suppliers'));
const PromptManagement = lazy(() => import('./pages/PromptManagement'));
const Helpdesk = lazy(() => import('./pages/Helpdesk'));
const TicketDetail = lazy(() => import('./pages/TicketDetail'));
const AgentDashboard = lazy(() => import('./pages/AgentDashboard'));
const TrendsDashboard = lazy(() => import('./pages/TrendsDashboard'));
const MetricsDashboard = lazy(() => import('./pages/MetricsDashboard'));
const Contracts = lazy(() => import('./pages/Contracts'));
const ContractTemplates = lazy(() => import('./pages/ContractTemplates'));
const ContractTemplateEditor = lazy(() => import('./pages/ContractTemplateEditor'));
const ContractDetail = lazy(() => import('./pages/ContractDetail'));
const SLAManagement = lazy(() => import('./pages/SLAManagement'));
const SLADashboard = lazy(() => import('./pages/SLADashboard'));
const SLAReportBuilder = lazy(() => import('./pages/SLAReportBuilder'));
const CustomerSLAReport = lazy(() => import('./pages/CustomerSLAReport'));
const HelpdeskPerformance = lazy(() => import('./pages/HelpdeskPerformance'));
const NPADashboard = lazy(() => import('./components/NPADashboard'));
const KnowledgeBase = lazy(() => import('./pages/KnowledgeBase'));
const TicketTemplates = lazy(() => import('./pages/TicketTemplates'));
const TicketMacros = lazy(() => import('./pages/TicketMacros'));
const Compliance = lazy(() => import('./pages/Compliance'));

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
    // Fetch CSRF token on app initialization
    const fetchCsrfToken = async () => {
      try {
        const { authAPI } = await import('./services/api');
        await authAPI.getCsrfToken();
      } catch (error) {
        // CSRF token fetch failure is not critical - will be set on first request
        console.warn('Failed to fetch CSRF token:', error);
      }
    };
    
    fetchCsrfToken();
    
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
            path="/leads-crm"
            element={
              <ProtectedRoute>
                <LeadsCRM />
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
            path="/campaigns/new/similar-business"
            element={
              <ProtectedRoute>
                <SimilarBusinessCampaign />
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
                <QuoteNewEnhanced />
              </ProtectedRoute>
            }
          />
          <Route
            path="/quotes/new/legacy"
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
            path="/opportunities"
            element={
              <ProtectedRoute>
                <Opportunities />
              </ProtectedRoute>
            }
          />
          <Route
            path="/opportunities/:id"
            element={
              <ProtectedRoute>
                <OpportunityDetail />
              </ProtectedRoute>
            }
          />
          <Route
            path="/contracts"
            element={
              <ProtectedRoute>
                <Contracts />
              </ProtectedRoute>
            }
          />
          <Route
            path="/contracts/templates"
            element={
              <ProtectedRoute>
                <ContractTemplates />
              </ProtectedRoute>
            }
          />
          <Route
            path="/contracts/templates/:id/edit"
            element={
              <ProtectedRoute>
                <ContractTemplateEditor />
              </ProtectedRoute>
            }
          />
          <Route
            path="/contracts/:id"
            element={
              <ProtectedRoute>
                <ContractDetail />
              </ProtectedRoute>
            }
          />
          <Route
            path="/sla"
            element={<ProtectedRoute><SLAManagement /></ProtectedRoute>}
          />
          <Route
            path="/sla/dashboard"
            element={<ProtectedRoute><SLADashboard /></ProtectedRoute>}
          />
          <Route
            path="/sla/reports"
            element={<ProtectedRoute><SLAReportBuilder /></ProtectedRoute>}
          />
          <Route
            path="/sla/customers/:customerId/report"
            element={<ProtectedRoute><CustomerSLAReport /></ProtectedRoute>}
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
            path="/compliance"
            element={
              <ProtectedRoute>
                <Compliance />
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
          <Route
            path="/helpdesk/agent-dashboard"
            element={
              <ProtectedRoute>
                <AgentDashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/helpdesk/performance"
            element={
              <ProtectedRoute>
                <HelpdeskPerformance />
              </ProtectedRoute>
            }
          />
          <Route
            path="/helpdesk/npa-dashboard"
            element={
              <ProtectedRoute>
                <NPADashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/helpdesk/knowledge-base"
            element={
              <ProtectedRoute>
                <KnowledgeBase />
              </ProtectedRoute>
            }
          />
          <Route
            path="/helpdesk/templates"
            element={
              <ProtectedRoute>
                <TicketTemplates />
              </ProtectedRoute>
            }
          />
          <Route
            path="/helpdesk/macros"
            element={
              <ProtectedRoute>
                <TicketMacros />
              </ProtectedRoute>
            }
          />
          <Route
            path="/trends"
            element={
              <ProtectedRoute>
                <TrendsDashboard />
              </ProtectedRoute>
            }
          />
          <Route
            path="/metrics"
            element={
              <ProtectedRoute>
                <MetricsDashboard />
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

