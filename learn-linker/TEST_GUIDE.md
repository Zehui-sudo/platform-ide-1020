# PeekView 技术验证测试指南

## 功能概述

本次技术验证实现了以下功能：
1. **CodeLens Provider** - 在选中代码上方显示"🤖 获取AI解释"提示
2. **WebView Panel** - 在侧边显示 Markdown 渲染的 AI 回复
3. **React + Markdown 渲染** - 复用 web-learner 的渲染组件，支持：
   - 语法高亮代码块
   - 数学公式（KaTeX）
   - 表格、列表、引用
   - 流式输出效果

## 测试步骤

### 1. 启动插件调试

```bash
# 在 VSCode 中打开项目
code /Users/zehuipu/platform-ide/learn-linker

# 按 F5 启动调试（或点击运行和调试面板的启动按钮）
```

这会打开一个新的 VSCode 窗口（扩展开发主机）。

### 2. 测试代码提示功能（两种方式）

#### 方式一：装饰器提示（主要方式）
1. 在新窗口中打开任意代码文件
2. 选中一段代码（例如一个函数）
3. 观察：
   - 选中代码末尾显示提示文字 "🤖 按 Cmd+Shift+E 获取AI解释"
   - 状态栏右侧显示 "✨ AI解释 (X行)" 按钮
4. 点击状态栏按钮或按快捷键触发

#### 方式二：CodeLens（备选）
1. 选中代码后，查看输出面板的调试日志
2. 如果 CodeLens 正常工作，代码上方会显示 "🤖 获取AI解释" 
3. 点击该提示打开 WebView Panel

### 3. 查看调试日志

打开输出面板（View -> Output），选择 "Extension Host" 查看日志：
- `[Extension]` - 扩展初始化日志
- `[CodeLens]` - CodeLens 相关日志
- `[Decorator]` - 装饰器相关日志
- `[Command]` - 命令执行日志

### 3. 测试快捷键触发

- 选中代码后按 `Cmd+Shift+E`（Mac）或 `Ctrl+Shift+E`（Windows/Linux）
- 应直接打开 AI 解释面板

### 4. 测试命令面板

1. 按 `Cmd+Shift+P`（Mac）或 `Ctrl+Shift+P`（Windows/Linux）打开命令面板
2. 输入以下命令进行测试：
   - `测试 PeekView 功能` - 直接测试预设代码的解释
   - `快速解释选中代码` - 解释当前选中的代码

### 5. 验证 Markdown 渲染效果

WebView 中应正确显示：
- **标题层级** - H1、H2、H3 等
- **代码块** - 带语言标识和语法高亮
- **内联代码** - `code` 样式
- **数学公式** - 如 $O(n \log n)$ 
- **表格** - 带边框和样式
- **列表** - 有序和无序列表
- **引用块** - 左边框样式
- **链接** - 可点击的超链接

### 6. 验证流式输出

- 观察内容是否逐行显示（模拟流式效果）
- 加载时应显示进度指示器

### 7. 验证主题适配

- 切换 VSCode 主题（亮色/暗色）
- WebView 内容应自动适应主题

## 性能验收标准

✅ **CodeLens 响应时间** < 300ms
- 选中代码后，CodeLens 应立即显示

✅ **WebView 打开时间** < 500ms  
- 点击 CodeLens 后，面板应快速打开

✅ **流式更新流畅**
- 内容逐行显示，无明显卡顿

✅ **ESC 快速关闭**
- 按 ESC 或点击关闭按钮可立即关闭面板

## 已知限制

1. **当前使用 WebView Panel 而非真正的 PeekView**
   - 原因：VSCode API 限制，无法直接创建内嵌的 PeekView
   - 后续可探索：Hover Provider 或 Decorations API

2. **模拟 AI 回复**
   - 当前使用预设的 Markdown 内容
   - 实际集成需要连接真实 AI 服务

3. **选区智能扩展未实现**
   - Task #001 的内容，待后续实现

## 技术亮点

1. **成功复用 web-learner 组件**
   - React + react-markdown 完整移植
   - 保留了所有 Markdown 功能

2. **双入口 Webpack 配置**
   - extension.js（插件主体）
   - webview.js（React 应用）

3. **VSCode API 集成**
   - CodeLens Provider
   - WebView 消息通信
   - 主题变量适配

## 下一步计划

1. 探索更接近 PeekView 的实现方案
2. 实现智能选区扩展（Task #001）
3. 集成真实 AI 服务
4. 添加知识点链接功能
5. 性能优化（缓存、懒加载等）

## 问题反馈

如遇到问题，请检查：
1. 是否已运行 `pnpm install`
2. 是否已运行 `pnpm compile`  
3. 控制台是否有错误信息
4. WebView 开发者工具（右键 -> 检查元素）