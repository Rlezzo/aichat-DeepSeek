import json
import os
import random
from hoshino import logger

class ConfigManager:
    def __init__(self, config_file='group_config.json', options_file='options.json'):
        self.config_file = os.path.join(os.path.dirname(__file__), config_file)
        self.options_file = os.path.join(os.path.dirname(__file__), options_file)
        self._ensure_file_exists(self.config_file, self._create_default_config)
        self._ensure_file_exists(self.options_file, self._create_default_options)
        self.configs = self._load_json(self.config_file)
        self.options = self._load_json(self.options_file)

    def _ensure_file_exists(self, file_path, create_func):
        if not os.path.exists(file_path):
            create_func(file_path)

    def _create_default_config(self, file_path):
        self._save_json(file_path, {})

    def _create_default_options(self, file_path):
        default_options = {
            "api_providers": {
                "deepseek": {
                    "models": ["deepseek-chat","deepseek-coder"],
                    "api_keys": ["sk-b099xxxxxx", "sk-b001xxxxxx", "sk-b092xxxxxx"],
                    "base_url": "https://api.deepseek.com"
                },
                "openai": {
                    "models": ["gpt-3.5-turbo", "gpt-4-turbo", "gpt-4o"],
                    "api_keys": ["sk-xxxxxx", "sk-yyyyyy", "sk-zzzzzz"],
                    "base_url": "https://api.openai.com"
                }
            },
            "default_settings": {

                "record": True,
                "proxy": "http://127.0.0.1:7890",
                "proxy_on": False,
                "max_tokens": 512,
                "temperature": 1.0,
                "timeout": 30
            }
        }
        self._save_json(file_path, default_options)

    def _load_json(self, file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _save_json(self, file_path, data):
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def get_config(self, group_id):
        return self.configs.get(group_id, {})

    def set_config(self, group_id, config):
        self.configs[group_id] = config
        self._save_json(self.config_file, self.configs)

    def get_options(self):
        return self.options

    def apply_default_settings(self, config, provider):
        default_settings = self.options["default_settings"]
        for key in ["proxy", "proxy_on", "max_tokens", "record", "temperature", "timeout"]:
            config[key] = default_settings[key]

        provider_options = self.options["api_providers"][provider]
        config["base_url"] = provider_options["base_url"]
        config["api_key"] = random.choice(provider_options["api_keys"])
        config["api_provider"] = provider

        return config
    
    def set_record(self, group_id, record_status):
        config = self.get_config(group_id)
        config['record'] = record_status
        self.set_config(group_id, config)

    def update_models(self, provider, models):
        self.options["api_providers"][provider]["models"] = models
        self._save_json(self.options_file, self.options)
        
    def reload_config(self):
        self.configs = self._load_json(self.config_file)
        self.options = self._load_json(self.options_file)
