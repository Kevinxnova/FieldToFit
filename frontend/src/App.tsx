import { ForYou, ForAI, AboutFieldToFit, LegacyPlatformEntry } from "./pages/Platform";
import { useEffect } from "react";
import {
  BrowserRouter,
  Link,
  Navigate,
  NavLink,
  Route,
  Routes,
  useLocation,
} from "react-router-dom";
import Explore from "./pages/Explore";
import Dossier from "./pages/Dossier";
import Admin from "./legacy/pages/Admin";
import {
  Account,
  Cases,
  Collection,
  Compare,
  Feedback,
  NotFound,
  Sources,
} from "./pages/WorkspacePages";
import {
  Icon,
  WorkspaceProvider,
  useWorkspace,
} from "./components/workspace/UI";
import Manage from "./pages/KnowledgeOps";
import TaskWorkbench from "./pages/TaskWorkbench";
import { DailyBriefs } from "./pages/KnowledgeReading";
import "./workspace.css";

function Shell() {
  const { pick, zh, dark, toggleLang, toggleTheme, compare, clearCompare } =
    useWorkspace();
  const location = useLocation();
  const links = [
    ["/for-you", "news", "For you", "For you"],
    ["/for-your-ai", "code", "For your AI", "For your AI"],
  ];
  const active = [
    ...links,
    ["/about", "info", "关于 FieldToFit", "About FieldToFit"],
    ["/collection", "bookmark", "我的收藏", "My collection"],
    ["/tasks", "book", "任务工作台", "Task workbench"],
    ["/briefs", "news", "每日简报", "Daily briefs"],
    ["/sources", "source", "数据来源", "Sources"],
    ["/admin", "settings", "运行管理", "Management"],
    ["/account", "user", "我的账户", "Account"],
    ["/feedback", "flag", "反馈需求", "Feedback"],
  ].find((x) => location.pathname === x[0] || location.pathname.startsWith(x[0] + "/"));
  useEffect(() => {
    window.scrollTo(0, 0);
    document.title = `FieldToFit · ${active ? pick(active[2], active[3]) : pick("资料详情", "Dossier")}`;
  }, [location.pathname, zh]);
  return (
    <div className="workspace">
      <a className="skip-link" href="#main-content">
        {pick("跳到主要内容", "Skip to content")}
      </a>
      <aside className="sidebar">
        <Link to="/for-you" className="brand" aria-label="FieldToFit">
          <img className="brand-logo brand-light" src="/brand/logo-horizontal-ink.svg" alt="FieldToFit" />
          <img className="brand-logo brand-dark" src="/brand/logo-horizontal-paper.svg" alt="FieldToFit" />
        </Link>
        <div className="brand-caption">
          {pick("给你看，也给你的 AI 用", "For you. For your AI.")}
        </div>
        <div className="nav-label">READ & CONNECT</div>
        <nav
          className="primary-nav"
          aria-label={pick("主导航", "Main navigation")}
        >
          {links.map(([url, icon, cn, en]) => (
            <NavLink key={url} to={url}>
              <Icon name={icon} size={19} />
              <span>{pick(cn, en)}</span>
              <small>{url === "/for-you" ? pick("给你看", "READ") : pick("给 AI 用", "MCP")}</small>
            </NavLink>
          ))}
        </nav>
        <div className="sidebar-note">
          <span className="note-star">✳</span>
          <p>
            {pick(
              "读懂重点，\n保留依据。",
              "Read the essentials.\nKeep the sources.",
            )}
          </p>
          <Link to="/feedback">
            {pick("分享你的真实需求", "Share a real need")}
            <Icon name="up" size={14} />
          </Link>
        </div>
        <nav
          className="secondary-nav"
          aria-label={pick("辅助导航", "More navigation")}
        >
          <NavLink to="/about"><Icon name="info" size={18} />{pick("关于 FieldToFit", "About FieldToFit")}</NavLink>
          <NavLink to="/collection"><Icon name="bookmark" size={18} />{pick("本地收藏", "Local bookmarks")}</NavLink>
          <NavLink to="/sources">
            <Icon name="source" size={18} />
            {pick("数据来源", "Sources")}
          </NavLink>
          <NavLink to="/admin">
            <Icon name="settings" size={18} />
            {pick("运行管理", "Management")}
          </NavLink>
          <button className="nav-unavailable" type="button" disabled>
            <Icon name="user" size={18} />
            <span>{pick("我的账户", "Account")}</span>
            <small className="coming-soon-badge">
              {pick("待开放", "Coming soon")}
            </small>
          </button>
        </nav>
        <div className="sidebar-footer">
          <span className="status-dot" />
          OPEN KNOWLEDGE · DAILY
        </div>
      </aside>
      <div className="workspace-main">
        <header className="topbar">
          <div className="breadcrumb">
            <span>FieldToFit</span>
            <span>/</span>
            <strong>
              {active
                ? pick(active[2], active[3])
                : pick("资料详情", "Dossier")}
            </strong>
          </div>
          <div className="topbar-actions">
            <span className="update-badge">
              <Icon name="clock" size={14} />
              {pick("每 1 天检查", "Checked daily")}
            </span>
            <button
              className="icon-button"
              aria-label={pick(
                dark ? "切换浅色" : "切换深色",
                dark ? "Light theme" : "Dark theme",
              )}
              onClick={toggleTheme}
            >
              <Icon name={dark ? "sun" : "moon"} size={18} />
            </button>
            <button className="language-button" onClick={toggleLang}>
              {zh ? "EN" : "中文"}
            </button>
            <Link
              to="/collection"
              className="avatar"
              aria-label={pick("我的资料", "My library")}
            >
              M
            </Link>
          </div>
        </header>
        <main id="main-content" className="page-content">
          {[/^\/legacy\//, /^\/(tasks|compare|cases|briefs|records)(\/|$)/].some(pattern => pattern.test(location.pathname)) && <p className="platform-notice">{pick("这是保留的兼容页面。新主入口是 For you 与 For your AI；案例仍暂缓。", "This is a compatibility page. Use For you and For your AI for the new platform; cases remain pending.")} <Link to="/for-you">For you →</Link></p>}
          <Routes>
            <Route path="/" element={<Navigate to="/for-you" replace />} />
            <Route path="/for-you" element={<ForYou />} />
            <Route path="/for-your-ai" element={<ForAI />} />
            <Route path="/about" element={<AboutFieldToFit />} />
            <Route path="/tasks" element={<TaskWorkbench />} />
            <Route path="/briefs" element={<DailyBriefs />} />
            <Route
              path="/information"
              element={<LegacyPlatformEntry />}
            />
            <Route path="/apps" element={<LegacyPlatformEntry />} />
            <Route path="/legacy/information" element={<Explore mode="information" />} />
            <Route path="/legacy/apps" element={<Explore mode="resource" />} />
            <Route path="/records/:id" element={<Dossier />} />
            <Route path="/collection" element={<Collection />} />
            <Route path="/compare" element={<Compare />} />
            <Route path="/sources" element={<Sources />} />
            <Route path="/connect" element={<Navigate to="/for-your-ai" replace />} />
            <Route path="/cases" element={<Cases />} />
            <Route path="/account" element={<Account />} />
            <Route path="/feedback" element={<Feedback />} />
            <Route path="/admin" element={<Manage />} />
            <Route
              path="/admin/curation"
              element={<Admin lang={zh ? "zh" : "en"} />}
            />
            <Route path="/discover" element={<Navigate to="/apps" replace />} />
            <Route
              path="/daily-news"
              element={<Navigate to="/information?kind=event" replace />}
            />
            <Route
              path="/community"
              element={<Navigate to="/feedback" replace />}
            />
            <Route path="*" element={<NotFound />} />
          </Routes>
          <footer className="page-footer">
            <Link to="/about">{pick("关于 FieldToFit", "About FieldToFit")}</Link>
            <p>
              {pick(
                "让知识有来处，让行动有依据。",
                "Knowledge with sources. Decisions with evidence.",
              )}
            </p>
            <Link to="/feedback">
              {pick("反馈与建议", "Feedback")}
              <Icon name="up" size={13} />
            </Link>
          </footer>
        </main>
      </div>
      {compare.length > 0 && !["/for-you", "/for-your-ai", "/about"].includes(location.pathname) && (
        <div className="compare-tray">
          <Icon name="compare" />
          <span>
            {pick(`已选择 ${compare.length} 项`, `${compare.length} selected`)}
          </span>
          <Link
            className={`button primary ${compare.length < 2 ? "disabled-link" : ""}`}
            to={`/compare?ids=${compare.join(",")}`}
            aria-disabled={compare.length < 2}
            onClick={(e) => {
              if (compare.length < 2) e.preventDefault();
            }}
          >
            {pick("查看对比", "Compare")}
            <Icon name="arrow" size={16} />
          </Link>
          <button
            className="icon-button"
            aria-label={pick("清空对比", "Clear selection")}
            onClick={clearCompare}
          >
            <Icon name="close" size={17} />
          </button>
        </div>
      )}
    </div>
  );
}
export default function App() {
  return (
    <WorkspaceProvider>
      <BrowserRouter>
        <Shell />
      </BrowserRouter>
    </WorkspaceProvider>
  );
}
