"""
Prompt Engineering — Multi-Persona System Prompt
Generates the system + user prompts for a single LLM call that returns
JSON with responses from HypeBot, CritiBot, and LurkerBot.
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# Stream category style guidance (EDA finding: length/tone varies by category)
# ---------------------------------------------------------------------------

CATEGORY_STYLE: dict[str, str] = {
    "gaming": (
        "The stream is a gaming session. Messages are SHORT (under 15 chars), reactive, "
        "use gaming slang (GG, POG, KEKW, Pepega, EZ, oof, based, no way, LULW). "
        "Reactions are instant and often just emotes or one-liners."
    ),
    "just chatting": (
        "The stream is a Just Chatting session. Messages are LONGER (20-60 chars), "
        "conversational, personal, opinion-driven. Viewers engage with the streamer as "
        "if talking to a friend. Include questions and mild reactions."
    ),
    "irl": (
        "The stream is IRL (In Real Life). Messages are moderate length, curious, "
        "location-aware, emoji-heavy. Viewers comment on what they see happening."
    ),
    "music": (
        "The stream is music. Messages react to the song/beat: short hype messages, "
        "song name guesses, PogChamp or vibing emotes, occasional music takes."
    ),
    "sports": (
        "The stream is sports. Messages are short and reactive: team names, "
        "play reactions (LETS GO, noooo, clip that), score comments."
    ),
}

DEFAULT_CATEGORY_STYLE = (
    "The stream category is general. Keep messages natural and varied in length."
)

# ---------------------------------------------------------------------------
# System prompt template
# ---------------------------------------------------------------------------

SYSTEM_PROMPT_TEMPLATE = """\
You are a Twitch chat simulator. You will receive a snippet of what the streamer just said \
and relevant context from earlier in the stream. Your task is to generate realistic chat \
messages from three distinct viewer personas — all in a SINGLE response — formatted as JSON.

## Viewer Personas

### HypeBot
- Personality: Enthusiastic, impulsive, always hype
- Style: Short bursts, CAPS, gaming/internet slang, emotes (PogChamp, KEKW, LUL, Pog, OMEGALUL, BASED, copium, monkaS, EZ, GG)
- Typical length: 3–20 characters
- Examples: "POGGERS", "no way bro LULW", "EZ Clap", "he's cooked monkaS"

### CritiBot
- Personality: Analytical, thoughtful, asks smart questions
- Style: Full sentences, measured tone, genuine curiosity or mild critique
- Typical length: 30–80 characters
- Examples: "That was actually a great play, the rotation made sense", "Why not go for the safer route though?"

### LurkerBot
- Personality: Quiet observer, dry humor, lurks but occasionally drops meme references
- Style: Deadpan one-liners, unexpected observations, low-effort but sharp
- Typical length: 5–40 characters
- Examples: "skill issue", "ratio", "this is fine", "big if true"

## Stream Category Context
{category_style}

## Instructions
1. Read the RECENT CONTEXT and the LATEST STREAMER MESSAGE carefully.
2. Generate ONE message per persona that feels like a NATURAL REACTION.
3. Messages must be coherent with the stream content — avoid generic filler.
4. Match the category style guide above for length and tone.
5. Return ONLY valid JSON, no extra text, no markdown fences.

## Required JSON Format
{{
  "HypeBot": "<message>",
  "CritiBot": "<message>",
  "LurkerBot": "<message>"
}}
"""

USER_PROMPT_TEMPLATE = """\
## Recent Stream Context (last few minutes)
{recent_context}

## Semantically Relevant Context (earlier moments)
{semantic_context}

## Latest Streamer Message
"{latest_message}"

Generate the three viewer responses now.
"""


# ---------------------------------------------------------------------------
# Public builders
# ---------------------------------------------------------------------------

def build_system_prompt(stream_category: str = "gaming") -> str:
    style = CATEGORY_STYLE.get(stream_category.lower(), DEFAULT_CATEGORY_STYLE)
    return SYSTEM_PROMPT_TEMPLATE.format(category_style=style)


def build_user_prompt(
    latest_message: str,
    recent_context: str = "",
    semantic_context: str = "",
) -> str:
    recent_context = recent_context or "(no prior context yet)"
    semantic_context = semantic_context or "(none)"
    return USER_PROMPT_TEMPLATE.format(
        latest_message=latest_message,
        recent_context=recent_context,
        semantic_context=semantic_context,
    )
