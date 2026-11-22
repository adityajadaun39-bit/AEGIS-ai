# 🎓 AEGIS: Viva Voce & Defense Q&A Preparation Guide

> **Purpose:** Comprehensive preparation guide for college final-year project defense, external examiner viva voce, and technical due diligence interviews.  
> **How to Use:** Each team member should thoroughly review their respective section and understand the cross-cutting architecture questions.

---

## 1. Top 10 High-Probability Examiner Questions (All Members Must Know)

### Q1: "Why can't we just use a better system prompt to prevent prompt injection?"
* **Strong Answer:**  
  *"System prompts and untrusted document data share the exact same context window and token stream in modern transformer models. Attention mechanisms calculate weights across all tokens indiscriminately. An attacker can use delimiter hijacking, instruction overrides, or few-shot examples to convince the model that the initial system prompt is outdated or superseded. Relying on the model to police itself is fundamentally insecure. AEGIS treats the LLM as an untrusted computation engine and enforces security externally at the tool proxy layer."*

### Q2: "Isn't the human in the loop supposed to be the ultimate authority? Why does AEGIS override human approval?"
* **Strong Answer:**  
  *"This is the central innovation of AEGIS. Empirical research and real-world red teaming prove that human operators suffer from alert fatigue and are easily socially engineered. A compromised agent does not ask: 'May I steal your database?' Instead, it writes: 'Please approve routine weekly analytics backup to our European subsidiary.' Human approvers cannot inspect the full multi-turn token lineage in real time. AEGIS enforces a mathematical invariant: if the underlying data lineage is tainted by untrusted instructions, the gateway denies the exfiltration regardless of what the human clicks."*

### Q3: "What is the computational overhead of AEGIS? Will it slow down my agent?"
* **Strong Answer:**  
  *"Our empirical benchmarks show a median gateway latency of only 20.57 milliseconds. We achieve this by ordering our pipeline sequentially from fastest to heaviest: HMAC identity check (<1ms) $\rightarrow$ Regex signature and DLP scan (<0.5ms) $\rightarrow$ In-process policy check (<1ms) $\rightarrow$ ONNX inference (<15ms). Tool execution only occurs if all preceding checks pass. Compared to LLM generation time (which typically takes 1,000 to 3,000 ms), AEGIS introduces less than 1% latency overhead."*

### Q4: "Why did you use SHA-256 for approval binding? How does canonical sorting work?"
* **Strong Answer:**  
  *"In Python and JSON specifications, key ordering in dictionaries is not guaranteed to be stable across serialization runs (`{'a': 1, 'b': 2}` vs `{'b': 2, 'a': 1}`). If we hashed raw JSON strings, identical payloads would produce different hashes. Our `calculate_payload_hash` function strips whitespace, sorts keys alphabetically, and encodes to UTF-8 before computing the SHA-256 digest. This guarantees a deterministic 64-character hex signature. If any field—destination, resource, or content—is altered, the hash immediately diverges."*

### Q5: "What prevents an attacker from forging a `provenance_context_id`?"
* **Strong Answer:**  
  *"Context IDs are cryptographically generated UUIDv4 tokens created exclusively on the server side when `register_document_context` executes after a verified document read. Clients cannot propose their own context ID or assign an `attack_id`. When an outbound action is proposed, `resolve_context_details` looks up the ID in the server's SQLite database. If the ID does not exist, has expired past its 30-minute TTL, or does not match stored records, the gateway fails closed and denies the request."*

### Q6: "Why use SQLite instead of PostgreSQL or MongoDB?"
* **Strong Answer:**  
  *"For our prototype and edge deployment model, SQLite provides a zero-configuration, serverless, single-file database that runs natively without external daemon dependencies. By configuring SQLite with Write-Ahead Logging (`WAL` mode) and a 10-second busy timeout, we successfully validated 50 concurrent worker threads processing 23.6 requests per second with zero database lockouts. For enterprise multi-node clusters, our repository pattern cleanly abstracts storage so migrating to PostgreSQL requires changing only the database connection string."*

### Q7: "How does the two-tier ML injection detector work?"
* **Strong Answer:**  
  *"Tier 1 is a deterministic regex and heuristic scanner covering over 200 attack signatures from BIPIA, OWASP LLM01, and JailbreakBench. It evaluates in under 0.5 milliseconds on CPU. Tier 2 is an optional on-device ONNX runtime transformer model (e.g. quantized DeBERTa-v3). Converting the model to ONNX runtime allows optimized C++ inference on CPU without loading heavy PyTorch or CUDA runtimes. This gives us sub-15ms local inference without transmitting proprietary customer data to external third-party moderation APIs."*

### Q8: "What happens if the policy engine crashes or encounters an exception?"
* **Strong Answer:**  
  *"AEGIS strictly adheres to the 'Fail-Closed' principle of secure software design. In `policy_engine.py` and `gateway.py`, all evaluation functions are wrapped in robust exception handlers. If an OPA subprocess times out, returns invalid JSON, or crashes, the function returns `(False, 'Policy evaluation failed')`. Under no circumstance does an unhandled error result in an open door."*

### Q9: "How does AEGIS correlate multi-stage attacks across different agent turns?"
* **Strong Answer:**  
  *"When an agent reads a document containing prompt injection, `register_document_context` generates a unique `attack_id` UUID and records it in `provenance_contexts`. When the agent later attempts an outbound action using that context, the gateway retrieves the existing `attack_id` and logs the denial under the exact same ID. In our SOC console, security analysts can query `/audit/attacks/{attack_id}` to view the complete forensic trace: Step 1 (document read allowed) $\rightarrow$ Step 2 (outbound email exfiltration denied)."*

### Q10: "Can AEGIS be bypassed if an agent encodes data in Base64 or Caesar cipher?"
* **Strong Answer:**  
  *"No, and this highlights the power of our architecture! Even if the agent obfuscates data in Base64 so that text regexes don't recognize it, the **Information Flow Control lattice does not depend on text scanning**. The lattice tracks **lineage**. Because the context was derived from an untrusted source, the gateway blocks the outbound sink regardless of the payload's encoding or content. The mathematical taint remains attached to the context."*

---

## 2. Individual Member Deep-Dive Questions

### Member 1: Gateway Core & Authentication
* **Question:** *"How do you prevent timing attacks when comparing authentication tokens?"*  
  * **Answer:** *"We use `hmac.compare_digest` in `app.py` and `agent_auth.py`. Standard string comparison (`==`) terminates at the first mismatched character, allowing an attacker to deduce the secret byte-by-byte using microsecond timing measurements. `hmac.compare_digest` operates in constant time regardless of where the mismatch occurs."*
* **Question:** *"How does approval consumption prevent race conditions?"*  
  * **Answer:** *"In `approval_store.update_approval_status`, we use an atomic SQL update query: `UPDATE approval_requests SET status = 'CONSUMED' WHERE approval_id = ? AND status = 'APPROVED'`. SQLite's transactional locking ensures only the first thread updates the rowcount to 1; concurrent duplicate requests update 0 rows and are rejected."*

### Member 2: AI Security & DLP
* **Question:** *"What is the difference between direct prompt injection and indirect prompt injection?"*  
  * **Answer:** *"Direct prompt injection occurs when the human user types an adversarial prompt into the chat box. Indirect prompt injection occurs when a third-party adversary embeds malicious instructions inside external content that the agent reads—such as a PDF, a webpage, or a customer ticket. The human user may be completely innocent, but the agent gets hijacked by the document."*
* **Question:** *"How do you handle false positives in the DLP scanner?"*  
  * **Answer:** *"For structured secrets like AWS keys (`AKIA[0-9A-Z]{16}`) and OpenAI tokens (`sk-...`), regex prefixes guarantee near-zero false positive rates. For numerical secrets like credit cards, we combine pattern matching with Luhn algorithm checksum validation."*

### Member 3: Formal Policy & IFC Lattice
* **Question:** *"Explain the mathematical difference between Join and Meet in your lattice."*  
  * **Answer:** *"In lattice theory, the Join ($\vee$) represents the Least Upper Bound (LUB). For confidentiality, when two documents of sensitivity 'Public' and 'Confidential' merge, the output must be confidential: $\text{Public} \vee \text{Confidential} = \text{Confidential}$. The Meet ($\wedge$) represents the Greatest Lower Bound (GLB). For integrity, trust degrades to the lowest level: $\text{Trusted} \wedge \text{Untrusted} = \text{Untrusted}$."*
* **Question:** *"Why did you implement an in-process policy evaluator alongside OPA?"*  
  * **Answer:** *"While Open Policy Agent (OPA) is an industry standard, spawning an external OPA subprocess for every agent action adds 20–40ms of process overhead and creates an external OS dependency. Our in-process policy engine evaluates rules in Python memory in under 0.2ms, while remaining 100% compliant with our declarative YAML and Rego specifications."*

### Member 4: SOC Dashboard & Visual Telemetry
* **Question:** *"How does Server-Sent Events (SSE) compare to WebSockets for this dashboard?"*  
  * **Answer:** *"WebSockets are bidirectional, which introduces stateful connection overhead and complex reconnection handling through HTTP proxies. Telemetry in a security operations center is inherently unidirectional: the gateway publishes events, and the dashboard consumes them. SSE runs over standard HTTP, supports automatic reconnection natively, and works seamlessly through corporate firewalls."*
* **Question:** *"How did you build the interactive Plotly attack graph?"*  
  * **Answer:** *"In `frontend/dashboard.py`, we construct a directed node graph using `plotly.graph_objects.Scatter`. Nodes represent the ingress document, agent working memory, and outbound action sink, color-coded by trust level. Annotated vectors visually depict how taint flows through memory and is blocked at the gateway boundary."*

### Member 5: DevOps, Benchmarks & QA
* **Question:** *"How do you test that your system doesn't deadlock under 50 concurrent requests?"*  
  * **Answer:** *"In `evaluation/run_load_test.py`, we launch a `ThreadPoolExecutor` with 50 worker threads making simultaneous requests to `execute_action`. We record every response and assert that zero requests return SQLite `OperationalError: database is locked`. We also measure the P95 and P99 latency percentiles to detect thread contention."*
* **Question:** *"What does your Docker Compose configuration orchestrate?"*  
  * **Answer:** *"It orchestrates two isolated services on a shared internal Docker network: `aegis-api` (FastAPI backend on port 8000) and `aegis-dashboard` (Streamlit console on port 8501). A shared named volume `aegis-data` persists the SQLite audit and approval database across container restarts. Healthchecks ensure the dashboard does not start until the API reports healthy."*
