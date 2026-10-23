import {Link} from '@fieldtofit/locale/router';
import {useWorkspace} from '../../components/workspace/UI';
import {ROOT} from './data';
import {FlagshipExplorer} from './FlagshipExplorer';
import './home.css';
import './atlas.css';
export function HomeAtlas(){const {pick}=useWorkspace();return <><header className="platform-section-heading evolution-home-heading"><div><p className="evolution-home-eyebrow">2017—2026</p><h2 id="llm-evolution" tabIndex={-1}>{pick('大模型技术演进','LLM technical evolution')}</h2></div><Link to={ROOT}>{pick('探索完整图谱','Explore full maps')} ↗</Link></header><p className="evolution-home-intro">{pick('训练形成能力，推理组织求解，系统让推训高效执行。三张总图，从技术转折连接到具体型号。','Training builds capabilities, inference organizes problem-solving, and systems execute both. Three maps connect technical turning points to specific models.')}</p><FlagshipExplorer home/></>;}
