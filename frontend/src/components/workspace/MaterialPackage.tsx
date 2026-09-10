import { useState } from 'react';
import { BASE, send } from '../../api/knowledge';
import { useWorkspace } from './UI';

export type PackageRef = { id: string; revision: number; name: string };
type Coverage = { requested_objects: number; available_objects: number; unavailable_objects: number; registered_materials: number; included_characters: number; link_only_materials: number; unavailable_materials: number; deferred_materials: number; all_stored_text_included: boolean };
type Package = { generated_at: string; coverage: Coverage; markdown?: string; objects?: unknown[] };

export function MaterialPackage({ references }: { references: PackageRef[] }) {
  const { pick } = useWorkspace();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [result, setResult] = useState<Package | null>(null);
  const [preview, setPreview] = useState('');
  const [copyMessage, setCopyMessage] = useState('');
  const copy = async () => {
    try {
      await navigator.clipboard.writeText(preview);
      setCopyMessage(pick('本次原文包已复制', 'Source package copied'));
    } catch {
      setCopyMessage(pick('浏览器未允许自动复制，请从下方文本框手动复制。', 'Automatic copying is unavailable. Copy from the text area below.'));
    }
  };
  const acquire = async (format: 'json' | 'markdown', download = false) => {
    setBusy(true); setError(''); setResult(null); setPreview(''); setCopyMessage('');
    try {
      const data = await send<Package>('/v1/platform/bundle', {
        objects: references.map(({ id, revision }) => ({ id, revision })), max_characters: 200000, format,
      });
      // Add service context outside original text. Never rewrite source bodies or their hashes.
      const service = new URL(BASE, window.location.origin).href.replace(/\/$/, '');
      const local = ['localhost', '127.0.0.1', '[::1]'].includes(new URL(service).hostname);
      const access = local
        ? 'Included text is readable offline. This service is local to the exporting computer; deferred reads need a client on that computer or a reachable deployment.'
        : 'Included text is readable offline. Deferred reads use this service and may require separately configured read access.';
      const content = format === 'markdown'
        ? data.markdown! + '\n\n## Service for continued reading\n' + service + '\n\n' + access + '\n'
        : JSON.stringify({ ...data, service_url: service, service_access_note: access }, null, 2);
      setResult(data); setPreview(content);
      if (download) {
        const url = URL.createObjectURL(new Blob([content], { type: format === 'markdown' ? 'text/markdown;charset=utf-8' : 'application/json;charset=utf-8' }));
        const a = document.createElement('a'); a.href = url;
        a.download = `fieldtofit-materials-${data.generated_at.slice(0, 10)}.${format === 'markdown' ? 'md' : 'json'}`;
        a.click(); window.setTimeout(() => URL.revokeObjectURL(url), 1000);
      }
    } catch (e) { setError((e as Error).message); }
    finally { setBusy(false); }
  };
  const coverage = result?.coverage;
  return <section className="platform-package" aria-label={pick('含原文资料包', 'Source text package')}>
    <h3>{pick('把原文一起交给 AI', 'Give your AI the source text too')}</h3>
    <p>{pick('包含选定发布版本的档案、所存原文、来源、未知项和截至该版本的公开历史。每包最多 10 个对象、20 万正文字符；超出部分附续读位置。', 'Includes selected publication revisions, stored source text, citations, unknowns and public history through those revisions. Up to 10 objects and 200,000 text characters, with continuation positions for the remainder.')}</p>
    <div className="platform-actions">
      <button className="button primary" disabled={busy || !references.length} onClick={() => acquire('json')}>{pick('预览含原文资料包', 'Preview source package')}</button>
      <button className="button" disabled={busy || !references.length} onClick={() => acquire('markdown', true)}>{pick('下载 Markdown 原文包', 'Download Markdown package')}</button>
      <button className="button" disabled={busy || !references.length} onClick={() => acquire('json', true)}>{pick('下载 JSON 原文包', 'Download JSON package')}</button>
    </div>
    {busy && <p role="status">{pick('正在核对版本并整理原文…', 'Checking revisions and gathering source text…')}</p>}
    {error && <p role="alert">{error}</p>}
    {coverage && <div className="platform-package-coverage" role="status">
      <strong>{coverage.all_stored_text_included ? pick('所存文本已全部包含', 'All stored text included') : pick('部分材料未包含，请查看包内说明', 'Some material is not included; see package details')}</strong>
      <p>{coverage.available_objects} / {coverage.requested_objects} {pick('个对象可用', 'objects available')} · {coverage.included_characters.toLocaleString()} {pick('正文字符', 'source characters')} · {coverage.link_only_materials} {pick('份仅有链接', 'link-only materials')} · {coverage.deferred_materials} {pick('份需续读', 'materials need continuation')} · {coverage.unavailable_materials} {pick('份材料不可用', 'unavailable materials')}</p>
      <p className="muted">{pick('范围限于已登记材料，不代表上游全部文档。文件中的原文可离线交给 AI；仅有链接和未包含部分仍需继续读取。导出后内容可能更新或撤回。', 'Coverage is limited to registered materials, not all upstream documentation. Included text works offline; links and omitted text require further reading. Sources may change or be withdrawn after export.')}</p>
    </div>}
    {preview && <details open><summary>{pick('查看本次资料包', 'Inspect this package')}</summary><button className="button" onClick={copy}>{pick('复制本次原文包', 'Copy this source package')}</button>{copyMessage && <p role="status">{copyMessage}</p>}<textarea aria-label={pick('含原文资料包预览', 'Source package preview')} readOnly rows={12} value={preview} /></details>}
  </section>;
}
