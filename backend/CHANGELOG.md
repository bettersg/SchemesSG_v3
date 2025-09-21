### Changelog

| No. | Previous | New | Comments |
|-----|----------|-----|----------|
| 1 | `RunnableWithMessageHistory` used in `Chatbot.initialise_graph` (`ml_logic/chatbotManager.py`) | Replaced with LangGraph compiled graph. Chat model initialization now uses `init_chat_model` instead of `AzureOpenAI` model. | - |
| 2 | Prompt & inputs, manually created `MessageHistory` | Defined `ChatbotState` (in `ml_logic/states.py`) to be passed in the graph. | Initially considered using `RunnableContext` for dynamic inputs like searches, but LangGraph caching requires search results to be modeled as nodes. Since caching is not a node, `ChatbotState` is used instead. |
| 3 | `InMemoryCache` | Custom wrapper around LangGraph’s `InMemoryCache` with LRU implementation for backward compatibility (`ml_logic/cache.py`). | Cache is initialized in `__init__`. Consider moving to `initialise()` to align more closely with singleton lifecycle management. |
| 4 | `Chatbot.get_session_history` | Implementation moved to `FirestoreChatSaver.get_session_history`. Introduced `Checkpoint` class to store more metadata for LangGraph checkpoint compatibility (`ml_logic/firestore_saver.py`). | Additional metadata is stored for compatibility and potential future use when more nodes are introduced. |
| 5 | Chain `stream` and `invoke` | Graph `stream` and `invoke` | Streaming requires special handling when caching is enabled. An additional cache check and token replay step simulate streaming for cached responses. |
| 6 | Old prompt | Updated prompt with tone, explicit request for questions, and inclusion of user’s first `query_text` into context. Prompts moved from `ml_logic/chatbotManager.py` to `ml_logic/prompts.py`. | `query_text` was not included previously, which could lead to irrelevant responses. Moving prompts to a dedicated module also separates concerns more cleanly. |
| 7 | - | Cleanup: text preprocessing moved to `ml_logic/text_utils.py`, logger setup to `utils/logging_setup.py`, and LLM configs to `ml_logic/config.py`. | - |

---

### Next Steps
- **Firestore saver**: Current implementation is a backward-compatibility measure. For agentic design patterns, saver needs to be redesigned with well-defined collections (possibly namespaces).  
- **Async support**: Async code in tests was removed. If async functionality is required, methods can be updated to use `ainvoke` / `astream`, with corresponding test refactoring.  