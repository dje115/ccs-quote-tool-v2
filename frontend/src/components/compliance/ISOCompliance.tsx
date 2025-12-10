import React, { useState } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Alert,
  Button,
  Grid,
} from '@mui/material';
import {
  CheckCircle,
  Schedule,
  Warning,
} from '@mui/icons-material';

interface ISOComplianceProps {
  standard: 'iso_27001' | 'iso_9001';
}

const ISOCompliance: React.FC<ISOComplianceProps> = ({ standard }) => {
  const standardName = standard === 'iso_27001' 
    ? 'ISO 27001 - Information Security Management'
    : 'ISO 9001 - Quality Management';

  return (
    <Box>
      <Alert severity="info" sx={{ mb: 3 }}>
        <Typography variant="h6" gutterBottom>
          {standardName}
        </Typography>
        <Typography variant="body2">
          ISO compliance management module is under development. This will include:
        </Typography>
        <ul>
          <li>Control/requirement tracking</li>
          <li>Compliance assessments</li>
          <li>Audit management</li>
          <li>Gap analysis and remediation planning</li>
          <li>Certificate tracking</li>
        </ul>
      </Alert>

      <Grid container spacing={3}>
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Controls/Requirements
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Track all {standard === 'iso_27001' ? 'security controls' : 'quality requirements'}
              </Typography>
              <Button variant="outlined" sx={{ mt: 2 }} disabled>
                Coming Soon
              </Button>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Assessments
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Record compliance assessments and evidence
              </Typography>
              <Button variant="outlined" sx={{ mt: 2 }} disabled>
                Coming Soon
              </Button>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Audits
              </Typography>
              <Typography variant="body2" color="text.secondary">
                Manage internal and external audits
              </Typography>
              <Button variant="outlined" sx={{ mt: 2 }} disabled>
                Coming Soon
              </Button>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default ISOCompliance;

