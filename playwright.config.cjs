const { defineConfig, devices } = require('@playwright/test');

module.exports = defineConfig({
  testDir: './tests/browser',
  testMatch: '**/*.spec.cjs',
  fullyParallel: false,
  workers: 1,
  timeout: 60_000,
  expect: { timeout: 15_000 },
  reporter: [['line']],
  outputDir: 'test-results/playwright',
  use: {
    ...devices['Desktop Chrome'],
    headless: true,
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure'
  },
  webServer: {
    command: 'python tests/browser/serve_fixture.py',
    cwd: __dirname,
    wait: {
      stdout: /JARVIS_BROWSER_PORT=(?<JARVIS_BROWSER_PORT>\d+)/
    },
    stdout: 'pipe',
    stderr: 'pipe',
    timeout: 30_000,
    reuseExistingServer: false,
    gracefulShutdown: {
      signal: 'SIGTERM',
      timeout: 1000
    }
  }
});
