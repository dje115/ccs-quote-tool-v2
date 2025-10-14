import React, { useState, useEffect } from 'react';
import { Box, Chip, CircularProgress, Snackbar, Alert, Badge } from '@mui/material';
import { Psychology as AiIcon } from '@mui/icons-material';
import { customerAPI } from '../services/api';
import { useNavigate } from 'react-router-dom';

/**
 * Global AI Analysis Monitor
 * Shows a persistent indicator when AI analysis is running on any customer
 * Polls all customers and displays active tasks
 */
const GlobalAIMonitor: React.FC = () => {
  const [runningAnalyses, setRunningAnalyses] = useState<any[]>([]);
  const [showCompletion, setShowCompletion] = useState<string | null>(null);
  const [isPolling, setIsPolling] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    // Only poll if user is authenticated
    const token = localStorage.getItem('access_token');
    if (!token) {
      console.log('[GlobalAIMonitor] No auth token found, skipping poll');
      return;
    }

    console.log('[GlobalAIMonitor] Starting polling...');
    setIsPolling(true);

    // Poll every 5 seconds to check for running analyses
    const pollInterval = setInterval(async () => {
      try {
        console.log('[GlobalAIMonitor] Polling for active analyses...');
        // Get all customers and check their AI analysis status
        const response = await customerAPI.list({ limit: 1000 });
        const customers = response.data.items || [];
        
        const activeAnalyses = customers.filter((customer: any) => 
          customer.ai_analysis_status === 'running' || customer.ai_analysis_status === 'queued'
        );
        
        console.log('[GlobalAIMonitor] Found active analyses:', activeAnalyses.length, activeAnalyses.map((a: any) => a.company_name));
        
        // Check if any previously running analysis has completed
        runningAnalyses.forEach((prevAnalysis: any) => {
          const stillRunning = activeAnalyses.find((a: any) => a.id === prevAnalysis.id);
          if (!stillRunning) {
            // Analysis completed!
            console.log('[GlobalAIMonitor] Analysis completed:', prevAnalysis.company_name);
            setShowCompletion(`AI analysis completed for ${prevAnalysis.company_name}`);
            setTimeout(() => setShowCompletion(null), 5000);
          }
        });
        
        setRunningAnalyses(activeAnalyses);
      } catch (error: any) {
        // Silently ignore auth errors (user logged out)
        if (error?.response?.status !== 401 && error?.response?.status !== 403) {
          console.error('[GlobalAIMonitor] Error polling for AI analyses:', error);
        } else {
          console.log('[GlobalAIMonitor] Auth error, stopping poll');
        }
      }
    }, 5000);

    return () => {
      console.log('[GlobalAIMonitor] Cleanup - stopping poll');
      clearInterval(pollInterval);
    };
  }, [runningAnalyses]);

  // Always show a debug indicator if polling
  return (
    <>
      {/* Debug indicator - always visible when component is loaded */}
      {isPolling && (
        <Box
          sx={{
            position: 'fixed',
            top: 80,
            right: 200,
            zIndex: 9999,
            fontSize: '10px',
            color: 'gray',
            opacity: 0.5,
          }}
        >
          Monitoring ({runningAnalyses.length} active)
        </Box>
      )}

      {/* Persistent indicator for running analyses */}
      {runningAnalyses.length > 0 && (
        <Box
          sx={{
            position: 'fixed',
            top: 20,
            right: 20,
            zIndex: 9999,
            display: 'flex',
            flexDirection: 'column',
            gap: 1,
          }}
        >
          {runningAnalyses.map((analysis: any) => (
            <Chip
              key={analysis.id}
              icon={<CircularProgress size={16} sx={{ color: 'white !important' }} />}
              label={`Analyzing: ${analysis.company_name}`}
              color="primary"
              onClick={() => navigate(`/customers/${analysis.id}`)}
              sx={{
                cursor: 'pointer',
                animation: 'pulse 2s infinite',
                '@keyframes pulse': {
                  '0%, 100%': { opacity: 1 },
                  '50%': { opacity: 0.7 },
                },
              }}
            />
          ))}
        </Box>
      )}

      {/* Completion notification */}
      <Snackbar
        open={!!showCompletion}
        autoHideDuration={5000}
        onClose={() => setShowCompletion(null)}
        anchorOrigin={{ vertical: 'top', horizontal: 'right' }}
      >
        <Alert 
          onClose={() => setShowCompletion(null)} 
          severity="success" 
          sx={{ width: '100%' }}
          icon={<AiIcon />}
        >
          {showCompletion}
        </Alert>
      </Snackbar>
    </>
  );
};

export default GlobalAIMonitor;
