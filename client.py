import base64
import os
from openai import AsyncOpenAI

class Client:
    client = AsyncOpenAI(api_key="", base_url="https://api.deepseek.com")
    model: str = "deepseek-chat"
    conversation: str = ""
    messages: list = []
    max_tokens: int = 4096
    
    def __init__(self, api_key="", base_url="https://api.deepseek.com", model="deepseek-chat", max_tokens=4096):
        self.client.api_key = api_key

        if base_url.strip() != "":
            self.client.base_url = base_url
        self.model = model
        self.max_tokens = max_tokens
        self.conversation = "default"
        self.messages = [
            {"role": "system", "content": "你是一个AI助手"},
        ]
        
    def load_conversation(self, conversation, message):
        self.conversation = conversation
        self.messages = message

    async def send(self, message, record=True):
        self.messages.append({"role": "user", "content": message})
        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=self.messages,
                max_tokens=self.max_tokens,
                timeout=30,
                stream=False
            )
            if response.choices[0].finish_reason == "content_filter":
                self.messages = self.messages[:-1]
                return "由于敏感内容被过滤，未返回消息"
            msg = response.choices[0].message.content.strip()
            if msg and record:
                self.messages.append({"role": "assistant", "content": msg})
            else:
                self.messages = self.messages[:-1]

            #token过长删除最早两条对话
            if response.usage.total_tokens > 3800 - self.max_tokens:
                del self.messages[1:5]
            return msg.strip()
        except Exception as e:
            self.messages = self.messages[:-1]
            if "This model's maximum context length is" in str(e):
                del self.messages[1:5]
                return "对话过长，已删除部分对话"
            if "Rate limit reached for" in str(e):
                return "API请求过于频繁，请稍后再试"
            if "You exceeded your current quota" in str(e):
                return f"api key({openai.api_key[0:len(openai.api_key)-8]}********)配额已用完，请更换api key"
            return f"发生错误: {str(e).strip()}"
