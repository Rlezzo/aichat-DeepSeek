> #### https://github.com/Cosmos01/aichat-chatGPT/tree/main的fork
> #### 发现一个国产AI:[DeepSeek](https://www.deepseek.com/)看上去很强很便宜，但是旧插件没法直接用了
> #### 旧版本用的openai0.28，现在openai1.30，于是修改了一下让它能用deepseek
> #### 注册送5百万tokens(一个月期限)
------
  
# aichat-DeepSeek
  
aichat插件魔改GPT-3.5 API版本  的DeepSeek适配版，国产ai所以删除了代理
  
## 命令(人格可换成会话)
1. `创建人格/新建人格/设置人格+人格名+空格+设定`: 创建新人格或修改现有人格，注意人格名不能大于24位
2. `查询人格/人格列表/获取人格`: 获取当前所有人格及当前人格
3. `选择人格/切换人格/默认人格+人格名`: 切换到对应人格，不填则使用默认人格
4. `/t+消息或@bot+消息`: 前面加上记住两字可以让关闭记忆功能的bot记住对话，记住两字不会放入对话
5. `重置人格/重置会话+人格名`: 重置人格，不填则重置当前人格，无当前人格则重置默认人格
6. `对话记忆+on/off`: 开启/关闭对话记忆，不加则返回当前状态
7. `删除会话+会话名` : 删除会话，不填则删除当前会话，默认会话不可删除
8. `删除对话+条数`: 删除倒数N条对话，负数则是从第N条开始删除，不加条数则删除上一条。1条对话指一次问与答，不需要乘2。
## 新增
10. `ai配置重载`: 重新加载配置文件，更新key等配置后使用
10.`查看模型/查询模型/更改模型/切换模型` 查看切换api所用模型
  
  
## 安装方法
1. 在HoshinoBot的插件目录modules下clone本项目 `git clone https://github.com/Rlezzo/aichat-DeepSeek.git`
2. 安装必要第三方库：`pip install openai`（当前是1.30版本）
3. 在 `config/__bot__.py`的MODULES_ON列表里加入 `aichat-DeepSeek`
4. 到config.ini中填写配置，基本只要填api_key(可以多个)，其他配置见下文。注意修改后保存为UTF-8。
5. 重启HoshinoBot (启动前确保关闭了浏览器)
6. 插件默认禁用，在要启用本插件的群中发送命令`启用 人工智障`
  

## 配置参数(填写时不要加引号)
- api-key
> 可以填写多个api-key，半角逗号(",")隔开，每次对话随机选择
- model 模型
> 默认"deepseek-chat"，目前有 deepseek-chat 和 deepseek-coder两种
- record 记忆开关
> 设为false则不会记录会话，除非你在对话前加上"记住"两个字(两个字会被删去)，这样可以节省很多费用。
- max_tokens 最大回答长度
> 改小了也能节省一些费用。
- interval 保存间隔
> 每进行N次对话就在本地保存会话记录，非记忆对话不计次。
- base_url API地址
> 需要修改API地址的填写，默认的就是deepseek的


<br><br><br><br><br><br><br><br>
------  
其他请参考原帖，感谢原作者，大部分都是原作者做的。

