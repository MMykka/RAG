# Database code for searching a user's chats (Postgres full-text search)
from sqlalchemy import text
from sqlalchemy.orm import Session

# Full-text search over one user's chats (titles and messages), in one query.
# - websearch_to_tsquery understands what people type in a search box: plain words (all must match),
#   "exact phrase", -excluded, or. Words are stemmed ("holidays" finds "holiday").
# - hits: the best matching message per chat (DISTINCT ON), found through the GIN index on
#   messages.search_vector, with a highlighted snippet from ts_headline.
# - chats whose title matches count too (a title match ranks above message matches).
# - Only the user's own chats are ever searched (c.user_id = :user_id in both parts).
SEARCH_SQL = text("""
WITH q AS (SELECT websearch_to_tsquery('english', :query) AS query),
hits AS (
    SELECT DISTINCT ON (m.conversation_id)
           m.conversation_id,
           m.id AS message_id,
           ts_rank(m.search_vector, q.query) AS rank,
           ts_headline('english', m.content, q.query, :headline_options) AS snippet
    FROM messages m
    JOIN conversations c ON c.id = m.conversation_id
    CROSS JOIN q
    WHERE c.user_id = :user_id AND m.search_vector @@ q.query
    ORDER BY m.conversation_id, rank DESC, m.id DESC
)
SELECT c.id, c.title, c.updated_at, h.message_id, h.snippet
FROM conversations c
CROSS JOIN q
LEFT JOIN hits h ON h.conversation_id = c.id
WHERE c.user_id = :user_id
  AND (h.conversation_id IS NOT NULL OR to_tsvector('english', c.title) @@ q.query)
ORDER BY (CASE WHEN to_tsvector('english', c.title) @@ q.query THEN 1 ELSE 0 END) + COALESCE(h.rank, 0) DESC,
         c.updated_at DESC
LIMIT :limit
""")
# matching words are wrapped in \x02 ... \x03 (characters that never appear in normal text)
HEADLINE_OPTIONS = "StartSel=\x02, StopSel=\x03, MaxWords=20, MinWords=8, MaxFragments=1"


def search_conversations(db: Session, user_id: int, query: str, limit: int = 20) -> list[dict]:
    rows = db.execute(SEARCH_SQL, {"query": query, "user_id": user_id, "limit": limit, "headline_options": HEADLINE_OPTIONS})
    return [dict(row._mapping) for row in rows]
