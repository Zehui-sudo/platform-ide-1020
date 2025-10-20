import * as vscode from 'vscode';
import { ExplainCodeLensProvider } from './providers/codeLensProvider';
import { SelectionDecoratorProvider } from './providers/selectionDecoratorProvider';
import { WebviewManager } from './webview/WebviewManager';
import { ContextCollector } from './services/contextCollector';
import { AiServiceFactory } from './services/ai/aiServiceFactory';

export function activate(context: vscode.ExtensionContext) {
	console.log('Learn-linker extension is now active!');
	
	// 输出扩展路径，便于调试
	console.log('Extension path:', context.extensionPath);

	// 创建 WebView 管理器
	const webviewManager = new WebviewManager(context);

	// 创建模拟 AI 服务（预留给后续使用）
	// const aiService = new MockAiService();

	// 注册 CodeLens Provider（备选方案1）
	const codeLensProvider = new ExplainCodeLensProvider(webviewManager);
	
	// 注册多种文件类型的 CodeLens
	const languageSelectors = [
		{ language: 'javascript', scheme: 'file' },
		{ language: 'typescript', scheme: 'file' },
		{ language: 'javascriptreact', scheme: 'file' },
		{ language: 'typescriptreact', scheme: 'file' },
		{ language: 'python', scheme: 'file' },
		{ language: 'java', scheme: 'file' },
		{ language: 'cpp', scheme: 'file' },
		{ language: 'c', scheme: 'file' },
		{ language: 'go', scheme: 'file' },
		{ language: 'rust', scheme: 'file' },
		{ pattern: '**/*', scheme: 'file' } // 兜底：所有文件
	];
	
	const codeLensDisposable = vscode.languages.registerCodeLensProvider(
		languageSelectors,
		codeLensProvider
	);
	
	console.log('[Extension] CodeLens provider registered for languages');
	
	// 创建选择装饰器提供者（备选方案2）
	const decoratorProvider = new SelectionDecoratorProvider();
	console.log('[Extension] Selection decorator provider created');

	// 注册解释代码命令
	const explainCommand = vscode.commands.registerCommand(
		'learn-linker.explainCode',
		async (document: vscode.TextDocument, range: vscode.Range) => {
			console.log('[Command] explainCode triggered');
			
			// 收集代码上下文
			const codeContext = await ContextCollector.collectContext(document, range);
			
			// 显示 WebView 并开始解释
			await webviewManager.showExplanation(codeContext);
			
			// 显示状态栏消息
			vscode.window.setStatusBarMessage('🤖 正在生成代码解释...', 3000);
		}
	);

	// 注册快捷键命令 (用于直接触发)
	const quickExplainCommand = vscode.commands.registerCommand(
		'learn-linker.quickExplain',
		async () => {
			console.log('[Command] quickExplain triggered');
			const editor = vscode.window.activeTextEditor;
			if (!editor) {
				vscode.window.showWarningMessage('请先选择要解释的代码');
				return;
			}

			const selection = editor.selection;
			if (selection.isEmpty) {
				vscode.window.showWarningMessage('请先选择要解释的代码');
				return;
			}

			// 收集代码上下文
			const codeContext = await ContextCollector.collectContext(
				editor.document, 
				selection
			);
			
			console.log('[Command] Selected code length:', codeContext.code.length);
			await webviewManager.showExplanation(codeContext);
			vscode.window.setStatusBarMessage('🤖 正在生成代码解释...', 3000);
		}
	);

	// 测试命令 - 用于验证功能
	const testCommand = vscode.commands.registerCommand(
		'learn-linker.testPeekView',
		async () => {
			const testCode = `function fibonacci(n) {
    if (n <= 1) return n;
    
    let prev = 0, curr = 1;
    for (let i = 2; i <= n; i++) {
        [prev, curr] = [curr, prev + curr];
    }
    return curr;
}`;
			const testContext = {
				code: testCode,
				language: 'javascript',
				fileName: 'test.js'
			};
			await webviewManager.showExplanation(testContext);
			vscode.window.showInformationMessage('测试 PeekView 功能已启动');
		}
	);

	// 配置 API Key 命令
	const configureApiKeyCommand = vscode.commands.registerCommand(
		'learn-linker.configureApiKey',
		async () => {
			const provider = await vscode.window.showQuickPick(
				['deepseek'],
				{
					placeHolder: '选择 AI 服务提供商'
				}
			);

			if (provider === 'deepseek') {
				const apiKey = await vscode.window.showInputBox({
					prompt: '请输入 DeepSeek API Key',
					placeHolder: 'sk-...',
					password: true,
					ignoreFocusOut: true,
					validateInput: (value) => {
						if (!value) {
							return 'API Key 不能为空';
						}
						if (!value.startsWith('sk-')) {
							return 'API Key 格式不正确';
						}
						return null;
					}
				});

				if (apiKey) {
					// 安全存储 API Key
					await context.secrets.store('learnLinker.deepseekApiKey', apiKey);
					
					// 更新配置，启用 DeepSeek
					await vscode.workspace.getConfiguration('learnLinker').update(
						'aiProvider', 
						'deepseek',
						vscode.ConfigurationTarget.Global
					);
					
					// 清除缓存的服务实例
					AiServiceFactory.clearInstance();
					
					vscode.window.showInformationMessage('API Key 已配置成功！');
				}
			}
		}
	);

	// 保留原有的 Hello World 命令用于测试
	const helloCommand = vscode.commands.registerCommand('learn-linker.helloWorld', () => {
		vscode.window.showInformationMessage('Learn-linker 插件已激活！选择代码查看 AI 解释。');
	});

	// 注册所有 disposables
	context.subscriptions.push(
		codeLensDisposable,
		decoratorProvider,
		explainCommand,
		quickExplainCommand,
		testCommand,
		configureApiKeyCommand,
		helloCommand
	);

	// 显示激活成功消息
	vscode.window.showInformationMessage('Learn-linker 已激活！选择代码后按 Cmd+Shift+K 获取AI解释。');
}

export function deactivate() {
	console.log('Learn-linker extension deactivated');
}
