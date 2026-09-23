"""Settings: Notion data source IDs, personal constants and goals."""

# Notion data source IDs (collection://...) in the Health Hub
DATA_SOURCES = {
    "fitness": "06c99d47-9eda-4d74-bc0b-642af21990d8",
    "lichaam": "8687299a-5ff9-4a24-b9af-faec94eb9e45",
    "slaap": "18059be9-4efc-4c32-a800-160a762d2e58",
    "activiteit": "7f7c2dcf-501b-4e9c-945c-32fc3d2d19c4",
}
NOTION_VERSION = "2025-09-03"

NAME = "Permata"
HEIGHT_M = 1.58
TIMEZONE = "Europe/Amsterdam"

# The dashboard ignores everything logged before this date (older rows stay in Notion)
START_DATE = "2026-09-23"

# Daily ring goals (Apple Watch)
GOAL_MOVE_KCAL = 500
GOAL_EXERCISE_MIN = 50
GOAL_STAND_HRS = 12
GOAL_STEPS = 10000

# Training + sleep goals
GOAL_SESSIONS_WEEK = 5
GOAL_SLEEP_HOURS = 8.0
GOAL_SLEEP_MIN_NIGHT = 7.0   # a "good night" for the monthly goal

# Fixed orders
FOCUS_ORDER = ["Glutes & Quads", "Back & Biceps", "Shoulders Chest & Triceps", "Cardio"]
INTENSITEIT_VOLGORDE = ["Low", "Medium", "High", "Max"]
DAYS_EN = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

# Sport -> (tone, icon) from the design system
SPORT_STYLE = {
    "Gym": ("move", "strength"),
    "Reformer Pilates": ("sleep", "yoga"),
    "Kickboxing": ("exercise", "heart"),
    "Kickboksen": ("exercise", "heart"),
    "Cardio": ("stand", "run"),
}
