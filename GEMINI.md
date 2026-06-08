# HYPER-SPECIFICATION CONTEXT: OMNIMATH-LOCAL & BRAND E-COMMERCE

## 🎯 PROJECT MISSION & CORE MOTTO
"Build a lean, high-performance mathematical reasoning engine optimized for local SSD deployment."
- **OmniMath-Local Engine:** A self-hosted Mathematical Reasoning and Verification Engine using a lightweight `deepseek-r1:1.5b` model combined with symbolic execution.

---

## 📦 SSD STORAGE STRATEGY (C: Drive)
The system is optimized for a <10GB footprint on the SSD to ensure stability:
- **Project Data Root:** `./data/`
- **Models:** `deepseek-r1:1.5b` (Ollama) and `bge-small-en-v1.5` (Embedder).
- **Vector DB:** Local ChromaDB instance stored in `./data/vector_db/`.
- **Raw Datasets:** Curated high-quality mathematical text stored in `./data/datasets/`.

---

## 🛠️ THE CORE TECH STACK & ARCHITECTURE COMPONENTS

### 1. Lean Math RAG Pipeline
- **Ingestion & Parsing:** Extract structured mathematical text and LaTeX from curated PDFs.
- **Vector Index:** ChromaDB using `bge-small-en-v1.5` for lightweight semantic search.

### 2. Local SLM Engine & Strict JSON Schemas
- **Inference Layer:** Local `Ollama` loading `deepseek-r1:1.5b`.
- **JSON Enforcement:** Pydantic validation for `reasoning_steps`, `core_formula`, and `final_answer`.
- **Symbolic Tool Verification:** `SymPy` library verification of algebraic accuracy.

### 3. Monitoring, Observability & Latency Budgets
- **Tracing Layer:** Complete integration with local Dockerized instances of `Langfuse` or `OpenTelemetry`. Trace execution timelines from ingestion to embedding retrieval, reranking metrics, and raw token generation speeds.
- **Performance Profiling:** Track explicit P50/P95 latency maps to isolate system calculation anomalies.
- **Graceful Degradation:** Implement internal processing countdown thresholds. If complex multi-step processing risks breaking our latency limit budget, automatically route computing paths to localized fallback scripts.

### 4. Fine-Tuning with QLoRA & DPO
- **Parameter Optimization:** Utilize Hugging Face's `TRL` (Transformer Reinforcement Learning) library for 4-bit PEFT/QLoRA adapter training on your local device.
- **Direct Preference Optimization (DPO):** Construct dual-response mapping criteria targeting behavioral shifts:
  - *Response A (Preferred):* Granular step-by-step mathematical reasoning, complete with explicit explanations and clean LaTeX equations.
  - *Response B (Rejected):* The final answer provided directly without a logical breakdown or proof.

### 5. Clothing Storefront E-Commerce (Track B)
- **Architecture:** React.js user client communicating with a resilient FastAPI backend routing configuration.
- **Database Engine:** `MySQL` or `SQLite` schemas built with absolute relational normalization, explicitly splitting static product parameters from dynamic variables (managing individual size metrics like S/M/L/XL and multi-color hex maps).

---

## 🏗️ SYSTEM CODE GUIDED PRINCIPLES FOR THE CLI
When generating or restructuring files, the Gemini CLI must guarantee:
1. Every storage-touching operation must run a health-gate check against `E:\omnimath_storage\` to prevent execution drops.
2. Code logic must be highly modular and split out completely into isolated routers, validation utilities, database model structures, and inference processing layers.
3. Every math response must natively support clean LaTeX formatting output strings.

---

## 📈 SYSTEM IMPLEMENTATION ROADMAP
- [x] Phase 1: Storage Mapping, Hardware Stress Verification, Environment Realignment.
- [x] Phase 2: FastAPI App Core Setup, Pydantic Integration, Asynchronous Ollama Connection Hooks.
- [ ] Phase 3: Text Parsing Pipeline, Hybrid Search Mechanics, Local ChromaDB Collections.
- [ ] Phase 4: SymPy Execution Sandbox, Langfuse Observability Tracing Layers.
- [ ] Phase 5: TRL Fine-Tuning Pipeline (QLoRA & DPO Calibration Blocks).