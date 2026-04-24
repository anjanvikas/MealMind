"""
MealMind v3 — Database Query Helpers

All DB operations. Uses telegram_chat_id for household lookup.
"""

import uuid
import json
from datetime import date, datetime, timedelta
from typing import Optional, List

from sqlalchemy import select, update, and_, func, extract
from sqlalchemy.orm import selectinload

from db.database import async_session
from db.models import (
    Household, Member, DislikedDish, StandingRule,
    MealHistory, SavedRecipe, ActivePlan, PatternSignal,
)


# ── Household ────────────────────────────────────────────────

async def get_household(chat_id: int) -> Optional[Household]:
    """Get a household by Telegram chat ID."""
    async with async_session() as session:
        result = await session.execute(
            select(Household).where(Household.telegram_chat_id == chat_id)
        )
        return result.scalar_one_or_none()


async def create_household(chat_id: int) -> Household:
    """Create a new household."""
    async with async_session() as session:
        household = Household(telegram_chat_id=chat_id)
        session.add(household)
        await session.commit()
        await session.refresh(household)
        return household


async def get_all_active_households() -> List[Household]:
    """Get all households with completed onboarding."""
    async with async_session() as session:
        result = await session.execute(
            select(Household).where(Household.onboarding_complete == True)
        )
        return list(result.scalars().all())


async def update_household(chat_id: int, **kwargs) -> None:
    """Update household fields by chat_id."""
    async with async_session() as session:
        await session.execute(
            update(Household)
            .where(Household.telegram_chat_id == chat_id)
            .values(**kwargs)
        )
        await session.commit()


async def update_onboarding_step(chat_id: int, step: int) -> None:
    """Update the onboarding step."""
    await update_household(chat_id, onboarding_step=step)


async def save_onboarding_data(chat_id: int, key: str, value) -> None:
    """Save a key-value pair into onboarding_data JSONB."""
    async with async_session() as session:
        household = await session.execute(
            select(Household).where(Household.telegram_chat_id == chat_id)
        )
        h = household.scalar_one_or_none()
        if h:
            data = h.onboarding_data or {}
            data[key] = value
            h.onboarding_data = data
            await session.commit()


async def complete_onboarding(chat_id: int) -> None:
    """Mark onboarding as complete."""
    await update_household(chat_id, onboarding_complete=True)


# ── Members ──────────────────────────────────────────────────

async def get_members(household_id: uuid.UUID) -> List[Member]:
    """Get all members of a household."""
    async with async_session() as session:
        result = await session.execute(
            select(Member).where(Member.household_id == household_id)
        )
        return list(result.scalars().all())


async def create_member(
    household_id: uuid.UUID,
    name: str,
    diet_type: str,
    spice_level: str = "medium",
    protein_goal: str = "high",
    allergies: list = None,
) -> Member:
    """Create a new member in a household."""
    async with async_session() as session:
        member = Member(
            household_id=household_id,
            name=name,
            diet_type=diet_type,
            spice_level=spice_level,
            protein_goal=protein_goal,
            allergies=allergies or [],
        )
        session.add(member)
        await session.commit()
        await session.refresh(member)
        return member


async def get_member_by_diet(
    household_id: uuid.UUID, diet_type: str
) -> Optional[Member]:
    """Get a member by diet type (for recipe assignment)."""
    async with async_session() as session:
        # Map diet types
        if diet_type in ["vegetarian", "vegan"]:
            result = await session.execute(
                select(Member).where(
                    and_(
                        Member.household_id == household_id,
                        Member.diet_type.in_(["vegetarian", "vegan"]),
                    )
                ).limit(1)
            )
        else:
            result = await session.execute(
                select(Member).where(
                    and_(
                        Member.household_id == household_id,
                        Member.diet_type == "non_vegetarian",
                    )
                ).limit(1)
            )
        member = result.scalar_one_or_none()

        # Fallback to first member
        if not member:
            result = await session.execute(
                select(Member)
                .where(Member.household_id == household_id)
                .limit(1)
            )
            member = result.scalar_one_or_none()
        return member


async def update_member_field(
    household_id: uuid.UUID, field: str, value
) -> None:
    """Update a field on all members of a household."""
    async with async_session() as session:
        await session.execute(
            update(Member)
            .where(Member.household_id == household_id)
            .values(**{field: value})
        )
        await session.commit()


async def update_member_allergies(
    household_id: uuid.UUID, allergies: list
) -> None:
    """Update allergies on all members."""
    await update_member_field(household_id, "allergies", allergies)


# ── Full Profile ─────────────────────────────────────────────

async def get_full_profile(household_id: uuid.UUID) -> dict:
    """Get complete household profile including members."""
    async with async_session() as session:
        result = await session.execute(
            select(Household)
            .options(selectinload(Household.members))
            .where(Household.id == household_id)
        )
        household = result.scalar_one_or_none()
        if not household:
            return {}

        members_data = []
        for m in household.members:
            members_data.append({
                "name": m.name,
                "diet_type": m.diet_type,
                "spice_level": m.spice_level,
                "protein_goal": m.protein_goal,
                "allergies": m.allergies or [],
                "disliked_ingredients": m.disliked_ingredients or [],
                "loved_dishes": m.loved_dishes or [],
                "cuisine_preferences": m.cuisine_preferences or [],
            })

        return {
            "id": str(household.id),
            "num_people": household.num_people,
            "has_cook": household.has_cook,
            "preferred_language": household.preferred_language,
            "budget": household.budget,
            "members": members_data,
        }


# ── Dislikes / Loved ────────────────────────────────────────

async def get_active_dislikes(household_id: uuid.UUID) -> List[str]:
    """Get dish names currently being avoided."""
    async with async_session() as session:
        members = await session.execute(
            select(Member.id).where(Member.household_id == household_id)
        )
        member_ids = [row[0] for row in members.all()]
        if not member_ids:
            return []

        result = await session.execute(
            select(DislikedDish.dish_name).where(
                and_(
                    DislikedDish.member_id.in_(member_ids),
                    DislikedDish.avoided_until >= date.today(),
                )
            )
        )
        return list(set(row[0] for row in result.all()))


async def get_loved_dishes(household_id: uuid.UUID) -> List[str]:
    """Get all loved dishes across members."""
    async with async_session() as session:
        result = await session.execute(
            select(Member.loved_dishes).where(
                Member.household_id == household_id
            )
        )
        loved = []
        for row in result.all():
            if row[0]:
                loved.extend(row[0])
        return list(set(loved))


async def add_dislike(
    household_id: uuid.UUID,
    dish_name: str,
    avoided_until: date,
    reason: str = None,
) -> None:
    """Add a disliked dish for all members."""
    async with async_session() as session:
        members = await session.execute(
            select(Member.id).where(Member.household_id == household_id)
        )
        member_ids = [row[0] for row in members.all()]

        for member_id in member_ids:
            dislike = DislikedDish(
                member_id=member_id,
                household_id=household_id,
                dish_name=dish_name,
                reason=reason,
                avoided_until=avoided_until,
            )
            session.add(dislike)
        await session.commit()


async def add_loved(household_id: uuid.UUID, dish_name: str) -> None:
    """Add a dish to the loved list of all members."""
    async with async_session() as session:
        members_result = await session.execute(
            select(Member).where(Member.household_id == household_id)
        )
        for member in members_result.scalars().all():
            current = member.loved_dishes or []
            if dish_name not in current:
                current.append(dish_name)
                member.loved_dishes = current
        await session.commit()


# ── Meal History ─────────────────────────────────────────────

async def get_recent_meals(
    household_id: uuid.UUID, days: int = 14
) -> List[str]:
    """Get dish names from the last N days."""
    async with async_session() as session:
        cutoff = date.today() - timedelta(days=days)
        result = await session.execute(
            select(MealHistory.dish_name).where(
                and_(
                    MealHistory.household_id == household_id,
                    MealHistory.meal_date >= cutoff,
                )
            )
        )
        return list(set(row[0] for row in result.all()))


async def get_last_meal(household_id: uuid.UUID) -> Optional[MealHistory]:
    """Get the most recent meal."""
    async with async_session() as session:
        result = await session.execute(
            select(MealHistory)
            .where(MealHistory.household_id == household_id)
            .order_by(MealHistory.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()


async def get_todays_last_meal(household_id: uuid.UUID) -> Optional[MealHistory]:
    """Get today's last meal (for rating nudge)."""
    async with async_session() as session:
        result = await session.execute(
            select(MealHistory).where(
                and_(
                    MealHistory.household_id == household_id,
                    MealHistory.meal_date == date.today(),
                )
            ).order_by(MealHistory.created_at.desc()).limit(1)
        )
        return result.scalar_one_or_none()


async def save_rating(
    household_id: uuid.UUID, dish_name: str, rating: str
) -> None:
    """Save a rating for the most recent instance of a dish."""
    async with async_session() as session:
        result = await session.execute(
            select(MealHistory).where(
                and_(
                    MealHistory.household_id == household_id,
                    MealHistory.dish_name == dish_name,
                )
            ).order_by(MealHistory.created_at.desc()).limit(1)
        )
        meal = result.scalar_one_or_none()
        if meal:
            meal.rating = rating
            await session.commit()


async def count_ratings(household_id: uuid.UUID) -> int:
    """Count total ratings for pattern detection trigger."""
    async with async_session() as session:
        result = await session.execute(
            select(func.count(MealHistory.id)).where(
                and_(
                    MealHistory.household_id == household_id,
                    MealHistory.rating.isnot(None),
                )
            )
        )
        return result.scalar() or 0


async def get_ratings_by_day_of_week(household_id: uuid.UUID) -> dict:
    """Get ratings grouped by day of week for pattern detection."""
    async with async_session() as session:
        result = await session.execute(
            select(
                MealHistory.dish_name,
                MealHistory.meal_type,
                MealHistory.rating,
                MealHistory.meal_date,
            ).where(
                and_(
                    MealHistory.household_id == household_id,
                    MealHistory.rating.isnot(None),
                )
            ).order_by(MealHistory.meal_date)
        )

        by_day = {}
        for dish, meal_type, rating, meal_date in result.all():
            day_name = meal_date.strftime("%A")
            if day_name not in by_day:
                by_day[day_name] = []
            by_day[day_name].append({
                "dish": dish,
                "meal_type": meal_type,
                "rating": rating,
            })
        return by_day


# ── Standing Rules ───────────────────────────────────────────

async def get_standing_rules(household_id: uuid.UUID) -> List[str]:
    """Get confirmed standing rules as readable strings."""
    async with async_session() as session:
        result = await session.execute(
            select(StandingRule).where(
                and_(
                    StandingRule.household_id == household_id,
                    StandingRule.confirmed == True,
                )
            )
        )
        return [f"{r.rule_key}: {r.rule_value}" for r in result.scalars().all()]


async def add_standing_rule(
    household_id: uuid.UUID,
    rule_key: str,
    rule_value: str,
    confirmed: bool = False,
) -> None:
    """Add a standing rule."""
    async with async_session() as session:
        rule = StandingRule(
            household_id=household_id,
            rule_key=rule_key,
            rule_value=rule_value,
            confirmed=confirmed,
        )
        session.add(rule)
        await session.commit()


# ── Active Plans ─────────────────────────────────────────────

async def get_active_plan(household_id: uuid.UUID) -> Optional[ActivePlan]:
    """Get the most recent active plan."""
    async with async_session() as session:
        result = await session.execute(
            select(ActivePlan)
            .where(ActivePlan.household_id == household_id)
            .order_by(ActivePlan.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()


async def save_plan(
    household_id: uuid.UUID, plan_text: str, plan_type: str = "week"
) -> ActivePlan:
    """Save a new meal plan."""
    async with async_session() as session:
        plan = ActivePlan(
            household_id=household_id,
            week_start=date.today(),
            plan_text=plan_text,
            plan_structured={"type": plan_type, "generated_at": str(datetime.utcnow())},
        )
        session.add(plan)
        await session.commit()
        await session.refresh(plan)
        return plan


# ── Saved Recipes ────────────────────────────────────────────

async def save_recipe(
    member_id: uuid.UUID, recipe: dict, url: str = None
) -> SavedRecipe:
    """Save a recipe to a member's profile."""
    async with async_session() as session:
        saved = SavedRecipe(
            member_id=member_id,
            name=recipe.get("dish_name", "Unknown"),
            source_url=url,
            cuisine_type=recipe.get("cuisine_type", ""),
            diet_type=recipe.get("diet_type", ""),
            key_ingredients=recipe.get("key_ingredients", []),
            protein_level=recipe.get("protein_level", "medium"),
        )
        session.add(saved)
        await session.commit()
        await session.refresh(saved)
        return saved


# ── Pattern Signals ──────────────────────────────────────────

async def save_pattern_signal(household_id: uuid.UUID, pattern: dict) -> None:
    """Save a detected pattern signal."""
    async with async_session() as session:
        signal = PatternSignal(
            household_id=household_id,
            pattern_type=pattern.get("pattern_type", "unknown"),
            pattern_data=pattern,
        )
        session.add(signal)
        await session.commit()


async def get_unsurfaced_patterns(household_id: uuid.UUID) -> List[PatternSignal]:
    """Get patterns that haven't been shown to the user yet."""
    async with async_session() as session:
        result = await session.execute(
            select(PatternSignal).where(
                and_(
                    PatternSignal.household_id == household_id,
                    PatternSignal.surfaced == False,
                )
            )
        )
        return list(result.scalars().all())


async def mark_pattern_surfaced(pattern_id: uuid.UUID) -> None:
    """Mark a pattern as surfaced to the user."""
    async with async_session() as session:
        await session.execute(
            update(PatternSignal)
            .where(PatternSignal.id == pattern_id)
            .values(surfaced=True)
        )
        await session.commit()


async def confirm_pattern(pattern_id: uuid.UUID) -> None:
    """Confirm a pattern and convert to standing rule."""
    async with async_session() as session:
        result = await session.execute(
            select(PatternSignal).where(PatternSignal.id == pattern_id)
        )
        pattern = result.scalar_one_or_none()
        if pattern:
            pattern.confirmed = True
            # Also add as a standing rule
            rule = StandingRule(
                household_id=pattern.household_id,
                rule_key=pattern.pattern_type,
                rule_value=json.dumps(pattern.pattern_data),
                confirmed=True,
            )
            session.add(rule)
            await session.commit()
