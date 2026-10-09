const { createRequire } = require('node:module')
const herramientas = createRequire(process.env.TEST_TOOLS_PATH + '/package.json')
const { defineConfig } = herramientas('@playwright/test')
module.exports = defineConfig({
  testDir: __dirname, testMatch: '**/*.spec.cjs', workers: 1, timeout: 90000, expect: { timeout: 10000 },
  outputDir: '/tmp/muneco-e2e/resultados',
  use: { actionTimeout: 15000, baseURL: 'http://127.0.0.1:5179', headless: true,
    launchOptions: { executablePath: '/usr/bin/google-chrome', args: ['--no-sandbox'] },
    screenshot: 'only-on-failure', trace: 'retain-on-failure' },
})
