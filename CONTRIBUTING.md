# Engineering Directives & Contribution Protocol

> "Quality is not an act, it is a habit." — Aristotle

Welcome to the **MeetingMind** engineering collective. This repository is not merely a collection of scripts; it is a **Neural Orchestration Engine** designed for high-availability, low-latency multilingual intelligence.

We enforce a rigorous engineering standard comparable to high-frequency trading firms or top-tier AI research labs (FAIR, DeepMind). This document is the **Canon**; adherence is mandatory.

---

## 🏗️ Table of Contents
1.  [Guiding Principles](#1-guiding-principles)
2.  [Development Environment](#2-development-environment)
3.  [Architectural Invariants](#3-architectural-invariants)
4.  [The Code Style ("The Standard")](#4-the-code-style-the-standard)
5.  [Testing & Verification](#5-testing--verification)
6.  [Submission Protocol (PRs)](#6-submission-protocol-prs)

---

## 1. Guiding Principles

### 1.1. Epistemological Certainty
"Intelligence without verification is hallucination." We do not accept stochastic behavior in the control plane. All new logic must be verifiable via deterministic unit tests.

### 1.2. Hermeticity
Domain logic must remain isolated from infrastructure volatility. We adhere strictly to the **Hexagonal Architecture (Ports and Adapters)**.
*   **Core**: `api.services`. Pure Python. No HTTP dependencies.
*   **Ports**: `api.types`. Strict interfaces.
*   **Adapters**: `api.views`. The dirty layer where HTTP meets Domain.

### 1.3. Zero-Implicit-Any
We enforce static analysis rigor. If the type checker cannot verify it, it does not exist. Generic `Dict` or `Any` types are rejected in strict mode.

---

## 2. Development Environment

We do not believe in "it works on my machine". The environment is deterministic.

### 2.1. Prerequisites
*   Python 3.11+ (CPython)
*   `ffmpeg` (for local signal processing simulation)
*   `git` (with GPG signing enabled preferred)

### 2.2. hydration
```bash
# 1. Clone the repository
git clone https://github.com/riteshroshann/meeting-mind-backened-baby-one.git
cd meeting-mind-backened-baby-one

# 2. Create a virtual environment (Sandbox)
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Install dev-tools
pip install black isort mypy flake8
```

---

## 3. Architectural Invariants

### 3.1. The Service Layer (`api/services.py`)
This is the **Sacred Core**.
*   **Stateless**: Functions must be referentially transparent where possible.
*   **No I/O in constructors**: Classes must differ I/O to execution methods.
*   **Dependency Injection**: Pass dependencies (like API keys) as arguments, do not read `os.environ` deep in the call stack.

### 3.2. The Type System (`api/types.py`)
We use `TypedDict` and `dataclasses` to define the schema of reality.
```python
# ✅ ACCEPTED
class AudioPayload(TypedDict):
    waveform: bytes
    sample_rate: int

# ❌ REJECTED
# Passing raw dicts around without schema.
```

---

## 4. The Code Style ("The Standard")

We follow **PEP 8** extended by **Black** (The Uncompromising Code Formatter).

### 4.1. Formatting
*   **Line Length**: 88 characters.
*   **Quotes**: Double quotes `"` preferred.
*   **Imports**: Sorted by `isort`.

### 4.2. Docstrings
We use the **Google Style** docstring format. Every public function must explain:
1.  **Args**: What comes in.
2.  **Returns**: What goes out.
3.  **Raises**: What can explode.

```python
def normalize_signal(signal: np.ndarray) -> np.ndarray:
    """Standardizes audio amplitude to [-1, 1].

    Args:
        signal: Raw PCM data as a numpy array.

    Returns:
        The normalized signal.

    Raises:
        ValueError: If signal energy is zero.
    """
```

---

## 5. Testing & Verification

We employ a "Defense in Depth" strategy.

### 5.1. Unit Tests
Test individual components in isolation. Mock external APIs (Bhashini, Gemini).
```bash
python manage.py test api.tests.unit
```

### 5.2. Integration Tests
Test the full HTTP flow.
```bash
python manage.py test api.tests.integration
```

### 5.3. Performance Tests
Ensure `O(1)` complexity for hot paths. No quadratic loops in the signal processing pipeline.

---

## 6. Submission Protocol (PRs)

1.  **Atomic Commits**: Commits should be small and semantic.
    *   `feat: ...`
    *   `fix: ...`
    *   `docs: ...`
2.  **Linear History**: Rebase your branch on `main`. Do not merge `main` into your branch.
3.  **The Checklist**:
    - [ ] `black .` run?
    - [ ] `mypy .` passing?
    - [ ] Tests green?
    - [ ] Docstrings added?

---

*By contributing, you agree that your code will be licensed under the MIT License and you transfer ownership of the intellectual property to the project maintainers.*
