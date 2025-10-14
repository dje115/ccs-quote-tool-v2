import React, { useState, useEffect } from 'react';
import { Chip, CircularProgress } from '@mui/material';
import { Psychology as AiIcon } from '@mui/icons-material';
import { customerAPI } from '../services/api';
import { useNavigate } from 'react-router-dom';

/**
 * Compact AI Analysis Monitor Badge for Header
 * Shows number of active AI analyses
 */
const AIMonitorBadge: React.FC = () => {
  const [activeCount, setActiveCount] = useState(0);
  const [completedCount, setCompletedCount] = useState(0);
  const [runningAnalyses, setRunningAnalyses] = useState<any[]>([]);
  const navigate = useNavigate();

  useEffect(() => {
    const token = localStorage.getItem('access_token');
    if (!token) return;

    const pollForStatus = async () => {
      try {
        const response = await customerAPI.list({ limit: 1000 });
        const customers = response.data.items || [];
        
        const activeAnalyses = customers.filter((customer: any) => 
          customer.ai_analysis_status === 'running' || customer.ai_analysis_status === 'queued'
        );

        // Count recently completed (within last 5 minutes)
        const fiveMinutesAgo = new Date(Date.now() - 5 * 60 * 1000);
        const recentlyCompleted = customers.filter((customer: any) => 
          customer.ai_analysis_status === 'completed' && 
          customer.ai_analysis_completed_at &&
          new Date(customer.ai_analysis_completed_at) > fiveMinutesAgo
        );
        
        // Log for debugging
        if (activeAnalyses.length > 0 || recentlyCompleted.length > 0) {
          console.log('[AIMonitorBadge] Poll:', {
            active: activeAnalyses.length,
            completed: recentlyCompleted.length,
            activeCustomers: activeAnalyses.map((c: any) => ({ name: c.company_name, status: c.ai_analysis_status })),
            completedCustomers: recentlyCompleted.map((c: any) => ({ name: c.company_name, completed_at: c.ai_analysis_completed_at }))
          });
        }
        
        setActiveCount(activeAnalyses.length);
        setCompletedCount(recentlyCompleted.length);
        setRunningAnalyses(activeAnalyses);
      } catch (error: any) {
        if (error?.response?.status !== 401 && error?.response?.status !== 403) {
          console.error('[AIMonitorBadge] Error polling:', error);
        }
      }
    };

    // Poll immediately on mount
    pollForStatus();

    // Then poll every 5 seconds
    const pollInterval = setInterval(pollForStatus, 5000);

    return () => clearInterval(pollInterval);
  }, []);

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

