"""
MealMind v3 — Entry Point

Starts the Telegram bot with all handlers + scheduler.
Uses python-telegram-bot v20+ (async, polling mode).
"""

from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
)

from config import get_settings
from bot.handlers.start import start_handler, onboarding_callback
from bot.handlers.planner import plan_handler, plan_callback
from bot.handlers.feedback import (
    rating_callback, dislike_callback, pattern_callback,
)
from bot.handlers.grocery import grocery_handler
from bot.handlers.cook_brief import cook_brief_handler
from bot.handlers.recipe_import import import_handler
from bot.router import message_router
from scheduler.jobs import setup_scheduler


def main():
    """Build and start the Telegram bot application."""
    settings = get_settings()

    print(f"🍽️  {settings.APP_NAME} v3 starting...")
    print(f"🤖 Claude model: {settings.CLAUDE_MODEL}")
    print(f"📡 Environment: {settings.ENVIRONMENT}")

    # Build the application
    app = ApplicationBuilder().token(settings.TELEGRAM_BOT_TOKEN).build()

    # ── Command handlers ─────────────────────────────────────
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("plan", plan_handler))
    app.add_handler(CommandHandler(
        "today",
        lambda u, c: plan_handler(u, c, plan_type="day"),
    ))
    app.add_handler(CommandHandler(
        "week",
        lambda u, c: plan_handler(u, c, plan_type="week"),
    ))
    app.add_handler(CommandHandler("grocery", grocery_handler))
    app.add_handler(CommandHandler("cook", cook_brief_handler))

    # ── Callback query handlers (inline buttons) ─────────────
    app.add_handler(CallbackQueryHandler(
        rating_callback, pattern=r"^rating:",
    ))
    app.add_handler(CallbackQueryHandler(
        dislike_callback, pattern=r"^dislike:",
    ))
    app.add_handler(CallbackQueryHandler(
        onboarding_callback, pattern=r"^onboard:",
    ))
    app.add_handler(CallbackQueryHandler(
        plan_callback, pattern=r"^plan:",
    ))
    app.add_handler(CallbackQueryHandler(
        pattern_callback, pattern=r"^pattern:",
    ))

    # ── Message handlers ─────────────────────────────────────
    # URL messages → recipe import
    app.add_handler(MessageHandler(
        filters.Entity("url") & ~filters.COMMAND,
        import_handler,
    ))

    # All other text messages → router
    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        message_router,
    ))

    # ── Scheduler ────────────────────────────────────────────
    setup_scheduler(app)

    # ── Start polling ────────────────────────────────────────
    print("🚀 Bot is running! Press Ctrl+C to stop.")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
