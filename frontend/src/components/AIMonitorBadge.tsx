import React, { useState, useEffect, useRef } from 'react';
import { Chip, CircularProgress } from '@mui/material';
import { Psychology as AiIcon } from '@mui/icons-material';
import { aiAnalysisAPI } from '../services/api';
import { useNavigate } from 'react-router-dom';
import { useWebSocketContext } from '../contexts/WebSocketContext';

/**
 * Compact AI Analysis Monitor Badge for Header
 * Shows number of active AI analyses
 * Uses WebSocket for real-time updates instead of polling
 */
const AIMonitorBadge: React.FC = () => {
  const [activeCount, setActiveCount] = useState(0);
  const [completedCount, setCompletedCount] = useState(0);
  const [runningAnalyses, setRunningAnalyses] = useState<any[]>([]);
  const navigate = useNavigate();
  const { subscribe, isConnected } = useWebSocketContext();
  const completedTimestampsRef = useRef<Map<string, number>>(new Map());

  // Initial load of running analyses - only if authenticated
  useEffect(() => {
    // Skip on public pages (login, signup)
    const isPublicPage = window.location.pathname === '/login' || window.location.pathname === '/signup';
    if (isPublicPage) {
      return;
    }
    
    // SECURITY: Gate on proven session state (/auth/me) instead of localStorage
    // HttpOnly cookies cannot be read by JavaScript, so we verify auth via API call
    const loadStatus = async () => {
      try {
        // First verify authentication via /auth/me endpoint
        const { authAPI } = await import('../services/api');
        try {
          await authAPI.getCurrentUser();
        } catch (authError: any) {
          // Not authenticated - skip loading status
          if (authError?.response?.status === 401 || authError?.response?.status === 403) {
            return;
          }
          console.error('[AIMonitorBadge] Auth check failed:', authError);
          return;
        }
      } catch (error) {
        // Skip if auth check fails
        return;
      }

      try {
        // User is authenticated - load status
        // Use dedicated endpoint for better performance
        const response = await aiAnalysisAPI.getStatus();
        const { running, queued, total_active } = response.data;
        
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
        
        setActiveCount(total_active);
        setRunningAnalyses(activeAnalyses);
        
        // Note: Recently completed count would require a separate query or endpoint
        // For now, we'll rely on WebSocket events for completion notifications
        setCompletedCount(0);
      } catch (error: any) {
        // Silently ignore 401/403 errors (user not authenticated)
        if (error?.response?.status !== 401 && error?.response?.status !== 403) {
          console.error('[AIMonitorBadge] Error loading status:', error);
        }
      }
    };

    loadStatus();
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
      };
      
      setRunningAnalyses((prev) => {
        const updated = [...prev, analysis].filter((a, index, self) => 
          index === self.findIndex((t) => t.id === a.id)
        );
        setActiveCount(updated.length);
        return updated;
      });
    });

    // Subscribe to ai_analysis.completed
    const unsubscribeCompleted = subscribe('ai_analysis.completed', (event) => {
      const customerId = event.data.customer_id;
      
      // Remove from running analyses
      setRunningAnalyses((prev) => {
        const updated = prev.filter((a) => a.id !== customerId);
        setActiveCount(updated.length);
        return updated;
      });
      
      // Add to completed count (will expire after 5 minutes)
      completedTimestampsRef.current.set(customerId, Date.now());
      setCompletedCount(completedTimestampsRef.current.size);
      
      // Clean up old completions after 5 minutes
      setTimeout(() => {
        completedTimestampsRef.current.delete(customerId);
        setCompletedCount(completedTimestampsRef.current.size);
      }, 5 * 60 * 1000);
    });

    // Subscribe to ai_analysis.failed
    const unsubscribeFailed = subscribe('ai_analysis.failed', (event) => {
      const customerId = event.data.customer_id;
      
      // Remove from running analyses
      setRunningAnalyses((prev) => {
        const updated = prev.filter((a) => a.id !== customerId);
        setActiveCount(updated.length);
        return updated;
      });
    });

    return () => {
      unsubscribeStarted();
      unsubscribeCompleted();
      unsubscribeFailed();
    };
  }, [isConnected, subscribe]);

  const handleClick = () => {
    if (runningAnalyses.length === 1) {
      // If only one analysis, go directly to it
      navigate(`/customers/${runningAnalyses[0].id}`);
    }
    // If multiple, could show a menu or go to first one
  };

  const isActive = activeCount > 0;
  const showCompleted = completedCount > 0;

  // Determine label based on state
  let label = 'AI Ready';
  if (isActive && showCompleted) {
    label = `${activeCount} Running, ${completedCount} Done`;
  } else if (isActive) {
    label = `${activeCount} AI Running`;
  } else if (showCompleted) {
    label = `${completedCount} Completed`;
  }

  return (
    <Chip
      icon={isActive ? 
        <CircularProgress size={16} sx={{ color: 'white !important' }} /> : 
        <AiIcon sx={{ fontSize: 18, color: 'white' }} />
      }
      label={label}
      onClick={isActive ? handleClick : undefined}
      sx={{
        backgroundColor: isActive 
          ? 'rgba(76, 175, 80, 0.3)' 
          : showCompleted 
          ? 'rgba(33, 150, 243, 0.3)' 
          : 'rgba(255, 255, 255, 0.15)',
        color: 'white',
        cursor: isActive ? 'pointer' : 'default',
        '&:hover': {
          backgroundColor: isActive 
            ? 'rgba(76, 175, 80, 0.4)' 
            : showCompleted 
            ? 'rgba(33, 150, 243, 0.4)' 
            : 'rgba(255, 255, 255, 0.2)',
        },
        ...(isActive && {
          animation: 'pulse 2s infinite',
          '@keyframes pulse': {
            '0%, 100%': { opacity: 1 },
            '50%': { opacity: 0.7 },
          },
        }),
      }}
    />
  );
};

export default AIMonitorBadge;

