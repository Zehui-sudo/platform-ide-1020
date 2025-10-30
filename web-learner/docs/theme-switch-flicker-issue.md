# 主题切换闪烁问题

## 问题描述
在 LearnNavBar 组件中切换学习主题（如从 Python 切换到 JavaScript）时，出现以下闪烁序列：
- 原主题 → 新主题 → 原主题 → 新主题

## 问题分析

### 1. 事件流程分析

用户点击主题选择器后的完整事件链：

```typescript
// LearnNavBar.tsx
handleSubjectChange(newSubject) {
  // 1. 用户点击新主题
  if (newSubject !== subject) {
    loadPath(newSubject);        // 异步加载新路径
    router.replace(`/learn?subject=${newSubject}`);  // 立即更新URL
  }
}
```

### 2. 问题：闪烁的具体时序

```
初始状态 - 显示 Python
用户点击 JavaScript
第一次闪烁（显示 JavaScript）
第二次闪烁（显示 Python）
- 最终跳回 JavaScript 状态稳定
```