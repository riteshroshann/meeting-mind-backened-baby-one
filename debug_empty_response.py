#!/usr/bin/env python3
"""
Debug script to check why transcript/translation are empty
"""
import os
import sys
import django
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'meeting_assistant.settings')
django.setup()

import json
import base64
import numpy as np
import soundfile as sf
import tempfile
from api.services import get_bhashini_service, APIError

def create_simple_hindi_audio():
    """Create a simple audio file with some content"""
    print("Creating test audio...")
    
    try:
        # Create a longer audio file (5 seconds)
        duration = 5.0  # seconds
        sample_rate = 16000
        samples = int(duration * sample_rate)
        
        # Create a simple sine wave (not silence)
        t = np.linspace(0, duration, samples, False)
        frequency = 440.0  # A note
        audio_data = 0.3 * np.sin(2 * np.pi * frequency * t).astype(np.float32)
        
        # Save to temporary file
        temp_path = f"test_audio_debug_{int(duration)}s.wav"
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.wav') as temp_file:
            sf.write(temp_file.name, audio_data, sample_rate)
            
            # Read back as bytes
            with open(temp_file.name, 'rb') as f:
                audio_bytes = f.read()
                audio_b64 = base64.b64encode(audio_bytes).decode('utf-8')
            
            os.unlink(temp_file.name)
        
        print(f"Test audio created: {len(audio_b64)} characters")
        print(f"Audio stats: {duration}s, {sample_rate}Hz, {len(audio_data)} samples")
        
        return audio_b64
        
    except Exception as e:
        print(f"Test audio creation failed: {str(e)}")
        return None

def test_bhashini_detailed():
    """Test Bhashini with detailed logging"""
    print("Testing Bhashini Service with Debug Info...")
    print("=" * 60)
    
    try:
        # Create test audio
        audio_b64 = create_simple_hindi_audio()
        if not audio_b64:
            print("❌ Cannot test without audio")
            return False
        
        # Get Bhashini service
        bhashini_service = get_bhashini_service()
        print(f"✅ Bhashini service initialized")
        print(f"🔑 API Token: {bhashini_service.api_token[:30]}...")
        print(f"🌐 Compute URL: {bhashini_service.compute_url}")
        print()
        
        # Test the actual processing
        print("🚀 Starting audio processing...")
        print(f"📤 Input: Hindi audio -> English translation")
        print(f"📏 Audio size: {len(audio_b64)} characters")
        
        result = bhashini_service.process_audio(
            audio_base64=audio_b64,
            source_lang="hi",
            target_lang="en", 
            audio_format="wav"
        )
        
        print("\n" + "=" * 60)
        print("📋 PROCESSING RESULTS:")
        print("=" * 60)
        
        # Detailed result analysis
        print("🔍 Raw result structure:")
        print(f"Result type: {type(result)}")
        print(f"Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
        
        print("\n📝 Content Analysis:")
        
        if 'transcription' in result:
            transcript = result['transcription']
            print(f"Transcription: '{transcript}' (length: {len(transcript)})")
            if len(transcript) == 0:
                print("⚠️  ISSUE: Transcription is empty!")
            else:
                print("✅ Transcription has content")
        
        if 'translation' in result:
            translation = result['translation']
            print(f"Translation: '{translation}' (length: {len(translation)})")
            if len(translation) == 0:
                print("⚠️  ISSUE: Translation is empty!")
            else:
                print("✅ Translation has content")
        
        if 'status' in result:
            print(f"Status: {result['status']}")
        
        # Full result dump
        print("\n🧾 Full Result JSON:")
        print(json.dumps(result, indent=2))
        
        return True
        
    except APIError as e:
        print(f"❌ Bhashini API Error: {e.message}")
        print(f"🔧 Service: {e.service}")
        print(f"📟 Status Code: {e.status_code}")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main debug function"""
    print("🔧 BHASHINI DEBUG ANALYSIS")
    print("=" * 60)
    print("Investigating why transcript/translation are empty...")
    print()
    
    # Test Bhashini service
    success = test_bhashini_detailed()
    
    print("\n" + "=" * 60)
    print("🎯 DEBUG SUMMARY")
    print("=" * 60)
    
    if success:
        print("✅ Bhashini service test completed")
        print("📊 Check the logs above to see why content might be empty")
    else:
        print("❌ Bhashini service test failed")
        print("🔧 Check your API configuration and network connection")
    
    print("\n💡 TROUBLESHOOTING TIPS:")
    print("1. Check if Bhashini API token is valid")
    print("2. Verify audio format and quality")
    print("3. Check if audio contains actual speech (not silence)")
    print("4. Verify network connectivity to Bhashini servers")
    print("5. Check if language codes are supported")
    
    print("=" * 60)

if __name__ == "__main__":
    main()
