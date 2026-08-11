import os
import sys
import time
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

load_dotenv()

from app.agent import LabAgent
from app.tracing import tracing_enabled
from structlog.contextvars import bind_contextvars, clear_contextvars
from app.middleware import new_correlation_id
from app.pii import hash_user_id

def generate_traces():
    if not tracing_enabled():
        print("Tracing is not enabled. Please check LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY in .env")
        return

    agent = LabAgent()
    
    messages = [
        "What is the refund policy?",
        "How can I return an item?",
        "Where is my order?",
        "Can I get a discount?",
        "My product is damaged.",
        "How long does shipping take?",
        "Do you ship internationally?",
        "I want to speak to a human.",
        "What are your business hours?",
        "Can I change my shipping address?"
    ]

    for i, msg in enumerate(messages):
        correlation_id = new_correlation_id()
        user_id = f"student-{i}"
        
        bind_contextvars(
            correlation_id=correlation_id,
            user_id_hash=hash_user_id(user_id),
            session_id=f"session-{i}",
            feature="qa",
            model=agent.model,
            env="dev",
        )
        
        print(f"[{i+1}/10] Sending request: '{msg}' (Correlation ID: {correlation_id})")
        try:
            result = agent.run(
                user_id=user_id,
                feature="qa",
                session_id=f"session-{i}",
                message=msg,
            )
            print(f" -> Success! Latency: {result.latency_ms}ms")
        except Exception as e:
            print(f" -> Failed: {e}")
        finally:
            clear_contextvars()
            
        time.sleep(1)
        
    print("\nSuccessfully sent 10 requests to generate traces.")
    
    # Flush the Langfuse client to ensure all background tasks are sent
    from app.tracing import get_langfuse_client
    client = get_langfuse_client()
    if hasattr(client, "flush"):
        print("Flushing Langfuse traces to server...")
        client.flush()
        
    print("Please check your Langfuse dashboard for the traces.")

if __name__ == "__main__":
    generate_traces()
