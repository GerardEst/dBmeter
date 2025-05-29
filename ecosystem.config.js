module.exports = {
  apps: [
    {
      name: 'dbmeter',
      script: '/var/www/dbmeter/venv/bin/python',
      args: '-m uvicorn main:app --host 0.0.0.0 --port 8000',
      cwd: '/var/www/dbmeter',
      instances: 1,
      autorestart: true,
      watch: false,
      max_memory_restart: '1G',
      time: true,
    },
  ],
};
