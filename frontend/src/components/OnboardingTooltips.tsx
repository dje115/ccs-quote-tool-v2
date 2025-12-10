import React, { useState, useEffect, useRef } from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import {
  Box,
  Paper,
  Typography,
  Button,
  IconButton,
  Dialog,
  DialogContent,
  DialogActions,
  Link,
  Alert,
  Chip,
  Tooltip
} from '@mui/material';
import {
  Close as CloseIcon,
  ArrowForward as ArrowForwardIcon,
  ArrowBack as ArrowBackIcon,
  Help as HelpIcon,
  Key as KeyIcon,
  Business as BusinessIcon,
  Psychology as PsychologyIcon,
  Settings as SettingsIcon
} from '@mui/icons-material';
import { settingsAPI } from '../services/api';

interface TooltipData {
  id: string;
  target: string; // CSS selector for element to highlight
  title: string;
  content: string;
  action?: {
    text: string;
    href?: string;
    onClick?: () => void;
  };
  position?: 'top' | 'bottom' | 'left' | 'right';
  links?: Array<{
    text: string;
    href: string;
  }>;
}

interface OnboardingTooltipsProps {
  isActive: boolean;
  onComplete: () => void;
  onSkip: () => void;
  onTabChange?: (tabIndex: number) => void;
}

const OnboardingTooltips: React.FC<OnboardingTooltipsProps> = ({
  isActive,
  onComplete,
  onSkip,
  onTabChange
}) => {
  const navigate = useNavigate();
  const location = useLocation();
  const [currentStep, setCurrentStep] = useState(0);
  const [tooltips, setTooltips] = useState<TooltipData[]>([]);
  const [loading, setLoading] = useState(true);
  const [targetElement, setTargetElement] = useState<HTMLElement | null>(null);
  const [showRedirectPopup, setShowRedirectPopup] = useState(false);

  // Check if company has AI analysis data
  const checkAIAnalysisStatus = async (): Promise<boolean> => {
    try {
      const response = await settingsAPI.get('/company-profile');
      const data = response.data;
      
      // Check if we have meaningful AI analysis data
      return !!(data.company_analysis && 
                typeof data.company_analysis === 'object' && 
                Object.keys(data.company_analysis).length > 0);
    } catch (error) {
      console.error('Failed to check AI analysis status:', error);
      return false;
    }
  };

  // Check if user has configured their own API keys
  const checkAPIKeysStatus = async (): Promise<boolean> => {
    try {
      // SECURITY: Use HttpOnly cookies (sent automatically with credentials: 'include')
      const response = await fetch('http://localhost:8000/api/v1/settings/api-status', {
        credentials: 'include',  // Send HttpOnly cookies
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const status = await response.json();
        // Check if any API key is configured (not using system defaults)
        return !!(status.openai?.configured || status.companies_house?.configured || status.google_maps?.configured);
      }
      return false;
    } catch (error) {
      console.error('Failed to check API keys status:', error);
      return false;
    }
  };

  useEffect(() => {
    if (!isActive) return;

    const loadTooltipData = async () => {
      try {
        setLoading(true);
        
        // Check if AI analysis is complete
        const hasAIAnalysis = await checkAIAnalysisStatus();
        
        // Only show tooltips if AI analysis is not complete
        if (!hasAIAnalysis) {
          // Check if we're on the Settings page
          if (location.pathname === '/settings') {
            // Show the detailed tooltips on Settings page
            setTooltips(getTooltipSteps());
          } else {
            // Show redirect popup to guide user to Settings
            setShowRedirectPopup(true);
          }
        } else {
          // User has completed setup, hide tooltips
          onComplete();
        }
      } catch (error) {
        console.error('Failed to load tooltip data:', error);
        // If we can't check status, show redirect popup if not on settings
        if (location.pathname !== '/settings') {
          setShowRedirectPopup(true);
        } else {
          setTooltips(getTooltipSteps());
        }
      } finally {
        setLoading(false);
      }
    };

    loadTooltipData();
  }, [isActive, onComplete, location.pathname]);

  const getTooltipSteps = (): TooltipData[] => {
    return [
      {
        id: 'company-profile-tab',
        target: '[data-tooltip="company-profile-tab"]',
        title: 'Complete Your Company Profile',
        content: 'Next, let\'s fill out your company profile. This information is crucial for the AI to generate personalized business intelligence and recommendations.',
        action: {
          text: 'Go to Company Profile',
          onClick: () => {
            // Navigate to Company Profile tab (index 2)
            if (onTabChange) {
              onTabChange(2);
            }
          }
        },
        position: 'bottom'
      },
      {
        id: 'company-details',
        target: '[data-tooltip="company-details"]',
        title: 'Fill in Your Company Details',
        content: 'Add your company name, address, website, and contact information. The more complete this is, the better the AI analysis will be.',
        position: 'top'
      },
      {
        id: 'company-description',
        target: '[data-tooltip="company-description"]',
        title: 'Describe Your Business',
        content: 'Tell us what your company does, who you serve, and what makes you unique. This helps the AI understand your business better.',
        position: 'top'
      },
      {
        id: 'ai-analysis-tab',
        target: '[data-tooltip="ai-analysis-tab"]',
        title: 'Run AI Business Intelligence',
        content: 'Once your profile is complete, run the AI analysis to get strategic insights, sales approaches, and marketing guidance tailored to your business.',
        action: {
          text: 'Go to AI Analysis',
          onClick: () => {
            // Navigate to AI Business Intelligence tab (index 3)
            if (onTabChange) {
              onTabChange(3);
            }
          }
        },
        position: 'bottom'
      },
      {
        id: 'run-ai-analysis',
        target: '[data-tooltip="run-ai-analysis"]',
        title: 'Generate Your AI Insights',
        content: 'Click this button to let AI analyze your business and generate personalized recommendations. The system will use your company profile to create strategic insights.',
        action: {
          text: 'Complete Setup',
          onClick: () => {
            // Attempt to run AI analysis
            const runButton = document.querySelector('[data-tooltip="run-ai-analysis"]') as HTMLElement;
            if (runButton) {
              runButton.click();
            }
            onComplete();
          }
        },
        position: 'top'
      }
    ];
  };

  useEffect(() => {
    if (!isActive || loading) return;

    // When we need to highlight elements, add pink background to key elements
    const highlightElements = () => {
      // Highlight the tabs that need attention
      const companyTab = document.querySelector('[data-tooltip="company-profile-tab"]');
      const aiTab = document.querySelector('[data-tooltip="ai-analysis-tab"]');
      const companyNameField = document.querySelector('[data-tooltip="company-name-field"]');
      const companyWebsites = document.querySelector('[data-tooltip="company-websites"]');
      const phoneNumbers = document.querySelector('[data-tooltip="phone-numbers"]');
      const companyWebsitesCard = document.querySelector('[data-tooltip="company-websites-card"]');
      const phoneNumbersCard = document.querySelector('[data-tooltip="phone-numbers-card"]');
      
      if (companyTab) {
        const tabElement = companyTab as HTMLElement;
        tabElement.style.backgroundColor = 'rgba(244, 67, 54, 0.1)';
      }
      
      if (aiTab) {
        const tabElement = aiTab as HTMLElement;
        tabElement.style.backgroundColor = 'rgba(244, 67, 54, 0.1)';
      }

      if (companyNameField) {
        const fieldElement = companyNameField as HTMLElement;
        fieldElement.style.backgroundColor = 'rgba(244, 67, 54, 0.05)';
      }

      if (companyWebsites) {
        const websitesElement = companyWebsites as HTMLElement;
        websitesElement.style.backgroundColor = 'rgba(244, 67, 54, 0.1)';
      }

      if (phoneNumbers) {
        const phoneElement = phoneNumbers as HTMLElement;
        phoneElement.style.backgroundColor = 'rgba(244, 67, 54, 0.1)';
      }

      // Also highlight the Card elements directly
      if (companyWebsitesCard) {
        const websitesCardElement = companyWebsitesCard as HTMLElement;
        websitesCardElement.style.backgroundColor = 'rgba(244, 67, 54, 0.15)';
      }

      if (phoneNumbersCard) {
        const phoneCardElement = phoneNumbersCard as HTMLElement;
        phoneCardElement.style.backgroundColor = 'rgba(244, 67, 54, 0.15)';
      }
    };

    const cleanupHighlights = () => {
      const companyTab = document.querySelector('[data-tooltip="company-profile-tab"]');
      const aiTab = document.querySelector('[data-tooltip="ai-analysis-tab"]');
      const companyNameField = document.querySelector('[data-tooltip="company-name-field"]');
      const companyWebsites = document.querySelector('[data-tooltip="company-websites"]');
      const phoneNumbers = document.querySelector('[data-tooltip="phone-numbers"]');
      const companyWebsitesCard = document.querySelector('[data-tooltip="company-websites-card"]');
      const phoneNumbersCard = document.querySelector('[data-tooltip="phone-numbers-card"]');
      
      if (companyTab) {
        const tabElement = companyTab as HTMLElement;
        tabElement.style.backgroundColor = '';
      }
      
      if (aiTab) {
        const tabElement = aiTab as HTMLElement;
        tabElement.style.backgroundColor = '';
      }

      if (companyNameField) {
        const fieldElement = companyNameField as HTMLElement;
        fieldElement.style.backgroundColor = '';
      }

      if (companyWebsites) {
        const websitesElement = companyWebsites as HTMLElement;
        websitesElement.style.backgroundColor = '';
      }

      if (phoneNumbers) {
        const phoneElement = phoneNumbers as HTMLElement;
        phoneElement.style.backgroundColor = '';
      }

      if (companyWebsitesCard) {
        const websitesCardElement = companyWebsitesCard as HTMLElement;
        websitesCardElement.style.backgroundColor = '';
      }

      if (phoneNumbersCard) {
        const phoneCardElement = phoneNumbersCard as HTMLElement;
        phoneCardElement.style.backgroundColor = '';
      }
    };

    if (location.pathname === '/settings' && isActive) {
      // Add a delay to ensure DOM elements are rendered, especially when navigating to Company Profile tab
      const timeoutId = setTimeout(() => {
        highlightElements();
      }, 500);
      
      return () => {
        clearTimeout(timeoutId);
        cleanupHighlights();
      };
    } else {
      cleanupHighlights();
    }
  }, [isActive, loading, location.pathname, onComplete, tooltips.length]);

  useEffect(() => {
    if (!isActive || loading) return;

    if (tooltips.length > 0) {
      const currentTooltip = tooltips[currentStep];
      if (!currentTooltip) {
        onComplete();
        return;
      }

      const element = document.querySelector(currentTooltip.target) as HTMLElement;
      setTargetElement(element);

      if (element) {
        element.scrollIntoView({ behavior: 'smooth', block: 'center' });
        
        // Add highlight effect
        element.style.position = 'relative';
        element.style.zIndex = '1001';
        element.style.backgroundColor = 'rgba(244, 67, 54, 0.1)';
        
        return () => {
          // Cleanup highlight
          element.style.position = '';
          element.style.zIndex = '';
          element.style.backgroundColor = '';
        };
      }
    }
  }, [currentStep, tooltips, isActive, loading, onComplete]);

  // Effect to highlight Settings menu when redirect popup is shown
  useEffect(() => {
    if (showRedirectPopup) {
      const settingsMenu = document.querySelector('[data-tooltip="settings-menu"]') as HTMLElement;
      if (settingsMenu) {
        // Add flashing animation
        settingsMenu.style.animation = 'flash 1s infinite';
        settingsMenu.style.boxShadow = '0 0 0 4px rgba(25, 118, 210, 0.8)';
        settingsMenu.style.borderRadius = '4px';
        settingsMenu.style.backgroundColor = 'rgba(25, 118, 210, 0.1)';

        // Add CSS animation for flashing
        const style = document.createElement('style');
        style.textContent = `
          @keyframes flash {
            0%, 50%, 100% { opacity: 1; }
            25%, 75% { opacity: 0.5; }
          }
        `;
        document.head.appendChild(style);

        return () => {
          // Cleanup
          settingsMenu.style.animation = '';
          settingsMenu.style.boxShadow = '';
          settingsMenu.style.borderRadius = '';
          settingsMenu.style.backgroundColor = '';
          if (style.parentNode) {
            style.parentNode.removeChild(style);
          }
        };
      }
    }
  }, [showRedirectPopup]);

  const handleNext = () => {
    if (currentStep < tooltips.length - 1) {
      setCurrentStep(currentStep + 1);
    } else {
      onComplete();
    }
  };

  const handlePrevious = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleSkip = () => {
    onSkip();
  };

  const handleGoToSettings = () => {
    setShowRedirectPopup(false);
    navigate('/settings');
  };

  const handleSkipRedirect = () => {
    setShowRedirectPopup(false);
    localStorage.setItem('onboarding-tooltips-seen', 'true');
  };

  // Show redirect popup if needed
  if (showRedirectPopup && location.pathname !== '/settings') {
    return (
      <Dialog open={showRedirectPopup} onClose={handleSkipRedirect} maxWidth="sm" fullWidth>
        <DialogContent sx={{ p: 3, textAlign: 'center' }}>
          <Box sx={{ display: 'flex', justifyContent: 'center', mb: 2 }}>
            <SettingsIcon sx={{ fontSize: 48, color: 'primary.main' }} />
          </Box>
          <Typography variant="h5" fontWeight="bold" gutterBottom>
            Complete Your Setup
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
            To get the most out of our AI-powered features, you need to complete your company profile and run the AI business intelligence analysis.
          </Typography>
          <Alert severity="info" sx={{ mb: 3, textAlign: 'left' }}>
            <Typography variant="body2">
              This will help us provide personalized recommendations, better lead analysis, and tailored marketing insights for your business.
            </Typography>
          </Alert>
        </DialogContent>
        <DialogActions sx={{ p: 3, justifyContent: 'center', gap: 2 }}>
          <Button onClick={handleSkipRedirect} color="inherit">
            Skip for Now
          </Button>
          <Button
            variant="contained"
            onClick={handleGoToSettings}
            startIcon={<SettingsIcon />}
            size="large"
          >
            Go to Settings
          </Button>
        </DialogActions>
      </Dialog>
    );
  }

  if (!isActive || loading) {
    return null;
  }

  // If we have tooltips but no redirect popup, show the tooltips
  if (tooltips.length === 0) {
    return null;
  }



  // If we're on the settings page and need to show guidance, just show a small non-blocking notification
  if (location.pathname === '/settings' && isActive && !showRedirectPopup) {
    return (
      <Box
        sx={{
          position: 'fixed',
          top: 80,
          right: 16,
          zIndex: 1000,
          maxWidth: 350
        }}
      >
        <Alert 
          severity="info" 
          onClose={handleSkip}
          sx={{ 
            borderRadius: 2,
            boxShadow: 3,
            '& .MuiAlert-action': {
              paddingTop: 0
            }
          }}
        >
          <Typography variant="subtitle2" fontWeight="bold" gutterBottom>
            Complete Your Setup
          </Typography>
          <Typography variant="body2">
            Fill in your website and phone number then click AI auto-fill profile - once complete select the AI business intelligence tab.
          </Typography>
        </Alert>
      </Box>
    );
  }

  // If we have tooltips and target elements, show a minimal tooltip
  if (tooltips.length > 0) {
    const currentTooltip = tooltips[currentStep];
    if (currentTooltip && targetElement) {
      return (
        <Tooltip
          open={true}
          title={
            <Box>
              <Typography variant="subtitle2" fontWeight="bold" gutterBottom>
                {currentTooltip.title}
              </Typography>
              <Typography variant="body2">
                {currentTooltip.content}
              </Typography>
              {currentTooltip.action && (
                <Button
                  variant="contained"
                  size="small"
                  onClick={currentTooltip.action.onClick || handleNext}
                  sx={{ mt: 1 }}
                >
                  {currentTooltip.action.text}
                </Button>
              )}
            </Box>
          }
          placement={currentTooltip.position || 'top'}
          arrow
        >
          <Box />
        </Tooltip>
      );
    }
  }

  return null;
};

export default OnboardingTooltips;
