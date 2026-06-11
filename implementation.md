# Implementation Plan: Mutual Fund FAQ Assistant (Facts-Only Q&A)

This document details the phase-wise implementation plan for the **Mutual Fund FAQ Assistant**. The plan is divided into structured phases to ensure progressive development, rigorous validation of facts-only constraints, and robust security/privacy compliance.

---

## Phase 1: Environment Setup & Data Ingestion (Corpus Building)

### Goals
Establish the project workspace, build the dataset scraper, and extract structured mutual fund text from official URLs.

### Tasks
- [x] **1.1. Project Initialization**:
  - Initialize directory structure (`backend/`, `frontend/`, `data/`).
  - Configure package dependencies (e.g., Python, FastAPI/Flask, Node/React, LangChain/LlamaIndex, Chromadb, BeautifulSoup4, Playwright/Requests).
- [x] **1.2. Corpus Crawler & Parser**:
  - Develop a scraper to fetch contents from the 5 target ICICI Prudential Growth Fund URLs specified in `problemstatement.md`.
  - Clean HTML markup, extracting core data fields (e.g., Expense Ratio, Exit Load, Minimum SIP, Riskometer, Fund Managers).
  - Handle duplicate links (e.g., duplicate entry for Balanced Advantage Fund).
- [x] **1.3. Structured Metadata Storage**:
  - Save scraped data as structured JSON files with schema matching the required attributes (text, source URL, scrape date).
- [x] **1.4. Daily Pipeline Scheduler**:
  - Implement a pipeline scheduler (`backend/scheduler.py`) to automate daily extraction, enrichment, and vector storage indexing at **10:00 AM IST** (04:30 AM UTC).

---

## Phase 2: Chunking, Embedding & Vector Store Setup

### Goals
Implement semantic, section-aware document processing to reduce noise and set up a vector storage system for accurate retrieval.

### Tasks
- [x] **2.1. Text Chunking Strategy (Section-Aware)**:
  - Implement preprocessing to strip out boilerplate footer navigation (calculators, stock sections, etc.).
  - Limit the list of mutual fund schemes managed by the managers to prevent metadata pollution.
  - Implement a logical section splitter that breaks documents into distinct, context-preserved chunks:
    - *Overview & Objective* (~400-600 characters)
    - *Minimum Investments* (~150 characters)
    - *Exit Load, Expenses & Tax* (~400 characters)
    - *Fund Management* (One chunk per manager, clean education/experience)
    - *Returns & Rankings* (~400 characters)
    - *Top Holdings* (Top 5-10 holdings)
- [x] **2.2. Vector DB Integration**:
  - Setup a local Vector DB instance using a lightweight engine like ChromaDB or FAISS.
  - Generate embeddings using a lightweight local model (`sentence-transformers/all-MiniLM-L6-v2`).
- [x] **2.3. Upsert Pipeline**:
  - Insert chunked documents into the Vector Store along with metadata schema:
    - `fund_title`
    - `source_url`
    - `last_updated`
    - `section_type` (e.g., `overview`, `minimum_investments`, `exit_load_and_expenses`, `management`, `returns`, `holdings`)

---

## Phase 3: Intent Classification & Guardrails (Query Refusal)

### Goals
Develop filters to intercept and handle non-factual, advisory, or out-of-scope user queries.

### Tasks
- [x] **3.1. Advisory Query Classifier**:
  - Create a rules-based or lightweight classifier (using keyword lists or LLM zero-shot classification) to detect investment advice requests (e.g., *"Should I invest?", "Which fund is better?"*).
- [x] **3.2. Refusal Response Handler**:
  - Design static, polite responses reinforcing the facts-only constraints.
  - Inject official guidance links (e.g., [AMFI](https://www.amfiindia.com) or [SEBI](https://www.sebi.gov.in)) into refusal responses.
- [x] **3.3. PII & Privacy Filter**:
  - Write pre-processing filters to detect and block inputs containing PAN numbers, Aadhaar, phone numbers, or account details.

---

## Phase 4: Retrieval and Generation (RAG Pipeline)

### Goals
Build the core retrieval system using local TF-IDF embeddings and integrate the Groq API to generate constrained responses.

### Tasks
- [x] **4.1. Retrieve & Rank**:
  - Implement vector search using local TF-IDF query transformation.
  - Implement a similarity threshold fallback: if closest match distance is above threshold (e.g. `1.15`), return an "out of knowledge base" response with no citation.
- [x] **4.2. Groq LLM Integration**:
  - Integrate the Groq API client with a fast completion model (`llama3-8b-8192` or `llama-3.1-8b-instant`).
  - Configure a strict system prompt targeting:
    - Maximum **3 sentences** response constraint.
    - Mandatory inclusion of exactly **one** matching source citation URL.
    - Addition of the footer format: `Last updated from sources: <date>`.
- [x] **4.3. Response Post-Processor**:
  - Implement validation checks to programmatically count and enforce sentence limits, format footers, and ensure correct source URL citations.


---

## Phase 5: Minimal User Interface Development

### Goals
Provide a clean, premium, and compliant frontend interface for user interaction.

### Tasks
- [x] **5.1. UI Layout & Branding**:
  - Design a sleek, responsive chat layout.
  - Render the permanent disclaimer prominently: `Facts-only. No investment advice.`
- [x] **5.2. Onboarding Experience**:
  - Display a welcoming message and exactly **three** clickable example questions (e.g., *"What is the exit load of the Liquid Fund?"*).
- [x] **5.3. Chat Logic & API Integration**:
  - Implement streaming/regular message exchanges between the user UI and RAG backend.


---

## Phase 6: Testing, Evaluation & Launch

### Goals
Assess retrieval accuracy, safety compliance, and system performance.

### Tasks
- [x] **6.1. Accuracy & Hallucination Testing**:
  - Create a test suite with factual queries to verify that responses match source documents precisely.
- [x] **6.2. Safety & Advisory Adversarial Testing**:
  - Test the chatbot with jailbreak queries and advisory prompts to ensure 100% refusal rates on advice.
- [x] **6.3. Documentation & Handover**:
  - Write the `README.md` containing setup instructions, limitations, and chosen architecture summary.
