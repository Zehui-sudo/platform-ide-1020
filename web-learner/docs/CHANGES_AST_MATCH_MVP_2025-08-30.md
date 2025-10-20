# Web-learner × Learn-linker AST 匹配（MVP）变更总结（2025-08-30）

## 为什么要改
- 聊天场景不再需要“混合匹配”：用户通常在某个知识点内部提问，聊天中自动做知识点匹配会分散注意力且价值有限。
- VSCode 插件（learn-linker）需要“解释圈选代码并跳转平台”能力：当用户圈选代码且涉及平台知识点时，需要精准返回相关知识点的深链以便跳转。
- 真实知识数据在 web-learner 端：原先 learn-linker 中的 knowledgeBase 仅用于单机测试，平台侧应以“真实内容”为基础构建可匹配的 AST 特征索引，并通过 API 对外提供匹配服务。

## 需要怎么改（方案）
- 平台端（web-learner）
  - 去除静态 TS 索引（knowledgeBase），改为从真实内容（public/content/*.md + javascript-learning-path.md）离线/启动时“正则抽取”构建 AST 特征索引（ast-index.json）。
  - 提供 `POST /api/ast-match` 接口，接受 learn-linker 传来的 AST 特征，使用索引进行匹配，返回深链 `/learn?language=...&section=...`。
  - 支持深链：前端根据 URL 中的 `section` 参数直接加载对应知识点内容。
  - 保留聊天体验纯净：默认关闭聊天中自动“知识点匹配”后处理。
- 插件端（learn-linker）
  - 生成 AST 特征后请求平台 `POST /api/ast-match`，获取匹配结果。
  - 在 Webview（AI 解释页面）中展示“相关知识点”深链，点击在系统浏览器打开 web-learner。

## 实际改了哪些

- 平台端（web-learner）
  1) 关闭聊天中的自动匹配
  - 文件: `src/store/learningStore.ts`
  - 变更: 增加开关 `ENABLE_CHAT_LINK_MATCHING = false` 并用该开关包裹原有“AI 回复后做知识链接识别”的逻辑，默认禁用。

  2) 支持深链直达知识点
  - 文件: `src/app/(learn)/learn/page.tsx`
  - 变更: 解析 URL 查询参数中的 `section`，在加载学习路径后调用 `loadSection(sectionId)`，从而支持 `/learn?language=javascript&section=<sectionId>` 直接跳转。

  3) 新的 AST 匹配 API（基于索引文件）
  - 文件: `src/app/api/ast-match/route.ts`
  - 变更要点：
    - runtime: edge；实现 `OPTIONS` 预检和 CORS 头（允许插件跨域调用）。
    - 从 `public/ast-index.json` 读取索引（通过 `new URL('/ast-index.json', req.nextUrl.origin)` 请求自身静态资源）。
    - 评分逻辑：
      - 要求 ≥50% 的 required 命中，否则丢弃。
      - optional 按权重累计分数；根据 `complexity` 做轻微调权。
      - 归一化得分到 [0,1]（启发式）。
    - 返回：`{ ok: true, primary, matches: [{ sectionId, title, language, score, url }] }`。
  - CORS: `Access-Control-Allow-Origin: *`，`POST, OPTIONS`。

  4) 正则构建 AST 特征索引（MVP）
  - 文件: `scripts/build-ast-index.mjs`
  - 功能:
    - 解析 `public/javascript-learning-path.md` 获取所有 `section.id` 与标题。
    - 读取 `public/content/${sectionId}.md`，提取代码块与正文。
    - 使用一组正则规则识别特征（如 async/await、try-catch、Array.map/filter/reduce、addEventListener、fetch、arrow-function、import、spread、destructuring、class、if、for 等）。
    - 权重策略：标题命中 +1.0；正文命中每次 +0.3（上限 0.6）；代码命中每次 +0.5（上限 1.5）；整体再归一化；≥0.9 作为 required。
    - 输出文件：`public/ast-index.json`，结构：
      ```json
      {
        "updatedAt": 1725000000000,
        "sections": [
          { "id": "...", "title": "...", "language": "javascript", "features": {"array-method": 1.0}, "required": ["array-method"] }
        ]
      }
      ```
  - npm 脚本:
    - `package.json` 新增：`"build:ast-index": "node ./scripts/build-ast-index.mjs"`

  5) 移除静态索引实现（避免与真实数据冲突）
  - 删除: `src/services/ast/knowledgeBase.ts`
  - 删除: `src/services/ast/astMatchService.ts`
  - 保留：`IMPLEMENTATION_PLAN_AST_MATCH_MVP.md`（实施方案文档）

- 插件端（learn-linker）
  6) 配置平台地址
  - 文件: `learn-linker/package.json`
  - 变更: 新增配置项 `learnLinker.webLearnerBaseUrl`（默认 `http://localhost:3000`）。

  7) 调用平台 API 并把结果传入 Webview
  - 文件: `src/webview/WebviewManager.ts`
  - 变更:
    - 在 AST 分析完成后，POST `${baseUrl}/api/ast-match`，Body 为 `{ features, language }`。
    - 若返回 `{ ok: true, matches }`，通过 `this.sendMessageToWebview({ type: 'knowledgeLinks', links: data.matches })` 传给 Webview。
    - 新增处理 `openUrl` 消息：使用 `vscode.env.openExternal` 在外部浏览器打开深链。

  8) Webview 中展示“相关知识点”并跳转
  - 文件: `src/webview/app/App.tsx`
  - 变更:
    - 新增状态 `knowledgeLinks`，监听 `knowledgeLinks` 消息后渲染位于 AI 解释区域下方的“相关知识点”区块。
    - 每个知识点以按钮形式展示，点击通过 `vscode.postMessage({ type: 'openUrl', url })` 请求主进程打开外链。

## 如何验证
1) 生成索引
- 在 `web-learner` 目录运行：`pnpm build:ast-index`，检查 `public/ast-index.json` 已生成且包含 sections。

2) 启动平台
- 在 `web-learner` 目录运行：`pnpm dev`，打开 `http://localhost:3000`。
- 检查深链：访问 `http://localhost:3000/learn?language=javascript&section=<sectionId>` 是否能直达内容。

3) 启动插件
- 在 `learn-linker` 目录运行：`pnpm compile`（或 `pnpm watch`），F5 运行扩展。
- 在 VSCode 设置 `learnLinker.webLearnerBaseUrl = http://localhost:3000`。
- 选中包含如 async/await 或数组 map/filter/reduce 的代码片段，执行“快速解释选中代码”（Cmd/Ctrl+Shift+K）。
- Webview 底部应出现“相关知识点”区块；点击跳转外部浏览器打开 web-learner 深链页面。

## 之后还有什么需要优化（下一阶段）
- Tree-sitter 精准抽取（索引构建）：用 AST 解析代码块替代正则，提高准确率与鲁棒性；在 Node 环境离线构建，API 仅读取索引。
- Python 支持：为 Python 侧的内容与代码块新增正则/AST 规则，生成索引并在 API 端按语言过滤。
- 特征与阈值调优：
  - 丰富特征词表与模糊匹配映射，覆盖更多 Web/JS 场景（如事件委托、模块系统细项等）。
  - 依据线下检验数据调整 required 判定与权重归一化策略，提升主知识点命中率（目标 >90%）。
- 安全与跨域：当前 CORS 为 `*` 便于联调；上线可收紧为允许名单。
- 构建集成：将 `build:ast-index` 集成到 CI/CD 流水线或 Next 构建后钩子，确保索引随内容更新而更新。
- 代码整洁：`src/services/ast/types.ts`（若存在）与路由内联类型统一整理；按需清理未使用的类型/工具。

## 备注
- 已创建实施计划文档：`IMPLEMENTATION_PLAN_AST_MATCH_MVP.md`，用于后续 Tree-sitter 版迭代与扩展说明。
- 聊天匹配默认关闭，如需恢复可在 `learningStore.ts` 将 `ENABLE_CHAT_LINK_MATCHING` 设为 `true`。

