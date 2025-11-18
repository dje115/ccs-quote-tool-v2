import React, { useState, useEffect, useRef } from 'react';
import { Box, Chip, CircularProgress, Snackbar, Alert, Badge } from '@mui/material';
import { Psychology as AiIcon } from '@mui/icons-material';
import { aiAnalysisAPI } from '../services/api';
import { useNavigate } from 'react-router-dom';
import { useWebSocketContext } from '../contexts/WebSocketContext';

/**
 * Global AI Analysis Monitor
 * Shows a persistent indicator when AI analysis is running on any customer
 * Uses WebSocket for real-time updates instead of polling
 */
const GlobalAIMonitor: React.FC = () => {
  const [runningAnalyses, setRunningAnalyses] = useState<any[]>([]);
  const [showCompletion, setShowCompletion] = useState<string | null>(null);
  const navigate = useNavigate();
  const { subscribe, isConnected } = useWebSocketContext();
  const runningAnalysesRef = useRef<any[]>([]);

  // Initial load of running analyses - only if authenticated
  useEffect(() => {
    // SECURITY: Gate on proven session state (/auth/me) instead of localStorage
    // HttpOnly cookies cannot be read by JavaScript, so we verify auth via API call
    const loadRunningAnalyses = async () => {
      try {
        // First verify authentication via /auth/me endpoint
        // This ensures we have a valid session before making other API calls
        const { authAPI } = await import('../services/api');
        try {
          await authAPI.getCurrentUser();
        } catch (authError: any) {
          // Not authenticated - skip loading analyses
          if (authError?.response?.status === 401 || authError?.response?.status === 403) {
            return;
          }
          // Other errors - log but continue (might be network issue)
          console.error('[GlobalAIMonitor] Auth check failed:', authError);
          return;
        }

        // User is authenticated - load running analyses
        // Use dedicated endpoint for better performance
        const response = await aiAnalysisAPI.getStatus();
        const { running, queued } = response.data;
        
        // Combine running and queued analyses
        const activeAnalyses = [
          ...running.map((item: any) => ({
            id: item.customer_id,
            company_name: item.company_name,
            ai_analysis_status: item.status,
            ai_analysis_task_id: item.task_id,
          })),
          ...queued.map((item: any) => ({
            id: item.customer_id,
            company_name: item.company_name,
            ai_analysis_status: item.status,
            ai_analysis_task_id: item.task_id,
          }))
        ];
        
        setRunningAnalyses(activeAnalyses);
        runningAnalysesRef.current = activeAnalyses;
      } catch (error: any) {
        // Silently ignore 401/403 errors (user not authenticated)
        if (error?.response?.status !== 401 && error?.response?.status !== 403) {
          console.error('[GlobalAIMonitor] Error loading analyses:', error);
        }
      }
    };

    loadRunningAnalyses();
  }, []);

  // Subscribe to AI analysis events via WebSocket
  useEffect(() => {
    if (!isConnected) return;

    // Subscribe to ai_analysis.started
    const unsubscribeStarted = subscribe('ai_analysis.started', (event) => {
      const analysis = {
        id: event.data.customer_id,
        company_name: event.data.customer_name,
        ai_analysis_status: 'running',
        ai_analysis_task_id: event.data.task_id,
      };
      
      setRunningAnalyses((prev) => {
        const updated = [...prev, analysis].filter((a, index, self) => 
          index === self.findIndex((t) => t.id === a.id)
        );
        runningAnalysesRef.current = updated;
        return updated;
      });
    });

    // Subscribe to ai_analysis.completed
    const unsubscribeCompleted = subscribe('ai_analysis.completed', (event) => {
      const customerId = event.data.customer_id;
      const customerName = event.data.customer_name;
      
      // Remove from running analyses
      setRunningAnalyses((prev) => {
        const updated = prev.filter((a) => a.id !== customerId);
        runningAnalysesRef.current = updated;
        
        // Check if this was previously running
        const wasRunning = runningAnalysesRef.current.find((a) => a.id === customerId);
        if (wasRunning) {
          setShowCompletion(`AI analysis completed for ${customerName}`);
          setTimeout(() => setShowCompletion(null), 5000);
        }
        
        return updated;
      });
    });

    // Subscribe to ai_analysis.failed
    const unsubscribeFailed = subscribe('ai_analysis.failed', (event) => {
      const customerId = event.data.customer_id;
      
      // Remove from running analyses
      setRunningAnalyses((prev) => {
        const updated = prev.filter((a) => a.id !== customerId);
        runningAnalysesRef.current = updated;
        return updated;
      });
    });

    return () => {
      unsubscribeStarted();
      unsubscribeCompleted();
      unsubscribeFailed();
    };
  }, [isConnected, subscribe]);

  return (
    <>
      {/* Debug indicator - shows WebSocket connection status */}
      {isConnected && (
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
          WebSocket Connected ({runningAnalyses.length} active)
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
