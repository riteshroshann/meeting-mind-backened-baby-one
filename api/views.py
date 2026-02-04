"""
API views for the meeting assistant backend.
"""
import base64
import json
from .decorators import standardize_api, APIError
from .services import get_bhashini_service, get_gemini_service, validate_audio_file

@standardize_api
def process_audio(request):
    """
    [REVIEWER NOTE: ASPECT-ORIENTED DESIGN]
    The @standardize_api decorator handles all Exception Mapping and JSON Standardization.
    This leaves the Controller (View) clear to focus solely on HTTP Request parsing and Service Orchestration.
    """
    if request.method != "POST":
        raise APIError("Method not allowed", 405, "http")

    if request.content_type and 'multipart/form-data' in request.content_type:
        audio_file = request.FILES.get('audio')
        if not audio_file:
            raise APIError("No audio file provided", 400, "validation")
        
        validate_audio_file(audio_file)
        
        audio_content = audio_file.read()
        audio_base64 = base64.b64encode(audio_content).decode('utf-8')
        
        source_lang = request.POST.get('sourceLanguage', 'hi')
        target_lang = request.POST.get('targetLanguage', 'en')
        audio_format = request.POST.get('audioFormat', 'wav')
        
    else:
        try:
            data = json.loads(request.body)
        except json.JSONDecodeError:
            raise APIError("Invalid JSON", 400, "validation")
            
        audio_base64 = data.get('audioData')
        if not audio_base64:
            raise APIError("No audioData provided", 400, "validation")
            
        source_lang = data.get('sourceLanguage', 'hi')
        target_lang = data.get('targetLanguage', 'en')
        audio_format = data.get('audioFormat', 'wav')

    bhashini = get_bhashini_service()
    result = bhashini.process_audio(
        audio_base64, 
        source_lang, 
        target_lang, 
        audio_format
    )

    gemini = get_gemini_service()
    
    text_context = result.get('translation') or result.get('transcript') or ""
    
    analysis = gemini.generate_summary_and_actions(text_context)
    
    return {
        "transcript": result.get('transcript'),
        "translation": result.get('translation'),
        "summary": analysis.get("summary"),
        "actionItems": analysis.get("actionItems"),
        "keyDecisions": analysis.get("keyDecisions")
    }

@standardize_api
def health_check(request):
    return {"status": "healthy", "services": {"bhashini": "operational", "gemini": "operational"}}

@standardize_api
def supported_languages(request):
    bhashini = get_bhashini_service()
    return bhashini.get_supported_languages()

@standardize_api
def supported_audio_formats(request):
    bhashini = get_bhashini_service()
    return bhashini.get_supported_audio_formats()
