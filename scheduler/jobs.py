"""
MealMind v3 — Scheduled Jobs

APScheduler cron jobs for proactive Telegram messages:
- Sunday 7 PM: weekly plan prompt
- Daily 9 PM: dinner rating nudge
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from db import queries as db
from bot.keyboards import rating_keyboard, yes_no_keyboard


def setup_scheduler(app):
    """Set up and start the APScheduler with cron jobs."""
    scheduler = AsyncIOScheduler(timezone="Asia/Kolkata")

    @scheduler.scheduled_job("cron", day_of_week="sun", hour=19)
    async def weekly_plan_prompt():
        """Sunday 7 PM — nudge all active households to plan their week."""
        print("⏰ Running: weekly plan prompt")
        households = await db.get_all_active_households()
        for h in households:
            try:
                await app.bot.send_message(
                    chat_id=h.telegram_chat_id,
                    text=(
                        "🍽️ Your week is coming up!\n"
                        "Should I plan meals for the week ahead?"
                    ),
                    reply_markup=yes_no_keyboard(
                        "plan:week:confirm", "plan:week:skip"
                    ),
                )
            except Exception as e:
                print(f"❌ Failed to send to {h.telegram_chat_id}: {e}")
        print(f"✅ Sent weekly prompts to {len(households)} households")

    @scheduler.scheduled_job("cron", hour=21)
    async def dinner_rating_nudge():
        """Daily 9 PM — ask about tonight's dinner."""
        print("⏰ Running: dinner rating nudge")
        households = await db.get_all_active_households()
        sent = 0
        for h in households:
            try:
                meal = await db.get_todays_last_meal(h.id)
                if meal and not meal.rating:
                    await app.bot.send_message(
                        chat_id=h.telegram_chat_id,
                        text=f"How was tonight's dinner — <b>{meal.dish_name}</b>?",
                        reply_markup=rating_keyboard(meal.dish_name),
                        parse_mode="HTML",
                    )
                    sent += 1
            except Exception as e:
                print(f"❌ Failed to send to {h.telegram_chat_id}: {e}")
        print(f"✅ Sent rating nudges to {sent} households")

    scheduler.start()
    print("⏰ Scheduler started (IST timezone)")
