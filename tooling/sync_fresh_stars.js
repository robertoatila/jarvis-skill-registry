const fs = require('fs');
const path = require('path');
const https = require('https');

const TOKEN = process.env.GITHUB_TOKEN || process.env.GH_TOKEN || '';
const CACHE_FILE = path.join(__dirname, '..', 'cache', 'starred_catalog.json');

function fetchPage(page) {
  return new Promise((resolve, reject) => {
    const headers = {
      'User-Agent': 'JARVIS-Sync-Engine',
      'Accept': 'application/vnd.github.v3+json'
    };
    if (TOKEN) {
      headers['Authorization'] = `Bearer ${TOKEN}`;
    }
    const options = {
      hostname: 'api.github.com',
      path: `/user/starred?per_page=100&page=${page}`,
      method: 'GET',
      headers: headers
    };
    https.get(options, (res) => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        if (res.statusCode >= 200 && res.statusCode < 300) {
          try {
            resolve(JSON.parse(data));
          } catch (e) {
            reject(e);
          }
        } else {
          reject(new Error(`GitHub API HTTP ${res.statusCode}: ${data}`));
        }
      });
    }).on('error', reject);
  });
}

async function run() {
  console.log('Iniciando sincronizacao de novos repositorios favoritados...');
  let existing = [];
  if (fs.existsSync(CACHE_FILE)) {
    existing = JSON.parse(fs.readFileSync(CACHE_FILE, 'utf-8'));
  }
  const existingMap = new Map();
  for (const r of existing) {
    existingMap.set(r.full_name || r.name, r);
  }
  console.log(`Existentes no catalogo local: ${existing.length}`);

  // Fetch first 3 pages (up to 300 latest stars) to catch all fresh favorites
  let added = 0;
  for (let p = 1; p <= 3; p++) {
    console.log(`Baixando pagina ${p} de estrelas...`);
    const pageData = await fetchPage(p);
    if (!pageData || pageData.length === 0) break;
    for (const r of pageData) {
      const key = r.full_name || r.name;
      const normalized = {
        name: r.name,
        full_name: r.full_name,
        html_url: r.html_url,
        description: r.description || '',
        stars: r.stargazers_count,
        language: r.language || 'Unknown',
        topics: r.topics || []
      };
      if (!existingMap.has(key)) {
        existing.unshift(normalized);
        existingMap.set(key, normalized);
        added++;
        console.log(`  + NOVO REPOSITORIO: ${r.full_name} (${r.stargazers_count} stars)`);
      }
    }
  }

  console.log(`Novos repositorios adicionados: ${added}`);
  console.log(`Total agora no catalogo: ${existing.length}`);
  fs.writeFileSync(CACHE_FILE, JSON.stringify(existing, null, 2), 'utf-8');
  console.log('Catalogo atualizado com sucesso em:', CACHE_FILE);
}

run().catch(err => {
  console.error('Erro na sincronizacao:', err);
});
