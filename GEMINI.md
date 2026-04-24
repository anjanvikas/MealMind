# AI Assistant Copilot Instructions

> **IMPORTANT:** This file is intended to be a living document. Whenever we learn new things, encounter recurring bugs, or establish new patterns, **you (the AI) should self-improvise and proactively update this file** with those learnings and design principles.

## Coding Standards
1. **Language & Framework**: Python 3, using `python-telegram-bot` v20+ (async, polling mode) for telegram bot functionality.
2. **Architecture**: Modular structure separating concerns:
   - `bot/`: Handlers, routers, and Telegram-specific UI.
   - `engine/`: AI processing, pattern detection, and Claude integration.
   - `db/`: Database models and connection management.
   - `scheduler/`: Background jobs and scheduled tasks.
3. **Typing & Docstrings**: Always use Python type hints and write clear, concise docstrings for all functions, classes, and modules.
4. **Configuration**: Never hardcode secrets. Always use `config.py` (e.g., with `pydantic-settings`) to manage `.env` configurations.

## Design Principles
1. **Conversational UX**: Ensure bot interactions are natural. Format messages consistently using Telegram-supported HTML/Markdown, avoiding rendering issues.
2. **Resilience & Fallbacks**: Implement robust error handling around external API calls (Claude, Database). Fail gracefully and inform the user without crashing the bot.
3. **Asynchronous Execution**: Keep I/O bound operations (LLM calls, DB queries) async to prevent blocking the main Telegram event loop.
4. **Modularity**: Keep components decoupled. The `engine` should not depend directly on `bot` specifics whenever possible.

## Learnings & Best Practices (Over Time)
- **Telegram Formatting**: Telegram's HTML parser is strict. Always ensure tags are properly closed to prevent `Bad Request: can't parse entities` errors.
- **Context Management**: Inject real-time temporal data (time, date) and maintain persistent conversational memory. Use `GEMINI.md` files for hierarchical context:
  - **Global**: `~/.gemini/GEMINI.md` for cross-project defaults.
  - **Workspace**: Root `GEMINI.md` for project-specific standards.
  - **JIT**: Directory-level `GEMINI.md` for component-specific context.
- **Memory Commands**: Use `/memory show` to inspect context, `/memory reload` to refresh, and `/memory add <text>` for persistent global memories.

---
*Note to AI: Keep this file updated as the project evolves.*
