"""
MealMind v3 — SQLAlchemy ORM Models

All tables including pattern_signals for the learning engine.
Uses telegram_chat_id (BIGINT) instead of whatsapp_number.
"""

import uuid
from datetime import datetime, date
from typing import Optional, List

from sqlalchemy import (
    String, Integer, BigInteger, Boolean, Text, Date,
    DateTime, ForeignKey,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, ARRAY, JSONB

from db.database import Base


class Household(Base):
    """A household using MealMind, identified by Telegram chat ID."""
    __tablename__ = "households"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    telegram_chat_id: Mapped[int] = mapped_column(
        BigInteger, unique=True, nullable=False
    )
    num_people: Mapped[int] = mapped_column(Integer, default=2)
    has_cook: Mapped[bool] = mapped_column(Boolean, default=True)
    preferred_language: Mapped[str] = mapped_column(String, default="english")
    budget: Mapped[str] = mapped_column(String, default="budget_friendly")
    onboarding_complete: Mapped[bool] = mapped_column(Boolean, default=False)
    onboarding_step: Mapped[int] = mapped_column(Integer, default=0)
    onboarding_data: Mapped[Optional[dict]] = mapped_column(JSONB, default=dict)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    # Relationships
    members: Mapped[List["Member"]] = relationship(
        back_populates="household", cascade="all, delete-orphan"
    )
    standing_rules: Mapped[List["StandingRule"]] = relationship(
        back_populates="household", cascade="all, delete-orphan"
    )
    meal_history: Mapped[List["MealHistory"]] = relationship(
        back_populates="household", cascade="all, delete-orphan"
    )
    active_plans: Mapped[List["ActivePlan"]] = relationship(
        back_populates="household", cascade="all, delete-orphan"
    )
    pattern_signals: Mapped[List["PatternSignal"]] = relationship(
        back_populates="household", cascade="all, delete-orphan"
    )


class Member(Base):
    """A member of a household with dietary preferences."""
    __tablename__ = "members"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    household_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("households.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    diet_type: Mapped[str] = mapped_column(String, nullable=False)
    spice_level: Mapped[str] = mapped_column(String, default="medium")
    protein_goal: Mapped[str] = mapped_column(String, default="high")
    allergies: Mapped[Optional[list]] = mapped_column(ARRAY(String), default=list)
    disliked_ingredients: Mapped[Optional[list]] = mapped_column(ARRAY(String), default=list)
    loved_dishes: Mapped[Optional[list]] = mapped_column(ARRAY(String), default=list)
    cuisine_preferences: Mapped[Optional[list]] = mapped_column(ARRAY(String), default=list)

    # Relationships
    household: Mapped["Household"] = relationship(back_populates="members")
    disliked_dishes: Mapped[List["DislikedDish"]] = relationship(
        back_populates="member", cascade="all, delete-orphan"
    )
    saved_recipes: Mapped[List["SavedRecipe"]] = relationship(
        back_populates="member", cascade="all, delete-orphan"
    )


class DislikedDish(Base):
    """A dish that a member dislikes — avoided until a certain date."""
    __tablename__ = "disliked_dishes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    member_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("members.id"), nullable=False
    )
    household_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("households.id"), nullable=True
    )
    dish_name: Mapped[str] = mapped_column(String, nullable=False)
    reason: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    avoided_until: Mapped[date] = mapped_column(Date, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    member: Mapped["Member"] = relationship(back_populates="disliked_dishes")


class StandingRule(Base):
    """Persistent rules for a household."""
    __tablename__ = "standing_rules"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    household_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("households.id"), nullable=False
    )
    rule_key: Mapped[str] = mapped_column(String, nullable=False)
    rule_value: Mapped[str] = mapped_column(String, nullable=False)
    confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    household: Mapped["Household"] = relationship(back_populates="standing_rules")


class MealHistory(Base):
    """Record of meals served."""
    __tablename__ = "meal_history"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    household_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("households.id"), nullable=False
    )
    meal_date: Mapped[date] = mapped_column(Date, nullable=False)
    meal_type: Mapped[str] = mapped_column(String, nullable=False)
    dish_name: Mapped[str] = mapped_column(String, nullable=False)
    diet_tag: Mapped[str] = mapped_column(String, nullable=False)
    rating: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    household: Mapped["Household"] = relationship(back_populates="meal_history")


class SavedRecipe(Base):
    """A recipe saved from a URL."""
    __tablename__ = "saved_recipes"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    member_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("members.id"), nullable=False
    )
    name: Mapped[str] = mapped_column(String, nullable=False)
    source_url: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    cuisine_type: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    diet_type: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    key_ingredients: Mapped[Optional[list]] = mapped_column(ARRAY(String), default=list)
    protein_level: Mapped[Optional[str]] = mapped_column(String, nullable=True)
    added_on: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    member: Mapped["Member"] = relationship(back_populates="saved_recipes")


class ActivePlan(Base):
    """The current active meal plan for a household."""
    __tablename__ = "active_plans"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    household_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("households.id"), nullable=False
    )
    week_start: Mapped[date] = mapped_column(Date, nullable=False)
    plan_text: Mapped[str] = mapped_column(Text, nullable=False)
    plan_structured: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    household: Mapped["Household"] = relationship(back_populates="active_plans")


class PatternSignal(Base):
    """Detected taste patterns for the learning engine."""
    __tablename__ = "pattern_signals"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    household_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("households.id"), nullable=False
    )
    pattern_type: Mapped[str] = mapped_column(String, nullable=False)
    pattern_data: Mapped[dict] = mapped_column(JSONB, nullable=False)
    surfaced: Mapped[bool] = mapped_column(Boolean, default=False)
    confirmed: Mapped[bool] = mapped_column(Boolean, default=False)
    detected_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow
    )

    household: Mapped["Household"] = relationship(back_populates="pattern_signals")
