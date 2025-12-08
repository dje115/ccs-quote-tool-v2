import React, { useState, useEffect } from 'react';
import { Typography, Box, Tooltip } from '@mui/material';
import { versionAPI } from '../services/api';

interface VersionInfo {
  version: string;
  build_date?: string;
  build_hash?: string;
  environment?: string;
}

const VersionDisplay: React.FC<{ variant?: 'footer' | 'inline' }> = ({ variant = 'footer' }) => {
  const [versionInfo, setVersionInfo] = useState<VersionInfo | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchVersion = async () => {
      try {
        const response = await versionAPI.get();
        setVersionInfo(response.data);
      } catch (error) {
        console.error('Failed to fetch version:', error);
        // Fallback version
        setVersionInfo({ version: '3.4.0' });
      } finally {
        setLoading(false);
      }
    };

    fetchVersion();
  }, []);

  if (loading || !versionInfo) {
    return null;
  }

  const versionText = `v${versionInfo.version}`;
  const tooltipText = [
    `Version: ${versionInfo.version}`,
    versionInfo.build_date && `Build Date: ${versionInfo.build_date}`,
    versionInfo.build_hash && `Build: ${versionInfo.build_hash?.substring(0, 7)}`,
    versionInfo.environment && `Environment: ${versionInfo.environment}`,
  ]
    .filter(Boolean)
    .join('\n');

  if (variant === 'inline') {
    return (
      <Tooltip title={tooltipText} arrow>
        <Typography
          variant="body2"
          color="text.secondary"
          sx={{
            fontSize: '0.75rem',
            opacity: 0.7,
            cursor: 'help',
          }}
        >
          {versionText}
        </Typography>
      </Tooltip>
    );
  }

  return (
    <Box
      sx={{
        position: 'fixed',
        bottom: 8,
        right: 16,
        zIndex: 1000,
      }}
    >
      <Tooltip title={tooltipText} arrow>
        <Typography
          variant="caption"
          color="text.secondary"
          sx={{
            fontSize: '0.7rem',
            opacity: 0.6,
            cursor: 'help',
            fontFamily: 'monospace',
          }}
        >
          {versionText}
        </Typography>
      </Tooltip>
    </Box>
  );
};

export default VersionDisplay;

