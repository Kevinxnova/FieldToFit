// Inventory authored strings, including JSX text, accessibility labels and templates.
import fs from 'node:fs';
import path from 'node:path';
import ts from '../../frontend/node_modules/typescript/lib/typescript.js';
const strings = {}, pairs = {};
function add(s, file) { if (/[\u3400-\u9fff]/.test(s)) (strings[s] ??= []).push(file); }
function walk(dir) { for (const entry of fs.readdirSync(dir, {withFileTypes:true})) {
  const file = path.join(dir, entry.name);
  if (entry.isDirectory()) { if (entry.name !== 'locale') walk(file); continue; }
  if (!/\.tsx?$/.test(file)) continue;
  const source = ts.createSourceFile(file, fs.readFileSync(file,'utf8'), ts.ScriptTarget.Latest, true, ts.ScriptKind.TSX);
  function visit(n) {
    if (ts.isStringLiteral(n) || ts.isNoSubstitutionTemplateLiteral(n) || ts.isTemplateHead(n) || ts.isTemplateMiddle(n) || ts.isTemplateTail(n)) add(n.text, file);
    if (ts.isJsxText(n)) add(n.text.replace(/\s+/g,' ').trim(), file);
    if (ts.isCallExpression(n) && n.expression.getText(source)==='pick' && n.arguments.length===2 && n.arguments.every(ts.isStringLiteral)) pairs[n.arguments[0].text]=n.arguments[1].text;
    ts.forEachChild(n, visit);
  } visit(source);
}}
walk('frontend/src');
process.stdout.write(JSON.stringify({strings,pairs},null,2));
