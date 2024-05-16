import configparser
import json
import os

class Config:
    _config = configparser.ConfigParser()
    api_keys: list = []  # API keys
    model: str = "deepseek-chat"  # 模型
    record: bool = True  # 是否记录对话
    conversations: dict = {}  # 会话列表
    groups: dict = {}  # 群组列表
    interval: int = 5  # 存档间隔
    max_tokens: int = 4096  # 最大字符数
    base_url: str = ""

    def __init__(self):
        config_path = os.path.join(os.path.dirname(__file__), 'config.ini')
        self._config.read(config_path, encoding='utf-8')
        self.load_conversations()
        api_keys = self._config.get("OPTION", "api_key", fallback="")
        self.api_keys = [key.strip() for key in api_keys.split(",") if key.strip()]
        self.model = self._config.get("OPTION", "model", fallback="deepseek-chat")
        self.record = self._config.getboolean("OPTION", "record", fallback=True)
        self.interval = self._config.getint("OPTION", "interval", fallback=5)
        self.max_tokens = self._config.getint("OPTION", "max_tokens", fallback=1000)
        self.base_url = self._config.get("OPTION", "base_url", fallback="https://api.deepseek.com")

        if not self._config.has_section("GROUP"):
            self._config.add_section("GROUP")
        for group, conversation in self._config.items("GROUP"):
            self.groups[group] = conversation if conversation in self.conversations else "default"

    def save_conversations(self):
        with open(os.path.join(os.path.dirname(__file__), 'conversations.json'), 'w', encoding='utf-8') as f:
            json.dump(self.conversations, f, ensure_ascii=False, indent=4)

    def load_conversations(self):
        conversations_path = os.path.join(os.path.dirname(__file__), 'conversations.json')
        if os.path.exists(conversations_path):
            with open(conversations_path, 'r', encoding='utf-8') as f:
                self.conversations = json.load(f)
        else:
            self.conversations = {}

    def save_config(self):
        if not self._config.has_section("OPTION"):
            self._config.add_section("OPTION")
        self._config.set("OPTION", "api_key", ",".join(self.api_keys))
        self._config.set("OPTION", "model", self.model)
        self._config.set("OPTION", "record", str(self.record).lower())
        self._config.set("OPTION", "interval", str(self.interval))
        self._config.set("OPTION", "max_tokens", str(self.max_tokens))
        self._config.set("OPTION", "base_url", self.base_url)

        for group, conversation in self.groups.items():
            self._config.set("GROUP", group, conversation if conversation in self.conversations else "default")
        config_path = os.path.join(os.path.dirname(__file__), 'config.ini')
        with open(config_path, 'w', encoding='utf-8') as f:
            self._config.write(f)
