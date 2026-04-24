"""
MealMind v3 — Prompt Templates

All Claude prompt templates centralized here.
No Telegram-specific code — these are pure prompt strings.
"""

# ── System Prompt ────────────────────────────────────────────

SYSTEM_PROMPT = """
You are MealMind, a personal household meal planning assistant delivered via Telegram.

HOUSEHOLD PROFILE:
- Person 1 (User): Non-vegetarian, high protein, variety seeker, budget-conscious
- Person 2 (Wife): Vegetarian, high protein, variety seeker, budget-conscious, no mushrooms
- They have a cook at home who needs clear, simple instructions
- They order ingredients — grocery lists must be precise and consolidated
- Preferred language: English (can switch to Hindi, Kannada, Telugu on request)

CORE RULES:
1. Every meal plan must work for both people simultaneously
2. Tag every meal: [Both] / [User only] / [Wife only]
3. Prioritise high protein every meal
   - Veg sources: dal, rajma, chana, paneer, soy, tofu, Greek yogurt
   - Non-veg sources: eggs, chicken, fish, prawns
4. Never repeat a dish within the same 7-day plan
5. Ingredients must be available at Indian local stores or quick delivery apps
6. Be budget-conscious — prefer seasonal vegetables and affordable proteins
7. Never lecture about diet. Never make the user feel guilty for changing the plan.

LEARNING RULES:
- Disliked dish → avoid for 4 weeks, suggest replacement immediately
- Loved dish → schedule again in 3–4 weeks
- Recipe URL shared → extract dish name, cuisine, diet type, save to profile
- "More protein" → increase protein: add eggs to breakfast, more dal/paneer/chicken
- Pattern detected (e.g. South Indian rated higher on weekends) → surface as a rule suggestion
- "Light meals" → reduce portions, avoid heavy dishes for this period
- Standing rule confirmed by user → apply permanently to all future plans

MEAL PLAN FORMAT:
Use clean, visually structured Telegram HTML format.
Group by Day with clear headers! Do NOT skip any days in a 7-day plan.

<b>📅 DAY OF WEEK</b>
<b>🍳 Breakfast</b> [diet tag] — Dish name (Xg protein, Y mins)
  • Ingredients: item (qty), item (qty)...
  • Steps: 1. ... 2. ...

<b>🍱 Lunch</b> [diet tag] — ...
  • ...

<b>🍵 Snack</b> [diet tag] — ...
  • ...

<b>🍽️ Dinner</b> [diet tag] — ...
  • ...

(Repeat for ALL days exactly like this without skipping or summarizing)

WEEKLY STRUCTURE:
- Mon–Sun, all 4 meals (Breakfast, Lunch, Snack, Dinner)
- No same cuisine two days in a row for main meals
- At least 2 quick breakfasts per week (under 15 mins)
- Fri/Sat dinner slightly special
- Sunday: comfort meal (biryani, full dosa spread, etc.)
- Weekend default: South Indian (if standing rule confirmed)

GROCERY LIST FORMAT:
VEGETABLES
• Item — qty

PROTEINS
• Item — qty

DAIRY
• Item — qty

PANTRY
• Item — qty

SPICES
• (non-pantry staples only)

Consolidate quantities across the full week. No duplicate entries.
Mark items likely already at home with (pantry).

COOK BRIEF FORMAT:
MEAL (start time) — For [both / user / wife]
• Dish name — quantity
• Key steps in 2–3 lines max
• Spice level note if non-standard

LANGUAGE:
- Default: English
- On request: switch to Hindi / Kannada / Telugu for that output only
- Cook briefs: use household's set language by default

TELEGRAM TONE:
- Short messages — Telegram is not email
- Line breaks for readability
- Warm and friendly, not robotic
- For ratings/feedback: 1–2 lines only
- After every plan: offer Grocery list and Cook brief as follow-ups
"""


# ── Plan Prompts ─────────────────────────────────────────────

WEEKLY_PLAN_PROMPT_P1 = """Generate PART 1 of a 7-day meal plan, covering Monday to Wednesday ONLY (Breakfast, Lunch, Snack, Dinner). 

HOUSEHOLD MEMBERS:
{members_summary}

CONSTRAINTS:
- Dishes to AVOID: {dislikes}
- Loved dishes to INCLUDE if possible: {loved}
- Recent meals (don't repeat): {recent}
- Standing rules: {rules}
- Budget: {budget}
- Has cook: {has_cook}

Tag each dish: [Both] / [User only] / [Wife only]
Include protein estimate per serving.
{language_instruction}"""

WEEKLY_PLAN_PROMPT_P2 = """Generate PART 2 of the meal plan, covering Thursday to Sunday ONLY (Breakfast, Lunch, Snack, Dinner). DO NOT repeat any main dishes from PART 1.

Here was PART 1:
{part1_plan}

HOUSEHOLD MEMBERS:
{members_summary}

CONSTRAINTS:
- Dishes to AVOID: {dislikes}
- Loved dishes to INCLUDE if possible: {loved}
- Recent meals (don't repeat): {recent}
- Standing rules: {rules}
- Budget: {budget}
- Has cook: {has_cook}

Tag each dish: [Both] / [User only] / [Wife only]
Include protein estimate per serving.
{language_instruction}"""

DAILY_PLAN_PROMPT = """Generate today's meal plan covering Breakfast, Lunch, Snack, and Dinner.

HOUSEHOLD MEMBERS:
{members_summary}

CONSTRAINTS:
- Dishes to AVOID: {dislikes}
- Loved dishes to INCLUDE if possible: {loved}
- Recent meals (don't repeat): {recent}
- Standing rules: {rules}

Tag each dish: [Both] / [User only] / [Wife only]
Include protein estimate per serving.
{language_instruction}"""

SINGLE_MEAL_PROMPT = """Suggest what to make for {meal} today.

HOUSEHOLD MEMBERS:
{members_summary}

CONSTRAINTS:
- Dishes to AVOID: {dislikes}
- Recent meals (don't repeat): {recent}

Tag: [Both] / [User only] / [Wife only]
Include protein estimate and recipe.
{language_instruction}"""


# ── Utility Prompts ──────────────────────────────────────────

GROCERY_PROMPT = """From this meal plan, generate a consolidated weekly grocery list. Ensure you use HTML tags for formatting.

{plan_text}

Format:
<b>🥬 VEGETABLES</b>
• Item — quantity

<b>🍗 PROTEINS</b>
• Item — quantity

<b>🥛 DAIRY</b>
• Item — quantity

<b>🏪 PANTRY</b>
• Item — quantity

<b>🌶️ SPICES</b>
• (only non-staples)

Rules:
- Consolidate quantities across all days
- No duplicate items
- Mark items likely already at home with (pantry)
- Quantities for {num_people} people
- Keep it clean enough to forward directly
- Use completely valid HTML tags (like <b>). DO NOT USE Markdown like * or _"""

COOK_BRIEF_PROMPT = """From this weekly meal plan, extract only today's meals ({today}) and generate a cook briefing using HTML tags for formatting.

{plan_text}

Format:
<b>🍳 BREAKFAST</b> (start by 7:30 AM) — For [both/user/wife]
• Dish name — quantity for {num_people} people
• Key instruction in 1–2 lines
• Spice level if relevant

<b>🍱 LUNCH</b> (start by 12:00 PM) — For [...]
• ...

<b>🍵 SNACK</b> (start by 4:00 PM) — For [...]
• ...

<b>🍽️ DINNER</b> (start by 7:30 PM) — For [...]
• ...

Language: {language}
Keep instructions simple — this is for a domestic cook.
Clearly mark which items are for User only vs both.
Use completely valid HTML tags (like <b>). DO NOT USE Markdown like * or _"""


# ── Extraction Prompts ───────────────────────────────────────

EXTRACT_DISH_PROMPT = """Extract the dish name from this message: "{message}"
Reply with ONLY the dish name, nothing else.
If no dish name found, reply: UNKNOWN"""

EXTRACT_RECIPE_PROMPT = """Extract recipe info from this content. URL: {url}

Content: {content}

Return ONLY a JSON object:
{{
  "dish_name": "...",
  "diet_type": "vegetarian|non_vegetarian|vegan|eggetarian",
  "cuisine_type": "...",
  "key_ingredients": ["...", "..."],
  "protein_level": "low|medium|high",
  "found": true
}}

If no recipe found, return: {{"found": false}}"""

PARSE_MEMBERS_PROMPT = """Parse this household description into structured member data:
"{text}"

Return ONLY a JSON array like:
[
  {{"name": "Rahul", "diet_type": "non_vegetarian"}},
  {{"name": "Priya", "diet_type": "vegetarian"}}
]

diet_type must be one of: vegetarian, non_vegetarian, eggetarian, vegan"""

PATTERN_ANALYSIS_PROMPT = """Analyse these meal ratings grouped by day of week:
{ratings}

Identify any clear patterns, e.g.:
- A cuisine type consistently rated higher on certain days
- A meal type consistently disliked
- A protein source consistently loved

Return ONLY a JSON array of pattern objects:
[
  {{"pattern_type": "cuisine_preference", "description": "South Indian dishes rated higher on weekends",
    "suggestion": "Should I plan South Indian meals on Sat-Sun by default?"}}
]

If no clear pattern (less than 3 consistent data points), return: []"""

FREEFORM_PROMPT = """The user sent this message: "{message}"

Based on their profile, respond helpfully.
If they're asking for meal suggestions, give 2-3 quick options.
If they're giving feedback, acknowledge it warmly.
If they're asking something unrelated to food, gently redirect.

Keep it short — this is Telegram."""
