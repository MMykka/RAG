from ollama import Client
from app.config import settings
from collections.abc import Iterator
import time



client = Client(host=settings.ollama_host)



def stream_chat(messages: list[dict], usage: dict) -> Iterator[str]:
    # Ask Ollama for the answer piece by piece instead of waiting for all of it.
    # messages looks like [{"role": "user", "content": "Hi"}]
    if settings.ollama_mock:
        answer = "This is a mock answer from the fake Llama"
        for piece in answer.split(" "):
            time.sleep(0.05)
            yield piece + " "
        
        usage["prompt"] = 10
        usage["answer"] = len(answer.split(" "))

        return 

    stream = client.chat(model=settings.ollama_model, messages=messages, stream=True, options={"num_predict": settings.ollama_max_tokens}
)   
    for chunk in stream:
        piece = chunk.message.content
        # The last chunk (done=True) has empty text, so skip empty pieces.
        if piece:
            # yield hands this piece out right away and pauses here until the caller asks for the next one.
            yield piece
        if chunk.done:
            usage["prompt"] = chunk.prompt_eval_count
            usage["answer"] = chunk.eval_count



