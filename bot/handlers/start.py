"""
MealMind v3 — Onboarding Handler (/start)

7-step onboarding flow using Telegram inline keyboards.
Free-text steps (members, allergies) use Claude to parse answers.
"""

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from db import queries as db
from engine.learner import parse_members_from_text
from bot.keyboards import (
    people_count_keyboard, allergy_none_keyboard, spice_keyboard,
    protein_keyboard, cook_keyboard, language_keyboard,
)

# ── Onboarding Questions ─────────────────────────────────────
# Steps with keyboard = button-driven, without = free-text

ONBOARDING_QUESTIONS = {
    0: {
        "text": "How many people am I planning for?",
        "keyboard": people_count_keyboard,
    },
    1: {
        "text": (
            "Names and diets?\n\n"
            "Example: <i>Rahul - non-veg, Priya - vegetarian</i>\n\n"
            "Just type naturally, I'll figure it out 😊"
        ),
        "keyboard": None,  # Free text
    },
    2: {
        "text": (
            "Any allergies or hard NO ingredients?\n\n"
            "Example: <i>no mushrooms, no prawns</i>\n"
            "Or tap below if all good!"
        ),
        "keyboard": allergy_none_keyboard,
    },
    3: {
        "text": "Spice level?",
        "keyboard": spice_keyboard,
    },
    4: {
        "text": "Protein goal?",
        "keyboard": protein_keyboard,
    },
    5: {
        "text": "Do you have a cook at home?",
        "keyboard": cook_keyboard,
    },
    6: {
        "text": "Preferred language for recipes?",
        "keyboard": language_keyboard,
    },
}


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command — begin or resume onboarding."""
    chat_id = update.effective_chat.id
    household = await db.get_household(chat_id)

    if household and household.onboarding_complete:
        await update.message.reply_text(
            "Welcome back! 🍽️\n\n"
            "Here's what I can do:\n"
            "• /plan — meal plan for this week\n"
            "• /today — today's meals\n"
            "• /grocery — shopping list\n"
            "• /cook — cook briefing\n\n"
            "Or just type naturally — <i>plan my week</i>, "
            "<i>what should I eat today?</i>, etc."
        )
        return

    if not household:
        await db.create_household(chat_id)

    # Start onboarding
    q = ONBOARDING_QUESTIONS[0]
    kb = q["keyboard"]() if q["keyboard"] else None
    await update.message.reply_text(
        "Namaste! 🙏 I'm <b>MealMind</b> — your personal meal planner.\n"
        "Let me set up your household in 2 mins.\n\n" + q["text"],
        reply_markup=kb,
        parse_mode="HTML",
    )


async def onboarding_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle inline button presses during onboarding."""
    query = update.callback_query
    await query.answer()
    chat_id = update.effective_chat.id
    data = query.data  # e.g. "onboard:spice:medium"

    parts = data.split(":", 2)
    if len(parts) < 3:
        return

    _, field, value = parts
    household = await db.get_household(chat_id)
    if not household:
        return

    # Save the answer
    await _save_button_answer(chat_id, household, field, value)

    # Advance
    next_step = household.onboarding_step + 1
    await _advance_onboarding(chat_id, next_step, context, update)


async def handle_onboarding_text(
    update: Update, context: ContextTypes.DEFAULT_TYPE, household
):
    """
    Handle free-text answers during onboarding.
    Called from message_router when onboarding is in progress.
    """
    chat_id = update.effective_chat.id
    text = update.message.text.strip()
    step = household.onboarding_step

    if step == 1:
        # Parse member names and diets via Claude
        members = await parse_members_from_text(text)
        for m in members:
            await db.create_member(
                household_id=household.id,
                name=m.get("name", "Member"),
                diet_type=m.get("diet_type", "non_vegetarian"),
            )
        await db.save_onboarding_data(chat_id, "members_raw", text)

    elif step == 2:
        # Parse allergies from free text
        if text.lower() not in ["none", "no", "nope", "nothing", "na"]:
            allergies = [
                item.strip().lower().replace("no ", "")
                for item in text.replace(",", "\n").split("\n")
                if item.strip()
            ]
            await db.update_member_allergies(household.id, allergies)
        await db.save_onboarding_data(chat_id, "allergies_raw", text)

    # Advance to next step
    next_step = step + 1
    await _advance_onboarding(chat_id, next_step, context, update)


async def _save_button_answer(chat_id: int, household, field: str, value: str):
    """Process and save a button-driven onboarding answer."""
    if field == "people":
        num = int(value) if value.isdigit() else 2
        await db.update_household(chat_id, num_people=num)

    elif field == "allergy":
        if value != "none":
            await db.update_member_allergies(household.id, [value])

    elif field == "spice":
        await db.update_member_field(household.id, "spice_level", value)

    elif field == "protein":
        await db.update_member_field(household.id, "protein_goal", value)

    elif field == "cook":
        await db.update_household(chat_id, has_cook=(value == "yes"))

    elif field == "lang":
        await db.update_household(chat_id, preferred_language=value)

    await db.save_onboarding_data(chat_id, field, value)


async def _advance_onboarding(chat_id, next_step, context, update):
    """Advance to the next onboarding step or complete."""
    if next_step >= len(ONBOARDING_QUESTIONS):
        # Onboarding complete!
        await db.complete_onboarding(chat_id)
        await context.bot.send_message(
            chat_id=chat_id,
            text=(
                "✅ All set! Your profiles are created.\n\n"
                "Here's what I can do:\n"
                "• /plan — full 7-day meal plan\n"
                "• /today — today's meals\n"
                "• /grocery — shopping list\n"
                "• /cook — cook briefing\n\n"
                "Just say <b>plan my week</b> to get started! 🍽️"
            ),
            parse_mode="HTML",
        )
        return

    await db.update_onboarding_step(chat_id, next_step)

    q = ONBOARDING_QUESTIONS[next_step]
    kb = q["keyboard"]() if q["keyboard"] else None
    await context.bot.send_message(
        chat_id=chat_id,
        text=q["text"],
        reply_markup=kb,
        parse_mode="HTML",
    )
