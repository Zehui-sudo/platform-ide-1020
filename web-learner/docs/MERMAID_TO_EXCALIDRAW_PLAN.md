# Mermaid to Excalidraw 静态 SVG 整合方案

## 1. 目标与概述

本文档旨在详细阐述将项目中现有的 Mermaid.js v11 渲染逻辑, 替换为基于 `mermaid-to-excalidraw` 的静态 SVG 生成方案。

**核心目标:**

1.  **风格统一:** 将 Mermaid 图表的渲染风格替换为更现代化、更美观的 Excalidraw 手绘风格。
2.  **静态输出:** 最终产物应为纯粹的、无交互的静态 SVG 图片, 类似于 `<img>` 标签, 而非一个可交互的组件。
3.  **性能优化:** 避免引入庞大的前端组件库, 确保对页面加载性能的影响降至最低。

## 2. 核心逻辑与渲染架构

为了实现静态、高性能的目标, 我们将采取一种完全绕过 React 组件渲染的技术路径。

**错误的路径 (已排除):**
`Mermaid 文本 -> Mermaid.js 渲染 -> SVG 输出 -> Excalidraw 组件解析 -> 交互式组件`
这个路径需要加载庞大的 `@excalidraw/excalidraw` 库, 违背了性能和静态化的初衷。

**正确的路径 (本方案采用):**
`Mermaid 文本 -> Mermaid 内部解析器 -> 结构化数据 -> Excalidraw 元素数据 -> 导出为静态 SVG`

此路径的详细步骤如下:

1.  **转换:** 使用 `mermaid-to-excalidraw` 库, 将 Mermaid 源码字符串转换为 Excalidraw 的场景数据 (一个包含 `elements` 和 `files` 的 JSON 对象)。此过程利用了 Mermaid.js 的内部解析器, 直接在数据层面进行映射, **不涉及任何 UI 渲染**。
2.  **导出:** 使用 `@excalidraw/utils` 这个轻量级工具库, 将上一步生成的 Excalidraw 场景数据直接导出为 SVG 元素 (`SVGElement`)。
3.  **注入:** 将生成的 SVG 元素动态注入到前端页面的一个 `<div>` 容器中, 完成静态图表的展示。

这个架构的优势是**高性能**和**简单性**。我们只在需要时、在客户端进行一次性的转换和导出, 最终的 DOM 中只增加了一个纯粹的 SVG, 没有任何多余的 JavaScript 逻辑和事件监听。

## 3. 依赖库变更

为了实施此方案, 需要对 `web-learner/package.json` 文件进行以下更改:

1.  **新增依赖:**
    ```json
    "dependencies": {
      ...
      "mermaid-to-excalidraw": "^1.3.0",
      "@excalidraw/utils": "^1.4.0"
    }
    ```
2.  **降级依赖:**
    `mermaid-to-excalidraw` 库依赖于 Mermaid v10.x。因此, 我们必须将项目中的 Mermaid 版本从 v11 降级以确保兼容性。
    ```json
    "dependencies": {
      ...
      "mermaid": "~10.9.0"
    }
    ```
3.  **无需引入的依赖:**
    *   `@excalidraw/excalidraw`: 这个是完整的 React UI 组件库, 在本方案中**不需要**安装。

完成修改后, 需要在 `web-learner` 目录下运行 `npm install` 或 `pnpm install`。

## 4. 代码更改分析

主要的修改将集中在 `web-learner/src/components/MermaidDiagram.tsx` 文件。

#### **重构 `MermaidDiagram.tsx`**

该组件将从一个动态渲染 Mermaid 的组件, 重构为一个动态生成并展示静态 Excalidraw 风格 SVG 的组件。

**伪代码实现:**

```tsx
// web-learner/src/components/MermaidDiagram.tsx

'use client';

import React, { useEffect, useRef, useState } from 'react';
// 1. 引入新的依赖
import { mermaidToExcalidraw } from 'mermaid-to-excalidraw';
import { exportToSvg } from '@excalidraw/utils';
import type { ExcalidrawElement } from '@excalidraw/excalidraw/element/types';

// ... (props interface)

export function MermaidDiagram({ code }: MermaidDiagramProps) {
  const containerRef = useRef<HTMLDivElement | null>(null);
  const [error, setError] = useState<string | null>(null);
  
  // 2. 之前的 normalizedCode 逻辑可以保留, 用于兼容旧的 Mermaid 语法
  const normalizedCode = useMemo(() => { /* ... */ }, [code]);

  useEffect(() => {
    let cancelled = false;

    async function renderStaticExcalidrawSvg() {
      setError(null);
      if (!containerRef.current) return;

      try {
        // 3. 步骤1: 将 Mermaid 码转换为 Excalidraw 场景数据
        const scene = await mermaidToExcalidraw(normalizedCode, {
          // 可选: 字体等配置
        });

        if (cancelled) return;

        // 4. 步骤2: 将场景数据导出为 SVG 元素
        const svgElement = await exportToSvg({
          elements: scene.elements,
          appState: {
            // 配置背景色、尺寸等导出选项
            viewBackgroundColor: 'transparent',
          },
          files: scene.files,
        });

        if (cancelled) return;

        // 5. 步骤3: 清空容器并注入新的 SVG
        containerRef.current.innerHTML = '';
        containerRef.current.appendChild(svgElement);

      } catch (e) {
        if (cancelled) return;
        setError(e instanceof Error ? e.message : 'Failed to render Mermaid diagram');
        // ... (错误处理逻辑)
      }
    }

    renderStaticExcalidrawSvg();

    return () => {
      cancelled = true;
    };
  }, [normalizedCode]);

  // 6. JSX 返回一个简单的 div 容器和错误显示逻辑
  if (error) {
    // ... (错误 UI)
  }

  return (
    <div
      ref={containerRef}
      className="my-4"
      data-role="mermaid-excalidraw-svg"
    />
  );
}
```

#### **相关脚本 (`lint-mermaid.mjs`, `fix-mermaid.mjs`)**

*   这些脚本基于正则表达式, 与 Mermaid 库本身解耦, 因此**不需要立即修改**。
*   但由于它们是为 v11 语法服务的, 在降级到 v10 后, 可能需要观察其行为。如果 v10 的某些有效语法被脚本错误地标记或修复, 未来可能需要调整这些脚本中的规则。

## 5. 风险与权衡

*   **主要风险:** **Mermaid 版本降级**。这是最大的影响。项目中如果使用了任何 Mermaid v11 的新特性 (新的图表类型、语法糖等), 在降级到 v10.9.0 后可能会渲染失败。需要对现有图表进行回归测试。
*   **优点:**
    *   **视觉提升:** 获得统一、美观的 Excalidraw 艺术风格。
    *   **性能卓越:** 最终产物为静态 SVG, 无需加载和运行庞大的 JS 库, 对性能友好。
    *   **维护简单:** 逻辑内聚在单一组件内, 易于理解和维护。
