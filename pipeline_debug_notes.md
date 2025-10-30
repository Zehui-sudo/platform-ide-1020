# Pipeline 持久化调试记录

## 目标
- 将流水线任务状态持久化到 `output/pipeline_jobs/jobs.json`，并在任务启动 5 秒内通过 `[pipeline]` 调试日志确认写盘成功。
- 解决内容生成阶段未正确结束的问题，定位脚本是否持续运行或前端状态未正确识别结束。

## 操作步骤
1. **jobManager.ts 持久化改造**
   - 引入实时写盘，去掉延迟定时器；使用 Promise 串行保证顺序。
   - 重新实现 `repoRoot()`，自上而下查找 `config.json` / `package.json`，避免 Next cwd 变化造成路径错误。
   - 新增调试日志：
     ```ts
     console.debug('[pipeline] createJob:', id, type, 'subject=', init?.subject, 'cwd=', process.cwd(), 'repoRoot=', repoRoot());
     console.debug('[pipeline] jobs persisted:', JOBS_STATE_FILE, 'items=', payload.length);
     ```
   - 在 `createJob` / `finishJob` / `updateStage` / `touchJob` 等位置调用 `scheduleFlush()`。

2. **spawn 文件更新**
   - `spawnIntegrated.ts`、`spawnChapters.ts` 中，在修改 `job` 字段（如 `outputPath`、`logPath`、`pid`）后调用 `touchJob(job)`，确保状态变更落盘。

3. **前端 Store 调整**
   - `themeGeneratorStore.ts` 移除 `persist(...)` 和 localStorage，改为启动时从 `/api/pipeline/jobs/latest` 拉取最近的 outline/content 任务，并在 `rehydrate()` 中恢复订阅。
   - 新增 API route：
     - `GET /api/pipeline/jobs` 返回全部 snapshot。
     - `GET /api/pipeline/jobs/latest?type=outline|content` 返回最近一次任务。
     - `GET /api/pipeline/jobs/[id]` 返回指定任务快照。

4. **调试措施**
   - 清理 `.next` 目录后重启 `pnpm --filter @platform-ide/web-learner dev`，确保 Next 加载新源码。
   - 运行大纲/内容任务，期望在服务器终端看到 `[pipeline] createJob` 及 `[pipeline] jobs persisted` 日志。
   - 若仍未出现日志，需进一步确认实际加载的模块路径、`console.debug` 输出是否被过滤等。

## 未解决的问题
- 重启后仍看不到任何 `[pipeline]` 调试日志，怀疑实际执行的编译产物未包含最新调整，需后续排查。

