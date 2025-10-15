from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Dict, Optional
from app.core.dependencies import get_current_active_user
from app.models.tenant import User
from app.services.translation_service import TranslationService

router = APIRouter()

# Initialize translation service
translation_service = TranslationService()


class TranslationRequest(BaseModel):
    text: str
    target_language: str
    source_language: Optional[str] = "en"


class TranslationResponse(BaseModel):
    success: bool
    translated_text: Optional[str] = None
    source_language: Optional[str] = None
    target_language: Optional[str] = None
    error: Optional[str] = None


class LanguageDetectionRequest(BaseModel):
    text: str


class LanguageDetectionResponse(BaseModel):
    success: bool
    language: Optional[str] = None
    error: Optional[str] = None


@router.post("/translate", response_model=TranslationResponse)
async def translate_text(
    request: TranslationRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Translate text from source language to target language using AI
    """
    try:
        result = await translation_service.translate(
            text=request.text,
            target_language=request.target_language,
            source_language=request.source_language
        )
        
        if result['success']:
            return TranslationResponse(
                success=True,
                translated_text=result['translated_text'],
                source_language=result['source_language'],
                target_language=result['target_language']
            )
        else:
            return TranslationResponse(
                success=False,
                error=result['error']
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Translation error: {str(e)}")


@router.post("/detect-language", response_model=LanguageDetectionResponse)
async def detect_language(
    request: LanguageDetectionRequest,
    current_user: User = Depends(get_current_active_user)
):
    """
    Detect the language of the provided text using AI
    """
    try:
        result = await translation_service.detect_language(request.text)
        
        if result['success']:
            return LanguageDetectionResponse(
                success=True,
                language=result['language']
            )
        else:
            return LanguageDetectionResponse(
                success=False,
                error=result['error']
            )
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Language detection error: {str(e)}")


@router.get("/supported-languages")
async def get_supported_languages(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get list of supported languages for translation
    """
    languages = [
        {"code": "en", "name": "English", "flag": "🇺🇸"},
        {"code": "es", "name": "Español", "flag": "🇪🇸"},
        {"code": "fr", "name": "Français", "flag": "🇫🇷"},
        {"code": "de", "name": "Deutsch", "flag": "🇩🇪"},
        {"code": "it", "name": "Italiano", "flag": "🇮🇹"},
        {"code": "pt", "name": "Português", "flag": "🇵🇹"},
        {"code": "nl", "name": "Nederlands", "flag": "🇳🇱"},
        {"code": "ru", "name": "Русский", "flag": "🇷🇺"},
        {"code": "ja", "name": "日本語", "flag": "🇯🇵"},
        {"code": "zh", "name": "中文", "flag": "🇨🇳"},
    ]
    
    return {"languages": languages}



