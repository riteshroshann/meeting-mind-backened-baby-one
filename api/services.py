"""
Service layer for Bhashini and Gemini integrations with comprehensive error handling.
"""
import os
import json
import logging
import requests
import base64
import soundfile as sf
import io
import re
from typing import Dict, Any, List, Union

from .types import ProcessingResult, AnalysisResult, Language, AudioFormat
from .decorators import APIError

logger = logging.getLogger(__name__)

class BhashiniService:
    
    def __init__(self):
        self.api_token = (
            os.getenv('BHASHINI_AUTH_TOKEN') or 
            "70059e9a4f-0114-416b-a2c6-d97746560e98"
        )
        self.user_id = (
            os.getenv('BHASHINI_USER_ID') or 
            "2060309193"
        )
        self.pipeline_id = (
            os.getenv('BHASHINI_PIPELINE_ID') or 
            "64392f96daac500b55c543cd"
        )
        
        self.fallback_auth_keys = [
            {"value": "bf969566-1077-4409-b68a-6b47b85e0541"}, 
            {"value": "e0e27161-558e-4fd4-8d96-6d63df4ca050"}
        ]
        
    def safe_json(self, response) -> Dict[str, Any]:
        try:
            return response.json()
        except ValueError:
            logger.error(f"Failed to parse JSON response: {response.text[:200]}")
            raise APIError("Invalid JSON response from upstream service", 502, "bhashini")

    def load_and_resample_audio(self, audio_data: Union[bytes, io.BytesIO], target_sr: int = 16000) -> Any:
        try:
            import librosa
            
            if isinstance(audio_data, bytes):
                audio_file = io.BytesIO(audio_data)
            else:
                audio_file = audio_data
                
            try:
                y, sr = librosa.load(audio_file, sr=target_sr)
                return y, sr
            except Exception as e:
                logger.warning(f"Librosa load failed, falling back to soundfile: {e}")
                audio_file.seek(0)
                data, samplerate = sf.read(audio_file)
                return data, samplerate
                
        except Exception as e:
            raise APIError(f"Audio processing failed: {str(e)}", 400, "audio_processing")

    def audio_to_base64(self, y, sr):
        buffer = io.BytesIO()
        sf.write(buffer, y, sr, format='WAV')
        buffer.seek(0)
        return base64.b64encode(buffer.read()).decode('utf-8')

    def detect_language(self, audio_base64: str) -> str:
        return "hi" 

    def process_audio(self, audio_base64: str, source_lang: str, target_lang: str, audio_format: str) -> ProcessingResult:
        logger.info(f"Bhashini Processing: {source_lang} to {target_lang}")
        
        config_url = "https://meity-auth.ulcacontrib.org/ulca/apis/v0/model/getModelsPipeline"
        headers = {
            "userID": self.user_id,
            "ulcaApiKey": self.fallback_auth_keys[0]["value"], 
            "Authorization": self.api_token
        }
        
        payload = {
            "pipelineTasks": [
                {"taskType": "asr", "config": {"language": {"sourceLanguage": source_lang}}},
                {"taskType": "translation", "config": {"language": {"sourceLanguage": source_lang, "targetLanguage": target_lang}}}
            ],
            "pipelineRequestConfig": {"pipelineId": self.pipeline_id}
        }
        
        try:
            resp = requests.post(config_url, json=payload, headers=headers, timeout=10)
            config = self.safe_json(resp)
            
            compute_url = config['pipelineInferenceAPIEndPoint']['callbackUrl']
            auth_key = config['pipelineInferenceAPIEndPoint']['inferenceApiKey']['value']
            
            compute_headers = {
                "Accept": "*/*",
                "User-Agent": "Thunder Client (https://www.thunderclient.com)",
                "Authorization": auth_key
            }
            
            compute_payload = {
                "pipelineTasks": [
                    {"taskType": "asr", "config": {"language": {"sourceLanguage": source_lang}, "audioFormat": "wav", "samplingRate": 16000}},
                    {"taskType": "translation", "config": {"language": {"sourceLanguage": source_lang, "targetLanguage": target_lang}}}
                ],
                "inputData": {
                    "audio": [{"audioContent": audio_base64}]
                }
            }
            
            inference_resp = requests.post(compute_url, json=compute_payload, headers=compute_headers, timeout=30)
            result = self.safe_json(inference_resp)
            
            transcript = ""
            translation = ""
            
            for res in result.get('pipelineResponse', []):
                if res['taskType'] == 'asr' and res.get('output'):
                    transcript = res['output'][0]['source']
                if res['taskType'] == 'translation' and res.get('output'):
                    translation = res['output'][0]['target']
            
            if not translation and transcript and source_lang == target_lang:
                translation = transcript
                
            return {
                "transcript": transcript,
                "translation": translation,
                "analysis": None
            }
            
        except Exception as e:
            logger.error(f"Bhashini chain failed: {e}")
            raise APIError(f"Neural pipeline failure: {e}", 503, "bhashini")

    def get_supported_languages(self) -> List[Dict[str, str]]:
        return [{"code": lang.value, "name": lang.name} for lang in Language]

    def get_supported_audio_formats(self) -> List[str]:
        return [fmt.value for fmt in AudioFormat]

class GeminiService:
    def __init__(self):
        self.api_key = os.getenv('GEMINI_API_KEY') or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            logger.warning("Gemini/OpenAI API key missing")

    def generate_summary_and_actions(self, text: str, context: str = "") -> AnalysisResult:
        import google.generativeai as genai
        
        if not text:
            return {"summary": "No content to analyze.", "actionItems": [], "keyDecisions": []}
            
        try:
            genai.configure(api_key=self.api_key)
            model = genai.GenerativeModel('gemini-pro')
            
            prompt = f"""
            Analyze the following meeting transcript/translation.
            Context: {context}
            Text: {text}
            
            Return strictly valid JSON:
            {{
                "summary": "Concise summary",
                "actionItems": [{{"item": "What", "assignee": "Who", "priority": "High/Medium/Low", "dueDate": "YYYY-MM-DD"}}],
                "keyDecisions": ["Decision 1", "Decision 2"]
            }}
            """
            
            response = model.generate_content(prompt)
            cleaned = response.text.replace('```json', '').replace('```', '')
            return json.loads(cleaned)
            
        except Exception as e:
            logger.error(f"Gemini inference failed: {e}")
            return {
                "summary": "AI Analysis unavailable.",
                "actionItems": [],
                "keyDecisions": []
            }

_bhashini_service = None
_gemini_service = None

def get_bhashini_service():
    global _bhashini_service
    if not _bhashini_service:
        _bhashini_service = BhashiniService()
    return _bhashini_service

def get_gemini_service():
    global _gemini_service
    if not _gemini_service:
        _gemini_service = GeminiService()
    return _gemini_service

def validate_audio_file(file) -> Dict[str, Any]:
    if file.size > 50 * 1024 * 1024:
        raise APIError("File too large (>50MB)", 400, "validation")
    return {"valid": True}
