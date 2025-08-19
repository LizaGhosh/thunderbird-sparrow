# Thunderbird - Sparrow

## 📋 Project Overview

The Sparrow Dev Test is a production-ready evaluation framework for AI-powered processing of industrial maintenance voice notes. It transcribes inputs, generates structured outputs with large language models (LLMs), and calculates detailed metrics to assess response quality and reliability.


### 1. Evaluation Framework

**Requirement:** Reusable evaluation framework + clear results layer

**Implementation:**

- **Central Engine:** `src/metrics.py` with MetricsCalculator for all workflows
- **Reusable:** Extendable design for new tasks and metrics
- **Consistency:** Shared calculation logic across workflows
- **One-Command Run:** `main.py` executes both workflows; `launch_web.py` starts an interactive dashboard

The **Metrics Calculation Module** evaluates **Voice Note Parser** outputs by comparing system-generated JSON directly against expected JSON, avoiding CSV tables for cleaner and faster processing.

#### Key Metrics
- **Schema Compliance** – % of outputs that follow the defined schema
- **Processing Success** – % of outputs where the system successfully generated a valid JSON object
- **Accuracy** – Direct field-level JSON comparison between system output and expected output

#### Accuracy Formulas
- **Work Triaging**
  ```
  Accuracy = (Category + Asset + Status + Work Type + Assignment (0/100 each)) / 5
  ```

- **Closing Comment**
  ```
  Accuracy = (Downtime + Comment Population (0/100 each)) / 2
  ```

#### Implementation Details
- **Work Triaging Metrics**
  - Checks compliance with schema
  - Validates processing success
  - Computes accuracy breakdown across: `Category`, `Asset`, `Status`, `Work Type`, `Assignment`

- **Closing Comment Metrics**
  - Checks compliance with schema
  - Validates processing success
  - Computes accuracy breakdown across: `Downtime`, `Comment Population`

- **Final Aggregation** Returns both **overall scores** and **component-level breakdowns**, providing insight into which dimensions perform strongly and which need improvement

**Technical Highlights:**
- Abstract base classes for provider consistency
- Modular, extendable architecture
- YAML-driven configuration (`config/config.yaml`)

### 2. Multi-Model Support

**Requirement:** Configurable models (Claude, Gemini) and parameters

**Implementation:**
- **Provider Abstraction:** AIProvider base class with Claude/Gemini implementations
- **Dynamic Config:** Models, temperature, and provider set in `config.yaml`
- **Fallbacks:** Automatic retries + exponential backoff

**Supported Models:**
- Claude: `claude-3-5-sonnet-20241022`, `claude-3-opus-20240229`
- Gemini: `gemini-1.5-pro`

### 3. Error Handling

**Requirement:** Graceful retries and API error management

**Implementation:**
- Centralized Error Classification (retryable vs. fatal)
- Exponential Backoff on transient failures
- Specific Log Messages for auth, rate limits, policy errors, etc.
- Graceful Degradation with model switching

### 4. Work Item Triaging Metrics

**Requirement:** Schema Validity, Category Accuracy, Asset Identification

**Implementation:**
- **Schema Validity:** Pydantic validation, strict field/type checks
- **Category Accuracy:** Four-way classification with context-aware routing
- **Asset Identification:** Asset-to-ID mapping, fuzzy matching, context validation

### 5. Closing Comment Metrics

**Requirement:** Schema Validity, Downtime Accuracy, Completeness

**Implementation:**
- **Schema Validity:** Validates required fields and formats
- **Downtime Accuracy:** Distinguishes equipment downtime vs. duration; null handling
- **Completeness:** Ensures work details, inventory, and verification steps captured

### 6. Results Presentation Layer

**Requirement:** Digestible summary + breakdowns

**Implementation:**
- **Dashboard:** Flask + Bootstrap web app with responsive design
- **Aggregate Metrics:** Success rates, accuracy, reliability
- **Per-Case Detail:** Explanations, progress bars, color-coded outcomes
- **Export Options:** Save results for reporting

### 7. Voice Processing

**Requirement:** Voice inputs supported

**Implementation:**
- **Whisper Integration:** Configurable model sizes, real-time transcription
- **Pipeline:** Audio → STT → AI analysis → Structured outputs → Metrics

### 8. Configuration & Environment

**Requirement:** Config support + `.env.example`

**Implementation:**
- Central `config.yaml` for provider/model settings
- API keys managed securely via `.env`
- Runtime overrides via web UI
- Clear setup docs in `README.md`

### 9. Single Command Execution

**Requirement:** Both workflows from one command

**Implementation:**
- `python main.py`: Full dataset
- `python test/test_first_three.py`: Quick validation
- `python launch_web.py`: Interactive web app
- Supports batch and voice input processing

### 10. Production-Ready Architecture

**Requirement:** Clarity and correctness > feature breadth

**Implementation:**
- Modular, Maintainable Code
- Resilient Error Handling
- Efficient JSON-based Metrics
- Scalable & Extensible Design

## 🔧 Technical Implementation

### Backend
- Provider Factory with fallback
- Metrics Engine: Pydantic + JSON comparison
- Voice Pipeline: PyAudio + Whisper → LLM → Validation
- Config Management: YAML + env vars

### Frontend
- Flask Web App with Bootstrap 5
- Dashboard: Aggregate + per-case views
- Interactive Config: Change runtime parameters in-browser

## 📊 Results & Validation

### Strengths
- Reliable cross-model evaluation
- Graceful failure recovery
- Clear, intuitive results
- Flexible config for varied setups

### Failure Modes Addressed
- Rate limits → retries
- Model downtime → fallbacks
- Schema errors → detailed logs
- Network issues → resilient handling

### Performance
- Fast JSON-based metrics
- Scales to large datasets
- Low memory footprint
- Real-time dashboard updates
