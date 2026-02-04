# Contributing to MeetingMind

> "Code is a liability. Architecture is an asset."

We welcome contributions that adhere to the rigorous engineering standards defined by this project's **Hexagonal Architecture**. This document outlines the protocols for engaging with the codebase.

---

## 1. Architectural Integrity

This repository adheres to a strict **Ports and Adapters** pattern.
*   **Domain Logic**: Must remain pure and isolated in `services.py`.
*   **Adapters**: External I/O (Bhashini, Gemini) must be mediated through strictly typed interfaces in `types.py`.
*   **Volatile Dependencies**: Never import `django.http` or `rest_framework` inside the core service layer.

**Invariant**: The `API Egress` latency must remain `O(1)` relative to the audio length regarding overhead. Do not introduce blocking I/O in the main thread outside of the designated `ThreadPoolExecutor`.

## 2. Type Safety Protocol

We enforce a **Zero-Implicit-Any** policy.
*   All function signatures must be fully annotated.
*   Use `TypedDict` for all JSON payloads.
*   Run `mypy --strict .` before submitting a PR.

```python
# ✅ ACEPTABLE
def process_signal(vector: np.ndarray[np.float32]) -> ProcessingResult: ...

# ❌ REJECTED
def process_signal(vector): ...
```

## 3. The "Atomic Commit" Philosophy

Commits should tell a story. We follow the [Karma](http://karma-runner.github.io/1.0/dev/git-commit-msg.html) convention strictly.

*   `feat`: A new feature (e.g., "feat: add marathi dialect support")
*   `fix`: A bug fix (e.g., "fix: tensor shape mismatch in audio normalization")
*   `perf`: A code change that improves performance
*   `docs`: Documentation only changes
*   `refactor`: A code change that neither fixes a bug nor adds a feature

**Rule**: If your PR includes a `feat` and a `refactor`, split them into two atomic commits.

## 4. Pull Request Lifecycle

1.  **Fork & Branch**: Create a feature branch (`feat/your-feature`).
2.  **Implementation**: Adhere to the `black` formatter.
3.  **Verification**: Ensure all unit tests pass.
4.  **Submission**: Open a PR with a description of the *Architectural Impact*.

---

*By contributing, you agree that your code will be licensed under the MIT License.*
