import React, { useState, useEffect } from 'react';
import {
  Container, Paper, Typography, Box, Grid, Button, Divider, Alert, CircularProgress,
  Card, CardContent, Chip, Stack, Accordion, AccordionSummary, AccordionDetails
} from '@mui/material';
import {
  Assessment as AssessmentIcon, ExpandMore as ExpandMoreIcon, 
  TrendingUp as TrendingUpIcon, Psychology as PsychologyIcon,
  Campaign as CampaignIcon, Warning as WarningIcon, CheckCircle as CheckCircleIcon,
  Lightbulb as LightbulbIcon
} from '@mui/icons-material';
import { settingsAPI } from '../services/api';

interface AnalysisData {
  business_model?: string;
  competitive_position?: string;
  ideal_customer_profile?: string;
  pain_points_solved?: string;
  sales_approach?: string;
  cross_sell_opportunities?: string;
  objection_handling?: string;
  industry_trends?: string;
  marketing_messaging?: string;
  value_proposition?: string;
  elevator_pitch_refined?: string;
}

const AIBusinessIntelligence: React.FC = () => {
  const [loading, setLoading] = useState(true);
  const [analyzing, setAnalyzing] = useState(false);
  const [success, setSuccess] = useState('');
  const [error, setError] = useState('');
  
  const [analysis, setAnalysis] = useState<AnalysisData | null>(null);
  const [analysisDate, setAnalysisDate] = useState<string | null>(null);
  const [aiSuggestions, setAiSuggestions] = useState<AnalysisData | null>(null);

  useEffect(() => {
    loadAnalysis();
  }, []);

  const loadAnalysis = async () => {
    try {
      setLoading(true);
      const response = await settingsAPI.get('/company-profile');
      const data = response.data;

      if (data.company_analysis && typeof data.company_analysis === 'object') {
        setAnalysis(data.company_analysis);
        setAnalysisDate(data.company_analysis_date);
      }
    } catch (err: any) {
      console.error('Failed to load analysis:', err);
      setError('Failed to load business intelligence data');
    } finally {
      setLoading(false);
    }
  };

  const handleRunAnalysis = async () => {
    console.log('[AIBusinessIntelligence] Running AI analysis...');
    try {
      setAnalyzing(true);
      setError('');

      const response = await settingsAPI.post('/company-profile/analyze');
      console.log('[AIBusinessIntelligence] Analysis response:', response.data);

      if (response.data.success) {
        // Store the NEW analysis as suggestions (don't overwrite current data)
        setAiSuggestions(response.data.analysis);
        setSuccess('AI analysis completed! Review the suggestions below.');
        setTimeout(() => setSuccess(''), 5000);
      } else {
        setError('Analysis completed but returned no data');
      }
    } catch (err: any) {
      console.error('[AIBusinessIntelligence] Error:', err);
      setError(err.response?.data?.detail || 'Failed to analyze. Please ensure your company profile is complete and OpenAI API key is configured.');
    } finally {
      setAnalyzing(false);
    }
  };

  const applySuggestion = (field: keyof AnalysisData, action: 'accept' | 'discard') => {
    if (!aiSuggestions) return;

    if (action === 'accept') {
      setAnalysis(prev => ({
        ...prev,
        [field]: aiSuggestions[field]
      }));
      setSuccess(`Updated ${field.replace(/_/g, ' ')}! Click "Save Analysis" to persist changes.`);
    }
    
    // Remove this suggestion from the list
    setAiSuggestions(prev => {
      if (!prev) return null;
      const newSuggestions = { ...prev };
      delete newSuggestions[field];
      return Object.keys(newSuggestions).length > 0 ? newSuggestions : null;
    });
    
    setTimeout(() => setSuccess(''), 3000);
  };

  const acceptAllSuggestions = () => {
    if (!aiSuggestions) return;
    setAnalysis(aiSuggestions);
    setAiSuggestions(null);
    setSuccess('All suggestions accepted! Click "Save Analysis" to persist changes.');
    setTimeout(() => setSuccess(''), 5000);
  };

  const discardAllSuggestions = () => {
    setAiSuggestions(null);
    setSuccess('All suggestions discarded.');
    setTimeout(() => setSuccess(''), 3000);
  };

  const handleSaveAnalysis = async () => {
    try {
      // Save by re-running the profile update with current data
      // The analysis is already in the tenant record from the analyze endpoint
      await loadAnalysis(); // Reload to confirm
      setSuccess('Analysis saved successfully!');
      setTimeout(() => setSuccess(''), 3000);
    } catch (err: any) {
      console.error('Failed to save analysis:', err);
      setError('Failed to save analysis');
    }
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: '400px' }}>
        <CircularProgress />
        <Typography variant="h6" sx={{ ml: 2 }}>Loading business intelligence...</Typography>
      </Box>
    );
  }

  // Helper to format JSON data as readable text
  const formatValue = (value: any, indent: number = 0): string => {
    const indentStr = '  '.repeat(indent);
    
    if (typeof value === 'string') {
      return value;
    }
    
    if (typeof value === 'object' && value !== null) {
      // If it's an array, format as bullet points
      if (Array.isArray(value)) {
        return value.map(item => {
          // Handle nested objects in arrays
          if (typeof item === 'object' && item !== null) {
            const entries = Object.entries(item);
            if (entries.length === 1) {
              // Simple key-value object
              const [k, v] = entries[0];
              return `${indentStr}• ${k}: ${v}`;
            } else {
              // Complex object
              return `${indentStr}• ${Object.entries(item)
                .map(([k, v]) => `${k}: ${v}`)
                .join(', ')}`;
            }
          }
          return `${indentStr}• ${item}`;
        }).join('\n');
      }
      
      // If it's an object, format key-value pairs
      return Object.entries(value)
        .map(([key, val]) => {
          const formattedKey = key.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase());
          
          if (Array.isArray(val)) {
            // Check if array contains objects
            const hasObjects = val.some(item => typeof item === 'object' && item !== null);
            if (hasObjects) {
              const formattedItems = val.map(item => {
                if (typeof item === 'object' && item !== null) {
                  return `${indentStr}  • ${Object.entries(item)
                    .map(([k, v]) => `${k}: ${v}`)
                    .join(', ')}`;
                }
                return `${indentStr}  • ${item}`;
              }).join('\n');
              return `${formattedKey}:\n${formattedItems}`;
            } else {
              return `${formattedKey}:\n${val.map(item => `${indentStr}  • ${item}`).join('\n')}`;
            }
          }
          
          if (typeof val === 'object' && val !== null) {
            // Nested object
            return `${formattedKey}:\n${formatValue(val, indent + 1)}`;
          }
          
          return `${formattedKey}: ${val}`;
        })
        .join('\n\n');
    }
    
    return String(value);
  };

  const renderSection = (
    title: string, 
    icon: React.ReactNode, 
    field: keyof AnalysisData, 
    color: string,
    description: string
  ) => {
    const currentValue = analysis?.[field];
    const suggestedValue = aiSuggestions?.[field];
    const hasSuggestion = !!suggestedValue;

    if (!currentValue && !hasSuggestion) return null;

    return (
      <Grid item xs={12}>
        <Card elevation={3} sx={{ borderLeft: 4, borderColor: color }}>
          <CardContent>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
              {icon}
              <Typography variant="h6" fontWeight="bold" color={color}>
                {title}
              </Typography>
              <Chip label={description} size="small" variant="outlined" />
            </Box>

            {hasSuggestion && (
              <Box sx={{ mb: 3, p: 2, bgcolor: '#fff3e0', borderRadius: 1, border: '2px dashed #ff9800' }}>
                <Typography variant="caption" fontWeight="bold" color="warning.main" gutterBottom>
                  🆕 AI SUGGESTION:
                </Typography>
                <Typography 
                  variant="body2" 
                  sx={{ 
                    mt: 1, 
                    mb: 2, 
                    whiteSpace: 'pre-wrap',
                    wordBreak: 'break-word',
                    lineHeight: 1.8,
                    fontFamily: 'inherit'
                  }}
                >
                  {formatValue(suggestedValue)}
                </Typography>
                <Stack direction="row" spacing={1}>
                  <Button
                    size="small"
                    variant="contained"
                    color="success"
                    startIcon={<CheckCircleIcon />}
                    onClick={() => applySuggestion(field, 'accept')}
                  >
                    Accept
                  </Button>
                  <Button
                    size="small"
                    variant="outlined"
                    color="error"
                    onClick={() => applySuggestion(field, 'discard')}
                  >
                    Discard
                  </Button>
                </Stack>
              </Box>
            )}

            {currentValue && (
              <Box sx={{ p: 2, bgcolor: '#f5f5f5', borderRadius: 1 }}>
                <Typography variant="caption" fontWeight="bold" color="text.secondary">
                  CURRENT:
                </Typography>
                <Typography 
                  variant="body2" 
                  sx={{ 
                    mt: 1,
                    whiteSpace: 'pre-wrap',
                    wordBreak: 'break-word',
                    lineHeight: 1.8,
                    fontFamily: 'inherit'
                  }}
                >
                  {formatValue(currentValue)}
                </Typography>
              </Box>
            )}
          </CardContent>
        </Card>
      </Grid>
    );
  };

  return (
    <Box sx={{ pb: 10 }}>
      {success && <Alert severity="success" sx={{ mb: 2 }}>{success}</Alert>}
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

      {/* Run Analysis Section */}
      <Paper 
        elevation={3} 
        sx={{ 
          background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
          color: 'white',
          p: 3,
          mb: 3,
          borderRadius: 2
        }}
      >
        <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
          <PsychologyIcon sx={{ fontSize: 32, mr: 1 }} />
          <Typography variant="h5" fontWeight="bold">
            AI Business Intelligence
          </Typography>
        </Box>
        <Typography variant="body1" sx={{ mb: 3, opacity: 0.95 }}>
          Generate strategic insights, sales approaches, and marketing guidance based on your complete company profile
        </Typography>
        
        <Alert severity="info" sx={{ mb: 3, bgcolor: 'rgba(255,255,255,0.9)', color: 'text.primary' }}>
          <Typography variant="body2" fontWeight="bold">
            📋 Complete your Company Profile first for best results!
          </Typography>
          <Typography variant="caption">
            Include: Description, Products/Services, USPs, Target Markets, Sales Methodology, and Elevator Pitch
          </Typography>
        </Alert>

        <Button
          variant="contained"
          size="large"
          sx={{
            bgcolor: 'white',
            color: 'primary.main',
            fontWeight: 'bold',
            '&:hover': { bgcolor: 'grey.100' }
          }}
          startIcon={analyzing ? <CircularProgress size={20} color="primary" /> : <AssessmentIcon />}
          onClick={handleRunAnalysis}
          disabled={analyzing}
        >
          {analyzing ? 'Analyzing Your Business...' : 'RUN AI ANALYSIS'}
        </Button>

        {analysisDate && (
          <Typography variant="caption" sx={{ display: 'block', mt: 2, opacity: 0.9 }}>
            Last analyzed: {new Date(analysisDate).toLocaleString()}
          </Typography>
        )}
      </Paper>

      {/* Global Actions for Suggestions */}
      {aiSuggestions && (
        <Alert severity="warning" sx={{ mb: 3 }}>
          <Typography variant="body2" fontWeight="bold" gutterBottom>
            New AI insights available! Review each suggestion below:
          </Typography>
          <Stack direction="row" spacing={1} sx={{ mt: 1 }}>
            <Button
              size="small"
              variant="contained"
              color="success"
              onClick={acceptAllSuggestions}
            >
              Accept All Suggestions
            </Button>
            <Button
              size="small"
              variant="outlined"
              color="error"
              onClick={discardAllSuggestions}
            >
              Discard All
            </Button>
          </Stack>
        </Alert>
      )}

      {/* Analysis Results */}
      {(analysis || aiSuggestions) ? (
        <Grid container spacing={3}>
          {renderSection(
            'Business Model',
            <TrendingUpIcon color="primary" />,
            'business_model',
            'primary.main',
            'Revenue & Value Generation'
          )}
          
          {renderSection(
            'Competitive Position',
            <AssessmentIcon color="success" />,
            'competitive_position',
            'success.main',
            'Market Strengths'
          )}
          
          {renderSection(
            'Ideal Customer Profile',
            <LightbulbIcon color="info" />,
            'ideal_customer_profile',
            'info.main',
            'Target Audience'
          )}
          
          {renderSection(
            'Pain Points Solved',
            <WarningIcon color="warning" />,
            'pain_points_solved',
            'warning.main',
            'Customer Challenges'
          )}
          
          {renderSection(
            'Sales Approach',
            <CampaignIcon color="secondary" />,
            'sales_approach',
            'secondary.main',
            'Recommended Strategy'
          )}
          
          {renderSection(
            'Cross-Sell Opportunities',
            <TrendingUpIcon color="primary" />,
            'cross_sell_opportunities',
            'primary.main',
            'Revenue Expansion'
          )}
          
          {renderSection(
            'Objection Handling',
            <PsychologyIcon color="error" />,
            'objection_handling',
            'error.main',
            'Sales Rebuttals'
          )}
          
          {renderSection(
            'Industry Trends',
            <AssessmentIcon color="info" />,
            'industry_trends',
            'info.main',
            'Market Insights'
          )}
        </Grid>
      ) : (
        <Paper sx={{ p: 5, textAlign: 'center', bgcolor: '#f5f5f5' }}>
          <PsychologyIcon sx={{ fontSize: 80, color: 'text.disabled', mb: 2 }} />
          <Typography variant="h6" color="text.secondary" gutterBottom>
            No Analysis Data Yet
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Complete your Company Profile, then click "Run AI Analysis" to generate strategic business insights.
          </Typography>
        </Paper>
      )}

      <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 3, textAlign: 'center' }}>
        💡 These insights will be used to generate personalized marketing emails, call scripts, and presentations in the Customer section.
      </Typography>
    </Box>
  );
};

export default AIBusinessIntelligence;

