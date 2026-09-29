1. Why did you choose your particular architecture and technology stack?

I opted for a modular hybrid architecture pairing a **FastAPI (Python)** backend with **Groq’s high-speed inference engine** and **browser-native Web Speech APIs (SpeechRecognition & SpeechSynthesis)**:

* **Sub-Second Latency & Low TTFT**: Voice conversations feel unnatural if response latency exceeds 1.5 seconds. By using Groq (`openai/gpt-oss-120b`), Time-to-First-Token is near-instantaneous (~200–300 ms), leaving ample budget for tool-calling and audio streaming without awkward conversational dead air.
* **Deterministic Server-Side Tool Calling**: Housing tool execution and state logic in FastAPI ensures robust query sanitization (e.g., regex normalizations from `ord 101` to `ORD-101`) before touching database records, minimizing hallucinated order details.
* **Zero-Friction Client-Side Audio**: Leveraging browser Web Speech APIs configured for Indian English (`en-IN`) eliminates the need for expensive third-party telephony SIP trunks or heavy WebRTC media servers, allowing evaluators to run and test the app friction-free directly in their browser.



2. What was the most difficult part of the assignment, and how did you solve it?

The most challenging aspect was **managing state transitions and preventing audio feedback loops (self-interruption)**:

* **The Problem**: Because speech recognition and speech synthesis run inside the same browser session, early iterations suffered from the microphone picking up the synthetic voice ("Aria") speaking through the laptop speakers, interpreting Aria's words as customer input and getting trapped in an infinite feedback loop.
* **The Solution**: I implemented strict conversational turn-taking lifecycle hooks in JavaScript:
1. The Web Speech recognition engine is explicitly stopped the instant an utterance is submitted for processing.
2. The recognition engine remains paused while the synthetic voice plays (`SpeechSynthesisUtterance`).
3. Listening is re-armed strictly inside the `onend` callback of the speech player, backed by visual state indicators (`Listening` $\rightarrow$ `Thinking` $\rightarrow$ `Speaking`) to keep the user aligned with the system's operational state.



3. If you had one more week to work on this, what would you improve first and why?

* **Full-Duplex Streaming with Barge-In / Interruption Handling**: In natural conversations, customers frequently interrupt if an agent provides information they already know. I would transition from turn-based polling to a bi-directional WebSocket audio pipeline (e.g., Deepgram Nova-2 streaming STT + Cartesia/ElevenLabs streaming TTS) paired with Voice Activity Detection (VAD) to immediately truncate agent speech when the user speaks.


* **Hinglish & Phonetic Normalization**: Many Indian customers mix Hindi and English (e.g., *"Mera order track kar do"*) or spell out alphanumeric codes with regional accents. Adding phonetic transliteration and multi-lingual prompt few-shot examples would drastically reduce entity extraction errors for Indian delivery addresses and names.


* **Semantic FAQ Cache**: Frequently asked static policy questions (e.g., *"What is your return policy?"*) could be served from a Redis semantic cache (embedding lookup) in under 50 ms without incurring an LLM call.



4. Imagine this agent is handling 1,000 customer conversations a day. What do you think would need to change or improve?

* **Stateful Distributed Session Management**: Currently, conversation history is kept in memory. At 1,000 calls/day with concurrent sessions, this would cause memory leaks and prevent horizontal scaling. I would store session states, conversation buffers, and tool outputs in a distributed cache like **Redis** keyed by a unique `call_session_id`.
* **Database Scaling & Connection Pooling**: Replace the in-memory mock dictionary with a production PostgreSQL/DynamoDB database utilizing connection pooling (PgBouncer) and read-replicas to prevent order lookup queries from choking the main transactional database.
* **Leaky-Bucket Rate Limiting & API Quotas**: Implement IP- and caller-based rate limiters to prevent bot abuse or runaway API billing spikes on inference providers.
* **Observability, Guardrail Auditing & Fallback Routing**:
* Integrate an LLM observability platform (such as **Langfuse** or **Helicone**) to monitor latency bottlenecks, token consumption, and hallucination rates.
* Set up secondary fallback providers (e.g., falling back from Groq to Anthropic/OpenAI or Deepgram to Whisper) in case of upstream downtime.
* Implement automated escalation triggers: if `customer_intent` unresolved rate or customer frustration metrics cross a threshold, automatically flag and hot-transfer the session to a human support agent.
