"""
URL configuration for the API endpoints.
"""
from django.urls import path
from . import views

urlpatterns = [
    # Main audio processing endpoint
    path('process-audio/', views.process_audio, name='process_audio'),
    
    # Enhanced audio processing with speaker diarization
    path('process-audio-with-speakers/', views.process_audio_with_speakers, name='process_audio_with_speakers'),
    
    # Speaker diarization only
    path('speaker-diarization/', views.speaker_diarization_only, name='speaker_diarization_only'),
    
    # Utility endpoints
    path('health/', views.health_check, name='health_check'),
    path('supported-languages/', views.supported_languages, name='supported_languages'),
    path('supported-audio-formats/', views.supported_audio_formats, name='supported_audio_formats'),
    path('supported-speaker-services/', views.supported_speaker_services, name='supported_speaker_services'),
]
