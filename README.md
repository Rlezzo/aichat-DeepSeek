> #### https://github.com/Cosmos01/aichat-chatGPT/tree/main的重制
> #### 发现一个国产AI:[DeepSeek](https://www.deepseek.com/)看上去很强很便宜，但是旧插件没法直接用了
> #### 旧版本用的openai0.28，现在openai1.35，之前的修改版记忆功能有问题，就重写了
> #### 注册白嫖5百万tokens(一个月期限)
------
  
# aichat
  
姑且添加了openai的支持，但是没有key，没有试过，只用deepseek挂代理试了一下可以用。没怎么经过测试，可能有bug
  
## 命令
1. `添加人格/设置人格+人格名+空格+设定`: 创建新人格或修改现有人格，注意人格名不能大于24位
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
  
  
## 安装方法
1. 在HoshinoBot的插件目录modules下clone**分支**remake
   
`git clone -b remake https://github.com/Rlezzo/aichat-DeepSeek.git aichat`

2. 安装必要第三方库：`pip install openai`（当前是1.35版本）
3. 在 `config/__bot__.py`的MODULES_ON列表里加入 `aichat`
4. 重启HoshinoBot
5. 插件默认启用
6. 填写配置文件

## 配置参数
程序会自动生成4个json文件
- options.json
```
{
  "api_providers": {
    "deepseek": { # api提供商
      "models": [ # 模型列表
        "deepseek-chat",
        "deepseek-coder"
      ],
      "api_keys": [ # 多个key从中随机选择
        "sk-b099xxxxxx",
        "sk-b001xxxxxx",
        "sk-b092xxxxxx"
      ],
      "base_url": "https://api.deepseek.com" # api地址
    },
    "openai": {
      "models": [
        "gpt-3.5-turbo",
        "gpt-4-turbo",
        "gpt-4o"
      ],
      "api_keys": [
        "sk-xxxxxx",
        "sk-yyyyyy",
        "sk-zzzzzz"
      ],
      "base_url": "https://api.openai.com"
    }
  },
  "default_settings": { # 群配置的默认模板
    "record": true, # 默认开启记忆
    "proxy": "http://127.0.0.1:7890", # 挂代理的地址
    "proxy_on": false, # 是否开启代理，默认关闭
    "max_tokens": 512, # ai返回的字数限制
    "temperature": 1.0, # 参考api文档，如deepseek的：代码生成/数学解题  0.0，数据抽取/分析	0.7， 通用对话	 1.0， 翻译 	1.1， 创意类写作/诗歌创作	1.25
    "timeout": 30 # 多久没返回消息视为超时
  }
}
```
- group_config.json
最开始是空的，在群里使用过以后会有内容，可以为每个群单独设置
```
{
  "111111111": { # 对应的群号
    "proxy": "http://127.0.0.1:7890", # 这个群用的代理地址
    "proxy_on": false, # 如果用了gpt4o之类的，需要开启代理
    "max_tokens": 512, # 返回的最大token
    "record": true, # 是否开启记忆
    "temperature": 1.0, # 上面有详细解释
    "timeout": 30, # 超时时间
    "base_url": "https://api.deepseek.com", # api地址
    "api_key": "sk-b092xxxxxx", # 从options.json里随机找的key，可以手动修改
    "api_provider": "deepseek", # api提供商
    "model": "deepseek-chat" # 选择的模型
  },
  "922222222": {
    "proxy": "http://127.0.0.1:7890",
    "proxy_on": false,
    "max_tokens": 512,
    "record": true,
    "temperature": 1.0,
    "timeout": 30,
    "base_url": "https://api.deepseek.com",
    "api_key": "sk-b092xxxxxx",
    "api_provider": "deepseek",
    "model": "deepseek-chat"
  }
}
```
- personas.json
人格，可以用命令加也可以手动添加，然后重启bot加载
```
{
  "default": [
    {
      "role": "system",
      "content": "你是一个AI助手"
    }
  ],
  "喵喵机": [
    {
      "role": "system",
      "content": "请你记住，现在开始你是一个非常可爱的猫娘"
    }
  ]
}
```
- group_conversations.json
> 保存的历史对话，一般不用管
- 可以自行修改的地方
`__init__.py`
所有群通用的，最多保存10条消息，就是5对问答，之后会删除最早的一条消息。

5次以内的问答，如果超过10240个字，也会删除最早的消息，可以自行修改，每次对话其实就是把历史记录都发送给AI。

保存间隔，新增10条消息保存一次对话，可自行修改，减少次数会频繁保存到硬盘。
```
# 最多保存几条消息，最多保存多少字(token)，几条消息保存一次(写到json文件)
conversation_manager = ConversationManager(max_messages=10, max_tokens=10240, save_threshold=10)

# 屏蔽词
black_word = ['今天我是什么少女', 'ba来一井']  # 如果有不想触发的词可以填在这里

# 第一次创建群配置信息时的默认模型
if not config:
    config = config_manager.apply_default_settings({}, 'deepseek')  # 默认使用deepseek
    config['model'] = 'deepseek-chat'  # 默认模型
    config_manager.set_config(group_id, config)


# 删除人格，因为人格是所有群公用，权限放开，可能会被其他群的人删除，可以设定权限

@sv.on_prefix('删除人格')
async def remove_persona_prefix(bot, ev: CQEvent):
    # if ev.user_id not in hoshino.config.SUPERUSERS:
    #     await bot.send(ev,"该功能仅限bot管理员使用")
    #     return
    # 判断权限，只有用户为群管理员或为bot设置的超级管理员才能使用
    u_priv = priv.get_user_priv(ev)
    if u_priv < sv.manage_priv:
        await bot.send(ev,"该功能仅限群管理员或为bot设置的超级管理员使用")
        return
```
手动修改群配置后，记得用`重载配置`刷新一下

### 注意，因为是国产ai所以非常和谐，原插件那种露骨的人格设定用不了，比较普通的那种设定可用（普通和理所当然究竟是什么呢

