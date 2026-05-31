import json
import os

CONFIG_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "config.json")

DEFAULT_CONFIG = {
    "api_key": "",
    "model": "deepseek-chat",
    "enable_optimization": True,
    "enable_autostart": False,
    "font_family": "Microsoft YaHei",
}


class Config:
    """Manages config.json read/write."""

    def __init__(self):
        self._data = {}
        self.load()

    def load(self):
        if os.path.exists(CONFIG_PATH):
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                self._data = json.load(f)
        else:
            self._data = dict(DEFAULT_CONFIG)
            self.save()

    def save(self):
        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(self._data, f, ensure_ascii=False, indent=4)

    def get(self, key, default=None):
        return self._data.get(key, default)

    def set(self, key, value):
        self._data[key] = value
        self.save()

    @property
    def api_key(self):
        return self._data.get("api_key", "")

    @property
    def model(self):
        return self._data.get("model", "deepseek-chat")

    @property
    def enable_optimization(self):
        return self._data.get("enable_optimization", True)

    @property
    def enable_autostart(self):
        return self._data.get("enable_autostart", False)

    @property
    def font_family(self):
        return self._data.get("font_family", "Microsoft YaHei")


# Global config instance
config = Config()
