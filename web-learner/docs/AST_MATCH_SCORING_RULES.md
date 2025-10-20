# AST 匹配核心特征与评分规则（MVP 草案）

本规则用于约束“平台 AST 匹配 API”如何从插件上传的 AST 特征中识别最相关的知识点，目的在于：
1) 必须命中该知识点的“核心特征”，避免通用特征导致的误报；2) 控制通用特征权重，避免大量 100% 满分。

## 评分规则
- 核心分层：每个知识点划分三类特征
  - core：必须命中其一；代表该知识点的本质特征
  - support：加分项；与主题强相关但非必要
  - generic：通用语法；仅少量加分，避免刷高
- 命中门槛：
  - 必须命中 ≥1 个 core
  - support 命中≥1个，或总命中≥2个（core+support）才计入排序（可放宽为仅 core 命中也计入，但优先级更低）
- 计分（建议公式）：
  - raw = 1.0×coreHits + 0.35×supportHits + 0.1×genericHits
  - 代码块命中 ×1.15；标题命中 +0.2（弱化标题过度放大）
  - normalize = min(raw / 4.0, 1)
- 模糊匹配：
  - 保留少量明确同义词（如 array-method ↔ .map/.filter/.reduce），禁止“包含关系”宽松命中（避免 import 误伤“动态导入”）
- 语言过滤：仅返回 language 匹配的条目

## 核心特征清单（精选）

以下为常用章节的 core/support/generic 提示，实际落地按章节 ID/标题关键字自动映射：

- 2.x 数组
  - 数组转换（map/filter/reduce）
    - core：`.map(` 或 `.filter(` 或 `.reduce(`
    - support：`arrow-function`
    - generic：`array-method` 其他
- 5.x 异步编程
  - async/await
    - core：`async` 或 `await` 或 `async-await`
    - support：`try-catch`
    - generic：`function`
  - 并发控制
    - core：`Promise.all(` 或 `Promise.race(`
  - 错误处理（异步）
    - core：`try-catch`
- 6.x DOM 与事件
  - 事件监听
    - core：`addEventListener(`
- 7.x 现代语法与模块
  - 动态导入
    - core：`import(`（动态 import 调用）
    - 说明：不以 `import` 关键字替代，避免异步场景误命中
- 8.x 网络与存储
  - fetch 基础
    - core：`fetch(`
  - 响应处理
    - core：`.json(`
  - 请求拦截
    - core：`AbortController(` 或 明确封装拦截逻辑（难以正则化，先以 `AbortController(` 代表）

以上清单作为 MVP 启发式，后续可通过离线评估逐步细化。

