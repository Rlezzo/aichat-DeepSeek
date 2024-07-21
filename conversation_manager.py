import json
import asyncio
import os

class ConversationManager:
    def __init__(self, personas_file='personas.json', conversations_file='group_conversations.json', max_messages=10, max_tokens=10240, save_threshold=10): 
        self.personas_file = os.path.join(os.path.dirname(__file__), personas_file)
        self.conversations_file = os.path.join(os.path.dirname(__file__), conversations_file)
        self.ensure_files_exist()
        self.max_messages = max_messages # 最多几条对话
        self.max_tokens = max_tokens # 相当于最大字数
        self.save_threshold = save_threshold  # 批量保存的阈值，全体添加了几条信息后保存一次
        self.save_counter = 0  # 计数器
        self.personas = self.load_personas()
        self.group_conversations = self.load_group_conversations()
        self.save_lock = asyncio.Lock()
        self.processing_groups = set()  # 记录正在处理中的群组
        
    def ensure_files_exist(self):
        # 确保personas文件存在
        if not os.path.exists(self.personas_file):
            self.create_default_personas()
        # 确保conversations文件存在
        if not os.path.exists(self.conversations_file):
            self.create_default_group_conversations()

    def create_default_personas(self):
        personas = {
            "default": [{"role": "system", "content": "你是一个AI助手"}],
            "喵喵机": [{"role": "system", "content": "你是一只猫娘"}]
        }
        with open(self.personas_file, 'w', encoding='utf-8') as f:
            json.dump(personas, f, ensure_ascii=False, indent=2)

    def create_default_group_conversations(self):
        with open(self.conversations_file, 'w', encoding='utf-8') as f:
            json.dump({}, f, ensure_ascii=False, indent=2)

    def load_personas(self):
        with open(self.personas_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def load_group_conversations(self):
        with open(self.conversations_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def initialize_group(self, group_id, persona):
        if group_id not in self.group_conversations:
            self.group_conversations[group_id] = {
                "persona": persona,
                "messages": self.personas[persona].copy()
            }

    def get_messages(self, group_id, record=True):
        group_data = self.group_conversations.get(group_id, {})
        persona = group_data.get("persona", "default")
        if not record:
            # 如果关闭记忆，只使用人设
            return self.personas[persona].copy()
        self.initialize_group(group_id, persona)
        return self.group_conversations[group_id]["messages"]

    def add_message(self, group_id, role, content, record=True):
        if not record:
            return
        messages = self.get_messages(group_id)
        messages.append({"role": role, "content": content})
        
        # 清理过多的消息
        if len(messages) > self.max_messages:
            messages.pop(1)
        
        # 清理超出token限制的消息
        total_tokens = sum(len(msg['content']) for msg in messages)
        while total_tokens > self.max_tokens:
            messages.pop(1)
            total_tokens = sum(len(msg['content']) for msg in messages)
        
        # 增加计数器，每次添加消息后可能触发批量保存
        self.save_counter += 1
        if self.save_counter >= self.save_threshold:
            self.save_counter = 0
            asyncio.create_task(self.save_group_conversations())

    def set_persona(self, group_id, persona):
        self.group_conversations[group_id] = {
            "persona": persona,
            "messages": self.personas[persona].copy()
        }

    async def save_group_conversations(self):
        async with self.save_lock:
            with open(self.conversations_file, 'w', encoding='utf-8') as f:
                json.dump(self.group_conversations, f, ensure_ascii=False, indent=2)

    def add_persona(self, persona_name, messages):
        self.personas[persona_name] = messages
        self.save_personas()

    def remove_persona(self, persona_name):
        if persona_name not in self.personas:
            raise ValueError(f"人格 '{persona_name}' 不存在")
        del self.personas[persona_name]
        self.save_personas()
        
    def save_personas(self):
        with open(self.personas_file, 'w', encoding='utf-8') as f:
            json.dump(self.personas, f, ensure_ascii=False, indent=2)
                
    def reset_conversation(self, group_id):
        if group_id not in self.group_conversations:
            self.initialize_group(group_id, "default")
        persona = self.group_conversations[group_id]["persona"]
        if persona not in self.personas:
            persona = "default"
            self.group_conversations[group_id]["persona"] = persona
        self.group_conversations[group_id]["messages"] = self.personas[persona].copy()
        asyncio.create_task(self.save_group_conversations())
        
    def get_personas_list(self):
        return list(self.personas.keys())
    
    def delete_conversation(self, group_id, num_pairs):
        if group_id not in self.group_conversations:
            return
        messages = self.group_conversations[group_id]["messages"]
        num_to_delete = num_pairs * 2
        if num_to_delete >= len(messages) - 1:
            self.reset_conversation(group_id)
        else:
            del messages[-num_to_delete:]
            asyncio.create_task(self.save_group_conversations())
            
    def set_processing(self, group_id, processing=True):
        if processing:
            self.processing_groups.add(group_id)
        else:
            self.processing_groups.discard(group_id)

    def is_processing(self, group_id):
        return group_id in self.processing_groups
