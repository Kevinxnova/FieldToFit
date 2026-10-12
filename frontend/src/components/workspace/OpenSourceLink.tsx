import { useWorkspace } from './UI';

export function OpenSourceLink({ onClick }: { onClick?: () => void }) {
  const { pick } = useWorkspace();
  return <a className="open-source-link" href="https://github.com/Kevinxnova/FieldToFit" target="_blank" rel="noopener noreferrer" onClick={onClick}
    aria-label={pick('FieldToFit 开源仓库，在新标签页打开 GitHub', 'FieldToFit source on GitHub, opens in a new tab')}>
    <span className="open-source-mark" aria-hidden="true" /><span>OPEN SOURCE</span>
  </a>;
}
