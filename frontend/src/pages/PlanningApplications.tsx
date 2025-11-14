import React, { useState, useEffect } from 'react';
import {
  Container,
  Paper,
  Typography,
  Button,
  Box,
  Chip,
  IconButton,
  TextField,
  InputAdornment,
  Tooltip,
  Grid,
  Card,
  CardContent,
  CircularProgress,
  Switch,
  FormControlLabel,
  Tabs,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Link,
  Checkbox,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  TableSortLabel
} from '@mui/material';
import {
  Search as SearchIcon,
  PlayArrow as PlayArrowIcon,
  Refresh as RefreshIcon,
  Architecture as ArchitectureIcon,
  LocationOn as LocationOnIcon,
  Schedule as ScheduleIcon,
  BusinessCenter as BusinessCenterIcon,
  Stop as StopIcon,
  Pause as PauseIcon,
  OpenInNew as OpenInNewIcon,
  Archive as ArchiveIcon
} from '@mui/icons-material';
import { planningAPI } from '../services/api';

interface PlanningApplication {
  id: string;
  reference: string;
  address: string;
  proposal: string;
  application_type?: string;
  status: string;
  county: string;
  relevance_score?: number;
  ai_summary?: string;
  created_at: string;
  is_archived?: boolean;
}

interface CountyConfig {
  code: string;
  name: string;
  enabled: boolean;
  is_scheduled: boolean;
  last_run_at?: string;
  next_run_at?: string;
  total_applications_found: number;
  new_applications_this_run: number;
  running?: boolean;
}

const PlanningApplications: React.FC = () => {
  const [activeTab, setActiveTab] = useState(0);
  const [applications, setApplications] = useState<PlanningApplication[]>([]);
  const [totalApplications, setTotalApplications] = useState(0);
  const [counties, setCounties] = useState<CountyConfig[]>([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [runningCounties, setRunningCounties] = useState<Set<string>>(new Set());
  
  // New state for sorting, filtering, and archiving
  const [sortField, setSortField] = useState<string>('created_at');
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('desc');
  const [typeFilter, setTypeFilter] = useState<string>('all');
  const [selectedApplications, setSelectedApplications] = useState<Set<string>>(new Set());
  const [showArchived, setShowArchived] = useState(false);

  useEffect(() => {
    loadData();
  }, []);

  // Add periodic refresh to check for task completion and update running states
  useEffect(() => {
    const interval = setInterval(() => {
      // Only refresh if we have running counties
      if (runningCounties.size > 0) {
        loadCounties();
        loadApplications();
      }
    }, 15000); // Check every 15 seconds when there are running tasks

    return () => clearInterval(interval);
  }, [runningCounties]);

  const loadData = async () => {
    try {
      setLoading(true);
      await Promise.all([
        loadCounties(),
        loadApplications()
      ]);
    } catch (error) {
      console.error('Error loading data:', error);
    } finally {
      setLoading(false);
    }
  };

  const loadCounties = async () => {
    try {
      const response = await planningAPI.getCountyStatus();
      const countiesData = response.data || [];
      
      // Transform to the expected format
      const countyConfigs: CountyConfig[] = countiesData.map(county => ({
        code: county.code,
        name: county.name,
        enabled: county.enabled,
        is_scheduled: county.is_scheduled || false,
        last_run_at: county.last_run_at,
        next_run_at: county.next_run_at,
        total_applications_found: county.total_applications_found || 0,
        new_applications_this_run: county.new_applications_this_run || 0
      }));
      
      setCounties(countyConfigs);
    } catch (error) {
      console.error('Error loading counties:', error);
    }
  };

  const loadApplications = async (includeArchived = false) => {
    try {
      const params: any = {
        page: 1,
        limit: 500,  // Request more applications to show all available
        include_archived: includeArchived
      };

      const response = await planningAPI.listApplications(params);
      
      // The backend returns { applications: [...], total: 288, page: 1, etc }
      // But axios wraps it in { data: { applications: [...], total: 288, page: 1, etc } }
      const applicationsData = response.data?.applications || [];
      const total = response.data?.total || 0;
      setApplications(applicationsData);
      setTotalApplications(total);
    } catch (error) {
      console.error('Error loading applications:', error);
    }
  };

  const handleRunCounty = async (countyCode: string) => {
    try {
      setRunningCounties(prev => new Set(prev).add(countyCode));
      
      await planningAPI.runCounty(countyCode);
      
      alert(`Planning applications fetch started for ${counties.find(c => c.code === countyCode)?.name}`);
      
      // Reload data to get updated information
      loadApplications();
      loadCounties();
      
      // Set a timeout to clear running state after 5 minutes as a fallback
      setTimeout(() => {
        setRunningCounties(prev => {
          const newSet = new Set(prev);
          newSet.delete(countyCode);
          return newSet;
        });
      }, 5 * 60 * 1000); // 5 minutes
      
    } catch (error) {
      console.error('Error running county:', error);
      alert('Failed to run planning fetch');
      // Clear running state on error
      setRunningCounties(prev => {
        const newSet = new Set(prev);
        newSet.delete(countyCode);
        return newSet;
      });
    }
  };

  const handleScheduleToggle = async (countyCode: string, enabled: boolean) => {
    try {
      await planningAPI.updateCountySchedule(countyCode, {
        is_scheduled: enabled,
        frequency_days: 14
      });
      
      // Update local state
      setCounties(prev => prev.map(county => 
        county.code === countyCode 
          ? { ...county, is_scheduled: enabled }
          : county
      ));
      
      // Reload to get updated next_run_at
      loadCounties();
    } catch (error) {
      console.error('Error updating schedule:', error);
      alert('Failed to update schedule');
    }
  };

  const handleStopCounty = async (countyCode: string) => {
    try {
      await planningAPI.stopCounty(countyCode);
      
      // Remove from running counties set
      setRunningCounties(prev => {
        const newSet = new Set(prev);
        newSet.delete(countyCode);
        return newSet;
      });
      
      alert(`Scan stopped for ${counties.find(c => c.code === countyCode)?.name}`);
      
      // Reload data to get updated information
      loadCounties();
    } catch (error) {
      console.error('Error stopping county:', error);
      alert('Failed to stop scan');
    }
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
    setSelectedApplications(new Set()); // Clear selections when switching tabs
    
    if (newValue === 0) {
      setShowArchived(false);
      loadApplications(false);
    } else if (newValue === 2) {
      setShowArchived(true);
      loadApplications(true);
    }
    // For tab 1 (counties), no need to load applications
  };

  // Sorting function
  const handleSort = (field: string) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  // Multi-select functions
  const handleSelectAll = (checked: boolean) => {
    if (checked) {
      // Use filteredAndSortedApplications instead of raw applications
      // This ensures we only select the currently visible/filtered applications
      setSelectedApplications(new Set(filteredAndSortedApplications.map(app => app.id)));
    } else {
      setSelectedApplications(new Set());
    }
  };

  const handleSelectApplication = (appId: string, checked: boolean) => {
    const newSelected = new Set(selectedApplications);
    if (checked) {
      newSelected.add(appId);
    } else {
      newSelected.delete(appId);
    }
    setSelectedApplications(newSelected);
  };

  const filteredAndSortedApplications = React.useMemo(() => {
    let filtered = applications.filter(app => {
      // Filter by archived status
      const archivedMatch = showArchived ? app.is_archived : !app.is_archived;
      if (!archivedMatch) return false;
      
      // Filter by search term
      const matchesSearch = 
        app.reference.toLowerCase().includes(searchTerm.toLowerCase()) ||
        app.address.toLowerCase().includes(searchTerm.toLowerCase()) ||
        app.proposal.toLowerCase().includes(searchTerm.toLowerCase());
      
      // Filter by type
      const matchesType = typeFilter === 'all' || app.application_type === typeFilter;
      
      return matchesSearch && matchesType;
    });

    // Sort applications
    filtered.sort((a, b) => {
      let aValue, bValue;
      
      if (sortField === 'reference') {
        aValue = a.reference;
        bValue = b.reference;
      } else if (sortField === 'application_type') {
        aValue = a.application_type || '';
        bValue = b.application_type || '';
      } else if (sortField === 'created_at') {
        aValue = new Date(a.created_at).getTime();
        bValue = new Date(b.created_at).getTime();
      } else {
        return 0;
      }
      
      if (aValue < bValue) return sortDirection === 'asc' ? -1 : 1;
      if (aValue > bValue) return sortDirection === 'asc' ? 1 : -1;
      return 0;
    });

    return filtered;
  }, [applications, searchTerm, typeFilter, sortField, sortDirection, showArchived]);

  // Helper functions for checkbox state calculation
  const getVisibleSelectedCount = () => {
    return filteredAndSortedApplications.filter(app => selectedApplications.has(app.id)).length;
  };

  const areAllVisibleSelected = () => {
    return filteredAndSortedApplications.length > 0 && 
           filteredAndSortedApplications.every(app => selectedApplications.has(app.id));
  };

  const areSomeVisibleSelected = () => {
    return getVisibleSelectedCount() > 0 && !areAllVisibleSelected();
  };

  const getApplicationTypeColor = (type?: string) => {
    switch (type?.toLowerCase()) {
      case 'commercial':
        return 'primary';
      case 'residential':
        return 'secondary';
      case 'industrial':
        return 'warning';
      default:
        return 'default';
    }
  };

  const getPlanningApplicationUrl = (app: PlanningApplication) => {
    // Construct URL based on county and reference number
    // For Leicester City Council applications - use the correct URL format
    if (app.county.toLowerCase().includes('leicester') && app.county.toLowerCase() !== 'leicestershire') {
      return `https://planning.leicester.gov.uk/Planning/Display/${app.reference}`;
    }
    // For Leicestershire County applications (rural areas)
    if (app.county.toLowerCase() === 'leicestershire') {
      return `https://publicaccess.leicestershire.gov.uk/portal/servlets/ApplicationSearchServlet?PKID=${app.reference}`;
    }
    // For other counties, provide a generic search link
    return `https://www.gov.uk/find-local-council`;
  };

  // Archive functions
  const handleArchiveApplications = async (appIds: string[]) => {
    try {
      await planningAPI.archiveApplications(appIds, !showArchived);
      
      // Update local state to reflect the change
      setApplications(prev => prev.map(app => 
        appIds.includes(app.id) ? { ...app, is_archived: !showArchived } : app
      ));
      
      setSelectedApplications(new Set());
      
      // Reload applications to ensure we have the latest data
      await loadApplications(showArchived);
      
      alert(`Successfully ${showArchived ? 'unarchived' : 'archived'} ${appIds.length} applications`);
    } catch (error) {
      console.error('Error archiving applications:', error);
      alert('Failed to archive applications');
    }
  };

  const handleBulkArchive = () => {
    const visibleSelectedApps = filteredAndSortedApplications.filter(app => selectedApplications.has(app.id));
    
    if (visibleSelectedApps.length === 0) {
      alert('Please select applications to archive');
      return;
    }
    
    const appIds = visibleSelectedApps.map(app => app.id);
    handleArchiveApplications(appIds);
  };

  return (
    <Container maxWidth="xl" sx={{ mt: 4, mb: 4 }}>
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" gutterBottom>
          Planning Applications
        </Typography>
        <Typography variant="body1" color="text.secondary">
          Monitor UK planning applications and generate leads from relevant developments
        </Typography>
      </Box>

      {/* Tabs */}
      <Paper sx={{ mb: 3 }}>
        <Tabs value={activeTab} onChange={handleTabChange} aria-label="planning applications tabs">
          <Tab 
            icon={<ArchitectureIcon />} 
            label="Applications" 
            iconPosition="start"
            value={0}
          />
          <Tab 
            icon={<BusinessCenterIcon />} 
            label="Counties" 
            iconPosition="start"
            value={1}
          />
          <Tab 
            icon={<ArchiveIcon />} 
            label="Archived" 
            iconPosition="start"
            value={2}
          />
        </Tabs>
      </Paper>

      {/* Applications Tab */}
      {activeTab === 0 && (
        <Paper sx={{ p: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
            <Box>
              <Typography variant="h6">
                {showArchived ? 'Archived Planning Applications' : 'Recent Planning Applications'}
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Showing {filteredAndSortedApplications.length} of {totalApplications} applications
              </Typography>
            </Box>
            <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
              <FormControl size="small" sx={{ minWidth: 120 }}>
                <InputLabel>Filter by Type</InputLabel>
                <Select
                  value={typeFilter}
                  label="Filter by Type"
                  onChange={(e) => setTypeFilter(e.target.value)}
                >
                  <MenuItem value="all">All Types</MenuItem>
                  <MenuItem value="commercial">Commercial</MenuItem>
                  <MenuItem value="residential">Residential</MenuItem>
                  <MenuItem value="industrial">Industrial</MenuItem>
                  <MenuItem value="other">Other</MenuItem>
                </Select>
              </FormControl>
              <TextField
                placeholder="Search applications..."
                size="small"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchIcon />
                    </InputAdornment>
                  ),
                }}
                sx={{ minWidth: 250 }}
              />
              {getVisibleSelectedCount() > 0 && (
                <Button
                  variant="contained"
                  color="warning"
                  startIcon={<ArchiveIcon />}
                  onClick={handleBulkArchive}
                >
                  {showArchived ? 'Unarchive' : 'Archive'} ({getVisibleSelectedCount()})
                </Button>
              )}
              <Button
                variant="outlined"
                startIcon={<RefreshIcon />}
                onClick={() => loadApplications(showArchived)}
              >
                Refresh
              </Button>
            </Box>
          </Box>

          {filteredAndSortedApplications.length === 0 ? (
            <Box sx={{ textAlign: 'center', py: 4 }}>
              <ArchitectureIcon sx={{ fontSize: 64, color: 'primary.main', mb: 2 }} />
              <Typography variant="h6" gutterBottom>
                No Planning Applications Found
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Run a county scan from the Counties tab to discover planning applications
              </Typography>
            </Box>
          ) : (
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell padding="checkbox">
                      <Checkbox
                        indeterminate={areSomeVisibleSelected()}
                        checked={areAllVisibleSelected()}
                        onChange={(e) => handleSelectAll(e.target.checked)}
                      />
                    </TableCell>
                    <TableCell>
                      <TableSortLabel
                        active={sortField === 'reference'}
                        direction={sortField === 'reference' ? sortDirection : 'asc'}
                        onClick={() => handleSort('reference')}
                      >
                        Reference
                      </TableSortLabel>
                    </TableCell>
                    <TableCell>Address</TableCell>
                    <TableCell>Proposal</TableCell>
                    <TableCell>
                      <TableSortLabel
                        active={sortField === 'application_type'}
                        direction={sortField === 'application_type' ? sortDirection : 'asc'}
                        onClick={() => handleSort('application_type')}
                      >
                        Type
                      </TableSortLabel>
                    </TableCell>
                    <TableCell>County</TableCell>
                    <TableCell>
                      <TableSortLabel
                        active={sortField === 'created_at'}
                        direction={sortField === 'created_at' ? sortDirection : 'asc'}
                        onClick={() => handleSort('created_at')}
                      >
                        Date
                      </TableSortLabel>
                    </TableCell>
                    <TableCell>Score</TableCell>
                    <TableCell>View</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {filteredAndSortedApplications.map((app) => {
                    const applicationUrl = getPlanningApplicationUrl(app);
                    const isSelected = selectedApplications.has(app.id);
                    return (
                      <TableRow key={app.id} hover selected={isSelected}>
                        <TableCell padding="checkbox">
                          <Checkbox
                            checked={isSelected}
                            onChange={(e) => handleSelectApplication(app.id, e.target.checked)}
                          />
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2" sx={{ fontWeight: 'medium' }}>
                            {app.reference}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2" sx={{ maxWidth: 200 }}>
                            {app.address.length > 60 ? `${app.address.substring(0, 60)}...` : app.address}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2" color="text.secondary" sx={{ maxWidth: 300 }}>
                            {app.proposal.length > 100 ? `${app.proposal.substring(0, 100)}...` : app.proposal}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          {app.application_type && (
                            <Chip 
                              label={app.application_type.replace('_', ' ')} 
                              color={getApplicationTypeColor(app.application_type) as any}
                              size="small"
                            />
                          )}
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            {app.county}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            {new Date(app.created_at).toLocaleDateString()}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          {app.relevance_score && (
                            <Chip 
                              label={app.relevance_score} 
                              color={app.relevance_score >= 70 ? 'success' : app.relevance_score >= 40 ? 'warning' : 'default'}
                              size="small"
                            />
                          )}
                        </TableCell>
                        <TableCell>
                          <Link 
                            href={applicationUrl} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}
                          >
                            View
                            <OpenInNewIcon sx={{ fontSize: 16 }} />
                          </Link>
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </Paper>
      )}

      {/* Counties Tab */}
      {activeTab === 1 && (
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            County Monitoring
          </Typography>
          <Typography variant="body2" color="text.secondary" sx={{ mb: 3 }}>
            Configure which counties to monitor and enable scheduled runs for planning applications
          </Typography>
          
          <Grid container spacing={2}>
            {loading ? (
              <Grid item xs={12} sx={{ textAlign: 'center', py: 4 }}>
                <CircularProgress />
              </Grid>
            ) : (
              counties.map((county) => (
                <Grid item xs={12} md={6} lg={4} key={county.code}>
                  <Card variant="outlined">
                    <CardContent>
                      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                          <LocationOnIcon color="primary" />
                          <Typography variant="h6">
                            {county.name}
                          </Typography>
                        </Box>
                        <Chip 
                          label={
                            runningCounties.has(county.code) 
                              ? "Running..." 
                              : county.enabled 
                                ? "Available" 
                                : "Disabled"
                          }
                          color={
                            runningCounties.has(county.code) 
                              ? "warning" 
                              : county.enabled 
                                ? "success" 
                                : "default"
                          }
                          size="small"
                          icon={runningCounties.has(county.code) ? <CircularProgress size={12} /> : undefined}
                        />
                      </Box>

                      <Box sx={{ mb: 2 }}>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                          <Typography variant="body2">Last Run:</Typography>
                          <Typography variant="body2">
                            {county.last_run_at 
                              ? new Date(county.last_run_at).toLocaleDateString()
                              : 'Never'
                            }
                          </Typography>
                        </Box>
                        <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                          <Typography variant="body2">Applications Found:</Typography>
                          <Typography variant="body2" fontWeight="medium">
                            {county.total_applications_found}
                          </Typography>
                        </Box>
                      </Box>

                      <Box sx={{ mb: 2 }}>
                        <FormControlLabel
                          control={
                            <Switch 
                              checked={county.is_scheduled}
                              onChange={(e) => handleScheduleToggle(county.code, e.target.checked)}
                              disabled={!county.enabled}
                            />
                          }
                          label={
                            <Box>
                              <Typography variant="body2">Scheduled (every 2 weeks)</Typography>
                              {county.next_run_at && county.is_scheduled && (
                                <Typography variant="caption" color="text.secondary">
                                  Next: {new Date(county.next_run_at).toLocaleDateString()}
                                </Typography>
                              )}
                            </Box>
                          }
                        />
                      </Box>

                      <Box sx={{ display: 'flex', gap: 1, justifyContent: 'flex-end' }}>
                        {runningCounties.has(county.code) ? (
                          <>
                            <Tooltip title="Stop Scan">
                              <Button
                                variant="outlined"
                                color="error"
                                size="small"
                                startIcon={<StopIcon />}
                                onClick={() => handleStopCounty(county.code)}
                              >
                                Stop
                              </Button>
                            </Tooltip>
                            <Tooltip title="Scan in Progress">
                              <Button
                                variant="contained"
                                size="small"
                                startIcon={<CircularProgress size={16} />}
                                disabled={true}
                                sx={{ cursor: 'not-allowed' }}
                              >
                                Running...
                              </Button>
                            </Tooltip>
                          </>
                        ) : (
                          <Tooltip title="Run Now">
                            <Button
                              variant="contained"
                              size="small"
                              startIcon={<PlayArrowIcon />}
                              onClick={() => handleRunCounty(county.code)}
                              disabled={!county.enabled}
                            >
                              Run Now
                            </Button>
                          </Tooltip>
                        )}
                      </Box>
                    </CardContent>
                  </Card>
                </Grid>
              ))
            )}
          </Grid>
        </Paper>
      )}

      {/* Archived Tab */}
      {activeTab === 2 && (
        <Paper sx={{ p: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
            <Box>
              <Typography variant="h6">
                Archived Planning Applications
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Showing {filteredAndSortedApplications.length} archived applications
              </Typography>
            </Box>
            <Box sx={{ display: 'flex', gap: 2, alignItems: 'center', flexWrap: 'wrap' }}>
              <FormControl size="small" sx={{ minWidth: 120 }}>
                <InputLabel>Filter by Type</InputLabel>
                <Select
                  value={typeFilter}
                  label="Filter by Type"
                  onChange={(e) => setTypeFilter(e.target.value)}
                >
                  <MenuItem value="all">All Types</MenuItem>
                  <MenuItem value="commercial">Commercial</MenuItem>
                  <MenuItem value="residential">Residential</MenuItem>
                  <MenuItem value="industrial">Industrial</MenuItem>
                  <MenuItem value="other">Other</MenuItem>
                </Select>
              </FormControl>
              <TextField
                placeholder="Search archived applications..."
                size="small"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                InputProps={{
                  startAdornment: (
                    <InputAdornment position="start">
                      <SearchIcon />
                    </InputAdornment>
                  ),
                }}
                sx={{ minWidth: 250 }}
              />
              {getVisibleSelectedCount() > 0 && (
                <Button
                  variant="contained"
                  color="success"
                  startIcon={<ArchiveIcon />}
                  onClick={handleBulkArchive}
                >
                  Unarchive ({getVisibleSelectedCount()})
                </Button>
              )}
              <Button
                variant="outlined"
                startIcon={<RefreshIcon />}
                onClick={() => loadApplications(true)}
              >
                Refresh
              </Button>
            </Box>
          </Box>

          {filteredAndSortedApplications.length === 0 ? (
            <Box sx={{ textAlign: 'center', py: 4 }}>
              <ArchiveIcon sx={{ fontSize: 64, color: 'primary.main', mb: 2 }} />
              <Typography variant="h6" gutterBottom>
                No Archived Applications Found
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Applications you archive from the Applications tab will appear here
              </Typography>
            </Box>
          ) : (
            <TableContainer>
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell padding="checkbox">
                      <Checkbox
                        indeterminate={areSomeVisibleSelected()}
                        checked={areAllVisibleSelected()}
                        onChange={(e) => handleSelectAll(e.target.checked)}
                      />
                    </TableCell>
                    <TableCell>
                      <TableSortLabel
                        active={sortField === 'reference'}
                        direction={sortField === 'reference' ? sortDirection : 'asc'}
                        onClick={() => handleSort('reference')}
                      >
                        Reference
                      </TableSortLabel>
                    </TableCell>
                    <TableCell>Address</TableCell>
                    <TableCell>Proposal</TableCell>
                    <TableCell>
                      <TableSortLabel
                        active={sortField === 'application_type'}
                        direction={sortField === 'application_type' ? sortDirection : 'asc'}
                        onClick={() => handleSort('application_type')}
                      >
                        Type
                      </TableSortLabel>
                    </TableCell>
                    <TableCell>County</TableCell>
                    <TableCell>
                      <TableSortLabel
                        active={sortField === 'created_at'}
                        direction={sortField === 'created_at' ? sortDirection : 'asc'}
                        onClick={() => handleSort('created_at')}
                      >
                        Date
                      </TableSortLabel>
                    </TableCell>
                    <TableCell>Score</TableCell>
                    <TableCell>View</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {filteredAndSortedApplications.map((app) => {
                    const applicationUrl = getPlanningApplicationUrl(app);
                    const isSelected = selectedApplications.has(app.id);
                    return (
                      <TableRow key={app.id} hover selected={isSelected}>
                        <TableCell padding="checkbox">
                          <Checkbox
                            checked={isSelected}
                            onChange={(e) => handleSelectApplication(app.id, e.target.checked)}
                          />
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2" sx={{ fontWeight: 'medium' }}>
                            {app.reference}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2" sx={{ maxWidth: 200 }}>
                            {app.address.length > 60 ? `${app.address.substring(0, 60)}...` : app.address}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2" color="text.secondary" sx={{ maxWidth: 300 }}>
                            {app.proposal.length > 100 ? `${app.proposal.substring(0, 100)}...` : app.proposal}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          {app.application_type && (
                            <Chip 
                              label={app.application_type.replace('_', ' ')} 
                              color={getApplicationTypeColor(app.application_type) as any}
                              size="small"
                            />
                          )}
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            {app.county}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">
                            {new Date(app.created_at).toLocaleDateString()}
                          </Typography>
                        </TableCell>
                        <TableCell>
                          {app.relevance_score && (
                            <Chip 
                              label={app.relevance_score} 
                              color={app.relevance_score >= 70 ? 'success' : app.relevance_score >= 40 ? 'warning' : 'default'}
                              size="small"
                            />
                          )}
                        </TableCell>
                        <TableCell>
                          <Link 
                            href={applicationUrl} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}
                          >
                            View
                            <OpenInNewIcon sx={{ fontSize: 16 }} />
                          </Link>
                        </TableCell>
                      </TableRow>
                    );
                  })}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </Paper>
      )}
    </Container>
  );
};

export default PlanningApplications;