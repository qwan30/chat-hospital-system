# ADR-004: Use Qwen2.5 3B/7B quantized via Ollama for MVP

## Metadata
- **ID:** ADR-004
- **Status:** Accepted
- **Decided by:** System Architect / Tech Lead
- **Date:** 2026-04-27
- **Last Updated:** 2026-06-07

## Context
For the AI chatbot to answer natural language questions and generate patient summaries, we need a Large Language Model (LLM). Due to strict hospital compliance guidelines (no PHI transmitted to external cloud systems), the LLM must run locally. Additionally, the system must run on standard developer laptops and low-cost hospital local servers with a target limit of 16GB RAM.

## Decision
We chose Qwen2.5 (3B and 7B parameter models, quantized to 4-bit) hosted locally via Ollama.

## Alternatives Considered
- **Llama 3 (8B quantized):** Highly capable, but has higher memory usage and slightly lower performance in Vietnamese clinical terminology contexts compared to Qwen2.5.
- **Proprietary Cloud LLMs (GPT-4o, Claude 3.5 Sonnet):** Rejected due to patient privacy and HIPAA compliance rules since data must remain local-first.

## Consequences
- **Pros:**
  - Excellent Vietnamese and English capabilities, especially in parsing structured clinical records.
  - Very low memory usage (approx. 4.5GB RAM for 7B Q4 quantized and 2.2GB for 3B Q4 quantized), fitting easily within the 16GB total system memory ceiling.
  - Ollama provides a simple, standard OpenAI-compatible API layer for local deployment.
- **Cons:**
  - Quantized local models have lower reasoning capacity compared to massive cloud models (GPT-4). Answer templates and strict system prompts are required to guide reasoning and prevent hallucinations.
  - Slower token generation rates if running on CPU without a GPU accelerator.
