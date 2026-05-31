from src.api.deepseek_client import DeepSeekClient

SYSTEM_PROMPT = """You are a prompt optimization expert. Improve the user's prompt for better clarity, specificity, and effectiveness.

Return your response EXACTLY in this format, with these exact headers:

[OPTIMIZED]
<the full optimized prompt text>

[NOTES]
<2-3 brief bullet points explaining what was improved and why>"""


class Optimizer:
    def __init__(self, client: DeepSeekClient):
        self._client = client

    def optimize(self, prompt_text: str) -> tuple[str, str]:
        """Returns (optimized_text, optimization_notes)."""
        response = self._client.chat(SYSTEM_PROMPT, prompt_text, temperature=0.7)
        optimized, notes = self._parse_response(response)
        return optimized, notes

    def _parse_response(self, response: str) -> tuple[str, str]:
        optimized = ""
        notes = ""
        if "[OPTIMIZED]" in response and "[NOTES]" in response:
            parts = response.split("[NOTES]")
            optimized = parts[0].replace("[OPTIMIZED]", "").strip()
            notes = parts[1].strip()
        else:
            optimized = response
            notes = ""
        return optimized, notes
