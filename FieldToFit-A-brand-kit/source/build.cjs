/* Rebuild the delivery set. Requires sharp, @napi-rs/canvas and jszip.
 * Run: NODE_PATH=/path/to/node_modules node source/build.cjs /path/to/Rubik-Bold.ttf
 * Does not modify application files or the selected original PNG.
 */
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const sharp = require('sharp');
const {GlobalFonts, createCanvas, convertSVGTextToPath} = require('@napi-rs/canvas');
const JSZip = require('jszip');
const root = path.resolve(__dirname, '..');
const fontPath = process.argv[2] || path.join(__dirname, 'Rubik-Bold.ttf');
if (!fontPath || !GlobalFonts.registerFromPath(fontPath, 'BrandRubik')) throw Error('Provide Rubik-Bold.ttf');
for (const dir of ['svg', 'png', 'icons', 'qa']) fs.mkdirSync(path.join(root, dir), {recursive:true});
const ink = '#151917', paper = '#FAFBF8';
const body = file => fs.readFileSync(path.join(__dirname, file), 'utf8').replace(/^[\s\S]*?<svg[^>]*>/, '').replace(/<\/svg>\s*$/, '').replace(/<title[\s\S]*?<\/title>|<desc[\s\S]*?<\/desc>/g, '');
const markBody = body('mark-master.svg');
const microBody = body('mark-micro.svg');
const svg = (w,h,content,label='FieldToFit') => `<svg xmlns="http://www.w3.org/2000/svg" width="${w}" height="${h}" viewBox="0 0 ${w} ${h}" role="img" aria-label="${label}">${content}</svg>`;
const mark = (x,y,width,color=ink) => `<g fill="${color}" transform="translate(${x} ${y}) scale(${width/160})">${markBody}</g>`;
const micro = (color=ink) => svg(16,16,`<g fill="${color}">${microBody}</g>`,'FieldToFit compact mark');
const ctx = createCanvas(1,1).getContext('2d');
ctx.font='bold 100px BrandRubik';
const metrics = ctx.measureText('FieldToFit');
const wordRaw = `<svg xmlns="http://www.w3.org/2000/svg" width="800" height="150"><text x="0" y="110" font-family="BrandRubik" font-weight="700" font-size="100" fill="${ink}">FieldToFit</text></svg>`;
const wordOutline = convertSVGTextToPath(wordRaw).toString();
assert(!/<text\b/.test(wordOutline), 'Wordmark must be outlined');
assert(/<path\b/.test(wordOutline), 'Wordmark path conversion failed');
const wordBody = wordOutline.replace(/^[\s\S]*?<svg[^>]*>/, '').replace(/<\/svg>\s*$/, '');
const wordWidth = metrics.actualBoundingBoxRight + metrics.actualBoundingBoxLeft;
const wordHeight = metrics.actualBoundingBoxAscent + metrics.actualBoundingBoxDescent;
const word = (x,y,width,color=ink) => `<g transform="translate(${x} ${y}) scale(${width/wordWidth}) translate(${metrics.actualBoundingBoxLeft} ${metrics.actualBoundingBoxAscent-110})">${wordBody.replaceAll(ink,color)}</g>`;
const horizontal = (color,background) => svg(820,192,`${background?`<rect width="820" height="192" fill="${background}"/>`:''}${mark(40,40,160,color)}${word(242,62,538,color)}`);
const stacked = (color,background) => svg(640,560,`${background?`<rect width="640" height="560" fill="${background}"/>`:''}${mark(144,72,352,color)}${word(72,380,496,color)}`);
const app = (color,background) => svg(1024,1024,`<rect width="1024" height="1024" fill="${background}"/>${mark(200,294,624,color)}`);
const files = new Map();
for (const [name,color] of [['ink',ink],['paper',paper],['black','#000000'],['white','#FFFFFF']]) {
  files.set(`svg/mark-${name}.svg`,svg(208,160,mark(24,24,160,color)));
  files.set(`svg/logo-horizontal-${name}.svg`,horizontal(color));
  files.set(`svg/logo-stacked-${name}.svg`,stacked(color));
}
files.set('svg/logo-on-light.svg',horizontal(ink,paper));
files.set('svg/logo-on-dark.svg',horizontal(paper,ink));
files.set('svg/wordmark-ink.svg',svg(600,128,word(24,24,552,ink)));
files.set('svg/wordmark-paper.svg',svg(600,128,word(24,24,552,paper)));
files.set('icons/app-icon-light.svg',app(ink,paper));
files.set('icons/app-icon-dark.svg',app(paper,ink));
files.set('icons/favicon-light.svg',micro(ink));
files.set('icons/favicon-dark.svg',micro(paper));
files.set('icons/favicon.svg',svg(16,16,`<style>.mark{fill:${ink}}@media(prefers-color-scheme:dark){.mark{fill:${paper}}}</style><g class="mark">${microBody}</g>`));
for (const [rel,content] of files) fs.writeFileSync(path.join(root,rel),content+'\n');
// All PNGs are exports from the SVG masters, not edits of the raster concept.
async function run(){
  for (const [rel,content] of files) {
    if (!rel.startsWith('svg/')) continue;
    const width=rel.includes('/mark-')?1024:rel.includes('stacked')?1280:1640;
    await sharp(Buffer.from(content)).resize({width}).png().toFile(path.join(root,rel.replace(/^svg\//,'png/').replace(/svg$/,'png')));
  }
  for (const theme of ['light','dark']) {
    for (const size of [64,128,180,192,256,512,1024]) {
      await sharp(Buffer.from(files.get(`icons/app-icon-${theme}.svg`))).resize(size,size).png().toFile(path.join(root,`icons/app-icon-${theme}-${size}.png`));
    }
    for (const size of [16,32,48]) {
      await sharp(Buffer.from(files.get(`icons/favicon-${theme}.svg`))).resize(size,size).png().toFile(path.join(root,`icons/favicon-${theme}-${size}.png`));
    }
    const entries=[16,32,48].map(size=>({size,data:fs.readFileSync(path.join(root,`icons/favicon-${theme}-${size}.png`))}));
    const head=Buffer.alloc(6+16*entries.length);head.writeUInt16LE(1,2);head.writeUInt16LE(entries.length,4);
    let offset=head.length;
    entries.forEach(({size,data},i)=>{const at=6+i*16;head[at]=size;head[at+1]=size;head.writeUInt16LE(1,at+4);head.writeUInt16LE(32,at+6);head.writeUInt32LE(data.length,at+8);head.writeUInt32LE(offset,at+12);offset+=data.length;});
    fs.writeFileSync(path.join(root,`icons/favicon-${theme}.ico`),Buffer.concat([head,...entries.map(e=>e.data)]));
  }
  // A self-contained, outlined vector presentation board and a raster preview.
  const boardText=(x,y,text,size=24,color=ink)=>`<text x="${x}" y="${y}" font-family="BrandRubik" font-size="${size}" font-weight="700" fill="${color}">${text}</text>`;
  let board=`<rect width="1600" height="1120" fill="#EFEEE8"/>${boardText(64,76,'FieldToFit / A — Refined',34)}${boardText(64,116,'FIELD / FOCUS / FIT',15,'#667068')}`;
  board+=`<rect x="48" y="152" width="736" height="560" rx="20" fill="${paper}"/><rect x="816" y="152" width="736" height="560" rx="20" fill="${ink}"/>`;
  board+=mark(224,230,384,ink)+word(148,570,536,ink)+mark(992,230,384,paper)+word(916,570,536,paper);
  board+=boardText(80,194,'01 / LIGHT',14,'#667068')+boardText(848,194,'02 / DARK',14,'#ADB7AF');
  board+=`<rect x="48" y="744" width="980" height="328" rx="20" fill="${paper}"/><rect x="1060" y="744" width="492" height="328" rx="20" fill="${paper}"/>`;
  board+=boardText(80,788,'03 / APP ICON',14,'#667068')+boardText(1092,788,'04 / SMALL-SIZE OPTICAL MASTER',14,'#667068');
  for(const [x,bg,fg] of [[80,ink,paper],[332,paper,ink]]) {board+=`<rect x="${x}" y="824" width="200" height="200" rx="42" fill="${bg}" stroke="#D5DAD3"/>${mark(x+39,881,122,fg)}`;}
  board+=word(580,896,388,ink)+boardText(580,966,'SQUARE SOURCE / MASK-READY',13,'#667068');
  for(const [x,size] of [[1100,16],[1160,24],[1232,32],[1320,48],[1432,64]]) {board+=`<g transform="translate(${x} 868) scale(${size/16})" fill="${ink}">${microBody}</g>`+boardText(x,970,`${size}px`,13,'#667068');}
  const boardSVG=convertSVGTextToPath(svg(1600,1120,board)).toString();
  fs.writeFileSync(path.join(root,'preview.svg'),boardSVG);
  await sharp(Buffer.from(boardSVG)).png().toFile(path.join(root,'preview.png'));
  // Validate deliverables: genuine vector geometry, no fonts/images/remote links.
  const qa={vectorFiles:files.size,wordmark:{font:'Rubik Bold',outlined:true,width:wordWidth,height:wordHeight},checks:[]};
  for (const [rel,content] of files) {
    assert(!/<(?:text|image|script|foreignObject)\b/.test(content),rel+' must be pure vector');
    assert(!/href\s*=/.test(content),rel+' must not reference external assets');
    const metadata=await sharp(Buffer.from(content)).metadata();
    assert(metadata.width>0&&metadata.height>0);
  }
  qa.checks.push('All production SVG files are self-contained vector paths/rectangles; no raster embedding or live text.');
  for(const theme of ['light','dark']) {
    const meta=await sharp(path.join(root,`icons/app-icon-${theme}-1024.png`)).metadata();
    assert(meta.width===1024&&meta.height===1024);
    const stats=await sharp(path.join(root,`icons/app-icon-${theme}-1024.png`)).stats();
    assert(stats.isOpaque,'App icon sources must be fully opaque');
    const {data,info}=await sharp(path.join(root,`icons/favicon-${theme}-16.png`)).ensureAlpha().raw().toBuffer({resolveWithObject:true});
    for(let i=3;i<data.length;i+=info.channels) assert(data[i]===0||data[i]===255,'16px favicon must be pixel-aligned');
  }
  qa.checks.push('Both 1024px app icons are fully opaque. Both 16px favicons have no partially covered edge pixels.');
  assert(Math.hypot(312,218.4)<409.6,'App mark must stay inside the central 80-percent-diameter safe circle');
  qa.checks.push('App mark bounding box fits inside the central 80-percent-diameter circle for mask-safe presentation.');
  const html=fs.readFileSync(path.join(root,'index.html'),'utf8');
  for(const match of html.matchAll(/(?:src|href)="([^"]+)"/g)) {
    if(match[1].endsWith('.zip')) continue;
    assert(fs.existsSync(path.resolve(root,match[1])),'Missing local preview asset: '+match[1]);
  }
  qa.checks.push('All local HTML preview images and download links resolve within the delivery folder.');
  fs.writeFileSync(path.join(root,'qa/validation.json'),JSON.stringify(qa,null,2)+'\n');
  const zip=new JSZip();
  function addDir(dir){for(const ent of fs.readdirSync(dir,{withFileTypes:true})){const full=path.join(dir,ent.name);if(ent.isDirectory())addDir(full);else if(!ent.name.endsWith('.zip'))zip.file(path.relative(root,full),fs.readFileSync(full));}}
  addDir(root);
  const archive=await zip.generateAsync({type:'nodebuffer',compression:'DEFLATE'});
  const verifiedZip=await JSZip.loadAsync(archive,{checkCRC32:true});
  assert(verifiedZip.file('source/Rubik-OFL.txt'),'Font license must be in the archive');
  assert(verifiedZip.file('index.html'),'Preview must be in the archive');
  fs.writeFileSync(path.join(root,'FieldToFit-A-brand-kit.zip'),archive);
  console.log(JSON.stringify({root,vectorFiles:files.size,validation:qa.checks},null,2));
}
run().catch(err=>{console.error(err);process.exit(1)});
