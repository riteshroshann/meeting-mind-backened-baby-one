from enum import Enum
from typing import TypedDict, List, Optional, Any
from dataclasses import dataclass

class Language(Enum):
    HINDI = "hi"
    ENGLISH = "en"
    BENGALI = "bn"
    TELUGU = "te"
    MARATHI = "mr"
    TAMIL = "ta"
    GUJARATI = "gu"
    KANNADA = "kn"
    MALAYALAM = "ml"
    PUNJABI = "pa"
    ODIA = "or"
    ASSAMESE = "as"
    URDU = "ur"
    NEPALI = "ne"
    SANSKRIT = "sa"
    SINDHI = "sd"
    KASHMIRI = "ks"
    MAITHILI = "mai"
    MANIPURI = "mni"
    BODO = "brx"
    KONKANI = "gom"
    SINHALA = "si"

class AudioFormat(Enum):
    WAV = "wav"
    MP3 = "mp3"
    FLAC = "flac"
    M4A = "m4a"
    OGG = "ogg"

class ActionItem(TypedDict):
    item: str
    assignee: str
    priority: str
    dueDate: str

class AnalysisResult(TypedDict):
    summary: str
    actionItems: List[ActionItem]
    keyDecisions: List[str]

class ProcessingResult(TypedDict):
    transcript: str
    translation: str
    analysis: Optional[AnalysisResult]

@dataclass
class APIResponse:
    success: bool
    data: Any
    meta: Dict[str, Any]
