from openai import OpenAI


class DeepSeekClient:
    """DeepSeek API wrapper using OpenAI-compatible SDK."""

    BASE_URL = "https://api.deepseek.com/v1"

    def __init__(self, api_key: str, model: str = "deepseek-chat"):
        self._api_key = api_key
        self._model = model
        self._client = None
        if api_key:
            self._client = OpenAI(api_key=api_key, base_url=self.BASE_URL)

    @property
    def is_configured(self):
        return self._client is not None

    def update_config(self, api_key: str, model: str = "deepseek-chat"):
        self._api_key = api_key
        self._model = model
        self._client = OpenAI(api_key=api_key, base_url=self.BASE_URL) if api_key else None

    def chat(self, system_prompt: str, user_prompt: str, temperature: float = 0.7) -> str:
        if not self._client:
            raise RuntimeError("DeepSeek client not configured. Please set API Key in settings.")
        response = self._client.chat.completions.create(
            model=self._model,
            temperature=temperature,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        return response.choices[0].message.content
