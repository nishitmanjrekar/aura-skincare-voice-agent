from agent import SYSTEM_PROMPT, run_agent_turn

test_queries = [
    # 1. Order lookup tool test
    "Where is my order ORD-101?",
    # 2. Policy test: Cancellation on an order that is already Out for Delivery
    "Can you cancel my order ORD-101?",
    # 3. Policy test: Return for opened product
    "I bought a face wash 5 days ago and opened it, can I return it?",
    # 4. Out of scope guardrail
    "Can you help me book a flight to Goa?"
]

messages = [{"role": "system", "content": SYSTEM_PROMPT}]

for query in test_queries:
    print(f"\nUser: {query}")
    messages.append({"role": "user", "content": query})
    reply, messages = run_agent_turn(messages)
    print(f"Aria: {reply}")