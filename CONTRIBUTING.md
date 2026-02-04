# Engineering Directives & Contribution Protocol

> "Code is a liability. Architecture is an asset."

We welcome contributions that improve the **intelligence**, **speed**, or **reliability** of MeetingMind. This document defines the rigorous engineering standards required to participate in the development of the *Minutes of Meeting Management System (M3S)*.

## 1. Core Philosophy

Our engineering culture is predicated on three invariants:

1.  **Minimalism ("Less is More")**: Write code that is clear, concise, and stateless. Complexity should only be introduced when strictly necessary to solve a problem inherent to the domain, not the solution.
2.  **Epistemological Certainty**: "Intelligence without verification is hallucination." We do not accept stochastic behavior in the control plane. All new logic must be verifiable via deterministic unit tests.
3.  **Hermeticity**: Domain logic must remain isolated from infrastructure volatility. We adhere strictly to the **Hexagonal Architecture**.

## 2. Development Lifecycle

We employ a linear, fork-based workflow to ensure main branch stability.

1.  **Fork & Clone**:
    ```bash
    git clone https://github.com/your-username/meeting-mind-backened-baby-one.git
    cd meeting-mind-backened-baby-one
    ```
2.  **Branching Strategy**: Use semantic branch names.
    *   `feat/organic-intelligence`: For new capabilities.
    *   `fix/tensor-alignment`: For bug remediation.
    *   `refactor/adapters`: For code restructuring.
3.  **Implementation**: Write your code.
    *   *Adhere to the Zero-Implicit-Any policy.*
    *   *Ensure O(1) complexity for hot paths.*
4.  **Verification**:
    ```bash
    python manage.py test
    ```
5.  **Submission**: Open a Pull Request (PR).
    *   *Title*: Semantic and descriptive (e.g., `feat: integrate whisper-v3 fallback`).
    *   *Body*: Explanation of the *Architectural Impact* and *Risk Assessment*.

## 3. Engineering Standards

### 3.1. Pythonic Rigor
*   **PEP 8**: Strict adherence is non-negotiable.
*   **Type Safety**: All function signatures must be fully annotated. `mypy` strict mode compatibility is expected.
    ```python
    # ✅ Compliant
    def compute_entropy(signal: np.ndarray) -> float: ...

    # ❌ Non-Compliant
    def compute_entropy(signal): ...
    ```

### 3.2. Architectural Boundaries
*   **Domain Purity**: The `services.py` layer must never import `django.http`, `rest_framework`, or `sys`. It serves as the pure business logic core.
*   **Adapter Isolation**: All external I/O (Database, Bhashini, Vertex AI) must be mediated through strict interfaces defined in `types.py`.

### 3.3. Dependency Hygiene
*   **Minimal Surface Area**: Keep `requirements.txt` sparse. Every new dependency increases the attack surface and container size. Discuss major additions (e.g., `pandas`, `scipy`) in an issue before integrating.

## 4. Testing Procedure

We do not rely on "it works on my machine".

*   **Unit Tests**: distinct logic blocks (e.g., `AudioProc`) must be tested in isolation.
*   **Integration Tests**: End-to-end API flows must be verified using the Django Test Client.

```bash
# Run the full suite
python manage.py test

# Run specific module
python manage.py test api.tests.test_audio_proc
```

---

*By contributing, you certify that you have the right to submit the code and agree that it will be licensed under the MIT License.*
