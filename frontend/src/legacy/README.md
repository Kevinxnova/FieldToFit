# 旧策展兼容模块

`App.tsx` 的 `/admin/curation` 路由加载这里的 `pages/Admin.tsx`。目录包含它实际使用的组件、API、语言文案和 hook，内部相对导入保持原结构。

本目录服务于旧 tools / issues / Newsletter 流程；当前知识库界面位于上一级 pages 和 components/workspace。不要把仍被引用的模块当作失效代码删除。新旧后台共用既有管理员鉴权，公开账户开放范围没有变化。
