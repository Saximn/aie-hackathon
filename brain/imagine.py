"""Optional visual memory card generator for learned skills.

Primary path: returns a markdown-formatted skill card (no external API needed).
Optional path: if OPENAI_API_KEY is available, attempts to generate a
Minecraft-style skill icon via DALL-E 3 and saves it to
``outputs/skill_cards/<skill_name>.png``.  If image generation fails for any
reason (missing key, quota exceeded, network error) the text card is returned
silently — no exception propagates to the caller.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path

LOG = logging.getLogger("omniplay.imagine")

_OUTPUT_DIR = Path("outputs") / "skill_cards"


class SkillCardGenerator:
    """Generates markdown skill cards with an optional DALL-E 3 icon."""

    def generate(self, skill_name: str, skill_description: str) -> str:
        """Return a markdown-formatted skill card.

        Always succeeds.  If an OpenAI API key is present an image icon is
        attempted; failures are logged at DEBUG level and the text card is
        returned regardless.

        Args:
            skill_name:        Short identifier for the skill (e.g. ``mine_wood``).
            skill_description: Human-readable description of what the skill does.

        Returns:
            A markdown string containing the skill card.
        """
        image_line = self._maybe_generate_image(skill_name, skill_description)
        card = f"## Skill: {skill_name}\n\n{skill_description}\n"
        if image_line:
            card += f"\n{image_line}\n"
        return card

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _maybe_generate_image(self, skill_name: str, skill_description: str) -> str:
        """Try to generate a skill icon; return markdown image tag or empty str."""
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            return ""
        try:
            return self._generate_image(skill_name, skill_description, api_key)
        except Exception as exc:  # noqa: BLE001
            LOG.debug("skill icon generation skipped for %r: %s", skill_name, exc)
            return ""

    def _generate_image(self, skill_name: str, skill_description: str, api_key: str) -> str:
        from openai import OpenAI  # lazy import — openai may not be installed

        client = OpenAI(api_key=api_key)
        prompt = (
            f"A Minecraft-style pixel art icon representing the skill '{skill_name}'. "
            f"Description: {skill_description}. "
            "Flat 2-D pixel art, 16x16 style, white background."
        )
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            n=1,
            response_format="url",
        )
        url = response.data[0].url
        if not url:
            return ""

        image_path = self._save_image(skill_name, url)
        if image_path:
            return f"![{skill_name} icon]({image_path})"
        return f"![{skill_name} icon]({url})"

    @staticmethod
    def _save_image(skill_name: str, url: str) -> str:
        """Download image to outputs/skill_cards/<name>.png; return local path or ''."""
        try:
            import urllib.request

            _OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
            dest = _OUTPUT_DIR / f"{skill_name}.png"
            urllib.request.urlretrieve(url, dest)  # noqa: S310
            return str(dest)
        except Exception as exc:  # noqa: BLE001
            LOG.debug("could not save skill icon for %r: %s", skill_name, exc)
            return ""


__all__ = ["SkillCardGenerator"]
