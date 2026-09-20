const { test, expect } = require('@playwright/test');

function fixtureBaseUrl() {
  const port = process.env.JARVIS_BROWSER_PORT;
  if (!/^\d+$/.test(port || '')) {
    throw new Error('JARVIS_BROWSER_PORT was not captured from the fixture server');
  }
  return `http://127.0.0.1:${port}`;
}

function ownedErrorCollector(page, baseUrl) {
  const errors = [];

  page.on('pageerror', (error) => {
    errors.push(`pageerror: ${error.message}`);
  });

  page.on('console', (message) => {
    if (message.type() !== 'error') return;
    const location = message.location();
    if (!location.url || location.url.startsWith(baseUrl)) {
      errors.push(`console: ${message.text()}`);
    }
  });

  return errors;
}

async function loadHud(page, baseUrl) {
  await page.route('https://fonts.googleapis.com/**', route => route.abort());
  await page.route('https://fonts.gstatic.com/**', route => route.abort());
  await page.goto(baseUrl + '/', { waitUntil: 'domcontentloaded' });
  await expect(page.locator('body')).toHaveClass(/jv-experience-ready/);
  await expect(page.locator('#jarvis-sidebar')).toBeVisible();
}

test('HUD smoke keeps navigation, receipt truth, theme and sidebar behavior operational', async ({ page }) => {
  const baseUrl = fixtureBaseUrl();
  const ownedErrors = ownedErrorCollector(page, baseUrl);

  await loadHud(page, baseUrl);

  await expect(page.locator('#markLivCockpit')).toBeVisible();
  await expect(page.locator('#markLivPhaseRail .mark-liv-phase')).toHaveCount(4);
  await expect(page.locator('#markLivCockpit [data-mark-module]')).toHaveCount(6);
  await expect(page.locator('#markLivTelemetryCluster')).toBeVisible();

  await page.locator('#markLivCockpit [data-mark-module="skills"]').click();
  await expect(page.locator('#tabArsenal')).toHaveClass(/active/);
  await page.locator('#markLivCockpit [data-mark-module="terminal"]').click();
  await expect(page.locator('#tabNeural')).toHaveClass(/active/);

  const body = page.locator('body');
  const root = page.locator('html');
  const sidebarToggle = page.locator('#sidebar-toggle');

  await expect(body).toHaveAttribute('data-sidebar-collapsed', 'false');
  await expect(sidebarToggle).toHaveAttribute('aria-expanded', 'true');

  await sidebarToggle.click();
  await expect(body).toHaveAttribute('data-sidebar-collapsed', 'true');
  await expect(sidebarToggle).toHaveAttribute('aria-expanded', 'false');
  await expect.poll(() => page.evaluate(() => localStorage.getItem('jarvis.sidebar.collapsed'))).toBe('true');

  await page.reload({ waitUntil: 'domcontentloaded' });
  await expect(body).toHaveClass(/jv-experience-ready/);
  await expect(body).toHaveAttribute('data-sidebar-collapsed', 'true');

  await sidebarToggle.click();
  await expect(body).toHaveAttribute('data-sidebar-collapsed', 'false');

  const themeToggle = page.locator('#theme-toggle');
  await expect(root).toHaveAttribute('data-theme', 'dark');
  const darkCanvas = await page.evaluate(() =>
    getComputedStyle(document.documentElement).getPropertyValue('--jv-color-bg-canvas').trim()
  );

  await themeToggle.click();
  await expect(root).toHaveAttribute('data-theme', 'light');
  await expect(themeToggle).toHaveAttribute('aria-pressed', 'true');
  await expect.poll(() => page.evaluate(() => localStorage.getItem('jarvis.theme'))).toBe('light');

  const lightCanvas = await page.evaluate(() =>
    getComputedStyle(document.documentElement).getPropertyValue('--jv-color-bg-canvas').trim()
  );
  expect(lightCanvas).not.toBe(darkCanvas);

  await page.reload({ waitUntil: 'domcontentloaded' });
  await expect(body).toHaveClass(/jv-experience-ready/);
  await expect(root).toHaveAttribute('data-theme', 'light');

  await page.locator('#theme-toggle').click();
  await expect(root).toHaveAttribute('data-theme', 'dark');

  const panelIds = [
    'tabNeural',
    'tabArsenal',
    'tabIngest',
    'tabSubagents',
    'tabSecurity',
    'tabPipeline',
    'tabObsidian'
  ];

  for (const panelId of panelIds) {
    const sidebarItem = page.locator(`#jarvis-sidebar [data-jarvis-tab="${panelId}"]`);
    await sidebarItem.click();
    await expect(page.locator(`#${panelId}`)).toHaveClass(/active/);
    await expect(sidebarItem).toHaveClass(/is-selected/);
    await expect(sidebarItem).toHaveAttribute('aria-current', 'page');
  }

  await page.locator('#jarvis-sidebar [data-jarvis-tab="tabPipeline"]').click();
  await expect(page.locator('#operationalMissionSelect')).toHaveValue('mis-browser-smoke');
  await expect(page.locator('#operationalStatus')).toContainText(
    'Missão mis-browser-smoke: EXECUTED_UNVERIFIED'
  );

  await expect(page.locator('#operationalMissionState')).toHaveText('EXECUTED_UNVERIFIED');
  await expect(page.locator('#operationalMissionOutcome')).toHaveText('—');
  await expect(page.locator('#operationalEventCount')).toHaveText('2');
  await expect(page.locator('#operationalAttemptCount')).toHaveText('1');
  await expect(page.locator('#operationalVerifiedCount')).toHaveText('0');
  await expect(page.locator('#operationalVerificationRate')).toHaveText('—');
  await expect(page.locator('#operationalTokens')).toHaveText('—');
  await expect(page.locator('#operationalCost')).toHaveText('—');
  await expect(page.locator('#operationalLatency')).toHaveText('—');
  await expect(page.locator('#operationalContextList')).toContainText('browser-fixture-source');
  await expect(page.locator('#operationalVerificationList')).toContainText(
    '— Nenhuma verificação observada.'
  );

  expect(ownedErrors).toEqual([]);

  await page.goto(baseUrl + '/assets/design-system/index.html', {
    waitUntil: 'domcontentloaded'
  });
  await expect(page.getByRole('heading', { name: 'JARVIS Design System' })).toBeVisible();
  await expect(page.locator('#cockpit')).toContainText('Operational Cockpit');
  await expect(page.locator('html')).toHaveAttribute('data-theme', 'dark');

  await page.locator('#theme-toggle').click();
  await expect(page.locator('html')).toHaveAttribute('data-theme', 'light');

  expect(ownedErrors).toEqual([]);
});
