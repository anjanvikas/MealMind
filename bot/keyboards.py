"""
MealMind v3 — Telegram Inline Keyboards

All inline keyboard builders for Telegram Bot.
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup


# ── Rating ───────────────────────────────────────────────────

def rating_keyboard(meal_name: str) -> InlineKeyboardMarkup:
    """Post-meal rating buttons."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("👍 Good", callback_data=f"rating:good:{meal_name}"),
            InlineKeyboardButton("👎 Didn't like", callback_data=f"rating:bad:{meal_name}"),
            InlineKeyboardButton("🔥 Loved it", callback_data=f"rating:loved:{meal_name}"),
        ]
    ])


def dislike_reason_keyboard(dish: str) -> InlineKeyboardMarkup:
    """Follow-up reason buttons after a 👎 rating."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Don't like this dish", callback_data=f"dislike:dish:{dish}"),
            InlineKeyboardButton("Too spicy", callback_data=f"dislike:spicy:{dish}"),
        ],
        [
            InlineKeyboardButton("Too bland", callback_data=f"dislike:bland:{dish}"),
            InlineKeyboardButton("Wrong portion", callback_data=f"dislike:portion:{dish}"),
        ],
    ])


# ── Yes / No ─────────────────────────────────────────────────

def yes_no_keyboard(yes_data: str, no_data: str) -> InlineKeyboardMarkup:
    """Generic yes/no confirmation buttons."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Yes", callback_data=yes_data),
            InlineKeyboardButton("No", callback_data=no_data),
        ]
    ])


# ── Plan Actions ─────────────────────────────────────────────

def plan_actions_keyboard() -> InlineKeyboardMarkup:
    """Post-plan action buttons."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📝 Grocery list", callback_data="plan:grocery"),
            InlineKeyboardButton("👨‍🍳 Cook brief today", callback_data="plan:cook"),
        ],
        [
            InlineKeyboardButton("🔄 Change something", callback_data="plan:change"),
        ],
    ])


# ── Onboarding ───────────────────────────────────────────────

def people_count_keyboard() -> InlineKeyboardMarkup:
    """How many people in the household."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("1", callback_data="onboard:people:1"),
            InlineKeyboardButton("2", callback_data="onboard:people:2"),
            InlineKeyboardButton("3+", callback_data="onboard:people:3"),
        ]
    ])


def allergy_none_keyboard() -> InlineKeyboardMarkup:
    """Quick 'none' button for allergies."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("None", callback_data="onboard:allergy:none")]
    ])


def spice_keyboard() -> InlineKeyboardMarkup:
    """Spice level selection."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Mild", callback_data="onboard:spice:mild"),
            InlineKeyboardButton("Medium", callback_data="onboard:spice:medium"),
            InlineKeyboardButton("Spicy 🌶️", callback_data="onboard:spice:spicy"),
        ]
    ])


def protein_keyboard() -> InlineKeyboardMarkup:
    """Protein goal selection."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("High protein 💪", callback_data="onboard:protein:high"),
            InlineKeyboardButton("Moderate", callback_data="onboard:protein:moderate"),
            InlineKeyboardButton("Not a priority", callback_data="onboard:protein:low"),
        ]
    ])


def cook_keyboard() -> InlineKeyboardMarkup:
    """Has cook at home."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Yes 👨‍🍳", callback_data="onboard:cook:yes"),
            InlineKeyboardButton("No", callback_data="onboard:cook:no"),
        ]
    ])


def language_keyboard() -> InlineKeyboardMarkup:
    """Language preference."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("English", callback_data="onboard:lang:english"),
            InlineKeyboardButton("Hindi", callback_data="onboard:lang:hindi"),
        ],
        [
            InlineKeyboardButton("Kannada", callback_data="onboard:lang:kannada"),
            InlineKeyboardButton("Telugu", callback_data="onboard:lang:telugu"),
        ],
    ])


# ── Pattern Confirmation ────────────────────────────────────

def pattern_confirm_keyboard(pattern_id: str) -> InlineKeyboardMarkup:
    """Confirm/reject a detected pattern."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("Yes, lock it in! ✅", callback_data=f"pattern:confirm:{pattern_id}"),
            InlineKeyboardButton("No thanks", callback_data=f"pattern:reject:{pattern_id}"),
        ]
    ])
