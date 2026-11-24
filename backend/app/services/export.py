# Export service: turns one conversation (with its messages) into a downloadable file.
# No database work here: the router loads the conversation and checks ownership first.
import json
import re
from datetime import datetime, timezone

from app.config import settings
from app.models.conversations import Conversation

ROLE_NAMES = {"user": "You", "assistant": "Assistant"}


def to_markdown(conversation: Conversation) -> str:
    # Title as h1, then the messages in order, each with who wrote it and when
    lines = [f"# {conversation.title}", ""]
    lines.append(f"*Exported {_stamp(datetime.now(timezone.utc))} · {len(conversation.messages)} messages*")
    for message in conversation.messages:
        lines += ["", "---", "", f"**{ROLE_NAMES.get(message.role, message.role)}** · {_stamp(message.created_at)}", "", message.content]
    return "\n".join(lines) + "\n"


def to_json(conversation: Conversation) -> str:
    # The same conversation as structured data, with metadata for each message
    messages = [
        {
            "role": message.role,
            "content": message.content,
            "created_at": message.created_at.isoformat(),
            "tokens_used": message.tokens_used,
            "sources": message.sources,
        }
        for message in conversation.messages
    ]
    data = {
        "conversation": {
            "id": conversation.id,
            "title": conversation.title,
            "created_at": conversation.created_at.isoformat(),
            "updated_at": conversation.updated_at.isoformat(),
        },
        "exported_at": datetime.now(timezone.utc).isoformat(),
        # The model is not stored per message, so this is the model the app is set to use now
        "model": settings.ollama_model,
        "message_count": len(messages),
        "total_tokens": sum(m["tokens_used"] or 0 for m in messages),
        "messages": messages,
    }
    return json.dumps(data, ensure_ascii=False, indent=2)


def filename(conversation: Conversation, extension: str) -> str:
    # "chat-12-holiday-questions.md": safe for every operating system and for the HTTP header
    slug = re.sub(r"[^a-z0-9]+", "-", conversation.title.lower()).strip("-")[:50].strip("-")
    return f"chat-{conversation.id}-{slug or 'untitled'}.{extension}"


def _stamp(moment: datetime) -> str:
    return moment.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
