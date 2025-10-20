# JavaScript 知识点内容生成工具

这个Python脚本用于批量生成JavaScript知识点的学习内容，基于 `javascript-knowledge-structure.md` 中定义的prompt模板。

## 功能特性

- 📚 批量生成97个JavaScript知识点内容（覆盖8章）
- 🎯 基于标准化的prompt模板
- 🔄 支持断点续传（跳过已生成文件）
- 📝 自动生成索引文件
- 🏷️ 自动添加AST匹配标签
- 📂 按章节组织输出文件
- 🤖 支持多种AI提供商（Gemini、OpenAI）

## 安装要求

```bash
# Python 3.7+
# 根据使用的AI服务选择安装
pip install google-generativeai  # 使用Google Gemini
pip install openai               # 使用OpenAI
```

## 配置

首次运行会自动创建 `config.json` 配置文件：

### 使用 Google Gemini（推荐）
```json
{
  "api_provider": "gemini",
  "gemini_api_key": "YOUR_GEMINI_API_KEY_HERE",
  "model": "gemini-pro",
  "temperature": 0.7,
  "max_tokens": 4000,
  "output_dir": "output",
  "batch_size": 5,
  "retry_times": 3,
  "retry_delay": 5
}
```

### 使用 OpenAI
```json
{
  "api_provider": "openai",
  "openai_api_key": "YOUR_OPENAI_API_KEY_HERE",
  "api_base": "https://api.openai.com/v1",
  "model": "gpt-4",
  "temperature": 0.7,
  "max_tokens": 4000,
  "output_dir": "output",
  "batch_size": 5,
  "retry_times": 3,
  "retry_delay": 5
}
```

### 配置说明
- `api_provider`: API提供商（"gemini" 或 "openai"）
- `gemini_api_key`: Google Gemini API密钥
- `openai_api_key`: OpenAI API密钥
- `model`: 使用的模型（gemini-pro, gpt-4等）
- `temperature`: 生成温度（0-1，越高越有创造性）
- `max_tokens`: 最大输出token数
- `output_dir`: 输出目录
- `batch_size`: 批处理大小（每批后休息）
- `retry_times`: 失败重试次数

## 获取API密钥

### Google Gemini
1. 访问 [Google AI Studio](https://makersuite.google.com/app/apikey)
2. 点击 "Get API Key" 创建新密钥
3. 复制密钥到配置文件

### OpenAI
1. 访问 [OpenAI Platform](https://platform.openai.com/api-keys)
2. 创建新的API密钥
3. 复制密钥到配置文件

## 快速开始（推荐用于测试）

1. **安装依赖**
   ```bash
   pip install google-generativeai
   ```

2. **创建配置文件**
   ```bash
   # 复制配置模板
   cp config.example.json config.json
   ```

3. **编辑 config.json，添加API密钥**
   ```json
   {
     "api_provider": "gemini",
     "gemini_api_key": "你的实际密钥",  // 在这里填入
     ...
   }
   ```
   
   ⚠️ **安全提示**：`config.json` 已加入 `.gitignore`，不会被提交到版本控制

4. **测试生成第1章内容**
   ```bash
   # 只生成第1章（23个知识点）
   python generate_knowledge_content.py --chapter 1
   ```

## 使用方法

### 交互式模式
```bash
python generate_knowledge_content.py
# 会显示菜单，可以选择按章节生成
```

### 命令行模式
```bash
# 生成所有知识点（跳过已存在）
python generate_knowledge_content.py --all

# 强制重新生成所有
python generate_knowledge_content.py --all --force

# 按章节生成（新功能）
python generate_knowledge_content.py --chapter 1              # 只生成第1章
python generate_knowledge_content.py --chapter 1,2,3          # 生成第1,2,3章
python generate_knowledge_content.py --chapter 1 --force      # 强制重新生成第1章

# 生成单个知识点
python generate_knowledge_content.py --single js-sec-1-1-1

# 仅生成索引
python generate_knowledge_content.py --index

# 使用自定义配置
python generate_knowledge_content.py --config my_config.json --all
```

## 输出结构

```
output/
├── chapter1/
│   ├── js-sec-1-1-1-变量声明（var-let-const）.md
│   ├── js-sec-1-1-2-基本数据类型（number-string-boolean）.md
│   └── ...
├── chapter2/
│   └── ...
├── chapter3/
│   └── ...
├── chapter4/
│   └── ...
├── chapter5/
│   └── ...
├── index.md              # 生成状态索引
└── generation_log.txt    # 生成日志
```

## 知识点列表

脚本现已包含完整8章共97个知识点：

### 第一章：语言基础（23个知识点）
- 1.1 变量与值（5个）
- 1.2 运算符与表达式（6个）
- 1.3 控制流（6个）
- 1.4 函数基础（6个）

### 第二章：复合数据类型（19个知识点）
- 2.1 数组（7个）
- 2.2 对象（7个）
- 2.3 字符串进阶（5个）

### 第三章：函数进阶（9个知识点）
- 3.1 高阶函数（5个）
- 3.2 this与上下文（4个）

### 第四章：面向对象编程（10个知识点）
- 4.1 构造函数与原型（4个）
- 4.2 类与继承（6个）

### 第五章：异步编程（14个知识点）
- 5.1 异步基础（4个）
- 5.2 Promise（5个）
- 5.3 async/await（5个）

### 第六章：DOM与事件（12个知识点）
- 6.1 DOM操作（6个）
- 6.2 事件处理（6个）

### 第七章：实用特性（14个知识点）
- 7.1 ES6+特性（5个）
- 7.2 模块化（4个）
- 7.3 错误处理（4个）

### 第八章：网络与存储（9个知识点）
- 8.1 网络请求（5个）
- 8.2 浏览器存储（4个）

## 生成的内容格式

每个知识点文件包含：
- 🎯 核心概念
- 📚 Level 1: 基础认知
- 📈 Level 2: 核心特性
- 🔍 Level 3: 对比学习
- 🚀 Level 4: 实战应用（有趣场景）
- 💡 记忆要点
- 元数据标签（用于AST匹配）

### 🎮 Level 4 实战应用特色

生成的实战示例会选择有趣的场景，包括：
- **游戏场景**：石头剪刀布、猜数字、迷宫探索等
- **创意互动**：颜色混合器、表情生成器、ASCII艺术等
- **美食相关**：披萨计算器、咖啡调配、食谱随机等
- **娱乐活动**：骰子游戏、幸运转盘、占卜算命等
- **日常趣味**：心情追踪、笑话生成、每日运势等

这些有趣的场景让学习JavaScript变得更加生动和有吸引力！

## 测试模式

如果没有配置API密钥，脚本会生成模拟内容用于测试输出格式。

## 扩展说明

### 添加更多知识点

编辑 `generate_knowledge_content.py` 中的 `define_knowledge_points` 方法：

```python
# 添加第六章
chapter6 = [
    KnowledgePoint("js-sec-6-1-1", "元素选择", "6", "6.1", "basic"),
    # ...
]
points.extend(chapter6)
```

### 自定义prompt模板

修改 `generate_prompt` 方法来调整生成的prompt格式。

### 使用其他AI API

修改 `call_ai_api` 方法以支持其他API（如Anthropic Claude、Azure OpenAI等）。

## 注意事项

1. **API限流**：脚本包含批次延迟和重试机制
2. **内容质量**：建议使用GPT-4或更高质量的模型
3. **成本控制**：每个知识点约消耗2000-4000 tokens
4. **断点续传**：默认跳过已存在文件，使用 `--force` 强制重新生成

## 故障排除

### 常见问题

1. **ImportError: No module named 'openai'**
   ```bash
   pip install openai
   ```

2. **API调用失败**
   - 检查API密钥是否正确
   - 确认网络连接
   - 查看 `generation_log.txt` 详细错误

3. **生成内容不完整**
   - 增加 `max_tokens` 配置值
   - 检查API响应是否被截断

## License

MIT