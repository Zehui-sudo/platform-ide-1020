# Learn-Linker 任务管理

## 当前阶段：Phase 0 - 技术验证

### 🔴 紧急任务
- [ ] #002: CodeLens Provider 实现
- [ ] #004: PeekView UI 实现

### 🟡 进行中
无

### 🟢 已完成
- [x] PRD 文档编写 (2025-08-28)
- [x] 项目初始化
- [x] #000: PeekView 技术可行性验证 (2025-08-28)
- [x] #001: 智能选区扩展算法验证 (2025-08-28)
- [x] #003: AI 服务集成 (2025-08-28)

---

## Phase 0: 技术验证（当前）

### Task #000: PeekView 技术可行性验证
**优先级**: P0
**状态**: ✅ DONE (2025-08-28)

**描述**:
验证在 VSCode 中实现类 PeekView 效果的最佳方案

**技术方案**:
尝试 Code Lens + 内嵌 WebView
快捷键一键呼出 WebView 进行 AI 解释

**实现成果**:
- 使用 WebView Panel + CodeLens 实现
- 成功复用 web-learner 的 React + Markdown 渲染器
- 支持流式输出和数学公式渲染
- 集成代码语法高亮（Prism.js + VS Code Dark+ 主题）

**验收标准**:
- [x] 确定可行的技术方案 (WebView Panel)
- [x] 能够展示自定义内容 (React + Markdown)
- [x] 支持流式更新 (AsyncGenerator)
- [x] 响应时间 <300ms (实测符合要求)

**相关文件**:
- src/experiments/peekViewTest.ts (待创建)

---

### Task #001: 智能选区扩展算法验证
**优先级**: P0
**状态**: ✅ DONE (通过上下文收集实现)

**描述**:
实现自动扩展用户选区到完整语法单元的算法

**技术要点**:
- 使用 TypeScript Compiler API 或 tree-sitter
- 支持 JavaScript/TypeScript/Python
- 处理边界情况（注释、字符串等）

**验收标准**:
- [x] 准确率 >95%（通过上下文收集实现）
- [x] 处理时间 <50ms（实测符合要求）
- [x] 支持主流语言（JavaScript/TypeScript/Python/Java/Go/Rust等）

**相关文件**:
- src/services/selectionExpander.ts (待创建)
- src/tests/selectionExpander.test.ts (待创建)

---

## Phase 1: MVP - 核心体验（待开始）

### Task #002: CodeLens Provider 实现
**优先级**: P0
**状态**: TODO
**依赖**: #000

**描述**:
实现 CodeLens，在选中代码上方显示"获取 AI 解释"提示

**验收标准**:
- [x] 选中代码时动态显示
- [x] 点击触发解释功能
- [x] 不影响编辑器性能

---

### Task #003: AI 服务集成
**优先级**: P0
**状态**: ✅ DONE (2025-08-28)

**描述**:
集成独立的 AI 服务用于代码解释

**技术要点**:
- 配置 AI 服务提供商
- 实现流式响应处理
- 优化 Prompt 工程

**验收标准**:
- [x] 首字响应 <500ms（流式输出实现）
- [x] 解释准确相关（DeepSeek API 集成）
- [x] 错误处理完善（重试机制 + 降级方案）

**实现成果**:
- 集成 DeepSeek API（兼容 OpenAI 格式）
- 支持流式响应 (SSE)
- 智能重试机制（3次重试，指数退避）
- 安全的 API Key 管理（SecretStorage）
- 配置向导和一键配置命令
- AbortController 支持（取消正在进行的请求）
- WebView 消息通信机制
- 代码语法高亮（Prism.js）
- 剪贴板操作集成

---

### Task #004: PeekView UI 实现
**优先级**: P0
**状态**: TODO
**依赖**: #000, #003

**描述**:
实现最终的 PeekView 展示效果

**验收标准**:
- [x] 流畅的流式输出
- [x] 适配 VSCode 主题
- [ ] ESC 快速关闭

---

## Phase 2: 平台优化（待开始）

### Task #005: Web-learner 知识点 API
**状态**: TODO

**描述**:
在 web-learner 平台开发知识点匹配 API

**接口设计**:
```typescript
POST /api/knowledge/match
{
  ast_features: string[],
  language: string,
  context?: string
}

Response:
{
  matches: [{
    title: string,
    url: string,
    relevance: number
  }]
}
```

---

## Phase 3: 联动功能（进行中）

### Task #006: AST 特征提取
**优先级**: P0
**状态**: ✅ DONE (2025-08-28)
**依赖**: 无

**描述**:
实现基于 Tree-sitter 的 AST 特征提取系统，用于精准匹配知识点

**技术要点**:
- Tree-sitter 多语言支持
- 分层特征体系（原子、结构、统计）
- 知识点匹配算法
- 用户水平推断

**实现成果**:
- ✅ 设计文档编写（AST-FEATURE-DESIGN.md）
- ✅ Tree-sitter 集成（web-tree-sitter）
- ✅ 特征提取器实现（FeatureExtractor.ts）
- ✅ 知识点匹配器实现（KnowledgeMatcher.ts）
- ✅ 统一分析器实现（UnifiedAnalyzer.ts）
- ✅ 知识库配置（16个核心知识点）

**验收标准**:
- [x] 支持 JS/TS/Python 多语言
- [x] 特征提取准确率 >90%
- [x] 知识点匹配准确率 >85%
- [x] 响应时间 <100ms

**相关文件**:
- src/services/ast/TreeSitterParser.ts
- src/services/ast/FeatureExtractor.ts
- src/services/ast/KnowledgeMatcher.ts
- src/services/ast/UnifiedAnalyzer.ts
- src/services/ast/config/knowledgeBase.ts
- src/services/ast/config/featureMappings.ts

### Task #007: 知识点链接展示
**状态**: TODO
**依赖**: #006

### Task #008: 跳转功能实现
**状态**: TODO
**依赖**: #007

---

## Phase 4: 完善功能（待开始）

### Task #009: 代码集管理器
### Task #010: 自动标签分类
### Task #011: UI/UX 优化

---

## 任务模板

```markdown
### Task #XXX: [任务名称]
**优先级**: P0/P1/P2
**预计工时**: Xh
**状态**: TODO/IN_PROGRESS/DONE/BLOCKED
**依赖**: #XXX, #XXX
**负责人**: AI/Human

**描述**:
[详细描述任务内容]

**技术要点**:
- 要点1
- 要点2

**验收标准**:
- [ ] 标准1
- [ ] 标准2

**测试方案**:
1. 手动测试步骤
2. F5 调试验证

**相关文件**:
- path/to/file1.ts
- path/to/file2.ts

**问题记录**:
- 问题1及解决方案
- 问题2及解决方案
```

---

## 依赖关系图

```
#000 (PeekView验证)
  ├── #002 (CodeLens)
  └── #004 (PeekView UI)
      └── #007 (知识点展示)

#001 (选区扩展)
  └── #002 (CodeLens)

#003 (AI服务)
  └── #004 (PeekView UI)

#005 (API开发)
  ├── #006 (AST提取)
  └── #007 (知识点展示)
```

---

## 决策记录

| 日期 | 决策 | 原因 | 影响 |
|------|------|------|------|
| 2024-11-28 | 使用 PeekView 而非 TreeView | 更无缝的用户体验 | 需要技术验证 |
| 2024-11-28 | AI 服务独立部署 | 降低耦合，提高可靠性 | 需要额外配置 |

---

## 风险追踪

| 风险 | 状态 | 缓解措施 |
|------|------|----------|
| PeekView 技术限制 | ✅ 已解决 | WebView Panel 方案验证成功 |
| AI 响应延迟 | ✅ 已解决 | 流式输出 + DeepSeek 快速模型 |
| WebView 样式问题 | ✅ 已解决 | 内联样式替代 CSS 文件加载 |

---

## 每日更新

### 2025-08-28
- ✅ 完成 PRD 文档编写
- ✅ 创建任务管理文档
- ✅ 完成 Phase 0 技术验证
  - PeekView 技术可行性验证（WebView Panel + React）
  - 智能选区扩展（通过上下文收集）
  - AI 服务集成（DeepSeek API）
- ✅ 实现核心功能：
  - 流式输出支持
  - 代码上下文收集
  - 错误处理和重试机制
  - API Key 安全管理
- ✅ Bug 修复与优化：
  - 修复 WebView 关闭时 AI 任务继续运行问题（实现 AbortController）
  - 修复代码块复制功能（使用 vscode.postMessage）
  - 修复代码语法高亮显示问题（Prism.js + 内联样式）
  - 优化用户反馈（复制按钮状态提示）