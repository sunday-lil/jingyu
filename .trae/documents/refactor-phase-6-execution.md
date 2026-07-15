# Refactor Phase 6: Bug Fixes, Crawler Polish, and Final Docs

## Context

Phases 0–5 of the comprehensive AI news system refactor are substantially complete: the `database` package, routes helpers, base template, partials, JS modules, and CSS modules are in place. 71 pytest tests pass except for three `tests/test_news_routes.py` page-render tests (`test_latest_page_renders`, `test_hot_page_renders`, `test_category_page_filters_by_category`) that fail with `500 INTERNAL SERVER ERROR` and the log message `未预期异常: unexpected '}'`. The root cause is a Jinja slice-syntax incompat (`news.summary[:150]`) in `templates/_macros.html:88` that is not parsed by the template engine. The template system also still loads the **old monolithic** `static/style.css` (110 KB) via `templates/_base.html:8`, even though the new modular `static/css/style.css` manifest exists — that means the new CSS modules are dead code and the old file is still being served.

This plan finishes the refactor: fix the two latent template/asset bugs, do the Phase 6 crawler polish, refresh the merged documentation, and add a top-level `README.md`. Behavior must stay identical; only structure, docs, and quality improve.

## Goals

1. Make `pytest -q` fully green (74 tests pass).
2. Wire the new modular CSS so the old monolithic file is no longer served.
3. Remove the `sys.path.append(...)` hack in the crawler and add type hints + module docstrings.
4. Refresh `docs/merged_document.md` and add `README.md` so the new layout is documented.
5. Smoke-test `/`, `/latest`, `/hot`, `/category/科技`, `/admin`, `/login` to confirm visual parity.

## Proposed changes

### 1. Critical bug fixes (must come first)

**1a. Fix `news.summary[:150]` slice in `_macros.html`**

- File: `c:\Users\Administrator\Desktop\webwrold\templates\_macros.html`
- Line 88 currently reads:
  ```html
  <p class="news-summary">{{ news.summary[:150] }}{% if news.summary|length > 150 %}...{% endif %}</p>
  ```
- Change to (mirroring the already-fixed `index.html`):
  ```html
  <p class="news-summary">{{ news.summary[0:150] }}{% if news.summary|length > 150 %}...{% endif %}</p>
  ```
- Why: this is the Jinja2 syntax that was causing the three test failures. The same `[:N]` shortcut was already fixed in `index.html` (lines 118 and 188) — apply the same fix here.

**1b. Point `_base.html` at the new modular CSS**

- File: `c:\Users\Administrator\Desktop\webwrold\templates\_base.html`
- Line 8 currently reads:
  ```html
  <link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
  ```
- Change to:
  ```html
  <link rel="stylesheet" href="{{ url_for('static', filename='css/style.css') }}">
  ```
- Why: `static/css/style.css` is the new entry-point manifest that `@import`s the seven modular files. The old `static/style.css` (the 110 KB monolith) becomes dead. After this change, also delete `c:\Users\Administrator\Desktop\webwrold\static\style.css` (the old monolithic file is no longer referenced anywhere — verified by grep). Removing it prevents future confusion.

### 2. Crawler polish (Phase 6)

**2a. Remove `sys.path.append(...)` hack from `crawler/main.py`**

- File: `c:\Users\Administrator\Desktop\webwrold\crawler\main.py`
- Lines 4–8 currently read:
  ```python
  import os
  import sys

  # 添加项目根目录到系统路径
  sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
  ```
- Remove the `os`/`sys` imports and the `sys.path.append(...)` block.
- Keep `from crawler.site_crawlers import NewsSiteCrawler` and `from crawler.database_handler import DatabaseHandler` (these are already package-relative).
- Add a module docstring at the top of the file:
  ```python
  """
  Crawler orchestration entry point.

  Runs the configured news sites through :class:`NewsSiteCrawler` and stores
  results via :class:`DatabaseHandler`. Invoked as a module
  (``python -m crawler.main``) from the project root.
  """
  ```
- Add type hints to: `NewsCrawler.__init__`, `crawl_site`, `crawl_all_sites`, `crawl_specific_site`, `store_results`, `run_full_cycle`, `run_site_cycle`, `run_crawler`.

**2b. Remove the same `sys.path.append(...)` hack from `crawler/database_handler.py`**

- File: `c:\Users\Administrator\Desktop\webwrold\crawler\database_handler.py`
- Lines 1–7 currently read:
  ```python
  import sys
  import os
  from datetime import datetime
  import logging

  # 添加项目根目录到系统路径
  sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

  from database import DatabaseManager
  ```
- Remove the `sys`/`os` imports and the `sys.path.append(...)` line.
- Keep `from database import DatabaseManager` (the project root must be on `sys.path` when running `python -m crawler.main`; this is documented in the README).
- Add module docstring:
  ```python
  """
  Bridges the crawler's output dictionaries and the project's database layer.

  Responsible for auto-categorising articles, deduplicating by title, and
  batching inserts through :class:`database.DatabaseManager`.
  """
  ```
- Add type hints to: `store_news_item`, `store_news_batch`, `_categorize_news`, `check_news_exists`, `get_latest_news_date`.

**2c. Add module docstring + type hints to `crawler/base_crawler.py`**

- File: `c:\Users\Administrator\Desktop\webwrold\crawler\base_crawler.py`
- Currently has no module docstring. Add:
  ```python
  """
  Base HTTP crawler providing anti-bot measures.

  Subclasses (e.g. :class:`crawler.site_crawlers.NewsSiteCrawler`) implement
  the actual parsing; this class only handles session creation, randomised
  user-agent headers, and polite delays.
  """
  ```
- Tighten existing type hints on `get` and `post` (return `Optional[requests.Response]`, use `Dict[str, str]` for headers, etc.).

**2d. Add module docstring to `crawler/site_crawlers.py`**

- File: `c:\Users\Administrator\Desktop\webwrold\crawler\site_crawlers.py`
- Add at the top:
  ```python
  """
  Site-specific news crawlers and HTML parsing rules.

  :class:`NewsSiteCrawler` extends :class:`BaseCrawler` with per-domain
  BeautifulSoup selectors (currently Sina, Xinhua, People). Add a new entry
  to ``SITE_RULES`` to support another source.
  """
  ```
- No type-hint changes needed — the file is already typed.

### 3. Documentation refresh

**3a. Update `docs/merged_document.md`**

- File: `c:\Users\Administrator\Desktop\webwrold\docs\merged_document.md`
- Update the "目录结构" tree (lines ~43–72) so it matches the post-refactor layout:
  ```
  ai-news/
  ├── app.py                 # 应用入口点（应用工厂模式）
  ├── config.py              # 多环境配置管理（支持 .env）
  ├── admin_tools.py         # 管理员命令行工具
  ├── requirements.txt       # 运行时依赖
  ├── requirements-dev.txt   # 开发/测试依赖（pytest）
  ├── .env.example           # 环境变量样例
  ├── .gitignore
  ├── database/              # 数据访问层（包）
  │   ├── __init__.py        # DatabaseManager 组合各 mixin
  │   ├── connection.py      # SQLite 连接/cursor 上下文管理器
  │   ├── schema.py          # CREATE TABLE 语句
  │   ├── users.py           # 用户 mixin
  │   ├── sessions.py        # 会话 mixin
  │   ├── news.py            # 新闻 mixin
  │   ├── comments.py        # 评论 mixin
  │   ├── interactions.py    # 点赞/投币/收藏 mixin
  │   ├── admin.py           # 管理员操作 mixin
  │   ├── stats.py           # 统计查询 mixin
  │   └── _helpers.py        # 内部共享工具
  ├── routes/                # 路由蓝图
  │   ├── __init__.py
  │   ├── auth.py            # 认证路由
  │   ├── news.py            # 新闻路由
  │   ├── admin.py           # 管理员路由
  │   ├── _helpers.py        # 分页/缓存/图片上传等辅助
  │   └── _validators.py     # 表单验证
  ├── utils/                 # 工具
  │   ├── auth.py
  │   ├── cache.py
  │   ├── anti_crawler.py
  │   └── logger.py
  ├── templates/             # Jinja2 模板
  │   ├── _base.html         # 基础布局（所有页面继承）
  │   ├── _nav.html          # 导航宏
  │   ├── _flash.html        # 闪现消息
  │   ├── _macros.html       # 分页/头像等宏
  │   ├── index.html         # 首页
  │   ├── login.html
  │   ├── register.html
  │   ├── profile.html
  │   ├── new.html
  │   ├── add_news.html
  │   ├── edit_news.html
  │   ├── search_results.html
  │   └── admin.html
  ├── static/                # 静态资源
  │   ├── css/               # 模块化样式（@import 入口）
  │   │   ├── style.css
  │   │   ├── 00-variables.css
  │   │   ├── 01-reset.css
  │   │   ├── 02-layout.css
  │   │   ├── 03-components.css
  │   │   ├── 04-pages.css
  │   │   ├── 05-auth.css
  │   │   ├── 06-admin.css
  │   │   └── pages/admin.css
  │   ├── js/                # 前端脚本
  │   │   ├── app.js
  │   │   └── pages/{index,news,profile,admin}.js
  │   └── uploads/           # 用户上传
  ├── tests/                 # pytest 套件
  │   ├── conftest.py
  │   ├── test_database.py
  │   ├── test_auth.py
  │   ├── test_news_routes.py
  │   └── test_admin_routes.py
  ├── crawler/               # 新闻爬虫
  │   ├── __init__.py
  │   ├── base_crawler.py
  │   ├── site_crawlers.py
  │   ├── database_handler.py
  │   └── main.py
  ├── docs/
  │   └── merged_document.md
  ├── cache/                 # 文件缓存
  └── logs/                  # 日志
  ```
- Update any line-count callouts (e.g. "1257 lines" for the old `database.py`, "110 KB" for the old `style.css`, "3830 lines" for `style.css`) to reflect the new modular sizes.
- Add a short "重构说明" subsection at the end summarizing the refactor: package layout, asset modularization, test coverage, and the `crawler` cleanup.

**3b. Add a top-level `README.md`**

- File: `c:\Users\Administrator\Desktop\webwrold\README.md` (new)
- Content (in English, matching the project's primary working language):
  - Project blurb (1 paragraph)
  - Features list
  - Quickstart:
    ```bash
    python -m venv venv
    venv\Scripts\activate
    pip install -r requirements.txt
    cp .env.example .env             # then edit SECRET_KEY
    python app.py
    # open http://127.0.0.1:5000
    ```
  - Running the tests:
    ```bash
    pip install -r requirements-dev.txt
    pytest -q
    ```
  - Running the crawler:
    ```bash
    python -m crawler.main --list
    python -m crawler.main --site sina
    python -m crawler.main
    ```
  - Environment variables table: `SECRET_KEY`, `UPLOAD_FOLDER`, `REDIS_URL`, `LOG_LEVEL`, `FLASK_CONFIG`
  - Project layout (compact tree, same as the doc update but trimmed)
  - Architecture notes (Flask app factory, blueprints, `database` package, modular assets, test layout)
  - "See `docs/merged_document.md` for the full technical reference" pointer

## Critical files to modify

- **Bug fix:** `templates/_macros.html`, `templates/_base.html`
- **Delete:** `static/style.css` (the old 110 KB monolith)
- **Crawler:** `crawler/main.py`, `crawler/database_handler.py`, `crawler/base_crawler.py`, `crawler/site_crawlers.py`
- **Docs:** `docs/merged_document.md` (update), `README.md` (new)

## Existing utilities to reuse

- All route helpers (`routes/_helpers.py`), validators (`routes/_validators.py`), database mixins, and template partials from earlier phases are unchanged.
- The new `static/css/style.css` manifest is unchanged — only `_base.html` is updated to load it.

## Verification

After the changes:

1. **Unit tests**:
   ```bash
   pytest -q
   ```
   Expect 74 tests, all green. The three previously failing tests (`test_latest_page_renders`, `test_hot_page_renders`, `test_category_page_filters_by_category`) should now pass.

2. **App boots**:
   ```bash
   python -c "from app import create_app; create_app('testing')"
   ```
   No warnings, no template errors.

3. **Crawler boots**:
   ```bash
   python -m crawler.main --list
   ```
   Should print the list of configured sites without import errors.

4. **Static asset check**:
   - Confirm `static/style.css` is gone and `static/css/style.css` is present.
   - `grep -r "static/style.css" templates/ static/ docs/` returns no matches.
   - Browser-load `/` and confirm no 404s in the network tab for CSS files.

5. **Visual smoke test** (via integrated browser):
   - Browse `/`, `/latest`, `/hot`, `/category/科技`, `/admin`, `/login`, `/register`, `/profile`.
   - Confirm pages render with the same layout/colors as before.

## Risks & rollback

- **Slice-syntax fix risk:** the `news.summary` object might not support slicing in some edge case (e.g. when summary is `None`). Mitigation: the surrounding `{% if news.summary %}` guard already handles `None`/empty, and the existing `index.html` already uses the same `[0:100]` / `[0:150]` pattern successfully.
- **CSS path change risk:** if any other template hard-codes `static/style.css`, it would 404. Mitigation: grep confirmed `_base.html` is the only reference; the old file is deleted only after the new path is in place.
- **Crawler `sys.path` removal risk:** the crawler is invoked as `python -m crawler.main` from the project root. The README documents `cd $PROJECT_ROOT && python -m crawler.main` as the canonical invocation. If the user's deployment invokes it from a different cwd, the `crawler` package import will fail — but this is no worse than the old code (which used a brittle absolute path).
- **Old `static/style.css` deletion:** irreversible, but the new manifest reproduces the same styles verbatim, so the visual output is unchanged.

We commit after each step (template fix → CSS migration → crawler polish → docs) so each can be reverted independently.
