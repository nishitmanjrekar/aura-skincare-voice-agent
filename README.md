# Aura Skincare AI Voice Agent – Technical Assignment Answers

### 1. Why did you choose your particular architecture and technology stack?

I chose a modular architecture combining a **FastAPI (Python) backend, Google's Gemini API, and browser-native Web Speech APIs (SpeechRecognition and SpeechSynthesis)**.

- **LLM-powered conversational intelligence:** I integrated Gemini Flash-Lite to handle natural-language conversations, understand customer intent, and generate contextual responses. Its function-calling capabilities allow the agent to interact with backend tools instead of relying entirely on generated responses.
- **Reliable server-side tool execution:** FastAPI manages business logic and tool execution. For example, when a customer asks about an order, the backend normalizes the order ID (such as converting `ord 101` to `ORD-101`) and retrieves the actual order information. This reduces the risk of hallucinated order details.
- **Automated call summarization:** Gemini also generates structured call summaries containing customer intent, order ID, resolution status, and a concise conversation summary.
- **Lightweight browser-based voice interaction:** Web Speech APIs handle speech recognition and text-to-speech, avoiding the need for expensive telephony infrastructure or a dedicated media server for this browser-based prototype.

This architecture provides a clear separation between conversational intelligence, business logic, and voice interaction, making the system easier to maintain and extend.

### 2. What was the most difficult part of the assignment, and how did you solve it?

The most challenging aspect was **managing voice interaction and conversational turn-taking reliably**.

- **The Problem:** Speech recognition and speech synthesis operate within the same browser session. If the microphone remains active while the agent is speaking, it can capture the synthetic voice and mistakenly interpret it as new customer input. This creates audio feedback loops and interrupts the conversation.
- **The Solution:** I worked on controlling the speech recognition and synthesis lifecycle:
  1. Stop or pause speech recognition when a customer utterance is submitted for processing.
  2. Keep recognition paused while the agent generates and speaks its response.
  3. Resume listening after speech synthesis finishes.
  4. Use visual state indicators such as Listening, Thinking, and Speaking to communicate the agent's current activity.

I also had to ensure that the Gemini integration preserved the existing tool-calling workflow and conversation history so that switching LLM providers did not break the application's business logic.

### 3. If you had one more week to work on this, what would you improve first and why?

I would prioritize three improvements:

- **Full-Duplex Voice Interaction with Barge-In:** The current interaction is turn-based. I would introduce a real-time audio pipeline using WebSockets, streaming speech recognition, and Voice Activity Detection (VAD). This would allow customers to interrupt the agent naturally instead of waiting for the entire response to finish.

- **Hinglish and Multilingual Support:** Indian customers frequently mix Hindi and English. I would improve language detection, phonetic normalization, and multilingual prompting so the agent can understand requests such as "Mera order track kar do" and accurately extract alphanumeric order IDs.

- **Semantic FAQ Caching:** Frequently asked questions about return policies, refunds, and delivery timelines could be handled through a semantic cache using embeddings and Redis. This would reduce repeated LLM requests, improve response times, and lower API costs.

### 4. Imagine this agent is handling 1,000 customer conversations a day. What do you think would need to change or improve?

I would focus on scalability, reliability, security, and observability.

- **Distributed Session Management:** Move conversation histories and session states from application memory into Redis or a persistent database. Each conversation would have a unique session ID, allowing multiple backend instances to handle concurrent conversations reliably.

- **Production Database and Connection Pooling:** Replace mock or in-memory order records with PostgreSQL or another production database. Implement connection pooling, indexing, and appropriate read replicas as traffic grows.

- **Rate Limiting and API Cost Management:** Introduce request limits, authentication, and caller-based throttling to prevent abuse and control Gemini API consumption. Add caching for frequently requested information.

- **Observability and Performance Monitoring:** Integrate tools such as Langfuse to monitor LLM latency, token consumption, tool execution, errors, and conversation quality. Track metrics such as average response time and successful order resolution rate.

- **Fallback and Error Handling:** Implement retry mechanisms and an alternative model or provider strategy to handle upstream API failures. Ensure that temporary LLM failures do not cause the entire application to crash.

- **Human Escalation:** Introduce escalation rules for unresolved queries, repeated failures, and frustrated customers. These conversations should be flagged for human support rather than allowing the agent to repeatedly provide ineffective responses.

The objective would be to evolve the prototype into a reliable customer-support system that can handle concurrent conversations without compromising response quality or operational stability.
