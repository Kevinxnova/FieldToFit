# 本地开发与浏览

环境：Python 3.12/3.13、Node.js 20+。默认使用本地 SQLite；浏览已有资料、基础检索和 MCP 读取不需要生成模型凭证。

## 安装

从当前开发分支取得本版源码；已有项目请先保存自己的改动。此命令不会选择 v1.0.0 的旧界面。

```bash
git clone --branch codex/metis-knowledge-workspace https://github.com/Kevinxnova/metis.git
cd metis
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
cp .env.example .env
cd frontend
npm ci
cd ..
```

已有 `.env` 时保留原配置。按需填写不同的管理员密码和定时任务密钥；保持 `METIS_PUBLIC_ACCOUNTS=0`。本地试用无需填写 Turso 或模型密钥。

## 启动

第一个终端，在仓库根目录：

```bash
./scripts/start-backend.sh
```

第二个终端：

```bash
cd frontend
npm run dev
```

打开 [本地工作台](http://localhost:5173/information)。后台为 `/admin`，旧策展兼容入口为 `/admin/curation`；公开账户没有登录表单。

```bash
curl http://127.0.0.1:8000/api/health
```

本版返回 `status: ok` 和 `version: v1.1.0-beta.1`。

## 第一次没有资料

新数据库为空是正常状态。可以显式导入仓库中的六条短引用和 GPT 整理样本：

```bash
source .venv/bin/activate
python -m examples.editorial.load
```

这是样本导入，不是全量真实运营数据。旧 PDF 技术样例不作为产品价值案例；主案例仍 pending。要采集真实来源，见 [内容维护](content.md)。

## 隔离验收，保留自己的数据

在新的终端设置以下变量，再启动后端或导入样本：

```bash
export PYTHON_DOTENV_DISABLED=1
export TURSO_DATABASE_URL=''
export TURSO_AUTH_TOKEN=''
export MINIMAX_API_KEY=''
export METIS_MODEL_API_KEY=''
export METIS_DATA_DIR="$(mktemp -d /tmp/metis-preview.XXXXXX)"
```

本版启动兼容脚本会遵守 `PYTHON_DOTENV_DISABLED=1`，不会重新载入仓库 `.env`。如需管理验收，另外在这个终端设置临时 `ADMIN_PASSWORD`。不要把验收数据目录与自己的运行目录混用。

## 检查

```bash
source .venv/bin/activate
PYTHON_DOTENV_DISABLED=1 TURSO_DATABASE_URL='' TURSO_AUTH_TOKEN='' pytest
cd frontend
npm run build
cd ..
python scripts/maintenance/check_repository.py
```

真实 Turso / MiniMax 集成检查默认跳过，需要单独配置受控环境并显式启用。MCP 和技术运行脚本见 [examples 导航](../../examples/README.md)。
