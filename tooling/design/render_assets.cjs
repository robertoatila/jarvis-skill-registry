// Optional raster exports. Usage: node render_assets.cjs [absolute sharp module path]
// SVG remains the editable source. No network or package installation is performed.
const fs = require('node:fs');
const path = require('node:path');
const sharp = require(process.argv[2] || 'sharp');
const root = path.resolve(__dirname, '../..');
async function main() {
  const manifest = JSON.parse(fs.readFileSync(path.join(root, 'docs/assets/asset-manifest.json'), 'utf8'));
  for (const asset of manifest) {
    const source = path.join(root, asset.path);
    const target = source.replace(/\.svg$/, '.png');
    await sharp(source).png({compressionLevel: 9}).toFile(target);
    console.log(path.relative(root, target));
  }
}
main().catch(error => { console.error(error); process.exitCode = 1; });
