-- MealMind v3 — Full Database Schema
-- Auto-executed by Docker on first boot via docker-entrypoint-initdb.d

CREATE EXTENSION IF NOT EXISTS "pgcrypto";

-- ── Households ──────────────────────────────────────────────
CREATE TABLE households (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  telegram_chat_id BIGINT UNIQUE NOT NULL,
  num_people INT DEFAULT 2,
  has_cook BOOLEAN DEFAULT true,
  preferred_language TEXT DEFAULT 'english',
  budget TEXT DEFAULT 'budget_friendly',
  onboarding_complete BOOLEAN DEFAULT false,
  onboarding_step INT DEFAULT 0,
  onboarding_data JSONB DEFAULT '{}',
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ── Members ─────────────────────────────────────────────────
CREATE TABLE members (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  household_id UUID REFERENCES households(id) ON DELETE CASCADE,
  name TEXT NOT NULL,
  diet_type TEXT NOT NULL,
  spice_level TEXT DEFAULT 'medium',
  protein_goal TEXT DEFAULT 'high',
  allergies TEXT[] DEFAULT '{}',
  disliked_ingredients TEXT[] DEFAULT '{}',
  loved_dishes TEXT[] DEFAULT '{}',
  cuisine_preferences TEXT[] DEFAULT '{}'
);

-- ── Disliked Dishes ─────────────────────────────────────────
CREATE TABLE disliked_dishes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  member_id UUID REFERENCES members(id) ON DELETE CASCADE,
  household_id UUID REFERENCES households(id),
  dish_name TEXT NOT NULL,
  reason TEXT,
  avoided_until DATE NOT NULL,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ── Standing Rules ──────────────────────────────────────────
CREATE TABLE standing_rules (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  household_id UUID REFERENCES households(id) ON DELETE CASCADE,
  rule_key TEXT NOT NULL,
  rule_value TEXT NOT NULL,
  confirmed BOOLEAN DEFAULT false,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ── Meal History ────────────────────────────────────────────
CREATE TABLE meal_history (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  household_id UUID REFERENCES households(id),
  meal_date DATE NOT NULL,
  meal_type TEXT NOT NULL,
  dish_name TEXT NOT NULL,
  diet_tag TEXT NOT NULL,
  rating TEXT,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ── Saved Recipes ───────────────────────────────────────────
CREATE TABLE saved_recipes (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  member_id UUID REFERENCES members(id),
  name TEXT NOT NULL,
  source_url TEXT,
  cuisine_type TEXT,
  diet_type TEXT,
  key_ingredients TEXT[],
  protein_level TEXT,
  added_on TIMESTAMPTZ DEFAULT NOW()
);

-- ── Active Plans ────────────────────────────────────────────
CREATE TABLE active_plans (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  household_id UUID REFERENCES households(id),
  week_start DATE NOT NULL,
  plan_text TEXT NOT NULL,
  plan_structured JSONB,
  created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ── Pattern Signals ─────────────────────────────────────────
CREATE TABLE pattern_signals (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  household_id UUID REFERENCES households(id),
  pattern_type TEXT NOT NULL,
  pattern_data JSONB NOT NULL,
  surfaced BOOLEAN DEFAULT false,
  confirmed BOOLEAN DEFAULT false,
  detected_at TIMESTAMPTZ DEFAULT NOW()
);

-- ── Indexes ─────────────────────────────────────────────────
CREATE INDEX idx_households_chat_id ON households(telegram_chat_id);
CREATE INDEX idx_members_household ON members(household_id);
CREATE INDEX idx_meal_history_household ON meal_history(household_id);
CREATE INDEX idx_meal_history_date ON meal_history(meal_date);
CREATE INDEX idx_disliked_dishes_until ON disliked_dishes(avoided_until);
CREATE INDEX idx_active_plans_household ON active_plans(household_id);
