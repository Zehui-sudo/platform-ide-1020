# Learn-linker VSCode Extension

VSCode 插件，提供代码的 AI 解释功能，支持流式输出和 Markdown 渲染。

## 功能特性

- 🤖 **AI 代码解释** - 选中代码获取智能解释
- ⚡ **流式输出** - 实时展示生成内容
- 📝 **Markdown 渲染** - 支持代码高亮、数学公式、表格等
- 🎯 **多种触发方式** - CodeLens、快捷键、命令面板

## 使用方法

### 1. 安装和启动

```bash
# 安装依赖
pnpm install

# 编译项目
pnpm compile

# 在 VSCode 中按 F5 启动调试
```

### 2. 触发 AI 解释

**方式一：CodeLens**
- 选中代码
- 点击代码上方的 "🤖 获取AI解释"

**方式二：快捷键**
- 选中代码
- 按 `Cmd+Shift+E` (Mac) 或 `Ctrl+Shift+E` (Windows/Linux)

**方式三：状态栏**
- 选中代码
- 点击状态栏右侧的 "✨ AI解释" 按钮

**方式四：命令面板**
- `Cmd+Shift+P` 打开命令面板
- 输入 "快速解释选中代码"

## 技术栈

- **VSCode Extension API** - 插件开发
- **React** - WebView UI 框架
- **react-markdown** - Markdown 渲染
- **TypeScript** - 类型安全
- **Webpack** - 打包构建

## 项目结构

```
learn-linker/
├── src/
│   ├── extension.ts              # 插件入口
│   ├── providers/                # CodeLens 和装饰器
│   ├── webview/                  # WebView 管理
│   │   ├── WebviewManager.ts     # WebView 面板管理
│   │   └── app/                  # React 应用
│   └── services/                 # AI 服务
├── dist/                         # 编译输出
└── package.json                  # 插件配置
```

## 开发命令

```bash
# 编译
pnpm compile

# 监听模式
pnpm watch

# 清理
pnpm clean

# 打包
pnpm package
```

## 配置选项

在 VSCode 设置中可配置：
- `learnLinker.enableCodeLens` - 启用/禁用 CodeLens 提示

## 后续计划

- [ ] Task #001: 智能选区扩展
- [ ] Task #002: 集成真实 AI 服务
- [ ] Task #003: 知识点链接功能
- [ ] Task #004: 代码集管理

## 当前版本

### 0.0.1 - 技术验证版

- ✅ CodeLens + WebView Panel 实现
- ✅ React + Markdown 渲染集成
- ✅ 流式输出支持
- ✅ 多种触发方式

## License

MIT
