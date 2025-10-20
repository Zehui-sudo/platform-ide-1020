// 测试文件 - 用于验证 Learn-linker 插件功能
// 1. 按 F5 启动调试
// 2. 在新窗口中打开此文件
// 3. 选中下面的函数代码
// 4. 按 Cmd+Shift+E 或查看提示

function fibonacci(n) {
    // 计算斐波那契数列
    if (n <= 1) return n;
    
    let prev = 0, curr = 1;
    for (let i = 2; i <= n; i++) {
        [prev, curr] = [curr, prev + curr];
    }
    return curr;
}

// 另一个测试函数
function quickSort(arr) {
    if (arr.length <= 1) return arr;
    
    const pivot = arr[0];
    const left = arr.slice(1).filter(x => x < pivot);
    const right = arr.slice(1).filter(x => x >= pivot);
    
    return [...quickSort(left), pivot, ...quickSort(right)];
}

// 测试步骤：
// 1. 选中任意函数
// 2. 查看是否出现以下提示：
//    - 选中代码末尾的装饰器提示
//    - 状态栏右侧的 AI 解释按钮
//    - （可能的）代码上方的 CodeLens
// 3. 使用 Cmd+Shift+P 输入 "测试 PeekView 功能" 直接测试