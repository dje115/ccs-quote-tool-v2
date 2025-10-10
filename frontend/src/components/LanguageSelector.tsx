import React, { useState } from 'react';
import {
  FormControl,
  Select,
  MenuItem,
  SelectChangeEvent,
  Box,
  Typography,
  Chip,
  Tooltip,
  IconButton,
  Menu,
  Avatar
} from '@mui/material';
import {
  Language as LanguageIcon,
  Translate as TranslateIcon
} from '@mui/icons-material';
import { useTranslation } from 'react-i18next';

interface Language {
  code: string;
  name: string;
  flag: string;
}

const languages: Language[] = [
  { code: 'en', name: 'English', flag: '🇺🇸' },
  { code: 'es', name: 'Español', flag: '🇪🇸' },
  { code: 'fr', name: 'Français', flag: '🇫🇷' },
  { code: 'de', name: 'Deutsch', flag: '🇩🇪' },
  { code: 'it', name: 'Italiano', flag: '🇮🇹' },
  { code: 'pt', name: 'Português', flag: '🇵🇹' },
  { code: 'nl', name: 'Nederlands', flag: '🇳🇱' },
  { code: 'ru', name: 'Русский', flag: '🇷🇺' },
  { code: 'ja', name: '日本語', flag: '🇯🇵' },
  { code: 'zh', name: '中文', flag: '🇨🇳' },
];

interface LanguageSelectorProps {
  variant?: 'select' | 'chip' | 'icon';
  showLabel?: boolean;
  size?: 'small' | 'medium';
}

const LanguageSelector: React.FC<LanguageSelectorProps> = ({
  variant = 'select',
  showLabel = true,
  size = 'medium'
}) => {
  const { i18n } = useTranslation();
  const [open, setOpen] = useState(false);
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null);

  const currentLanguage = languages.find(lang => lang.code === i18n.language) || languages[0];

  const handleLanguageChange = (event: SelectChangeEvent) => {
    const newLanguage = event.target.value;
    i18n.changeLanguage(newLanguage);
    // Save the user's language preference
    localStorage.setItem('i18nextLng', newLanguage);
  };

  const handleChipClick = () => {
    setOpen(true);
  };

  const handleIconClick = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleClose = () => {
    setAnchorEl(null);
  };

  const changeLanguage = (lng: string) => {
    i18n.changeLanguage(lng);
    localStorage.setItem('i18nextLng', lng);
    handleClose();
  };

  if (variant === 'chip') {
    return (
      <Tooltip title={`${currentLanguage.flag} ${currentLanguage.name}`}>
        <Chip
          icon={<TranslateIcon />}
          label={showLabel ? currentLanguage.name : ''}
          onClick={handleChipClick}
          size={size}
          variant="outlined"
          sx={{ cursor: 'pointer' }}
        />
      </Tooltip>
    );
  }

  if (variant === 'icon') {
    return (
      <>
        <Tooltip title={`${currentLanguage.flag} ${currentLanguage.name}`}>
          <IconButton
            onClick={handleIconClick}
            size={size}
            sx={{ color: 'inherit' }}
            aria-controls={Boolean(anchorEl) ? 'language-menu' : undefined}
            aria-haspopup="true"
            aria-expanded={Boolean(anchorEl) ? 'true' : undefined}
          >
            <LanguageIcon />
          </IconButton>
        </Tooltip>
        <Menu
          id="language-menu"
          anchorEl={anchorEl}
          open={Boolean(anchorEl)}
          onClose={handleClose}
          MenuListProps={{
            'aria-labelledby': 'language-button',
          }}
          anchorOrigin={{
            vertical: 'bottom',
            horizontal: 'right',
          }}
          transformOrigin={{
            vertical: 'top',
            horizontal: 'right',
          }}
        >
          {languages.map((language) => (
            <MenuItem
              key={language.code}
              selected={language.code === i18n.language}
              onClick={() => changeLanguage(language.code)}
            >
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Typography component="span" sx={{ fontSize: '1.2em' }}>
                  {language.flag}
                </Typography>
                <Typography variant="body2">{language.name}</Typography>
              </Box>
            </MenuItem>
          ))}
        </Menu>
      </>
    );
  }

  return (
    <Box sx={{ minWidth: 120 }}>
      <FormControl fullWidth size={size}>
        {showLabel && (
          <Typography variant="caption" color="text.secondary" sx={{ mb: 0.5 }}>
            Language
          </Typography>
        )}
        <Select
          value={i18n.language}
          onChange={handleLanguageChange}
          displayEmpty
          size={size}
          startAdornment={<TranslateIcon sx={{ mr: 1, color: 'text.secondary' }} />}
          sx={{
            '& .MuiSelect-select': {
              display: 'flex',
              alignItems: 'center',
              gap: 1
            }
          }}
        >
          {languages.map((language) => (
            <MenuItem key={language.code} value={language.code}>
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <span style={{ fontSize: '1.2em' }}>{language.flag}</span>
                <Typography variant="body2">{language.name}</Typography>
              </Box>
            </MenuItem>
          ))}
        </Select>
      </FormControl>
    </Box>
  );
};

export default LanguageSelector;
