import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  LinearProgress,
  Chip,
  Grid,
  Alert,
  CircularProgress,
  IconButton,
  Tooltip,
  Collapse,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider,
  Stack
} from '@mui/material';
import {
  Favorite as HeartIcon,
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  Refresh as RefreshIcon,
  ExpandMore as ExpandMoreIcon,
  ExpandLess as ExpandLessIcon,
  LocalFireDepartment as FireIcon,
  Assignment as TicketIcon,
  Receipt as QuoteIcon,
  Schedule as ScheduleIcon
} from '@mui/icons-material';
import { customerHealthAPI } from '../services/api';

interface CustomerHealthWidgetProps {
  customerId: string;
  daysBack?: number;
  compact?: boolean;
}

interface HealthData {
  health_score?: number;
  factors?: string[];
  risks?: Array<{
    type: string;
    severity: 'low' | 'medium' | 'high';
    description: string;
  }>;
  recommendations?: string[];
  trends?: {
    direction: 'up' | 'down' | 'stable';
    period: string;
  };
  digest?: string;
  timestamp?: string;
}

const CustomerHealthWidget: React.FC<CustomerHealthWidgetProps> = ({
  customerId,
  daysBack = 90,
  compact = false
}) => {
  const [healthData, setHealthData] = useState<HealthData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expanded, setExpanded] = useState(!compact);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadHealthData();
  }, [customerId, daysBack]);

  const loadHealthData = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await customerHealthAPI.getHealth(customerId, daysBack);
      setHealthData(response.data);
    } catch (err: any) {
      console.error('Error loading customer health:', err);
      setError(err.response?.data?.detail || 'Failed to load health data');
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await loadHealthData();
    setRefreshing(false);
  };

  const getHealthColor = (score?: number) => {
    if (!score) return 'default';
    if (score >= 80) return 'success';
    if (score >= 60) return 'warning';
    return 'error';
  };

  const getHealthLabel = (score?: number) => {
    if (!score) return 'Unknown';
    if (score >= 80) return 'Excellent';
    if (score >= 60) return 'Good';
    if (score >= 40) return 'Fair';
    return 'At Risk';
  };

  const getRiskColor = (severity: string) => {
    switch (severity) {
      case 'high':
        return 'error';
      case 'medium':
        return 'warning';
      default:
        return 'info';
    }
  };

  if (loading && !healthData) {
    return (
      <Card>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: 200 }}>
            <CircularProgress />
          </Box>
        </CardContent>
      </Card>
    );
  }

  if (error && !healthData) {
    return (
      <Card>
        <CardContent>
          <Alert severity="error">{error}</Alert>
        </CardContent>
      </Card>
    );
  }

  const healthScore = healthData?.health_score || 0;
  const healthColor = getHealthColor(healthScore);
  const healthLabel = getHealthLabel(healthScore);

  return (
    <Card
      sx={{
        height: '100%',
        display: 'flex',
        flexDirection: 'column',
        background: `linear-gradient(135deg, ${healthColor === 'success' ? '#e8f5e9' : healthColor === 'warning' ? '#fff3e0' : '#ffebee'} 0%, #ffffff 100%)`,
        border: `2px solid`,
        borderColor: `${healthColor}.main`,
        transition: 'all 0.3s ease',
        '&:hover': {
          boxShadow: 6,
          transform: 'translateY(-2px)'
        }
      }}
    >
      <CardContent sx={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
        {/* Header */}
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', mb: 2 }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <HeartIcon color={healthColor as any} sx={{ fontSize: 32 }} />
            <Box>
              <Typography variant="h6" component="div" fontWeight="bold">
                Customer Health
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Last {daysBack} days
              </Typography>
            </Box>
          </Box>
          <Box sx={{ display: 'flex', gap: 0.5 }}>
            <Tooltip title="Refresh">
              <IconButton
                size="small"
                onClick={handleRefresh}
                disabled={refreshing}
              >
                <RefreshIcon fontSize="small" />
              </IconButton>
            </Tooltip>
            {!compact && (
              <IconButton
                size="small"
                onClick={() => setExpanded(!expanded)}
              >
                {expanded ? <ExpandLessIcon /> : <ExpandMoreIcon />}
              </IconButton>
            )}
          </Box>
        </Box>

        {/* Health Score */}
        <Box sx={{ mb: 3 }}>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 1 }}>
            <Typography variant="h3" component="div" fontWeight="bold" color={`${healthColor}.main`}>
              {healthScore}
            </Typography>
            <Chip
              label={healthLabel}
              color={healthColor as any}
              size="small"
              icon={healthScore >= 80 ? <CheckCircleIcon /> : healthScore >= 60 ? <WarningIcon /> : <FireIcon />}
            />
          </Box>
          <LinearProgress
            variant="determinate"
            value={healthScore}
            color={healthColor as any}
            sx={{
              height: 8,
              borderRadius: 4,
              bgcolor: 'grey.200',
              '& .MuiLinearProgress-bar': {
                borderRadius: 4
              }
            }}
          />
        </Box>

        {/* Factors */}
        {healthData?.factors && healthData.factors.length > 0 && (
          <Box sx={{ mb: 2 }}>
            <Typography variant="subtitle2" color="text.secondary" gutterBottom>
              Key Factors
            </Typography>
            <Stack direction="row" spacing={1} flexWrap="wrap" gap={1}>
              {healthData.factors.slice(0, 3).map((factor, idx) => (
                <Chip
                  key={idx}
                  label={factor}
                  size="small"
                  variant="outlined"
                  color={healthColor as any}
                />
              ))}
            </Stack>
          </Box>
        )}

        {/* Expanded Details */}
        <Collapse in={expanded}>
          <Divider sx={{ my: 2 }} />
          
          {/* Risks */}
          {healthData?.risks && healthData.risks.length > 0 && (
            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <WarningIcon fontSize="small" />
                Risks
              </Typography>
              <List dense>
                {healthData.risks.map((risk, idx) => (
                  <ListItem key={idx} sx={{ px: 0 }}>
                    <ListItemIcon sx={{ minWidth: 36 }}>
                      <Chip
                        label={risk.severity}
                        size="small"
                        color={getRiskColor(risk.severity) as any}
                      />
                    </ListItemIcon>
                    <ListItemText
                      primary={risk.type}
                      secondary={risk.description}
                      primaryTypographyProps={{ variant: 'body2' }}
                      secondaryTypographyProps={{ variant: 'caption' }}
                    />
                  </ListItem>
                ))}
              </List>
            </Box>
          )}

          {/* Recommendations */}
          {healthData?.recommendations && healthData.recommendations.length > 0 && (
            <Box sx={{ mb: 2 }}>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <CheckCircleIcon fontSize="small" />
                Recommendations
              </Typography>
              <List dense>
                {healthData.recommendations.map((rec, idx) => (
                  <ListItem key={idx} sx={{ px: 0 }}>
                    <ListItemIcon sx={{ minWidth: 36 }}>
                      <CheckCircleIcon fontSize="small" color="success" />
                    </ListItemIcon>
                    <ListItemText
                      primary={rec}
                      primaryTypographyProps={{ variant: 'body2' }}
                    />
                  </ListItem>
                ))}
              </List>
            </Box>
          )}

          {/* Trends */}
          {healthData?.trends && (
            <Box>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                {healthData.trends.direction === 'up' ? (
                  <TrendingUpIcon fontSize="small" color="success" />
                ) : healthData.trends.direction === 'down' ? (
                  <TrendingDownIcon fontSize="small" color="error" />
                ) : (
                  <ScheduleIcon fontSize="small" color="info" />
                )}
                Trend
              </Typography>
              <Typography variant="body2" color="text.secondary">
                {healthData.trends.period}
              </Typography>
            </Box>
          )}

          {/* Digest */}
          {healthData?.digest && (
            <Box sx={{ mt: 2 }}>
              <Typography variant="subtitle2" color="text.secondary" gutterBottom>
                Summary
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>
                {healthData.digest}
              </Typography>
            </Box>
          )}
        </Collapse>

        {error && healthData && (
          <Alert severity="error" sx={{ mt: 2 }} onClose={() => setError(null)}>
            {error}
          </Alert>
        )}
      </CardContent>
    </Card>
  );
};

export default CustomerHealthWidget;

