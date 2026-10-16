const { chromium } = require('playwright');
const assert = require('node:assert/strict');

(async () => {
  console.log('[*] Conectando ao HUD Cockpit em http://127.0.0.1:8899/ ...');
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  
  await page.goto('http://127.0.0.1:8899/', { waitUntil: 'domcontentloaded' });
  await page.waitForSelector('#markLivDock', { timeout: 10000 });
  
  // 1. Verificar botão do HOLO na barra de dock flutuante Mark-LIV
  const holoDockBtn = page.locator('#markLivDock button[data-mark-action="holo"]');
  await holoDockBtn.waitFor({ state: 'visible', timeout: 5000 });
  const title = await holoDockBtn.getAttribute('title');
  console.log('[PASS] Botão HOLO na dock Mark-LIV visível! Título:', title);
  assert.equal(title, 'HOLO — Deck Holográfico 3D com Gestos');

  // 2. Navegar para a aba Obsidian Vault pelo dock Mark-LIV
  await page.click('#markLivDock button[data-mark-action="obsidian"]');
  await page.waitForTimeout(600);
  const text = await page.textContent('#tabObsidian');
  assert.ok(text.includes('Deck Holográfico com Controle por Gestos'), 'Cartão HOLO presente na aba Obsidian');
  console.log('[PASS] Cartão do HOLO presente e renderizado na aba Obsidian Vault!');

  await browser.close();
  console.log('[OK] TODOS OS TESTES DE INTEGRAÇÃO DO HUD COCKPIT PASSARAM COM 100% DE SUCESSO!');
})();
