# MeetingMind

> "The gap between acoustic signal and semantic understanding is high-dimensional. We collapse it."

---

### Abstract

MeetingMind is not merely a transcription tool; it is a **neural orchestration engine** engineered to bridge the latency between human speech and structured digital intelligence. By fusing precise signal processing with state-of-the-art Automatic Speech Recognition (ASR) and Large Language Model (LLM) reasoning, we engineer a pipeline that transmutes raw audio waveforms into deterministic, queryable insights.

This system is built for the **multilingual reality** of the modern enterprise, leveraging the **Bhashini** compute stack to achieve near-native fidelity across 12+ Indic languages, coupled with **Gemini Pro's** reasoning capabilities for context-aware synthesis.

---

### The Architecture

The system adheres to a strict **Hexagonal Architecture (Ports and Adapters)**, isolating the core domain logic from the volatility of external compute substrates.

```mermaid
graph TD
    subgraph "Compute Substrate"
        Bhashini[Bhashini Neural Cloud]
        Vertex[Google Vertex AI]
    end

    subgraph "Core Domain"
        Ingress[Signal Ingress] -->|16kHz PCM| Norm[Normalization Layer]
        Norm -->|Vector| Adapter[Neural Adapter]
        Adapter <-->|gRPC| Bhashini
        Adapter -->|Text Stream| Reasoner[Inference Engine]
        Reasoner <-->|HTTPS| Vertex
        Reasoner -->|Structured JSON| Egress[API Egress]
    end

    Client -->|Multipart| Ingress
    Egress -->|JSON| Client
```

#### 1. The Signal Plane
Audio is not treated as a file, but as a **high-dimensional signal**. The `AudioProc` layer enforces a rigorous normalization protocol:
- **Resampling**: All inputs are downsampled to `16kHz` to match the receptive field of the Conformer ASR models.
- **Normalization**: Amplitudes are standardized to maximize the signal-to-noise ratio before neural inference.
- **Heuristics**: A dual-fallback mechanism (`librosa` / `soundfile`) ensures `O(1)` reliability even in constrained, non-GPU runtime environments.

#### 2. The Neural Plane
We do not reinvent the wheel; we orchestrate the best-in-class models.
- **Acoustic Model**: Bhashini (Dhruva) provides the foundational ASR/NMT layer, optimized for the phoneme diversity of the Indian subcontinent.
- **Reasoning Model**: Gemini Pro acts as the "Decision Head", taking raw transcripts and applying chain-of-thought prompting to extract action items, intent, and sentiment with **zero-shot** generalization.

---

### The Stack Ensemble

> "We stand on the shoulders of giants, orchestrating a symphony of deterministic state and probabilistic reasoning."

Our dependency graph is minimal yet complete, optimized for the intersection of signal processing and web standards.

| Component | Artifact | Version | Role | Rationale |
| :--- | :--- | :--- | :--- | :--- |
| **Runtime** | `python:3.11-slim-bullseye` | `3.11` | Execution Environment | Leveraging the specialized opcodes for adaptive specialization in CPython 3.11, reducing interpreter overhead by ~10-60%. |
| **Orchestrator** | `Django` | `4.2.7 LTS` | Web Framework | The "batteries-included" monolith providing robust ORM, middleware chains, and security headers out of the box. Essential for strict state management. |
| **WSGI Interface** | `gunicorn` | `21.2.0` | Application Server | Pre-fork worker model handling concurrent request/response cycles. Configured for 'sync' workers to handle high-cpu signal processing tasks without thread contention. |
| **Signal Core** | `librosa` | `0.10.1` | Audio Analysis | The gold standard. Utilizing STFT (Short-Time Fourier Transform) and Mel-frequency cepstral coefficients (MFCCs) for precise spectral analysis and resampling. |
| **Audio I/O** | `soundfile` + `libsndfile` | `0.12.1` | Codec Binding | C-level bindings for reading/writing audio files. Bypasses Python's slow file I/O for raw PCM data handling. |
| **Tensor Ops** | `numpy` | `1.24.3` | Numerical Compute | Providing contiguous memory arrays for O(1) audio buffer manipulation before serialization. |
| **Inference SDK** | `google-generativeai` | `0.3.2` | Model Bridge | The GRPC interface to the Gemini reasoning substrate, handling managing tokens, temperature, and safety settings. |
| **Static Asset** | `whitenoise` | `6.6.0` | CDN Middleware | Radically simplified static file serving directly from the WSGI application, eliminating the need for Nginx in containerized environments. |
| **Environment** | `python-dotenv` | `1.0.0` | Configuration | 12-Factor App compliance. Strict separation of code and config via environment variable injection. |
| **Utilities** | `joblib` | `1.3.2` | Pipelining | Optimized disk-caching and parallel execution helpers, ensuring expensive transforms are memoized where applicable. |

---


### Protocol Definition

The API is strictly typed and deterministic.

**Endpoint**: `POST /api/process-audio/`

**Payload**:
- `audio`: The raw waveform (WAV/MP3/M4A). High-fidelity preferred.
- `sourceLanguage`: ISO-639-1 identifier (e.g., `hi`, `bn`).
- `targetLanguage`: ISO-639-1 identifier (e.g., `en`).
- `preMeetingNotes`: Auxiliary vectors to bias the attention mechanism of the LLM.

**Output**:
```json
{
  "success": true,
  "meta": {
    "latency_ms": 420.5,
    "method": "POST"
  },
  "data": {
    "transcript": "...",
    "translation": "...",
    "summary": "...",
    "actionItems": [ ... ]
  }
}
```

---

### Deployment & Replicability

We prioritize **reproducibility** over configuration.

**1. Clone the Source**
```bash
git clone https://github.com/riteshroshann/meeting-mind-backened-baby-one.git
cd meeting-mind-backened-baby-one
```

**2. Hydrate Dependencies**
```bash
pip install -r requirements.txt
```

**3. Inject Secrets**
Create a `.env` file. You need the **Bhashini ULCA** keys and **Google Vertex** credentials.
```env
BHASHINI_USER_ID=...
ULCA_API_KEY=...
```


**4. Ignite**
```bash
python manage.py runserver
```

---
*Built by [Ritesh Roshan](https://github.com/riteshroshann).*
