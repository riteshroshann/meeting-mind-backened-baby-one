"""
API views for the meeting assistant backend.
Handles audio processing, transcription, translation, and AI analysis.
"""
import json
import logging
import base64
import time
from datetime import datetime
from typing import Dict, Any

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
from django.core.files.uploadedfile import InMemoryUploadedFile

from .services import (
    get_bhashini_service, 
    get_gemini_service, 
    validate_audio_file, 
    get_audio_format_from_filename,
    get_service_health,
    APIError
)

logger = logging.getLogger(__name__)

def add_cors_headers(response):
    """Add CORS headers to response"""
    response["Access-Control-Allow-Origin"] = "*"
    response["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    response["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return response

def log_request_info(request, endpoint_name):
    """Log request information for debugging"""
    origin = request.META.get('HTTP_ORIGIN', 'Unknown')
    user_agent = request.META.get('HTTP_USER_AGENT', 'Unknown')
    logger.info(f"Processing {endpoint_name} request from: {origin}")
    logger.info(f"User agent: {user_agent}")

def create_error_response(error: APIError, request_start_time: float) -> JsonResponse:
    """Create standardized error response"""
    duration = time.time() - request_start_time
    logger.error(f"API error after {duration:.2f}s: {error.message}")
    
    response = JsonResponse({
        'success': False,
        'error': error.message,
        'service': error.service,
        'duration': f"{duration:.2f}s"
    }, status=error.status_code)
    
    return add_cors_headers(response)

def create_success_response(data: Dict[str, Any], request_start_time: float) -> JsonResponse:
    """Create standardized success response"""
    duration = time.time() - request_start_time
    logger.info(f"Request completed successfully in {duration:.2f}s")
    
    response_data = {
        'success': True,
        'duration': f"{duration:.2f}s",
        **data
    }
    
    response = JsonResponse(response_data)
    return add_cors_headers(response)

@csrf_exempt
@require_http_methods(["POST", "OPTIONS"])
def process_audio(request):
    """Handle audio processing requests"""
    if request.method == "OPTIONS":
        response = JsonResponse({})
        return add_cors_headers(response)
    
    request_start_time = time.time()
    log_request_info(request, "audio processing")
    
    try:
        # Parse request data
        if request.content_type and 'multipart/form-data' in request.content_type:
            # Handle multipart form data
            audio_file = request.FILES.get('audio')
            source_lang = request.POST.get('sourceLanguage', 'hi')
            target_lang = request.POST.get('targetLanguage', 'en')
            pre_meeting_notes = request.POST.get('preMeetingNotes', '')
            
            if not audio_file:
                raise APIError("No audio file provided", 400, "validation")
            
            # Validate audio file
            validation_result = validate_audio_file(audio_file)
            if not validation_result['valid']:
                raise APIError(validation_result['error'], 400, "validation")
            
            # Read and encode audio file
            audio_content = audio_file.read()
            audio_base64 = base64.b64encode(audio_content).decode('utf-8')
            audio_format = get_audio_format_from_filename(audio_file.name)
            
            logger.info(f"Processing: {audio_file.name} ({len(audio_content)} bytes) | {source_lang} -> {target_lang}")
            
        else:
            # Handle JSON data
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                raise APIError("Invalid JSON data", 400, "validation")
            
            audio_base64 = data.get('audioData')
            source_lang = data.get('sourceLanguage', 'hi')
            target_lang = data.get('targetLanguage', 'en')
            pre_meeting_notes = data.get('preMeetingNotes', '')
            audio_format = data.get('audioFormat', 'wav')
            
            if not audio_base64:
                raise APIError("No audio data provided", 400, "validation")
            
            logger.info(f"Processing: JSON audio data ({len(audio_base64)} chars) | {source_lang} -> {target_lang}")
        
        # Normalize language codes
        source_lang = source_lang.split('-')[0].lower()
        target_lang = target_lang.split('-')[0].lower()
        
        # Log pre-meeting notes status
        logger.info(f"Pre-meeting notes provided: {'Yes' if pre_meeting_notes.strip() else 'No'}")
        
        # Process audio through Bhashini
        bhashini_service = get_bhashini_service()
        bhashini_result = bhashini_service.process_audio(
            audio_base64, source_lang, target_lang, audio_format
        )
        
        # Extract transcript and translation from Bhashini result
        transcript = ""
        translation = ""
        
        # Handle both direct Bhashini response and processed response formats
        if 'pipelineResponse' in bhashini_result:
            # Handle raw Bhashini response format
            for response in bhashini_result['pipelineResponse']:
                if response['taskType'] == 'asr' and response.get('output'):
                    transcript = response['output'][0].get('source', '')
                elif response['taskType'] == 'translation' and response.get('output'):
                    translation = response['output'][0].get('target', '')
        elif 'transcription' in bhashini_result:
            # Handle processed response format from services.py
            transcript = bhashini_result.get('transcription', '')
            translation = bhashini_result.get('translation', '')
        
        # Log extraction results for debugging
        logger.info(f"Extracted transcript: '{transcript[:100]}...' (length: {len(transcript)})")
        logger.info(f"Extracted translation: '{translation[:100]}...' (length: {len(translation)})")
        
        # If no translation was performed (same language), use transcript as translation
        if not translation and transcript:
            translation = transcript
            logger.info("Using transcript as translation (same language)")
        
        # If still no content, check for any text in the Bhashini result
        if not transcript and not translation:
            logger.warning("No transcript or translation extracted from Bhashini result")
            logger.warning(f"Raw Bhashini result keys: {list(bhashini_result.keys())}")
            
            # Try to extract from any available source
            if isinstance(bhashini_result, dict):
                for key, value in bhashini_result.items():
                    if isinstance(value, str) and len(value.strip()) > 0:
                        logger.info(f"Found text in key '{key}': {value[:50]}...")
                        if not transcript:
                            transcript = value
                        if not translation:
                            translation = value
        
        # Generate AI summary using Gemini
        gemini_service = get_gemini_service()
        
        # Prepare content for AI analysis
        content_for_analysis = translation or transcript
        
        # If we have no content from audio processing, create a meaningful fallback
        if not content_for_analysis or content_for_analysis.strip() == "":
            logger.warning("No transcript/translation content available for AI analysis")
            
            # Create a basic response with metadata
            if pre_meeting_notes and pre_meeting_notes.strip():
                # Use pre-meeting notes if available
                content_for_analysis = f"Pre-meeting notes: {pre_meeting_notes}"
                logger.info("Using pre-meeting notes for AI analysis")
            else:
                # Create a fallback message
                content_for_analysis = "Audio processing completed but no transcript was generated. This could be due to audio quality, silence, or language detection issues."
                logger.info("Using fallback content for AI analysis")
        
        ai_analysis = gemini_service.generate_summary_and_actions(
            content_for_analysis, pre_meeting_notes
        )
        
        # Prepare response data
        response_data = {
            'data': {
                'transcript': transcript,
                'translation': translation,
                'summary': ai_analysis['summary'],
                'actionItems': ai_analysis['actionItems'],
                'keyDecisions': ai_analysis['keyDecisions']
            },
            'metadata': {
                'sourceLanguage': source_lang,
                'targetLanguage': target_lang,
                'audioFormat': audio_format,
                'processedAt': datetime.now().isoformat(),
                'preMeetingNotesProvided': bool(pre_meeting_notes.strip())
            }
        }
        
        return create_success_response(response_data, request_start_time)
        
    except APIError as e:
        return create_error_response(e, request_start_time)
    except Exception as e:
        logger.error(f"Unexpected error in audio processing: {str(e)}")
        error = APIError(f"Internal server error: {str(e)}", 500, "server")
        return create_error_response(error, request_start_time)

@csrf_exempt
@require_http_methods(["GET", "OPTIONS"])
def health_check(request):
    """Health check endpoint"""
    if request.method == "OPTIONS":
        response = JsonResponse({})
        return add_cors_headers(response)
    
    try:
        health_data = get_service_health()
        status_code = 200 if health_data['status'] == 'healthy' else 503
        response = JsonResponse(health_data, status=status_code)
        return add_cors_headers(response)
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        response = JsonResponse({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.now().isoformat()
        }, status=503)
        return add_cors_headers(response)

@csrf_exempt
@require_http_methods(["GET", "OPTIONS"])
def supported_languages(request):
    """Get supported languages"""
    if request.method == "OPTIONS":
        response = JsonResponse({})
        return add_cors_headers(response)
    
    try:
        bhashini_service = get_bhashini_service()
        languages = bhashini_service.get_supported_languages()
        response = JsonResponse({
            'success': True,
            'languages': languages,
            'count': len(languages)
        })
        return add_cors_headers(response)
    except Exception as e:
        logger.error(f"Error getting supported languages: {str(e)}")
        response = JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
        return add_cors_headers(response)

@csrf_exempt
@require_http_methods(["GET", "OPTIONS"])
def supported_audio_formats(request):
    """Get supported audio formats"""
    if request.method == "OPTIONS":
        response = JsonResponse({})
        return add_cors_headers(response)
    
    try:
        bhashini_service = get_bhashini_service()
        formats = bhashini_service.get_supported_audio_formats()
        response = JsonResponse({
            'success': True,
            'formats': formats,
            'count': len(formats)
        })
        return add_cors_headers(response)
    except Exception as e:
        logger.error(f"Error getting supported audio formats: {str(e)}")
        response = JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
        return add_cors_headers(response)

@csrf_exempt
@require_http_methods(["POST", "OPTIONS"])
def process_audio_with_speakers(request):
    """Handle enhanced audio processing with speaker diarization"""
    if request.method == "OPTIONS":
        response = JsonResponse({})
        return add_cors_headers(response)
    
    request_start_time = time.time()
    log_request_info(request, "enhanced audio processing with speakers")
    
    try:
        # Parse request data (same as process_audio)
        if request.content_type and 'multipart/form-data' in request.content_type:
            # Handle multipart form data
            audio_file = request.FILES.get('audio')
            source_lang = request.POST.get('sourceLanguage', 'hi')
            target_lang = request.POST.get('targetLanguage', 'en')
            pre_meeting_notes = request.POST.get('preMeetingNotes', '')
            include_diarization = request.POST.get('includeDiarization', 'true').lower() == 'true'
            
            if not audio_file:
                raise APIError("No audio file provided", 400, "validation")
            
            # Validate audio file
            validation_result = validate_audio_file(audio_file)
            if not validation_result['valid']:
                raise APIError(validation_result['error'], 400, "validation")
            
            # Read and encode audio file
            audio_content = audio_file.read()
            audio_base64 = base64.b64encode(audio_content).decode('utf-8')
            audio_format = get_audio_format_from_filename(audio_file.name)
            
            logger.info(f"Enhanced Processing: {audio_file.name} ({len(audio_content)} bytes) | {source_lang} -> {target_lang} | Speakers: {include_diarization}")
            
        else:
            # Handle JSON data
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                raise APIError("Invalid JSON data", 400, "validation")
            
            audio_base64 = data.get('audioData')
            source_lang = data.get('sourceLanguage', 'hi')
            target_lang = data.get('targetLanguage', 'en')
            pre_meeting_notes = data.get('preMeetingNotes', '')
            include_diarization = data.get('includeDiarization', True)
            audio_format = data.get('audioFormat', 'wav')
            
            if not audio_base64:
                raise APIError("No audio data provided", 400, "validation")
            
            logger.info(f"Enhanced Processing: JSON audio data ({len(audio_base64)} chars) | {source_lang} -> {target_lang} | Speakers: {include_diarization}")
        
        # Normalize language codes
        source_lang = source_lang.split('-')[0].lower()
        target_lang = target_lang.split('-')[0].lower()
        
        # Process audio with speaker diarization
        bhashini_service = get_bhashini_service()
        enhanced_result = bhashini_service.process_audio_with_speakers(
            audio_base64, source_lang, target_lang, audio_format, include_diarization
        )
        
        # Extract data for AI analysis and speaker information
        transcript = enhanced_result.get('transcription', '')
        translation = enhanced_result.get('translation', '')
        speakers = enhanced_result.get('speakers', [])
        speaker_count = enhanced_result.get('speaker_count', 0)
        
        # Enhanced content for AI analysis (include speaker info if available)
        content_for_analysis = translation or transcript
        if speakers and speaker_count > 1:
            speaker_summary = f"\n\nSpeaker Analysis: {speaker_count} speakers identified:\n"
            for i, speaker in enumerate(speakers, 1):
                speaker_summary += f"- Speaker {i} ({speaker['speaker_id']}): {speaker['total_duration']}s total speaking time\n"
            content_for_analysis += speaker_summary
        
        # Generate AI summary using Gemini
        gemini_service = get_gemini_service()
        ai_analysis = gemini_service.generate_summary_and_actions(
            content_for_analysis, pre_meeting_notes
        )
        
        # Prepare enhanced response data
        response_data = {
            'data': {
                'transcript': transcript,
                'translation': translation,
                'summary': ai_analysis['summary'],
                'actionItems': ai_analysis['actionItems'],
                'keyDecisions': ai_analysis['keyDecisions'],
                'speakers': speakers,
                'speakerCount': speaker_count,
                'speakerLabels': enhanced_result.get('speaker_labels', []),
                'diarizationStatus': enhanced_result.get('diarization_status', 'disabled')
            },
            'metadata': {
                'sourceLanguage': source_lang,
                'targetLanguage': target_lang,
                'audioFormat': audio_format,
                'processedAt': datetime.now().isoformat(),
                'preMeetingNotesProvided': bool(pre_meeting_notes.strip()),
                'speakerDiarizationEnabled': include_diarization,
                'speakersDetected': speaker_count
            }
        }
        
        return create_success_response(response_data, request_start_time)
        
    except APIError as e:
        return create_error_response(e, request_start_time)
    except Exception as e:
        logger.error(f"Unexpected error in enhanced audio processing: {str(e)}")
        error = APIError(f"Internal server error: {str(e)}", 500, "server")
        return create_error_response(error, request_start_time)

@csrf_exempt
@require_http_methods(["POST", "OPTIONS"])
def speaker_diarization_only(request):
    """Handle speaker diarization only (without ASR/translation)"""
    if request.method == "OPTIONS":
        response = JsonResponse({})
        return add_cors_headers(response)
    
    request_start_time = time.time()
    log_request_info(request, "speaker diarization only")
    
    try:
        # Parse request data
        if request.content_type and 'multipart/form-data' in request.content_type:
            audio_file = request.FILES.get('audio')
            service_id = request.POST.get('serviceId', 'ai4bharat/whisper-medium-hi--gpu--t4')
            
            if not audio_file:
                raise APIError("No audio file provided", 400, "validation")
            
            # Validate audio file
            validation_result = validate_audio_file(audio_file)
            if not validation_result['valid']:
                raise APIError(validation_result['error'], 400, "validation")
            
            # Read and encode audio file
            audio_content = audio_file.read()
            audio_base64 = base64.b64encode(audio_content).decode('utf-8')
            
            logger.info(f"Speaker Diarization Only: {audio_file.name} ({len(audio_content)} bytes) | Service: {service_id}")
            
        else:
            # Handle JSON data
            try:
                data = json.loads(request.body)
            except json.JSONDecodeError:
                raise APIError("Invalid JSON data", 400, "validation")
            
            audio_base64 = data.get('audioData')
            service_id = data.get('serviceId', 'ai4bharat/whisper-medium-hi--gpu--t4')
            
            if not audio_base64:
                raise APIError("No audio data provided", 400, "validation")
            
            logger.info(f"Speaker Diarization Only: JSON audio data ({len(audio_base64)} chars) | Service: {service_id}")
        
        # Process speaker diarization
        bhashini_service = get_bhashini_service()
        speaker_result = bhashini_service.speaker_diarization(audio_base64, service_id)
        
        # Prepare response data
        response_data = {
            'data': {
                'speakers': speaker_result.get('speakers', []),
                'speakerCount': speaker_result.get('speaker_count', 0),
                'speakerLabels': speaker_result.get('speaker_labels', []),
                'status': speaker_result.get('status', 'unknown'),
                'rawOutput': speaker_result.get('raw_output', [])
            },
            'metadata': {
                'serviceId': service_id,
                'processedAt': datetime.now().isoformat(),
                'speakersDetected': speaker_result.get('speaker_count', 0),
                'endpoint': 'https://dhruva-api.bhashini.gov.in/services/inference/pipeline'
            }
        }
        
        return create_success_response(response_data, request_start_time)
        
    except APIError as e:
        return create_error_response(e, request_start_time)
    except Exception as e:
        logger.error(f"Unexpected error in speaker diarization: {str(e)}")
        error = APIError(f"Internal server error: {str(e)}", 500, "server")
        return create_error_response(error, request_start_time)

@csrf_exempt
@require_http_methods(["GET", "OPTIONS"])
def supported_speaker_services(request):
    """Get supported speaker diarization services"""
    if request.method == "OPTIONS":
        response = JsonResponse({})
        return add_cors_headers(response)
    
    try:
        bhashini_service = get_bhashini_service()
        services = bhashini_service.get_supported_speaker_diarization_services()
        response = JsonResponse({
            'success': True,
            'services': services,
            'count': len(services),
            'documentation': 'https://dhruva-api.bhashini.gov.in/services/inference/pipeline'
        })
        return add_cors_headers(response)
    except Exception as e:
        logger.error(f"Error getting supported speaker services: {str(e)}")
        response = JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
        return add_cors_headers(response)
