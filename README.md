# Platform IDE

Platform IDE 是一个集成的学习平台项目，包含在线代码学习网站和 VSCode 插件。

## 项目结构

```
platform-ide/
├── web-learner/        # 在线代码学习平台 (Next.js)
├── learn-linker/       # VSCode 插件项目
├── packages/           # 共享代码包（预留）
├── pnpm-workspace.yaml # pnpm workspace 配置
├── package.json        # 根目录包管理
└── tsconfig.base.json  # 共享的 TypeScript 配置
```

## 技术栈

### Web Learner
- **框架**: Next.js 15.4
- **UI库**: Radix UI + Tailwind CSS
- **状态管理**: Zustand
- **代码编辑器**: CodeMirror
- **AI集成**: Vercel AI SDK

### Learn Linker (VSCode Extension)
- **框架**: VSCode Extension API
- **构建工具**: Webpack
- **语言**: TypeScript

## 快速开始

### 安装依赖

```bash
# 使用 pnpm 安装所有依赖
pnpm install
```

### 开发命令

```bash
# 同时启动两个项目
pnpm dev

# 单独启动 Web 学习平台
pnpm dev:web

# 单独启动 VSCode 插件开发
pnpm dev:ext

# 构建所有项目
pnpm build

# 运行代码检查
pnpm lint

# 清理所有 node_modules
pnpm clean:modules
```

## 项目特性

### Web Learner 功能
- 📚 交互式代码学习环境
- 🤖 AI 辅助学习功能
- 📝 Markdown 内容渲染
- 🎯 实时代码执行
- 📊 学习进度追踪

### Learn Linker 功能
- 🔗 连接 VSCode 与在线学习平台
- 📖 同步学习内容
- 🚀 快速代码片段导入

## 开发指南

### 添加新的共享代码

1. 在 `packages/` 目录下创建新的包
2. 更新 `pnpm-workspace.yaml` 配置
3. 在需要使用的项目中添加依赖

### 项目间依赖管理

使用 workspace 协议引用内部包：
```json
{
  "dependencies": {
    "@platform-ide/shared": "workspace:*"
  }
}
```

## 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交更改
4. 推送到分支
5. 创建 Pull Request

## License

MIT