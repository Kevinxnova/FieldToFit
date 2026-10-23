import {type ReactNode} from 'react';
import {useLocation} from '@fieldtofit/locale/router';
import {useWorkspace} from '../../components/workspace/UI';
import {PageMetadata} from '../../search';
import {FlagshipExplorer} from './FlagshipExplorer';
import './atlas.css';
export {NodeDetail} from './NodeDetail';
export function AtlasMap({navigation,footer}:{navigation:ReactNode;footer:ReactNode}){
  const {pick}=useWorkspace(),location=useLocation();
  return <div className="evo-page atlas-page"><PageMetadata title={pick('大模型技术演进 · FieldToFit','LLM technical evolution · FieldToFit')} description={pick('2017—2026训练、推理、系统三张技术总图，追溯旗舰型号的公开技术路线。','Trace disclosed flagship approaches across training, inference and systems maps, 2017–2026.')} path={location.pathname}/>{navigation}<header className="evo-hero atlas-master-hero"><p className="evo-eyebrow">2017—2026</p><h1>{pick('大模型技术演进','How large models evolved')}</h1><p>{pick('沿时间理解技术的分叉与汇合，再看今天的模型走到了哪里。','Follow technical branches through time, then see where today’s models fit.')}</p></header><FlagshipExplorer/>{footer}</div>;
}
