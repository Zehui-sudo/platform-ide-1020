好的，作为一名顶级的Python教育专家，我将为你生成关于 **re 模块基础** 的详细教学内容。

---

## re 模块基础

### 🎯 核心概念
`re` 模块是 Python 的文本处理“瑞士军刀”，它让你能用一套强大的“规则”（即正则表达式模式）来高效地查找、匹配、提取和替换复杂的字符串。

### 💡 使用方式
使用 `re` 模块通常分为三步：
1.  **`import re`**: 导入正则表达式模块。
2.  **定义模式 (Pattern)**: 创建一个字符串，描述你想要匹配的文本规则。
3.  **调用函数**: 使用 `re` 模块的函数（如 `re.search()`, `re.findall()`）将模式应用到目标字符串上。

### 📚 Level 1: 基础认知（30秒理解）
想象一下，你想在一大段文字中找到第一个出现的Email地址。`re.search()` 就像一个智能侦探，它会根据你给的“嫌疑人画像”（模式），在文本中搜索，一旦找到第一个匹配的，就立刻告诉你结果。

```python
import re

# 目标文本
text = "你好，我的邮箱是 my_email@example.com，请联系我。另一个邮箱是 old.email@work.net。"

# 定义一个简单的邮箱模式（\w+ 表示一个或多个字母/数字/下划线）
pattern = r'\w+@\w+\.\w+'

# 使用 re.search() 查找第一个匹配项
match = re.search(pattern, text)

if match:
    print(f"🎉 找到了第一个匹配的邮箱: {match.group(0)}")
else:
    print("😔 没有找到任何匹配的邮箱。")

# 预期输出:
# 🎉 找到了第一个匹配的邮箱: my_email@example.com
```

### 📈 Level 2: 核心特性（深入理解）
`re.search()` 找到一个就收工了，但我们往往需要更多功能。来看看 `re` 模块的两个核心利器。

#### 特性1: `re.findall()` - 查找所有匹配项
与 `re.search()` 不同，`re.findall()` 会像一个勤劳的搜查队，把文本中所有符合模式的字符串都找出来，并放到一个列表里返回。

```python
import re

# 目标文本，包含多个电话号码
log_data = "用户张三的电话是 138-1234-5678，李四的电话是 159-8765-4321，客服电话是 400-800-9000。"

# 定义一个匹配电话号码的模式（\d 表示数字，{n} 表示重复n次）
# \d{3}-\d{4}-\d{4} 匹配 XXX-XXXX-XXXX 格式
# \d{3}-\d{3}-\d{4} 匹配 XXX-XXX-XXXX 格式
# | 表示“或”
pattern = r'\d{3}-\d{4}-\d{4}|\d{3}-\d{3}-\d{4}'

# 使用 re.findall() 查找所有匹配的电话号码
phone_numbers = re.findall(pattern, log_data)

print(f"🔍 从日志中提取到的所有电话号码: {phone_numbers}")

# 预期输出:
# 🔍 从日志中提取到的所有电话号码: ['138-1234-5678', '159-8765-4321', '400-800-9000']
```

#### 特性2: `re.sub()` - 搜索并替换
`re.sub()` 是一个强大的“查找与替换”工具。它会找到所有符合模式的子串，并将它们替换成你指定的新内容。这在数据清洗和格式化时非常有用。

```python
import re

# 原始评论，包含不雅词汇
comment = "这个产品真是太棒了！简直是 fantastic！不过那个 a_bad_word 真的很影响体验。"

# 定义要屏蔽的词汇模式
pattern = r'fantastic|a_bad_word'

# 使用 re.sub() 将匹配到的词替换为 '*'
cleaned_comment = re.sub(pattern, '***', comment)

print(f"原文: {comment}")
print(f"净化后的评论: {cleaned_comment}")

# 预期输出:
# 原文: 这个产品真是太棒了！简直是 fantastic！不过那个 a_bad_word 真的很影响体验。
# 净化后的评论: 这个产品真是太棒了！简直是 ***！不过那个 *** 真的很影响体验。
```

### 🔍 Level 3: 对比学习（避免陷阱）
初学者最容易混淆 `re.match()` 和 `re.search()`。它们看似相似，实则工作方式有天壤之别。

**陷阱：** 认为 `re.match()` 和 `re.search()` 都能在字符串任意位置查找。

```python
import re

text = "My user ID is Python_123."
pattern = r'Python_\d+'

# === 错误用法 ===
# ❌ 尝试使用 re.match() 在字符串中间查找模式
# re.match() 只从字符串的 *开头* 开始匹配，如果开头不匹配，就直接返回 None。
match_obj = re.match(pattern, text)

print(f"❌ 使用 re.match() 的结果: {match_obj}")
# 解释：因为 "My user ID..." 并不以 "Python_123" 开头，所以 re.match() 匹配失败。
# 预期输出:
# ❌ 使用 re.match() 的结果: None


# === 正确用法 ===
# ✅ 使用 re.search() 在整个字符串中搜索第一个匹配项
# re.search() 会扫描整个字符串，直到找到第一个匹配的位置。
search_obj = re.search(pattern, text)

if search_obj:
    print(f"✅ 使用 re.search() 的结果: 找到了 '{search_obj.group(0)}'")
else:
    print("✅ 使用 re.search() 未找到匹配项")
# 解释：re.search() 不在乎模式是否在开头，它成功在字符串中间找到了 "Python_123"。
# 预期输出:
# ✅ 使用 re.search() 的结果: 找到了 'Python_123'
```
**结论：** 如果你需要确保字符串以某个模式开头，用 `re.match()`；如果只是想在字符串中找到某个模式（不限位置），请始终使用 `re.search()`。

### 🚀 Level 4: 实战应用（真实场景）
**场景：** 🕵️‍♂️ 破译星际间谍密电

你是一名星际情报分析员，截获了一段来自敌方间谍的加密信息。信息中混杂着大量无用数据，但其中隐藏着多个格式为 `[PLANET:行星名-CODE:4位数字]` 的关键情报。你的任务是编写一个Python脚本，快速提取出所有的行星和对应的密码。

```python
import re

# 截获的加密信息
encoded_message = """
***BEGIN TRANSMISSION***
Noise... static... from [PLANET:Mars-CODE:4815]... request confirmed.
...more static... Target is [PLANET:Jupiter-CODE:1623].
System alert: [PLANET:Saturn-CODE:4299] is now online.
...garbled data...
***END TRANSMISSION***
"""

# 定义匹配关键情报的模式
# (.*?) - 非贪婪匹配任意字符，作为第一个捕获组（行星名）
# (\d{4}) - 精确匹配4个数字，作为第二个捕获组（密码）
pattern = r'\[PLANET:(.*?)-CODE:(\d{4})\]'

# 使用 re.findall() 提取所有匹配的情报
# findall 会返回一个元组列表，每个元组包含所有捕获组的内容
intelligence_data = re.findall(pattern, encoded_message)

print("--- 正在破译星际密电... ---\n")

if intelligence_data:
    print(f"🎉 成功破译！发现 {len(intelligence_data)} 条关键情报：")
    for planet, code in intelligence_data:
        print(f"  📍 行星: {planet}, 🔑 密码: {code}")
else:
    print("😔 未在密电中发现任何有效情报。")

# 预期输出:
# --- 正在破译星际密电... ---
#
# 🎉 成功破译！发现 3 条关键情报：
#   📍 行星: Mars, 🔑 密码: 4815
#   📍 行星: Jupiter, 🔑 密码: 1623
#   📍 行星: Saturn, 🔑 密码: 4299
```

### 💡 记忆要点
- **第一步**: 永远记得 `import re`。
- **找一个 vs 找所有**: `re.search()` 找到第一个就停，返回一个匹配对象（Match Object）；`re.findall()` 找遍全文，返回一个包含所有匹配字符串的列表。
- **从头匹配 vs 全文搜索**: `re.match()` 只从字符串开头匹配，而 `re.search()` 会扫描整个字符串。日常使用 `re.search()` 更为普遍。