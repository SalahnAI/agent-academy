"""Central configuration for the academy."""

import os
from pathlib import Path

MODEL_NAME = os.getenv("ACADEMY_MODEL", "qwen3:8b")
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")

TEMPERATURE = 0.4

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
