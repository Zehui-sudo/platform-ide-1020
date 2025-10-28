module.exports = {
  apps: [
    {
      name: 'platform-api',
      script: 'uvicorn',
      cwd: '/opt/platform-ide',
      interpreter: '/opt/platform-ide/venv/bin/python',
      args: 'scripts.api_server:app --host 0.0.0.0 --port 8000',
      env_file: '/opt/platform-ide/.env',
      env: {
        PYTHONUNBUFFERED: '1',
        SANDBOX_IMAGE: 'platform-ide-python-sandbox:latest',
        CONFIG_PATH: '/opt/platform-ide/config.json'
      }
    },
    {
      name: 'platform-web',
      cwd: '/opt/platform-ide',
      script: 'pnpm',
      args: '--filter @platform-ide/web-learner start',
      env_file: '/opt/platform-ide/.env',
      env: {
        NODE_ENV: 'production'
      }
    }
  ]
};
