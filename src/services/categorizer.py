from src.api.deepseek_client import DeepSeekClient
from src.config_loader import config

SYSTEM_PROMPT = """You are a prompt analysis assistant. Given a user's prompt, do two things:

1. CATEGORY: Classify the prompt into the most appropriate category.
2. TITLE: Generate a concise title (max 15 characters) that captures the essence of the prompt.

Return your response in EXACTLY this one-line-per-tag format:
[TITLE] <concise title>
[CATEGORY] <category name>

Category rules:
- If the prompt fits one of the given categories, use that exact category name.
- If none match well, suggest a new concise category name (2-4 characters)."""


class Categorizer:
    def __init__(self, client: DeepSeekClient):
        self._client = client

    def classify(self, prompt_text: str) -> tuple[str, str]:
        """Returns (title, category)."""
        categories = config.categories
        cat_list = "、".join(categories)
        user_msg = f"Available categories: {cat_list}\n\nPrompt:\n{prompt_text}"
        result = self._client.chat(SYSTEM_PROMPT, user_msg, temperature=0.3)
        title, category = self._parse(result)
        if not title:
            title = prompt_text[:40].replace("\n", " ").strip()
        if not category:
            category = "其他"
        return title, category

    def _parse(self, response: str) -> tuple[str, str]:
        title = ""
        category = ""
        current_section = None
        for line in response.strip().split("\n"):
            line = line.strip()
            if not line:
                continue
            if line.startswith("[TITLE]"):
                current_section = "title"
                val = line.replace("[TITLE]", "").strip()
                if val:
                    title = val
            elif line.startswith("[CATEGORY]"):
                current_section = "category"
                val = line.replace("[CATEGORY]", "").strip()
                if val:
                    category = val
            elif current_section == "title" and not title:
                title = line
            elif current_section == "category" and not category:
                category = line
        return title, category
