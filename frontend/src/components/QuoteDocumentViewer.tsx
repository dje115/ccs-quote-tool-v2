import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Tabs,
  Tab,
  Button,
  CircularProgress,
  Alert,
  Divider,
  List,
  ListItem,
  ListItemText,
  Chip,
  IconButton,
  Tooltip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Card,
  CardContent,
  Grid
} from '@mui/material';
import {
  Download as DownloadIcon,
  Print as PrintIcon,
  Edit as EditIcon,
  Refresh as RefreshIcon
} from '@mui/icons-material';
import { quoteAPI } from '../services/api';

interface QuoteDocumentViewerProps {
  quoteId: string;
  onEdit?: (documentType: string) => void;
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

const TabPanel: React.FC<TabPanelProps> = ({ children, value, index }) => {
  return (
    <div role="tabpanel" hidden={value !== index}>
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
};

const QuoteDocumentViewer: React.FC<QuoteDocumentViewerProps> = ({
  quoteId,
  onEdit
}) => {
  const [activeTab, setActiveTab] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [documents, setDocuments] = useState<Record<string, any>>({});

  const documentTypes = [
    { value: 'parts_list', label: 'Parts List' },
    { value: 'technical', label: 'Technical Document' },
    { value: 'overview', label: 'Overview' },
    { value: 'build', label: 'Build Document' }
  ];

  useEffect(() => {
    loadDocuments();
  }, [quoteId]);

  const loadDocuments = async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await quoteAPI.getDocuments(quoteId);
      if (response.data?.documents) {
        // Load content for each document
        const docs: Record<string, any> = {};
        for (const doc of response.data.documents) {
          try {
            const docResponse = await quoteAPI.getDocument(quoteId, doc.document_type);
            docs[doc.document_type] = docResponse.data;
          } catch (error) {
            console.error(`Error loading ${doc.document_type}:`, error);
          }
        }
        setDocuments(docs);
      }
    } catch (error: any) {
      console.error('Error loading documents:', error);
      setError(error.response?.data?.detail || 'Failed to load documents');
    } finally {
      setLoading(false);
    }
  };

  const renderDocumentContent = (document: any, documentType: string) => {
    if (!document || !document.content) {
      return <Alert severity="info">No content available</Alert>;
    }

    const content = document.content;

    // Special rendering for overview document with tiers
    if (documentType === 'overview') {
      const sections = content.sections || [];
      const tiersSection = sections.find((s: any) => s.id === 'tiers');
      const tiers = tiersSection?.content || {};
      
      return (
        <Box>
          {sections
            .sort((a: any, b: any) => (a.order || 0) - (b.order || 0))
            .map((section: any, index: number) => {
              // Special rendering for tiers section
              if (section.id === 'tiers' && tiers && Object.keys(tiers).length > 0) {
                const tierKeys = ['tier_1', 'tier_2', 'tier_3'];
                return (
                  <Paper key={section.id || index} sx={{ p: 3, mb: 2 }}>
                    <Typography variant="h6" gutterBottom>
                      {section.title || 'Solution Options'}
                    </Typography>
                    <Divider sx={{ mb: 3 }} />
                    <Grid container spacing={3}>
                      {tierKeys.map((tierKey) => {
                        const tier = tiers[tierKey];
                        if (!tier) return null;
                        
                        const pricing = tier.pricing_breakdown || {};
                        const labourTotal = pricing.labour?.total_cost || 0;
                        const materialsTotal = pricing.materials?.total_cost || 0;
                        const subtotal = labourTotal + materialsTotal;
                        const tax = pricing.estimated_tax || (subtotal * 0.20);
                        const total = pricing.total_including_tax || (subtotal + tax);
                        
                        return (
                          <Grid item xs={12} md={4} key={tierKey}>
                            <Card 
                              variant="outlined" 
                              sx={{ 
                                height: '100%', 
                                display: 'flex', 
                                flexDirection: 'column',
                                border: tierKey === 'tier_2' ? '2px solid' : '1px solid',
                                borderColor: tierKey === 'tier_2' ? 'primary.main' : 'divider'
                              }}
                            >
                              <CardContent sx={{ flexGrow: 1 }}>
                                <Box sx={{ mb: 2 }}>
                                  <Typography variant="h5" component="div" gutterBottom color="primary">
                                    {tier.name || tierKey.replace('tier_', 'Tier ').replace('_', ' ')}
                                  </Typography>
                                  {tierKey === 'tier_2' && (
                                    <Chip label="Recommended" color="primary" size="small" sx={{ mb: 1 }} />
                                  )}
                                </Box>
                                
                                <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                                  {tier.description || ''}
                                </Typography>
                                
                                {tier.key_features && tier.key_features.length > 0 && (
                                  <Box sx={{ mb: 2 }}>
                                    <Typography variant="subtitle2" gutterBottom>
                                      Key Features:
                                    </Typography>
                                    <List dense>
                                      {tier.key_features.map((feature: string, idx: number) => (
                                        <ListItem key={idx} sx={{ py: 0.5, px: 0 }}>
                                          <ListItemText 
                                            primary={feature}
                                            primaryTypographyProps={{ variant: 'body2' }}
                                          />
                                        </ListItem>
                                      ))}
                                    </List>
                                  </Box>
                                )}
                              </CardContent>
                              
                              <Box sx={{ p: 2, bgcolor: 'grey.50', borderTop: '1px solid', borderColor: 'divider' }}>
                                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                                  <Typography variant="body2">Subtotal:</Typography>
                                  <Typography variant="body2" fontWeight="medium">
                                    £{subtotal.toFixed(2)}
                                  </Typography>
                                </Box>
                                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                                  <Typography variant="body2">VAT:</Typography>
                                  <Typography variant="body2" fontWeight="medium">
                                    £{tax.toFixed(2)}
                                  </Typography>
                                </Box>
                                <Divider sx={{ my: 1 }} />
                                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                                  <Typography variant="h6">Total:</Typography>
                                  <Typography variant="h6" fontWeight="bold" color="primary">
                                    £{total.toFixed(2)}
                                  </Typography>
                                </Box>
                              </Box>
                            </Card>
                          </Grid>
                        );
                      })}
                    </Grid>
                  </Paper>
                );
              }
              
              // Regular section rendering
              return (
                <Paper key={section.id || index} sx={{ p: 3, mb: 2 }}>
                  <Typography variant="h6" gutterBottom>
                    {section.title || `Section ${index + 1}`}
                  </Typography>
                  <Divider sx={{ mb: 2 }} />
                  {Array.isArray(section.content) ? (
                    <List>
                      {section.content.map((item: any, idx: number) => {
                        if (typeof item === 'string') {
                          return (
                            <ListItem key={idx}>
                              <ListItemText primary={item} />
                            </ListItem>
                          );
                        } else if (typeof item === 'object' && item !== null) {
                          return (
                            <ListItem key={idx}>
                              <ListItemText 
                                primary={item.description || item.title || JSON.stringify(item)}
                                secondary={item.notes || item.category || undefined}
                              />
                            </ListItem>
                          );
                        }
                        return null;
                      })}
                    </List>
                  ) : typeof section.content === 'string' ? (
                    <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
                      {section.content}
                    </Typography>
                  ) : (
                    <Typography variant="body2" color="text.secondary">
                      {JSON.stringify(section.content, null, 2)}
                    </Typography>
                  )}
                </Paper>
              );
            })}
        </Box>
      );
    }

    // Special rendering for parts list
    if (documentType === 'parts_list') {
      const lineItems = content.line_items || (content.sections?.[0]?.content || []);
      
      if (!Array.isArray(lineItems) || lineItems.length === 0) {
        return <Alert severity="info">No line items in parts list</Alert>;
      }

      const subtotal = content.pricing_summary?.subtotal || 
        lineItems.reduce((sum: number, item: any) => sum + (parseFloat(item.total_price) || 0), 0);
      const taxRate = content.pricing_summary?.tax_rate || 20;
      const taxAmount = content.pricing_summary?.tax_amount || (subtotal * taxRate / 100);
      const totalAmount = content.pricing_summary?.total_amount || (subtotal + taxAmount);

      return (
        <Box>
          <TableContainer component={Paper} variant="outlined">
            <Table size="small" sx={{ minWidth: 1000 }}>
              <TableHead>
                <TableRow>
                  <TableCell sx={{ width: 50 }}>#</TableCell>
                  <TableCell sx={{ minWidth: 300 }}>Description</TableCell>
                  <TableCell sx={{ minWidth: 150 }}>Part Number</TableCell>
                  <TableCell align="right" sx={{ width: 100 }}>Qty</TableCell>
                  <TableCell align="right" sx={{ width: 120 }}>Unit Price</TableCell>
                  <TableCell align="right" sx={{ width: 120 }}>Cost Price</TableCell>
                  <TableCell align="right" sx={{ width: 120 }}>Total</TableCell>
                  <TableCell sx={{ minWidth: 120 }}>Category</TableCell>
                  <TableCell sx={{ minWidth: 150 }}>Supplier</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {lineItems.map((item: any, index: number) => (
                  <TableRow key={item.id || index} hover>
                    <TableCell>{index + 1}</TableCell>
                    <TableCell>{item.description || item.category || '-'}</TableCell>
                    <TableCell>{item.part_number || '-'}</TableCell>
                    <TableCell align="right">{item.quantity || 1}</TableCell>
                    <TableCell align="right">£{parseFloat(item.unit_price || 0).toFixed(2)}</TableCell>
                    <TableCell align="right">£{parseFloat(item.cost_price || 0).toFixed(2)}</TableCell>
                    <TableCell align="right" sx={{ fontWeight: 'medium' }}>
                      £{parseFloat(item.total_price || 0).toFixed(2)}
                    </TableCell>
                    <TableCell>{item.category || '-'}</TableCell>
                    <TableCell>{item.supplier || '-'}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>

          <Box sx={{ mt: 3, display: 'flex', justifyContent: 'flex-end' }}>
            <Paper sx={{ p: 2, minWidth: 300 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="body2">Subtotal:</Typography>
                <Typography variant="body2" fontWeight="medium">£{subtotal.toFixed(2)}</Typography>
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="body2">Tax ({taxRate}%):</Typography>
                <Typography variant="body2" fontWeight="medium">£{taxAmount.toFixed(2)}</Typography>
              </Box>
              <Divider sx={{ my: 1 }} />
              <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                <Typography variant="h6">Total:</Typography>
                <Typography variant="h6" fontWeight="bold" color="primary">
                  £{totalAmount.toFixed(2)}
                </Typography>
              </Box>
            </Paper>
          </Box>
        </Box>
      );
    }

    // Default rendering for other document types
    const sections = content.sections || [];

    if (sections.length === 0) {
      return <Alert severity="info">No sections in this document</Alert>;
    }

    return (
      <Box>
        {sections
          .sort((a: any, b: any) => (a.order || 0) - (b.order || 0))
          .map((section: any, index: number) => (
            <Paper key={section.id || index} sx={{ p: 3, mb: 2 }}>
              <Typography variant="h6" gutterBottom>
                {section.title || `Section ${index + 1}`}
              </Typography>
              <Divider sx={{ mb: 2 }} />
              {Array.isArray(section.content) ? (
                <List>
                  {section.content.map((item: any, idx: number) => {
                    // Handle both string and object items
                    if (typeof item === 'string') {
                      return (
                        <ListItem key={idx}>
                          <ListItemText primary={item} />
                        </ListItem>
                      );
                    } else if (typeof item === 'object' && item !== null) {
                      // Render object items as formatted text
                      return (
                        <ListItem key={idx}>
                          <ListItemText 
                            primary={item.description || item.title || JSON.stringify(item)}
                            secondary={item.notes || item.category || undefined}
                          />
                        </ListItem>
                      );
                    }
                    return null;
                  })}
                </List>
              ) : typeof section.content === 'string' ? (
                <Typography variant="body1" sx={{ whiteSpace: 'pre-wrap' }}>
                  {section.content}
                </Typography>
              ) : (
                <Typography variant="body2" color="text.secondary">
                  {JSON.stringify(section.content, null, 2)}
                </Typography>
              )}
            </Paper>
          ))}
      </Box>
    );
  };

  const handlePrint = () => {
    window.print();
  };

  const handleDownload = async (documentType: string) => {
    // TODO: Implement PDF download
    alert('PDF download coming soon');
  };

  if (loading) {
    return (
      <Box sx={{ display: 'flex', justifyContent: 'center', p: 4 }}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ m: 2 }}>
        {error}
      </Alert>
    );
  }

  return (
    <Box>
      <Paper sx={{ mb: 2 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', p: 2 }}>
          <Typography variant="h5">Quote Documents</Typography>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Tooltip title="Refresh">
              <IconButton onClick={loadDocuments}>
                <RefreshIcon />
              </IconButton>
            </Tooltip>
            <Button startIcon={<PrintIcon />} onClick={handlePrint} variant="outlined">
              Print
            </Button>
          </Box>
        </Box>

        <Tabs value={activeTab} onChange={(_, newValue) => setActiveTab(newValue)}>
          {documentTypes.map((docType, index) => (
            <Tab
              key={docType.value}
              label={
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  {docType.label}
                  {documents[docType.value] && (
                    <Chip label={`v${documents[docType.value].version}`} size="small" />
                  )}
                </Box>
              }
            />
          ))}
        </Tabs>
      </Paper>

      {documentTypes.map((docType, index) => (
        <TabPanel key={docType.value} value={activeTab} index={index}>
          <Paper sx={{ p: 3 }}>
            <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
              <Typography variant="h6">{docType.label}</Typography>
              <Box sx={{ display: 'flex', gap: 1 }}>
                {onEdit && documents[docType.value] && (
                  <Button
                    startIcon={<EditIcon />}
                    onClick={() => onEdit(docType.value)}
                    variant="outlined"
                  >
                    Edit
                  </Button>
                )}
                <Button
                  startIcon={<DownloadIcon />}
                  onClick={() => handleDownload(docType.value)}
                  variant="outlined"
                >
                  Download PDF
                </Button>
              </Box>
            </Box>
            <Divider sx={{ mb: 2 }} />
            {documents[docType.value] ? (
              renderDocumentContent(documents[docType.value], docType.value)
            ) : (
              <Alert severity="info">
                {docType.label} document not found. Generate the quote first.
              </Alert>
            )}
          </Paper>
        </TabPanel>
      ))}
    </Box>
  );
};

export default QuoteDocumentViewer;

