"""Central configuration for the academy."""

import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()  # picks up ANTHROPIC_API_KEY from a local .env if present

MODEL_NAME = os.getenv("ACADEMY_MODEL", "claude-opus-4-8")

# Room for a full lesson in one response.
MAX_TOKENS = 8192

# Language the lessons and quizzes are written in.
LANGUAGE = os.getenv("ACADEMY_LANGUAGE", "English")

# How many concepts the planner puts in a session's syllabus.
NUM_CONCEPTS = int(os.getenv("ACADEMY_CONCEPTS", "3"))

# Quiz questions per concept.
NUM_QUESTIONS = 3

# How many times the teacher may re-explain a concept the coach judged unmastered.
MAX_REMEDIATIONS = 1

# Where lesson notes are saved as markdown (your personal study notebook).
NOTES_DIR = Path(os.getenv("ACADEMY_NOTES", "notes"))
