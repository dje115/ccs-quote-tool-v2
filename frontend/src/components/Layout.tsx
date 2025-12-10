import React, { useState, useEffect } from 'react';
import {
  Box,
  Drawer,
  AppBar,
  Toolbar,
  List,
  Typography,
  Divider,
  IconButton,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Avatar,
  Menu,
  MenuItem
} from '@mui/material';
import {
  Menu as MenuIcon,
  Dashboard as DashboardIcon,
  People as PeopleIcon,
  TrendingUp as LeadsIcon,
  PersonAdd as PersonAddIcon,
  Campaign as CampaignIcon,
  Description as QuotesIcon,
  Settings as SettingsIcon,
  Logout as LogoutIcon,
  AccountCircle,
  Group as GroupIcon,
  Business as CompetitorsIcon,
  Security as SecurityIcon,
  Architecture as ArchitectureIcon,
  LocalShipping as LocalShippingIcon,
  Psychology as PsychologyIcon,
  Support as SupportIcon,
  Timeline as TimelineIcon,
  Assessment as AssessmentIcon,
  Work as OpportunitiesIcon,
  Description as ContractsIcon,
  Assignment as AssignmentIcon,
  Description as TemplateIcon,
  Build as MacroIcon,
  Security as SecurityIcon
} from '@mui/icons-material';
import { useNavigate, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import SimpleLanguageSelector from './SimpleLanguageSelector';
import GlobalAIMonitor from './GlobalAIMonitor';
import AIMonitorBadge from './AIMonitorBadge';
import OnboardingTooltips from './OnboardingTooltips';
import VersionDisplay from './VersionDisplay';
import { settingsAPI } from '../services/api';

const drawerWidth = 240;

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const { t } = useTranslation();
  const [mobileOpen, setMobileOpen] = useState(false);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);
  const [showOnboardingTooltips, setShowOnboardingTooltips] = useState(false);

  const user = JSON.parse(localStorage.getItem('user') || '{}');

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const handleMenu = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const handleLogout = () => {
    localStorage.clear();
    navigate('/login');
  };

  // Check AI analysis status and show tooltips if needed
  const checkTooltipStatus = async () => {
    try {
      const response = await settingsAPI.get('/company-profile');
      const data = response.data;
      
      // Check if we have meaningful AI analysis data
      const hasAIAnalysis = !!(data.company_analysis && 
                              typeof data.company_analysis === 'object' && 
                              Object.keys(data.company_analysis).length > 0);
      
      // Check if user has seen tooltips before
      const hasSeenTooltips = localStorage.getItem('onboarding-tooltips-seen');
      
      // Show tooltips if no AI analysis (regardless of whether user has seen them before)
      if (!hasAIAnalysis && user.email) {
        setShowOnboardingTooltips(true);
      }
    } catch (error) {
      console.error('Failed to check AI analysis status:', error);
    }
  };

  // Check on component mount and when user changes
  useEffect(() => {
    if (user.email) {
      checkTooltipStatus();
    }
  }, [user.email]);

  const handleTooltipComplete = () => {
    setShowOnboardingTooltips(false);
    localStorage.setItem('onboarding-tooltips-seen', 'true');
  };

  const handleTooltipSkip = () => {
    setShowOnboardingTooltips(false);
    localStorage.setItem('onboarding-tooltips-seen', 'true');
  };

  const menuItems = [
    { text: t('navigation.dashboard'), icon: <DashboardIcon />, path: '/dashboard' },
    { text: t('navigation.customers'), icon: <PeopleIcon />, path: '/customers' },
    { text: 'Leads', icon: <PersonAddIcon />, path: '/leads-crm' },
    { text: t('navigation.discoveries'), icon: <LeadsIcon />, path: '/leads' },
    { text: 'Opportunities', icon: <OpportunitiesIcon />, path: '/opportunities' },
    { text: t('navigation.planning'), icon: <ArchitectureIcon />, path: '/planning-applications' },
    { text: t('navigation.campaigns'), icon: <CampaignIcon />, path: '/campaigns' },
    { text: t('navigation.quotes'), icon: <QuotesIcon />, path: '/quotes' },
    { text: 'Contracts', icon: <ContractsIcon />, path: '/contracts' },
    { text: 'Helpdesk', icon: <SupportIcon />, path: '/helpdesk' },
    { text: 'Helpdesk Performance', icon: <AssessmentIcon />, path: '/helpdesk/performance' },
    { text: 'NPA Dashboard', icon: <AssignmentIcon />, path: '/helpdesk/npa-dashboard' },
    { text: 'Knowledge Base', icon: <PsychologyIcon />, path: '/helpdesk/knowledge-base' },
    { text: 'Ticket Templates', icon: <TemplateIcon />, path: '/helpdesk/templates' },
    { text: 'Ticket Macros', icon: <MacroIcon />, path: '/helpdesk/macros' },
    { text: 'SLA Management', icon: <AssessmentIcon />, path: '/sla' },
    { text: 'SLA Dashboard', icon: <AssessmentIcon />, path: '/sla/dashboard' },
    { text: 'SLA Reports', icon: <AssessmentIcon />, path: '/sla/reports' },
    { text: 'Trends', icon: <TimelineIcon />, path: '/trends' },
    { text: 'Metrics', icon: <AssessmentIcon />, path: '/metrics' },
        { text: 'Suppliers', icon: <LocalShippingIcon />, path: '/suppliers' },
        { text: t('navigation.competitors'), icon: <CompetitorsIcon />, path: '/competitors' },
        { text: 'AI Prompts', icon: <PsychologyIcon />, path: '/prompts', adminOnly: true },
    { text: t('navigation.users'), icon: <GroupIcon />, path: '/users' },
    { text: 'Compliance', icon: <SecurityIcon />, path: '/compliance', adminOnly: true },
    { text: t('navigation.settings'), icon: <SettingsIcon />, path: '/settings' },
  ];

  const drawer = (
    <div>
      <Toolbar>
        <Typography variant="h6" noWrap component="div">
          CCS Quote Tool
        </Typography>
      </Toolbar>
      <Divider />
      <List>
        {menuItems.map((item) => {
          // Check if item requires admin access
          const user = JSON.parse(localStorage.getItem('user') || '{}');
          const isAdmin = user.role === 'super_admin' || user.role === 'admin' || user.role === 'tenant_admin';
          if ((item as any).adminOnly && !isAdmin) {
            return null;
          }
          
          return (
            <ListItem key={item.text} disablePadding>
              <ListItemButton
                selected={location.pathname === item.path}
                onClick={() => navigate(item.path)}
              >
                <ListItemIcon>{item.icon}</ListItemIcon>
                <ListItemText primary={item.text} />
              </ListItemButton>
            </ListItem>
          );
        })}
      </List>
      <Divider />
      <List>
        <ListItem disablePadding>
          <ListItemButton onClick={() => navigate('/settings')} data-tooltip="settings-menu">
            <ListItemIcon>
              <SettingsIcon />
            </ListItemIcon>
            <ListItemText primary="Settings" />
          </ListItemButton>
        </ListItem>
      </List>
    </div>
  );

  return (
    <Box sx={{ display: 'flex' }}>
      <AppBar
        position="fixed"
        sx={{
          width: { sm: `calc(100% - ${drawerWidth}px)` },
          ml: { sm: `${drawerWidth}px` },
        }}
      >
        <Toolbar>
          <IconButton
            color="inherit"
            aria-label="open drawer"
            edge="start"
            onClick={handleDrawerToggle}
            sx={{ mr: 2, display: { sm: 'none' } }}
          >
            <MenuIcon />
          </IconButton>
          <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
            {menuItems.find(item => item.path === location.pathname)?.text || 'CCS Quote Tool'}
          </Typography>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
            <AIMonitorBadge />
            <SimpleLanguageSelector />
            <Typography variant="body2">
              {user.email || 'User'}
            </Typography>
            <IconButton
              size="large"
              aria-label="account of current user"
              aria-controls="menu-appbar"
              aria-haspopup="true"
              onClick={handleMenu}
              color="inherit"
            >
              <AccountCircle />
            </IconButton>
            <Menu
              id="menu-appbar"
              anchorEl={anchorEl}
              anchorOrigin={{
                vertical: 'top',
                horizontal: 'right',
              }}
              keepMounted
              transformOrigin={{
                vertical: 'top',
                horizontal: 'right',
              }}
              open={Boolean(anchorEl)}
              onClose={handleClose}
            >
              <MenuItem onClick={() => { handleClose(); navigate('/profile'); }}>
                Profile
              </MenuItem>
              <MenuItem onClick={() => { handleClose(); navigate('/settings'); }}>
                {t('navigation.settings')}
              </MenuItem>
              <Divider />
              <MenuItem onClick={handleLogout}>
                <LogoutIcon sx={{ mr: 1 }} /> {t('navigation.logout')}
              </MenuItem>
            </Menu>
          </Box>
        </Toolbar>
      </AppBar>
      <Box
        component="nav"
        sx={{ width: { sm: drawerWidth }, flexShrink: { sm: 0 } }}
      >
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={handleDrawerToggle}
          ModalProps={{
            keepMounted: true,
          }}
          sx={{
            display: { xs: 'block', sm: 'none' },
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
          }}
        >
          {drawer}
        </Drawer>
        <Drawer
          variant="permanent"
          sx={{
            display: { xs: 'none', sm: 'block' },
            '& .MuiDrawer-paper': { boxSizing: 'border-box', width: drawerWidth },
          }}
          open
        >
          {drawer}
        </Drawer>
      </Box>
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          width: { sm: `calc(100% - ${drawerWidth}px)` },
          mt: 8,
          display: 'flex',
          flexDirection: 'column',
          minHeight: 'calc(100vh - 64px)'
        }}
      >
        {children}
        
        {/* Global Onboarding Tooltips */}
        <OnboardingTooltips
          isActive={showOnboardingTooltips}
          onComplete={handleTooltipComplete}
          onSkip={handleTooltipSkip}
        />
        
        {/* Version Display */}
        <VersionDisplay variant="footer" />
      </Box>
    </Box>
  );
};

export default Layout;



