from ollama import Client
from app.config import settings
from collections.abc import Iterator

client = Client(host=settings.ollama_host)

def stream_chat(messages: list[dict]) -> Iterator[str]:
    # Ask Ollama for the answer piece by piece instead of waiting for all of it.
    # messages looks like [{"role": "user", "content": "Hi"}]
    stream = client.chat(model=settings.ollama_model, messages=messages, stream=True, options={"num_predict": settings.ollama_max_tokens}
)
    for chunk in stream:
        piece = chunk.message.content
        # The last chunk (done=True) has empty text, so skip empty pieces.
        if piece:
            # yield hands this piece out right away and pauses here until the caller asks for the next one.
            yield piece


