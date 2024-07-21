import re
from hoshino import Service, logger, priv
from hoshino.typing import CQEvent
from nonebot.message import Message
from .conversation_manager import ConversationManager
from .config_manager import ConfigManager
from .client_manager import ClientManager

help_text = """1. `添加人格/设置人格+人格名+空格+设定`: 创建新人格或修改现有人格，注意人格名不能大于24位
2. `人格列表`: 获取当前所有人格及当前人格
3. `切换人格+人格名`: 切换到对应人格，不填则使用默认人格
4. `/t+消息或@bot+消息`: 进行对话
5. `重置人格/重置会话+人格名`: 重置当前人格/会话记忆
6. `删除人格+人格名`: 删除人格选项
7. `对话记忆+开/关`: 开启/关闭对话记忆
8. `删除对话+条数N`: 删除倒数N对对话，一问一答
9. `ai配置重载/重载配置`: 重新加载配置文件，手动更新配置文件后用
10.`查询模型/模型列表` 查看api所用模型
11.`切换模型` 切换api所用模型
"""

sv = Service('aichat', enable_on_default=True, help_=help_text)

# 最多保存几条消息，最多保存多少字(token)，几条消息保存一次(写到json文件)
conversation_manager = ConversationManager(max_messages=10, max_tokens=10240, save_threshold=10)
config_manager = ConfigManager()
client_manager = ClientManager()

black_word = ['今天我是什么少女', 'ba来一井']  # 如果有不想触发的词可以填在这里

# 通过@机器人+问题触发，不需要可以注释掉
@sv.on_message('group')
async def ai_reply(bot, ev: CQEvent):
    msg = str(ev['message'])
    if msg.startswith(f'[CQ:at,qq={ev["self_id"]}]') or msg.endswith(f'[CQ:at,qq={ev["self_id"]}]'):
        text = re.sub(r'\[CQ:at,qq=\d+\]', '', msg).strip()
        ev.message = Message(text)
        await ai_reply_prefix(bot, ev)

# 测试对话+问题，和AI聊天
@sv.on_prefix('/t')
async def ai_reply_prefix(bot, ev: CQEvent):
    group_id = str(ev.group_id)
    if conversation_manager.is_processing(group_id):
        await bot.send(ev, "等待回复中，请稍后再对话")
        return
    conversation_manager.set_processing(group_id, True)
    
    text = str(ev.message.extract_plain_text()).strip()
    if text == '' or text in black_word:
        return
    try:
        config = config_manager.get_config(group_id)
        if not config:
            config = config_manager.apply_default_settings({}, 'deepseek')  # 默认使用deepseek
            config['model'] = 'deepseek-chat'  # 默认模型
            config_manager.set_config(group_id, config)

        msg = await get_chat_response(group_id, text, config)
        if msg:
            await bot.send(ev, msg)
    except Exception as err:
        logger.error(f"Error during AI response: {err}")
        await bot.send(ev, f"发生错误: {err}")
    finally:
        conversation_manager.set_processing(group_id, False)

async def get_chat_response(group_id, text, config):
    record = config.get("record", True)
    messages = conversation_manager.get_messages(group_id, record)
    
    # 将用户的问题临时添加到消息中
    messages.append({"role": "user", "content": text})
    
    # 获取同配置的客户端
    client = client_manager.get_client(config)
    try:
        response = await client.chat.completions.create(
            model=config["model"],
            messages=messages,
            stream=False,
            max_tokens=config["max_tokens"],
            temperature=config["temperature"],
            timeout=config["timeout"]
        )
        reply = response.choices[0].message.content.strip()
        if record:
            # 开启记忆就保存一对对话
            conversation_manager.add_message(group_id, "user", text)
            conversation_manager.add_message(group_id, "assistant", reply)
        return reply
    except Exception as e:
        messages.pop()
        logger.error(f"Error in get_chat_response: {e}")
        err = str(e) if len(str(e)) < 133 else str(e)[:133]
        return f"发生错误: {err}"

@sv.on_prefix('切换人格')
async def change_persona(bot, ev: CQEvent):
    group_id = str(ev.group_id)
    persona = str(ev.message.extract_plain_text()).strip()
    if persona:
        if persona in conversation_manager.personas:
            conversation_manager.set_persona(group_id, persona)
            await bot.send(ev, f"已切换人格为：{persona}")
        else:
            await bot.send(ev, f"人格 '{persona}' 不存在")
    else:
        conversation_manager.set_persona(group_id, "default")
        await bot.send(ev, "已重置为default人格")
        
@sv.on_fullmatch(('重置会话', '重置人格'))
async def reset_conversation_prefix(bot, ev: CQEvent):
    group_id = str(ev.group_id)
    conversation_manager.reset_conversation(group_id)
    await bot.send(ev, "会话已重置")

@sv.on_fullmatch('人格列表')
async def get_personas_list_prefix(bot, ev: CQEvent):
    group_id = str(ev.group_id)
    current_persona = conversation_manager.group_conversations.get(group_id, {}).get("persona", "default")
    personas_list = conversation_manager.get_personas_list()
    await bot.send(ev, f"本群当前人格：{current_persona}\n可用人格：{', '.join(personas_list)}")

@sv.on_prefix(('添加人格', '设置人格'))
async def add_persona_prefix(bot, ev: CQEvent):
    args = str(ev.message.extract_plain_text()).strip().split(maxsplit=1)
    if len(args) < 2:
        await bot.send(ev, "用法：添加人格 <人格名> <人设信息>")
        return
    persona_name, initial_message = args
    if len(persona_name) > 24:
        await bot.send(ev, "人格名过长")
        return
    conversation_manager.add_persona(persona_name, [{"role": "system", "content": initial_message}])
    await bot.send(ev, f"人格 '{persona_name}' 添加成功")

@sv.on_prefix('删除人格')
async def remove_persona_prefix(bot, ev: CQEvent):
    # if user_id not in hoshino.config.SUPERUSERS:
    #     await bot.send(ev,"该功能仅限bot管理员使用")
    #     return
    # 判断权限，只有用户为群管理员或为bot设置的超级管理员才能使用
    u_priv = priv.get_user_priv(ev)
    if u_priv < sv.manage_priv:
        await bot.send(ev,"该功能仅限群管理员或为bot设置的超级管理员使用")
        return
    persona_name = str(ev.message.extract_plain_text()).strip()
    group_id = str(ev.group_id)
    if not persona_name:
        await bot.send(ev, "用法：删除人格 <人格名>")
        return
    try:
        current_persona = conversation_manager.group_conversations.get(group_id, {}).get("persona", "default")
        conversation_manager.remove_persona(persona_name)
        if current_persona == persona_name:
            conversation_manager.set_persona(group_id, "default")
        await bot.send(ev, f"人格 '{persona_name}' 删除成功")
    except ValueError as e:
        await bot.send(ev, str(e))

@sv.on_prefix('删除对话')
async def delete_conversation(bot, ev: CQEvent):
    group_id = str(ev.group_id)
    try:
        num_pairs = int(str(ev.message.extract_plain_text()).strip())
        if num_pairs <= 0:
            await bot.send(ev, "请输入大于0的数字")
            return
        conversation_manager.delete_conversation(group_id, num_pairs)
        await bot.send(ev, f"已删除本群的最近 {num_pairs} 对对话")
    except ValueError:
        await bot.send(ev, "请输入有效的数字")
        
@sv.on_prefix('对话记忆')
async def set_record(bot, ev: CQEvent):
    group_id = str(ev.group_id)
    text = str(ev.message.extract_plain_text()).strip().lower()
    if text in ['开启', '开', 'on', '启用']:
        config_manager.set_record(group_id, True)
        await bot.send(ev, f"本群的对话记忆已开启")
    elif text in ['关闭', '关', 'off', '禁用']:
        config_manager.set_record(group_id, False)
        await bot.send(ev, f"本群的对话记忆已关闭")
    else:
        await bot.send(ev, "用法：对话记忆 开启/关闭 或 开/关 或 on/off 或 启用/禁用")

@sv.on_fullmatch(('查询模型', '模型列表'))
async def query_models(bot, ev: CQEvent):
    group_id = str(ev.group_id)
    config = config_manager.get_config(group_id)
    client = client_manager.get_client(config)

    try:
        available_models = await fetch_and_get_models(client)
        config_manager.update_models(config["api_provider"], available_models)
    except Exception as e:
        logger.error(f"Error fetching models: {e}")
        await bot.send(ev, "更新模型列表失败")
        return

    if not available_models:
        await bot.send(ev, "获取模型列表失败")
        return

    model_list = ', '.join(available_models)
    await bot.send(ev, f"当前可用的模型有：{model_list}")
    
@sv.on_prefix('切换模型')
async def switch_model(bot, ev: CQEvent):
    group_id = str(ev.group_id)
    model_name = str(ev.message.extract_plain_text()).strip()
    config = config_manager.get_config(group_id)
    provider = config["api_provider"]
    available_models = config_manager.get_options()["api_providers"][provider]["models"]

    if not model_name or model_name not in available_models:
        model_list = ', '.join(available_models)
        await bot.send(ev, f"当前可用的模型有：{model_list}")
    else:
        config['model'] = model_name
        config_manager.set_config(group_id, config)
        await bot.send(ev, f"模型已切换为：{model_name}")

@sv.on_fullmatch(('重载配置','ai配置重载'))
async def reload_config(bot, ev: CQEvent):
    config_manager.reload_config()
    await bot.send(ev, "配置已重载")
    
# 获取deepseek模型列表
async def fetch_and_get_models(client):
    model_ids = []
    models_paginator = client.models.list()
    async for model in models_paginator:
        model_ids.append(model.id)
    return model_ids
