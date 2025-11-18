import React, { useState, useEffect } from 'react';
import {
  Card,
  CardContent,
  Typography,
  Box,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  Avatar,
  Chip,
  CircularProgress,
  Alert,
  IconButton,
  Tooltip,
  Divider,
  Paper,
  Stack
} from '@mui/material';
import {
  Phone as PhoneIcon,
  Email as EmailIcon,
  Meeting as MeetingIcon,
  Note as NoteIcon,
  Assignment as TicketIcon,
  Receipt as QuoteIcon,
  Refresh as RefreshIcon,
  MoreVert as MoreVertIcon
} from '@mui/icons-material';
import { customerHealthAPI } from '../services/api';
import { format, formatDistanceToNow } from 'date-fns';

interface CustomerTimelineProps {
  customerId: string;
  limit?: number;
  activityTypes?: string[];
}

interface TimelineItem {
  type: string;
  subtype?: string;
  id: string;
  title: string;
  description?: string;
  timestamp: string;
  created_by?: string;
  customer_id?: string;
  lead_id?: string;
  status?: string;
  priority?: string;
}

const CustomerTimeline: React.FC<CustomerTimelineProps> = ({
  customerId,
  limit = 50,
  activityTypes
}) => {
  const [timeline, setTimeline] = useState<TimelineItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    loadTimeline();
  }, [customerId, limit, activityTypes]);

  const loadTimeline = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await customerHealthAPI.getTimeline(customerId, limit, activityTypes);
      setTimeline(response.data.timeline || []);
    } catch (err: any) {
      console.error('Error loading timeline:', err);
      setError(err.response?.data?.detail || 'Failed to load timeline');
    } finally {
      setLoading(false);
    }
  };

  const getActivityIcon = (type: string, subtype?: string) => {
    switch (type) {
      case 'sales_activity':
        switch (subtype) {
          case 'call':
            return <PhoneIcon />;
          case 'email':
            return <EmailIcon />;
          case 'meeting':
            return <MeetingIcon />;
          default:
            return <NoteIcon />;
        }
      case 'helpdesk_ticket':
      case 'helpdesk_comment':
        return <TicketIcon />;
      case 'quote':
        return <QuoteIcon />;
      default:
        return <NoteIcon />;
    }
  };

  const getActivityColor = (type: string) => {
    switch (type) {
      case 'sales_activity':
        return 'primary';
      case 'helpdesk_ticket':
      case 'helpdesk_comment':
        return 'warning';
      case 'quote':
        return 'success';
      default:
        return 'default';
    }
  };

  const formatTimestamp = (timestamp: string) => {
    try {
      const date = new Date(timestamp);
      return {
        relative: formatDistanceToNow(date, { addSuffix: true }),
        absolute: format(date, 'PPp')
      };
    } catch {
      return { relative: 'Unknown', absolute: 'Unknown' };
    }
  };

  if (loading) {
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

  if (error) {
    return (
      <Card>
        <CardContent>
          <Alert severity="error">{error}</Alert>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card sx={{ height: '100%' }}>
      <CardContent>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
          <Typography variant="h6" component="div" fontWeight="bold">
            Activity Timeline
          </Typography>
          <Tooltip title="Refresh">
            <IconButton size="small" onClick={loadTimeline}>
              <RefreshIcon />
            </IconButton>
          </Tooltip>
        </Box>

        {timeline.length === 0 ? (
          <Box sx={{ textAlign: 'center', py: 4 }}>
            <Typography variant="body2" color="text.secondary">
              No activity found
            </Typography>
          </Box>
        ) : (
          <List sx={{ maxHeight: 600, overflow: 'auto' }}>
            {timeline.map((item, idx) => {
              const timeInfo = formatTimestamp(item.timestamp);
              const isLast = idx === timeline.length - 1;
              
              return (
                <React.Fragment key={item.id}>
                  <ListItem
                    sx={{
                      px: 0,
                      py: 1.5,
                      '&:hover': {
                        bgcolor: 'action.hover',
                        borderRadius: 1
                      }
                    }}
                  >
                    <ListItemAvatar>
                      <Avatar
                        sx={{
                          bgcolor: `${getActivityColor(item.type)}.main`,
                          width: 40,
                          height: 40
                        }}
                      >
                        {getActivityIcon(item.type, item.subtype)}
                      </Avatar>
                    </ListItemAvatar>
                    <ListItemText
                      primary={
                        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flexWrap: 'wrap' }}>
                          <Typography variant="subtitle2" component="span" fontWeight="medium">
                            {item.title}
                          </Typography>
                          {item.status && (
                            <Chip
                              label={item.status}
                              size="small"
                              color={item.status === 'won' ? 'success' : item.status === 'lost' ? 'error' : 'default'}
                            />
                          )}
                          {item.priority && (
                            <Chip
                              label={item.priority}
                              size="small"
                              variant="outlined"
                              color={item.priority === 'urgent' ? 'error' : item.priority === 'high' ? 'warning' : 'default'}
                            />
                          )}
                        </Box>
                      }
                      secondary={
                        <Box>
                          {item.description && (
                            <Typography variant="body2" color="text.secondary" sx={{ mt: 0.5 }}>
                              {item.description.length > 150
                                ? `${item.description.substring(0, 150)}...`
                                : item.description}
                            </Typography>
                          )}
                          <Stack direction="row" spacing={1} sx={{ mt: 0.5 }}>
                            <Typography variant="caption" color="text.secondary">
                              {timeInfo.relative}
                            </Typography>
                            {item.created_by && (
                              <>
                                <Typography variant="caption" color="text.secondary">•</Typography>
                                <Typography variant="caption" color="text.secondary">
                                  {item.created_by}
                                </Typography>
                              </>
                            )}
                          </Stack>
                        </Box>
                      }
                    />
                  </ListItem>
                  {!isLast && <Divider variant="inset" component="li" />}
                </React.Fragment>
              );
            })}
          </List>
        )}
      </CardContent>
    </Card>
  );
};

export default CustomerTimeline;

