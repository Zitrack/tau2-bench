# Tau2-ZH — the first native Chinese domain for τ²-bench

> **This fork hosts Tau2-ZH**: a 50-task, dual-control Chinese university-academic-affairs domain for [τ²-bench](https://github.com/sierra-research/tau2-bench) (MIT, scoring pinned to **v1.0.1**), plus the first Chinese **pass^k leaderboard across 5 LLMs**.
>
> **[简体中文](#项目简介与榜单)** · Domain PR: **[#596](https://github.com/sierra-research/tau2-bench/pull/596)** · Dataset: **[ZitrackHF/tau2-zh-campus](https://huggingface.co/datasets/ZitrackHF/tau2-zh-campus)** · Upstream README: [`main` branch](https://github.com/sierra-research/tau2-bench)
>
> **Code pin**: benchmark off tag [`campus-v2.2.0`](https://github.com/Zitrack/tau2-bench/releases/tag/campus-v2.2.0) or branch `dev/campus` — this default branch is a showcase snapshot, not the benchmark code.

The full domain documentation lives at [`src/tau2/domains/campus/README.md`](src/tau2/domains/campus/README.md). This root page is the project showcase.

## What is Tau2-ZH?

τ²-bench evaluates tool-using conversational agents against a policy document, a tool API, and an LLM-simulated user. Tau2-ZH adds the first **native Chinese** domain, `campus` — a university academic-affairs service scenario:

- **Policy engineering** — a 36-clause Chinese regulation with 14 engineered edge-case clauses (time windows, prerequisites, exceptions, cross-references, maintenance windows, per-semester quotas).
- **Dual-control environment** — the simulated *student* operates their own campus-app tools (upload documents, confirm/sign); the agent can only **guide**, hitting τ²'s core finding that guiding a user is harder than acting alone.
- **50 tasks** (15 easy / 20 medium / 15 hard, incl. 29 zero-write tasks — 20 with explicit refusal semantics), a seeded dual database of 14 tables (11 business + env anchor + 3 student-app), 15 agent tools + 4 student tools, all-Chinese error messages.
- **Deterministic scoring** — DB dual-hash (agent + user sides) + entity-substring checks; no LLM judge in the reward path.
- **173 tests** covering the error catalog, state machines, deadline-guard matrix, task self-consistency lint, upstream-contract pins, and a **50-task gold-replay CI** (any exception or invariant violation fails the suite; countermeasure aligned with upstream #499).

## Leaderboard — 5 LLMs × 50 tasks × 4 trials (= 200 simulations per model)

| # | Model (agent under test) | pass^1 | pass^4 | avg turns | GOAT credits |
|---|---|---|---|---|---|
| 1 | **DeepSeek V4.1-Flash** (anchor) | 0.975 | 0.900 | 6.07 | — (official API) |
| 2 | Qwen3.8-Flash | 0.860 | 0.720 | 5.41 | 3.780 |
| 3 | GLM-5.3 | 0.805 | 0.680 | 5.17 | 23.195 |
| 4 | GLM-5.3-Flash | 0.790 | 0.680 | 5.12 | 2.192 |
| 5 | MiMo-V2.6-Pro | 0.855 | 0.660 | 5.19 | 1.816 |

> **Scope note for the table**: the anchor row was collected on the **first generation of assertion strings** (the other four rows after the strings were revised); all figures are **v2.0.0-era as-run results** (no re-runs). Full disclosures — task-era detail, terminations, tier breakdown, run-code provenance, cost caliber — live in the domain README §3.

- **v1.1.1 patch (2026-10-05/06)**: consistency fixes (policy↔code↔gold) — tasks H01 (two-document illness deferrals) and H06 (special-channel 10-workday window, re-anchored) were corrected and all rows re-anchored via a 40-sim overlay; per-row pre-patch values are preserved. Rows 3/4 swap places at equal pass^4 (0.680) by pass^1. See the domain [Changelog](https://github.com/Zitrack/tau2-bench/blob/dev/campus/src/tau2/domains/campus/README.md#8-changelog) and PR #596 updates (parts 1–5).
- user simulator + NL judge pinned to **DeepSeek V4.1-Flash** (`deepseek-flash`) for every row; temperature 0; seed 20261004; max_steps 60.
- **E14 t1 was an upstream-infrastructure outage** (4 retry waves, `provider temporarily unavailable`): excluding that trial gives MiMo 0.840/0.660 pre-patch and 0.860/0.680 on the current v1.1.1 overlay — both calibers documented.
- GOAT credits include prompt-cache effects (GLM-5.3: no cache benefit, 1.63 cr/M; MiMo: 98.9% cache hit, 0.12 cr/M) — a 13× billing spread across rows, disclosed as-is.

Full protocol, judge calibration (132-sample human study), and failure typology: [`src/tau2/domains/campus/README.md`](src/tau2/domains/campus/README.md) and the PR description in [#596](https://github.com/sierra-research/tau2-bench/pull/596).

## Reproduce

```bash
git clone --branch campus-v2.2.0 https://github.com/Zitrack/tau2-bench && cd tau2-bench
uv sync
pytest tests/test_domains/test_campus          # 173 tests
uv run tau2 run --domain campus --agent llm_agent \
  --agent-llm <provider>/<model> \
  --user user_simulator --user-llm deepseek/deepseek-flash \
  --task-split-name base
```

## Changelog

Latest first; full history in [Releases](https://github.com/Zitrack/tau2-bench/releases) and the domain [Changelog](https://github.com/Zitrack/tau2-bench/blob/dev/campus/src/tau2/domains/campus/README.md#8-changelog):

- **v2.2.0 (2026-10-08)** — task-statement self-containment, disclosure set, data hygiene (policy v1.4.2 unchanged): the 15 tasks that cited an unpublished internal tool-specification document now carry inline guidance; authoring terms and evaluation jargon naturalized — **68 leaves** total, itemized in the cleanup record shipped with this release; disclosure set landed in the domain README (policy-text eras, task-era detail, limitations, the M16 root-cause note, difficulty tiers, run-code provenance, cost caliber); student profile fields rectified (display-only); `manifest.json` binds code to data. Evidence governance: asset freeze policy, harness-metadata scrub (model reasoning traces kept with a redistribution note), the second-round calibration batch, a public data validator. **173 tests**. Scoring contract fields unchanged vs v2.1.0; leaderboard numbers remain v2.0.0-era as-run results. [Tag & manifest](https://github.com/Zitrack/tau2-bench/releases/tag/campus-v2.2.0).

- **v2.1.0 (2026-10-07)** — task-statement cleanup & guard expansion (policy v1.4.2): authoring markers swept from every task-text leaf (101 sites; counted as marker occurrences across string leaves; full accounting ships with the v2.2.0 release cleanup record), M06's statement rewritten to its zero-write refusal semantics; policy gains a version footer (article text unchanged); guards: full-leaf marker scan, task self-consistency lint, upstream-contract pins, solo-mode raise; **167 tests**. Scoring contract fields are byte-identical to v2.0.0: `communicate_info`, `env_assertions`, `initial_state`, per-task `user_tools`, and the core fields of every gold action (`action_id`/`requestor`/`name`/`arguments`). Four gold-action **info** text sites were cleaned (M05 ×1, H01 ×2, H15 ×1) — free-text annotations only, never read by the evaluator. Leaderboard numbers remain the v2.0.0-era as-run results. [Tag & manifest](https://github.com/Zitrack/tau2-bench/releases/tag/campus-v2.1.0).
- **v2.0.0 (2026-10-06)** — data-contract release: QA metadata stripped from public dataset & raw runs (notes/issues/P0x); policy meta-annotations scrubbed → v1.4.1; calibers recomputed (54 env_assertions / 29 zero-write incl. 20 refusal / 157 pytest); raw runs & judge calibration published as release assets. [Tag & manifest](https://github.com/Zitrack/tau2-bench/releases/tag/campus-v2.0.0).
- **v1.1.5 (2026-10-06)** — release discoverability & runtime version metadata: fork banner on the root `README.md` (release tags are self-explanatory on clone); `tau2.domains.campus.__version__` / `POLICY_VERSION` / `SCORING_PROTOCOL` exposed at runtime (engine stays `tau2==1.0.1`). [Tag & manifest](https://github.com/Zitrack/tau2-bench/releases/tag/campus-v1.1.5).
- **v1.1.4 (2026-10-06)** — proxy-pickup closure details (art. 33): authorization-code validity anchored to the **signing time** (art. 33); service requests distinguish missing-ID vs missing-sign (no more re-sign steering). [Tag & manifest](https://github.com/Zitrack/tau2-bench/releases/tag/campus-v1.1.4).
- **v1.1.3 (2026-10-06)** — proxy-pickup document closure (art. 33); ticket `target_grade_id` is window-input only (art. 16); public `tasks.json` stripped of internal QA metadata.
- **v1.1.2 (2026-10-06)** — undeclared hospital level → returned-for-supplement (art. 12); confirmation receipts agree with settled state.
- **v1.1.1 (2026-10-05/06)** — hardening: pre-settle, user-side deadline guards, special-channel terminal transition, monotonic waitlist positions; H01/H06 gold re-anchored (40-sim overlay).

Dataset (tasks / policy / seed DBs): [huggingface.co/datasets/ZitrackHF/tau2-zh-campus](https://huggingface.co/datasets/ZitrackHF/tau2-zh-campus)

## Repository layout (this fork)

| branch / path | content |
|---|---|
| `main` | pristine mirror of upstream `sierra-research/tau2-bench` |
| **`tau2-zh`** (default) | **this page + the full campus domain** — the project showcase |
| `dev/campus` | the exact branch the upstream PR #596 is filed from |
| `src/tau2/domains/campus/` | domain code: `data_model / user_data_model / tools / user_tools / environment` |
| `data/tau2/domains/campus/` | `policy.md` + `db.json` + `user_db.json` + `tasks.json` (50) + `split_tasks.json` |
| `tests/test_domains/test_campus/` | 173 tests |

## License & credits

Code and domain content released under the upstream **MIT license**. τ²-bench by Sierra Research ([upstream repo](https://github.com/sierra-research/tau2-bench), paper: [*τ²-Bench: Evaluating Conversational Agents in a Dual-Control Environment*](https://arxiv.org/abs/2506.07982)). All institutions, people, and records in the campus domain are fictional ("Qingchuan University"); policy material is rewritten and de-identified from public regulations. Tau2-ZH is an **unofficial**, independent extension — **not affiliated with Sierra Research**. Questions or feedback: **via GitHub Issues** on this fork ([Zitrack/tau2-bench Issues](https://github.com/Zitrack/tau2-bench/issues)).

---

<a id="项目简介与榜单"></a>

# Tau2-ZH — τ²-bench 的第一个原生中文域

> 本 fork 承载 **Tau2-ZH**：一个 50 题、双控（dual-control）的中文高校教务办事域，面向 [τ²-bench](https://github.com/sierra-research/tau2-bench)（MIT 许可，计分钉在 **v1.0.1**），并附带首个覆盖 5 个大模型的中文 **pass^k 榜单**。
>
> Domain PR: **[#596](https://github.com/sierra-research/tau2-bench/pull/596)** · 数据集：**[ZitrackHF/tau2-zh-campus](https://huggingface.co/datasets/ZitrackHF/tau2-zh-campus)** · 上游 README：[`main` 分支](https://github.com/sierra-research/tau2-bench)
>
> **代码锚点**：请基于 tag [`campus-v2.2.0`](https://github.com/Zitrack/tau2-bench/releases/tag/campus-v2.2.0) 或分支 `dev/campus` 跑基准——本默认分支为展示快照，非基准代码。

完整的域文档位于 [`src/tau2/domains/campus/README.md`](src/tau2/domains/campus/README.md)，本页为项目展示主页。

## 项目简介

τ²-bench 让工具调用型对话 Agent 面对政策文档、工具 API 与 LLM 模拟用户。Tau2-ZH 为其新增第一个**原生中文**域 `campus`——高校教务办事服务场景：

- **政策工程**：36 条中文教务规程，埋 14 类规则陷阱（时间窗 / 前置条件 / 例外 / 条款互引 / 维护窗口 / 学期额度）；
- **双控环境**：模拟*学生*本人在自己的"教务 App"上执行操作（上传材料 / 确认签署），Agent 只能**引导**——正对应 τ² 论文"引导用户比自己动手更难"的核心发现；
- **50 道分层任务**（15 易 / 20 中 / 15 难，含 29 道零写任务——其中 20 道具明确拒绝语义）+ 14 表种子双库（11 业务表＋env 锚＋3 学生端表） + 15 个 Agent 工具与 4 个学生工具，全中文错误信息；
- **程序化判分**：Agent/学生双侧数据库终态双哈希 + 实体串逐字命中，奖励路径无 LLM 裁判；
- **173 项测试**：覆盖错误文案目录、状态机、deadline 守卫矩阵、任务自洽 lint、上游契约钉，以及 **50 题全量金标重放 CI**（任何异常或不变量破坏即失败；对齐上游 #499 的反制措施）。

## 榜单 — 5 个大模型 × 50 题 × 4 次（每模型 200 场模拟）

| # | 模型（被测 agent） | pass^1 | pass^4 | 平均轮次 | GOAT credits |
|---|---|---|---|---|---|
| 1 | **DeepSeek V4.1-Flash**（锚点） | 0.975 | 0.900 | 6.07 | —（官方 API） |
| 2 | Qwen3.8-Flash | 0.860 | 0.720 | 5.41 | 3.780 |
| 3 | GLM-5.3 | 0.805 | 0.680 | 5.17 | 23.195 |
| 4 | GLM-5.3-Flash | 0.790 | 0.680 | 5.12 | 2.192 |
| 5 | MiMo-V2.6-Pro | 0.855 | 0.660 | 5.19 | 1.816 |

> **榜单表口径注**：锚点行采集于**断言串第一代**（其余四行采集于换串后）；全部数字为 **v2.0.0 时代 as-run 结果**（未重跑）。完整披露——任务时代明细、终止披露、难度分层、运行代码版本、成本口径——见域 README §3。

- **v1.1.1 补丁（2026-10-05/06）**：一致性修复（政策↔代码↔金标）——H01（因病缓考双材料）与 H06（特别通道十工作日窗，重锚）两题修复后，经 40 sims overlay 对全部 5 行重跑重锚；各行 pre-patch 原值保留。pass^4 同为 0.680 的第 3/4 名按 pass^1 排序互换。详见域 [变更记录](https://github.com/Zitrack/tau2-bench/blob/dev/campus/src/tau2/domains/campus/README.md#8-变更记录) 与 PR #596 Updates（part 1–5）。
- user simulator 与 NL judge 每行钉在 **DeepSeek V4.1-Flash**（`deepseek-flash`）；temperature=0；seed=20261004；max_steps=60。
- **E14 t1 为上游基础设施故障**（4 波重试，`provider temporarily unavailable`）：剔除该 trial，MiMo 修复前 0.840/0.660、现行 v1.1.1 overlay 0.860/0.680——两种口径均已披露。
- GOAT credits 含 prompt 缓存收益（GLM-5.3 无缓存收益 1.63 cr/M；MiMo 98.9% 命中 0.12 cr/M）——13× 计费差异如实披露。

完整协议、判分校准（132 条人工审计）与失败类型学：[`src/tau2/domains/campus/README.md`](src/tau2/domains/campus/README.md) 与 [#596](https://github.com/sierra-research/tau2-bench/pull/596) 的 PR 描述。

## 复现

```bash
git clone --branch campus-v2.2.0 https://github.com/Zitrack/tau2-bench && cd tau2-bench
uv sync
pytest tests/test_domains/test_campus          # 173 项测试
uv run tau2 run --domain campus --agent llm_agent \
  --agent-llm <provider>/<model> \
  --user user_simulator --user-llm deepseek/deepseek-flash \
  --task-split-name base
```

## 变更日志

最新在上；完整历史见 [Releases](https://github.com/Zitrack/tau2-bench/releases) 与域 [变更记录](https://github.com/Zitrack/tau2-bench/blob/dev/campus/src/tau2/domains/campus/README.md#8-变更记录)：

- **v2.2.0（2026-10-08）**——任务陈述自足化、披露集与数据整饰（政策 v1.4.2 不变）：原引用未公开内部《工具规格》文档的 15 题改为内联指引；作者用语与评测语域自然化——共 **68 叶**，逐条见随本版发布的清洗记录；披露集落域 README（政策三时代、任务时代明细、局限、M16 成因注记、难度分层、run-code 溯源、成本口径）；学生档案字段校正（仅展示字段）；`manifest.json` 绑定代码与数据。证据治理：资产冻结纪律、harness 元数据洗刷（模型思维链保留并附再分发说明）、校准第二轮批次、公开数据校验器。**173 项测试**。判分契约字段与 v2.1.0 相比零变化；榜单数字仍为 v2.0.0 时代 as-run 结果。[Tag 与版本清单](https://github.com/Zitrack/tau2-bench/releases/tag/campus-v2.2.0)。

- **v2.1.0（2026-10-07）**——任务陈述清洗与守卫扩展（政策 v1.4.2）：任务文本全字符串叶清扫作者标记（101 处；按字符串叶上的标记出现次数计，全量对账随 v2.2.0 发布的清洗记录公布），M06 陈述重写为零写拒绝语义；政策新增版本脚注（条款正文不变）；守卫：全叶标记扫描、任务自洽 lint、上游契约钉、solo 抛错；**167 项测试**。判分契约字段与 v2.0.0 逐字节一致：communicate_info、env_assertions、initial_state、逐题 user_tools，以及金标动作全部核心字段（action_id / requestor / name / arguments）；金标动作的 info 自由文本清理了 4 处（M05×1、H01×2、H15×1），evaluator 不读该文本。榜单数字仍为 v2.0.0 时代 as-run 结果。[Tag 与版本清单](https://github.com/Zitrack/tau2-bench/releases/tag/campus-v2.1.0)。
- **v2.0.0（2026-10-06）**——数据契约版本：公开数据集与原始跑批的 QA 元数据全量剥离（notes/issues/P0x）；政策元注记清除 → v1.4.1；口径重算（54 条断言 / 29 零写含 20 拒绝 / 157 项 pytest）；原始跑批与判分校准以 Release assets 公开。[Tag 与版本清单](https://github.com/Zitrack/tau2-bench/releases/tag/campus-v2.0.0)。
- **v1.1.5（2026-10-06）**——发布可发现性与运行时版本元数据：根 `README.md` 增加 fork 横幅（clone 发布 tag 即自解释）；`tau2.domains.campus.__version__` / `POLICY_VERSION` / `SCORING_PROTOCOL` 运行时可读（引擎仍钉 `tau2==1.0.1`）。[Tag 与版本清单](https://github.com/Zitrack/tau2-bench/releases/tag/campus-v1.1.5)。
- **v1.1.4（2026-10-06）**——第 33 条闭环细节（代领授权）：代领授权码有效期锚定**签署时刻**（第 33 条）；服务单据查询区分"缺证件"与"缺签署"（不再误导重新签署）。[Tag 与版本清单](https://github.com/Zitrack/tau2-bench/releases/tag/campus-v1.1.4)。
- **v1.1.3（2026-10-06）**——代领证件闭环（第 33 条）；工单 `target_grade_id` 仅作判窗输入（第 16 条）；公开 `tasks.json` 剥离内部 QA 元数据。
- **v1.1.2（2026-10-06）**——未申报医院等级 → 退回补报（第 12 条）；确认回执与结算终态一致。
- **v1.1.1（2026-10-05/06）**——加固：pre-settle、用户侧 deadline 守卫、特别通道终态迁移、候补位次单调；H01/H06 金标重锚（40 sims overlay）。

数据集（任务集 / 政策 / 种子库）：[huggingface.co/datasets/ZitrackHF/tau2-zh-campus](https://huggingface.co/datasets/ZitrackHF/tau2-zh-campus)

## 仓库结构（本 fork）

| 分支 / 路径 | 内容 |
|---|---|
| `main` | 上游 `sierra-research/tau2-bench` 的纯净镜像 |
| **`tau2-zh`**（默认） | **本页 + 完整 campus 域**——项目展示 |
| `dev/campus` | 上游 PR #596 的确切来源分支 |
| `src/tau2/domains/campus/` | 域代码：`data_model / user_data_model / tools / user_tools / environment` |
| `data/tau2/domains/campus/` | `policy.md` + `db.json` + `user_db.json` + `tasks.json`（50）+ `split_tasks.json` |
| `tests/test_domains/test_campus/` | 173 项测试 |

## 许可与致谢

代码与域内容遵循上游 **MIT 许可**。τ²-bench 由 Sierra Research 开发（[上游仓库](https://github.com/sierra-research/tau2-bench)，论文：[*τ²-Bench: Evaluating Conversational Agents in a Dual-Control Environment*](https://arxiv.org/abs/2506.07982)）。campus 域中的全部机构、人名与记录均为虚构（"青川大学 / Qingchuan University"）；政策素材改写自公开法规并脱敏。Tau2-ZH 为**非官方**独立扩展，**与 Sierra Research 无隶属/关联关系**（unofficial / not affiliated with Sierra Research）。问题或反馈请**经 GitHub Issues** 提出（[Zitrack/tau2-bench Issues](https://github.com/Zitrack/tau2-bench/issues)）。
