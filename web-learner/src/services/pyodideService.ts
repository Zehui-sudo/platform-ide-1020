interface ExecutionResponse {
  status: 'success' | 'timeout' | 'error';
  language: string;
  stdout: string;
  stderr: string;
  exitCode: number | null;
  timedOut: boolean;
  duration: number;
}

const API_BASE = (process.env.NEXT_PUBLIC_BACKEND_URL || '').replace(/\/$/, '');
const EXECUTE_ENDPOINT = `${API_BASE}/api/execute/run`;

class RemoteExecutionService {
  async runPython(code: string): Promise<{ output: string; error: string | null }> {
    const res = await fetch(
      EXECUTE_ENDPOINT,
      {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ language: 'python', code }),
      }
    );

    if (!res.ok) {
      const text = await res.text();
      throw new Error(`执行服务不可用：${res.status} ${text}`);
    }

    const data = (await res.json()) as ExecutionResponse;
    if (data.status === 'timeout') {
      throw new Error('执行超时，请优化代码或减少运行时间。');
    }

    return {
      output: data.stdout ?? '',
      error: data.stderr ? String(data.stderr) : null,
    };
  }
}

export const pyodideService = new RemoteExecutionService();
