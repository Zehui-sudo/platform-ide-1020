import { createRoot } from 'react-dom/client';
import App from './App';
import 'katex/dist/katex.min.css';

// 获取 VS Code API
declare global {
    interface Window {
        acquireVsCodeApi?: () => any;
        vscode?: any;
        vsCodeApiReady?: boolean;
    }
}

// 使用全局的 vscode API（如果已经被内联脚本获取）
// 或者自己获取（如果还没有）
const vscode = window.vscode || (window.acquireVsCodeApi ? window.acquireVsCodeApi() : null);

if (!vscode) {
    console.error('Failed to get VSCode API');
}

// 渲染 React 应用
const container = document.getElementById('root');
if (container) {
    const root = createRoot(container);
    root.render(<App vscode={vscode} />);
}