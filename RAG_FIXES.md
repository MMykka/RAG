# RAG Fixes

Every fix that made the RAG (finding the right document pieces and answering from them) better.
Newest at the top. Speed changes are in `OPTIMIZATIONS.md`; this file is about answer quality.
"Chunk" = one piece of a document, stored with its embedding in the `chunks` table.

---

## 1. Answers credited the wrong policy (2026-11-24)

**Problem:** "What are the company equipments?" was answered with the right rules (laptops, phones and accessories stay company property) but credited them to "POL-08: Dress Code" and claimed the handbook had no general mention of company equipment.

**Cause:** `scripts/ingest_documents.py` cut every document every 1000 characters, without looking at its sections. POL-13 was cut in half: its title `## POL-13: Company Equipment` landed at the end of one chunk and its rules at the start of the next, whose only title was `## POL-14`. The search found the chunk with the rules (rank 2) but not the one with the title, so Llama saw the rules without their policy name, next to unrelated chunks (POL-08 among them), and guessed a title.

**Solution:** Cut Markdown at its `#` and `##` headings, so each section (one policy) is one chunk with its title (`split_document` in `scripts/ingest_documents.py`). A section longer than 1000 characters is still cut into overlapping parts, with its heading repeated at the top of every part. `###` headings stay inside their section, `#` lines inside code blocks are ignored, and text without headings is still cut every 1000 characters. Re-ran the ingest: `company_policies.md` went from 22 chunks to 26, every one starting with its heading. The same question now ranks POL-13 first and Llama answers "According to POL-13: Company Equipment ...". Checked that vacation days, medical certificate, hotel limit and "Who is the CEO?" (not in the handbook, so "I don't know") still answer correctly. Tests: `backend/tests/test_ingest.py` (7 tests, e.g. every piece keeps its heading). Confirmed live in the chat by the user: "what is the company equipment policy" -> "The Company Equipment Policy (POL-13) states:" followed by all six rules, word for word.

---

## 2. The first question after a pause was slow (2026-11-20)

**Problem:** After a few idle minutes, the first question waited about 2.7 s before the search even started.

**Cause:** Ollama unloads `nomic-embed-text` after 5 idle minutes, and loading it back takes seconds; once loaded, embedding a question takes about 65 ms.

**Solution:** `keep_alive="30m"` on both embedding calls in `app/services/llm.py`, so the model stays loaded for 30 minutes. Details and timings in `OPTIMIZATIONS.md`.

---

## 3. Questions and document pieces were embedded the same way (2026-11-20)

**Problem:** The first version of `embed_documents` sent the raw text to the embedding model, which makes matches between a short question and a long document piece weaker.

**Cause:** `nomic-embed-text` is trained to tell questions and documents apart by a prefix; without it, both are treated alike.

**Solution:** Document pieces are embedded with `search_document: ` in front (`embed_documents`), questions with `search_query: ` (`embed_query`), both in `app/services/llm.py`.

---

## 4. A useless extra chunk at the end of documents (2026-11-20)

**Problem:** A 2500-character text was cut into pieces of 1000, 1000, 900 and 100 characters; the last piece only repeated the end of the one before it.

**Cause:** The cutting loop kept going after a piece had already reached the end of the text.

**Solution:** `split_text` stops as soon as a piece reaches the end (now `[1000, 1000, 900]`), so no duplicate chunk competes in the search.

---

## 5. "Empty" files were stored as a chunk (2026-11-20)

**Problem:** A file saved empty by a Windows editor was not skipped; it was stored as a 1-character chunk.

**Cause:** Many Windows editors start a file with an invisible BOM mark, so the file was never really empty when read as plain UTF-8.

**Solution:** The ingest script reads files with `utf-8-sig`, which removes the BOM, so empty files are skipped.

---

## Known problems, not fixed yet

**Problem:** Every retrieved chunk is listed as a source of an answer, even unrelated ones (e.g. "Dress Code" for an equipment question).
**Cause:** The search always returns the `RAG_TOP_K` (5) closest chunks, however far they are from the question; there is no cut-off.
**Solution (idea):** Skip chunks whose distance is clearly worse than the best one (or above a fixed limit) before building the prompt and the sources list. Needs testing on real questions to pick the limit.

**Problem:** The model is small (`llama3.2`, 3B) and sometimes adds guesses ("accessories likely include headphones").
**Cause:** Small models follow "answer only from the context" less strictly than larger ones.
**Solution (idea):** Try a larger model in `OLLAMA_MODEL` (e.g. an 8B model) if the PCs can run it, and compare answers and speed on the same questions.
