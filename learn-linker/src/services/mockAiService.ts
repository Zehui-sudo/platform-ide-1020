import { IAiService, CodeContext } from './ai/IAiService';

export class MockAiService implements IAiService {
    private mockResponses = [
        `# 代码解释

这段代码展示了一个 **函数式编程** 的实现示例。让我为您详细解释：

## 主要功能

该代码片段实现了以下核心功能：

1. **数据处理** - 对输入数据进行转换和处理
2. **错误处理** - 包含了完整的异常捕获机制
3. **性能优化** - 使用了缓存策略提升性能

## 代码结构

\`\`\`javascript
// 示例代码展示
function processData(input) {
    try {
        // 数据验证
        if (!input) {
            throw new Error('Input is required');
        }
        
        // 数据转换
        const transformed = input
            .filter(item => item.isValid)
            .map(item => ({
                ...item,
                processed: true,
                timestamp: Date.now()
            }));
        
        return transformed;
    } catch (error) {
        console.error('Processing failed:', error);
        return [];
    }
}
\`\`\`

## 关键概念

### 1. 函数式编程
- 使用了 \`map\` 和 \`filter\` 等高阶函数
- 避免了副作用，保持函数纯净性

### 2. 错误边界
代码使用了 try-catch 结构来捕获和处理异常：

| 错误类型 | 处理方式 | 返回值 |
|---------|---------|--------|
| 空输入 | 抛出异常 | 空数组 |
| 处理错误 | 记录日志 | 空数组 |
| 验证失败 | 过滤掉 | 继续处理 |

### 3. 性能考虑

优化点包括：
- **惰性求值** - 使用链式调用减少中间变量
- **批量处理** - 一次性处理所有数据
- **缓存机制** - 避免重复计算

## 数学公式示例

如果涉及算法复杂度分析，时间复杂度为：

$$O(n) = n \\cdot \\log(n)$$

其中 $n$ 表示数据集大小。

## 最佳实践建议

1. **添加类型定义** - 使用 TypeScript 提供类型安全
2. **单元测试** - 编写测试覆盖边界情况
3. **文档注释** - 添加 JSDoc 注释说明函数用途

> 💡 **提示**: 这种模式特别适合处理大量数据的场景，可以轻松扩展和维护。

## 相关知识点

- [函数式编程基础](https://example.com/fp-basics)
- [JavaScript 高阶函数](https://example.com/higher-order-functions)
- [错误处理最佳实践](https://example.com/error-handling)`,

        `# 算法分析

这是一个经典的 **动态规划** 算法实现。

## 算法说明

该算法使用了动态规划来解决优化问题，核心思想是：

\`\`\`python
def fibonacci(n):
    """计算斐波那契数列的第n项"""
    if n <= 1:
        return n
    
    # 使用动态规划优化
    dp = [0] * (n + 1)
    dp[0], dp[1] = 0, 1
    
    for i in range(2, n + 1):
        dp[i] = dp[i-1] + dp[i-2]
    
    return dp[n]
\`\`\`

## 复杂度分析

- **时间复杂度**: $O(n)$
- **空间复杂度**: $O(n)$

## 优化建议

可以进一步优化空间复杂度到 $O(1)$：

\`\`\`python
def fibonacci_optimized(n):
    if n <= 1:
        return n
    
    prev, curr = 0, 1
    for _ in range(2, n + 1):
        prev, curr = curr, prev + curr
    
    return curr
\`\`\``,
    ];

    getName(): string {
        return 'Mock AI Service';
    }

    async validateConfig(): Promise<boolean> {
        return true; // Mock service 始终有效
    }

    /**
     * 生成模拟的AI回复，支持流式输出
     */
    public async* generateExplanation(context: CodeContext, signal?: AbortSignal): AsyncGenerator<string> {
        try {
            // 随机选择一个模拟回复
            const response = this.mockResponses[Math.floor(Math.random() * this.mockResponses.length)];
            
            // 将回复按行分割，模拟流式输出
            const lines = response.split('\n');
            
            for (let i = 0; i < lines.length; i++) {
                // 检查是否被取消
                if (signal?.aborted) {
                    throw new Error('Request aborted');
                }
                
                const line = lines[i];
                // 模拟网络延迟
                await this.delay(30 + Math.random() * 50);
                yield line + '\n';
            }
        } catch (error) {
            console.error('[MockAI] Error in generateExplanation:', error);
            throw error;
        }
    }

    /**
     * 获取完整的AI回复（非流式）
     */
    public async getFullExplanation(context: CodeContext, signal?: AbortSignal): Promise<string> {
        // 检查是否被取消
        if (signal?.aborted) {
            throw new Error('Request aborted');
        }
        
        // 随机选择一个模拟回复
        const response = this.mockResponses[Math.floor(Math.random() * this.mockResponses.length)];
        
        // 模拟处理延迟
        await this.delay(500);
        
        // 再次检查是否被取消
        if (signal?.aborted) {
            throw new Error('Request aborted');
        }
        
        // 在回复开头添加代码上下文
        return `## 您选中的代码：

\`\`\`${context.language}
${context.code}
\`\`\`

---

${response}`;
    }

    /**
     * 检测代码语言（简单实现）
     */
    private detectLanguage(code: string): string {
        if (code.includes('function') || code.includes('const') || code.includes('let')) {
            return 'javascript';
        }
        if (code.includes('def ') || code.includes('import ')) {
            return 'python';
        }
        if (code.includes('public') || code.includes('class ') || code.includes('void')) {
            return 'java';
        }
        if (code.includes('fn ') || code.includes('let mut')) {
            return 'rust';
        }
        return 'plaintext';
    }

    private delay(ms: number): Promise<void> {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
}