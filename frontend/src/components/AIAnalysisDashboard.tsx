import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  TextField,
  CircularProgress,
  Alert,
  Chip,
  LinearProgress,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Divider,
  Paper,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions
} from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  Business as BusinessIcon,
  Assessment as AssessmentIcon,
  Warning as WarningIcon,
  CheckCircle as CheckCircleIcon,
  Search as SearchIcon,
  Refresh as RefreshIcon,
  Visibility as VisibilityIcon,
  Download as DownloadIcon
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';

interface AIAnalysisDashboardProps {
  companyData?: any;
  onAnalysisComplete?: (analysis: any) => void;
}

interface AnalysisResult {
  company_name: string;
  analysis: {
    company_overview?: string;
    industry_analysis?: string;
    size_assessment?: string;
    growth_potential?: string;
    it_needs_assessment?: string;
    lead_score?: number;
    decision_makers?: string[];
    competitive_advantages?: string[];
    risk_factors?: string[];
    recommended_approach?: string;
    next_steps?: string[];
    opportunities?: string[];
    urgency?: string;
    budget_estimate?: string;
    timeline?: string;
  };
  source_data?: {
    companies_house?: any;
    google_maps?: any;
  };
}

const AIAnalysisDashboard: React.FC<AIAnalysisDashboardProps> = ({
  companyData,
  onAnalysisComplete
}) => {
  const { t } = useTranslation();
  const [analysisResult, setAnalysisResult] = useState<AnalysisResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [detailedView, setDetailedView] = useState(false);

  const runAnalysis = async (companyName: string, companyNumber?: string) => {
    setLoading(true);
    setError('');

    try {
      const token = localStorage.getItem('access_token');
      const response = await fetch('/api/v1/ai-analysis/analyze-company', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          company_name: companyName,
          company_number: companyNumber
        })
      });

      if (!response.ok) {
        throw new Error('Failed to analyze company');
      }

      const result = await response.json();
      
      if (result.success) {
        setAnalysisResult(result);
        if (onAnalysisComplete) {
          onAnalysisComplete(result);
        }
      } else {
        setError(result.error || 'Analysis failed');
      }
    } catch (err) {
      setError(`Error: ${err}`);
    } finally {
      setLoading(false);
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return '#4caf50';
    if (score >= 60) return '#ff9800';
    return '#f44336';
  };

  const getUrgencyColor = (urgency: string) => {
    switch (urgency?.toLowerCase()) {
      case 'high': return 'error';
      case 'medium': return 'warning';
      case 'low': return 'success';
      default: return 'default';
    }
  };

  const ScoreIndicator: React.FC<{ score: number }> = ({ score }) => (
    <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
      <Box sx={{ width: '100%', mr: 1 }}>
        <LinearProgress
          variant="determinate"
          value={score}
          sx={{
            height: 20,
            borderRadius: 10,
            backgroundColor: '#e0e0e0',
            '& .MuiLinearProgress-bar': {
              backgroundColor: getScoreColor(score),
              borderRadius: 10
            }
          }}
        />
      </Box>
      <Typography variant="h6" sx={{ minWidth: 60, textAlign: 'center' }}>
        {score}/100
      </Typography>
    </Box>
  );

  const AnalysisCard: React.FC<{ title: string; children: React.ReactNode; icon?: React.ReactNode }> = ({
    title,
    children,
    icon
  }) => (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          {icon}
          <Typography variant="h6" sx={{ ml: icon ? 1 : 0 }}>
            {title}
          </Typography>
        </Box>
        {children}
      </CardContent>
    </Card>
  );

  const QuickInsights = () => {
    if (!analysisResult?.analysis) return null;

    const analysis = analysisResult.analysis;
    
    return (
      <Grid container spacing={3}>
        <Grid
          size={{
            xs: 12,
            md: 6
          }}>
          <AnalysisCard
            title="Lead Score"
            icon={<AssessmentIcon color="primary" />}
          >
            <ScoreIndicator score={analysis.lead_score || 0} />
            <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap' }}>
              <Chip
                label={analysis.urgency || 'Unknown'}
                color={getUrgencyColor(analysis.urgency || '')}
                size="small"
              />
              <Chip
                label={analysis.size_assessment || 'Unknown Size'}
                variant="outlined"
                size="small"
              />
              <Chip
                label={analysis.industry_analysis || 'Unknown Industry'}
                variant="outlined"
                size="small"
              />
            </Box>
          </AnalysisCard>
        </Grid>
        <Grid
          size={{
            xs: 12,
            md: 6
          }}>
          <AnalysisCard
            title="Business Overview"
            icon={<BusinessIcon color="primary" />}
          >
            <Typography variant="body2" sx={{ mb: 2 }}>
              {analysis.company_overview || 'No overview available'}
            </Typography>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
              <Typography variant="body2">Growth Potential:</Typography>
              <Typography variant="body2" fontWeight="bold">
                {analysis.growth_potential || 'Unknown'}
              </Typography>
            </Box>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
              <Typography variant="body2">Budget Estimate:</Typography>
              <Typography variant="body2" fontWeight="bold">
                {analysis.budget_estimate || 'Unknown'}
              </Typography>
            </Box>
            <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
              <Typography variant="body2">Timeline:</Typography>
              <Typography variant="body2" fontWeight="bold">
                {analysis.timeline || 'Unknown'}
              </Typography>
            </Box>
          </AnalysisCard>
        </Grid>
        <Grid size={12}>
          <AnalysisCard
            title="IT Infrastructure Needs"
            icon={<TrendingUpIcon color="primary" />}
          >
            <Typography variant="body2">
              {analysis.it_needs_assessment || 'No assessment available'}
            </Typography>
          </AnalysisCard>
        </Grid>
        <Grid
          size={{
            xs: 12,
            md: 6
          }}>
          <AnalysisCard
            title="Opportunities"
            icon={<CheckCircleIcon color="success" />}
          >
            {analysis.opportunities && analysis.opportunities.length > 0 ? (
              <List dense>
                {analysis.opportunities.map((opportunity, index) => (
                  <ListItem key={index} sx={{ py: 0.5 }}>
                    <ListItemIcon>
                      <CheckCircleIcon color="success" fontSize="small" />
                    </ListItemIcon>
                    <ListItemText primary={opportunity} />
                  </ListItem>
                ))}
              </List>
            ) : (
              <Typography variant="body2" color="text.secondary">
                No specific opportunities identified
              </Typography>
            )}
          </AnalysisCard>
        </Grid>
        <Grid
          size={{
            xs: 12,
            md: 6
          }}>
          <AnalysisCard
            title="Risk Factors"
            icon={<WarningIcon color="warning" />}
          >
            {analysis.risk_factors && analysis.risk_factors.length > 0 ? (
              <List dense>
                {analysis.risk_factors.map((risk, index) => (
                  <ListItem key={index} sx={{ py: 0.5 }}>
                    <ListItemIcon>
                      <WarningIcon color="warning" fontSize="small" />
                    </ListItemIcon>
                    <ListItemText primary={risk} />
                  </ListItem>
                ))}
              </List>
            ) : (
              <Typography variant="body2" color="text.secondary">
                No significant risk factors identified
              </Typography>
            )}
          </AnalysisCard>
        </Grid>
      </Grid>
    );
  };

  const DetailedAnalysis = () => {
    if (!analysisResult?.analysis) return null;

    const analysis = analysisResult.analysis;

    return (
      <Grid container spacing={3}>
        <Grid size={12}>
          <Paper sx={{ p: 3 }}>
            <Typography variant="h5" gutterBottom>
              Detailed Analysis Report
            </Typography>
            <Typography variant="body1" sx={{ mb: 3 }}>
              {analysis.company_overview || 'No detailed overview available'}
            </Typography>

            <Grid container spacing={3}>
              <Grid
                size={{
                  xs: 12,
                  md: 6
                }}>
                <Typography variant="h6" gutterBottom>
                  Company Information
                </Typography>
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" color="text.secondary">Industry</Typography>
                  <Typography variant="body1">{analysis.industry_analysis || 'Not specified'}</Typography>
                </Box>
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" color="text.secondary">Company Size</Typography>
                  <Typography variant="body1">{analysis.size_assessment || 'Not specified'}</Typography>
                </Box>
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" color="text.secondary">Growth Potential</Typography>
                  <Typography variant="body1">{analysis.growth_potential || 'Not specified'}</Typography>
                </Box>
                <Box sx={{ mb: 2 }}>
                  <Typography variant="body2" color="text.secondary">Budget Estimate</Typography>
                  <Typography variant="body1">{analysis.budget_estimate || 'Not specified'}</Typography>
                </Box>
                <Box>
                  <Typography variant="body2" color="text.secondary">Timeline</Typography>
                  <Typography variant="body1">{analysis.timeline || 'Not specified'}</Typography>
                </Box>
              </Grid>

              <Grid
                size={{
                  xs: 12,
                  md: 6
                }}>
                <Typography variant="h6" gutterBottom>
                  Engagement Strategy
                </Typography>
                <Typography variant="body1" sx={{ mb: 3 }}>
                  {analysis.recommended_approach || 'No specific approach recommended'}
                </Typography>

                {analysis.next_steps && analysis.next_steps.length > 0 && (
                  <>
                    <Typography variant="h6" gutterBottom>
                      Next Steps
                    </Typography>
                    <List dense>
                      {analysis.next_steps.map((step, index) => (
                        <ListItem key={index}>
                          <ListItemText primary={`${index + 1}. ${step}`} />
                        </ListItem>
                      ))}
                    </List>
                  </>
                )}
              </Grid>

              {analysis.decision_makers && analysis.decision_makers.length > 0 && (
                <Grid size={12}>
                  <Typography variant="h6" gutterBottom>
                    Key Decision Makers
                  </Typography>
                  <List dense>
                    {analysis.decision_makers.map((maker, index) => (
                      <ListItem key={index}>
                        <ListItemText primary={maker} />
                      </ListItem>
                    ))}
                  </List>
                </Grid>
              )}

              {analysis.competitive_advantages && analysis.competitive_advantages.length > 0 && (
                <Grid size={12}>
                  <Typography variant="h6" gutterBottom>
                    Competitive Advantages
                  </Typography>
                  <List dense>
                    {analysis.competitive_advantages.map((advantage, index) => (
                      <ListItem key={index}>
                        <ListItemIcon>
                          <CheckCircleIcon color="success" />
                        </ListItemIcon>
                        <ListItemText primary={advantage} />
                      </ListItem>
                    ))}
                  </List>
                </Grid>
              )}
            </Grid>
          </Paper>
        </Grid>
      </Grid>
    );
  };

  return (
    <Box>
      {/* Search Section */}
      <Paper sx={{ p: 3, mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          Company Analysis
        </Typography>
        <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
          <TextField
            fullWidth
            label="Company Name"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Enter company name to analyze"
          />
          <Button
            variant="contained"
            onClick={() => runAnalysis(searchQuery)}
            disabled={loading || !searchQuery.trim()}
            startIcon={loading ? <CircularProgress size={20} /> : <SearchIcon />}
          >
            {loading ? 'Analyzing...' : 'Analyze'}
          </Button>
        </Box>
        
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}

        {analysisResult && (
          <Box sx={{ display: 'flex', gap: 1, mt: 2 }}>
            <Button
              variant="outlined"
              startIcon={<VisibilityIcon />}
              onClick={() => setDetailedView(!detailedView)}
            >
              {detailedView ? 'Quick View' : 'Detailed View'}
            </Button>
            <Button
              variant="outlined"
              startIcon={<RefreshIcon />}
              onClick={() => runAnalysis(searchQuery)}
            >
              Refresh Analysis
            </Button>
          </Box>
        )}
      </Paper>

      {/* Analysis Results */}
      {loading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
          <CircularProgress />
          <Typography sx={{ ml: 2 }}>Analyzing company data...</Typography>
        </Box>
      )}

      {analysisResult && !loading && (
        <Box>
          {detailedView ? <DetailedAnalysis /> : <QuickInsights />}
        </Box>
      )}

      {!analysisResult && !loading && (
        <Paper sx={{ p: 4, textAlign: 'center' }}>
          <AssessmentIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" gutterBottom>
            No Analysis Available
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Enter a company name above to start the AI analysis process
          </Typography>
        </Paper>
      )}
    </Box>
  );
};

export default AIAnalysisDashboard;






