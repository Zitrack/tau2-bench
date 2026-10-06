# Tau2-ZH — the first native Chinese domain for τ²-bench

> **This fork hosts Tau2-ZH**: a 50-task, dual-control Chinese university-academic-affairs domain for [τ²-bench](https://github.com/sierra-research/tau2-bench) (MIT, scoring pinned to **v1.0.1**), plus the first Chinese **pass^k leaderboard across 5 LLMs**.
>
> **[简体中文](#项目简介与榜单)** · Domain PR: **[#596](https://github.com/sierra-research/tau2-bench/pull/596)** · Dataset: **[ZitrackHF/tau2-zh-campus](https://huggingface.co/datasets/ZitrackHF/tau2-zh-campus)** · Upstream README: [`main` branch](https://github.com/sierra-research/tau2-bench)

The full domain documentation lives at [`src/tau2/domains/campus/README.md`](src/tau2/domains/campus/README.md). This root page is the project showcase.

## What is Tau2-ZH?

τ²-bench evaluates tool-using conversational agents against a policy document, a tool API, and an LLM-simulated user. Tau2-ZH adds the first **native Chinese** domain, `campus` — a university academic-affairs service scenario:

- **Policy engineering** — a 36-clause Chinese regulation with 14 engineered edge-case clauses (time windows, prerequisites, exceptions, cross-references, maintenance windows, per-semester quotas).
- **Dual-control environment** — the simulated *student* operates their own campus-app tools (upload documents, confirm/sign); the agent can only **guide**, hitting τ²'s core finding that guiding a user is harder than acting alone.
- **50 tasks** (15 easy / 20 medium / 15 hard, incl. 17 refusal tasks scored by zero-DB-write), a seeded 14-table database, 15 agent tools + 4 student tools, all-Chinese error messages.
- **Deterministic scoring** — DB dual-hash (agent + user sides) + entity-substring checks; no LLM judge in the reward path.
- **141 tests** covering the error catalog, state machines, deadline-guard matrix, and a **50-task gold-replay CI** (any exception or invariant violation fails the suite; countermeasure aligned with upstream #499).

## Leaderboard — 5 LLMs × 50 tasks × 4 trials (= 200 simulations per model)

| # | Model (agent under test) | pass^1 | pass^4 | avg turns | GOAT credits |
|---|---|---|---|---|---|
| 1 | **DeepSeek V4.1-Flash** (anchor) | 0.975 | 0.900 | 6.07 | — (official API) |
| 2 | Qwen3.8-Flash | 0.860 | 0.720 | 5.41 | 3.780 |
| 3 | GLM-5.3 | 0.805 | 0.680 | 5.17 | 23.195 |
| 4 | GLM-5.3-Flash | 0.790 | 0.680 | 5.12 | 2.192 |
| 5 | MiMo-V2.6-Pro | 0.855 | 0.660 | 5.19 | 1.816 |

- **v1.1.1 patch (2026-10-05/06)**: consistency fixes (policy↔code↔gold) — tasks H01 (two-document illness deferrals) and H06 (special-channel 10-workday window, re-anchored) were corrected and all rows re-anchored via a 40-sim overlay; per-row pre-patch values are preserved. Rows 3/4 swap places at equal pass^4 (0.680) by pass^1. See the domain [Changelog](https://github.com/Zitrack/tau2-bench/blob/dev/campus/src/tau2/domains/campus/README.md#8-changelog) and PR #596 updates (parts 1–3).
- user simulator + NL judge pinned to **DeepSeek V4.1-Flash** (`deepseek-flash`) for every row; temperature 0; seed 20261004; max_steps 60.
- **E14 t1 was an upstream-infrastructure outage** (4 retry waves, `provider temporarily unavailable`): excluding that trial gives MiMo 0.840/0.660 pre-patch and 0.860/0.680 on the current v1.1.1 overlay — both calibers documented.
- GOAT credits include prompt-cache effects (GLM-5.3: no cache benefit, 1.63 cr/M; MiMo: 98.9% cache hit, 0.12 cr/M) — a 13× billing spread across rows, disclosed as-is.

Full protocol, judge calibration (132-sample human study), and failure typology: [`src/tau2/domains/campus/README.md`](src/tau2/domains/campus/README.md) and the PR description in [#596](https://github.com/sierra-research/tau2-bench/pull/596).

## Reproduce

```bash
uv sync
pytest tests/test_domains/test_campus          # 141 tests
uv run tau2 run --domain campus --agent llm_agent \
  --agent-llm <provider>/<model> \
  --user user_simulator --user-llm deepseek/deepseek-flash \
  --task-split-name base
```

Dataset (tasks / policy / seed DBs): [huggingface.co/datasets/ZitrackHF/tau2-zh-campus](https://huggingface.co/datasets/ZitrackHF/tau2-zh-campus)

## Repository layout (this fork)

| branch / path | content |
|---|---|
| `main` | pristine mirror of upstream `sierra-research/tau2-bench` |
| **`tau2-zh`** (default) | **this page + the full campus domain** — the project showcase |
| `dev/campus` | the exact branch the upstream PR #596 is filed from |
| `src/tau2/domains/campus/` | domain code: `data_model / user_data_model / tools / user_tools / environment` |
| `data/tau2/domains/campus/` | `policy.md` + `db.json` + `user_db.json` + `tasks.json` (50) + `split_tasks.json` |
| `tests/test_domains/test_campus/` | 141 tests |

## License & credits

Code and domain content released under the upstream **MIT license**. τ²-bench by Sierra Research ([upstream repo](https://github.com/sierra-research/tau2-bench), paper: [*τ²-Bench: Evaluating Conversational Agents in a Dual-Control Environment*](https://arxiv.org/abs/2506.07982)). All institutions, people, and records in the campus domain are fictional ("Qingchuan University"); policy material is rewritten and de-identified from public regulations.

---

<a id="项目简介与榜单"></a>

# Tau2-ZH — τ²-bench 的第一个原生中文域

> 本 fork 承载 **Tau2-ZH**：一个 50 题、双控（dual-control）的中文高校教务办事域，面向 [τ²-bench](https://github.com/sierra-research/tau2-bench)（MIT 许可，计分钉在 **v1.0.1**），并附带首个覆盖 5 个大模型的中文 **pass^k 榜单**。
>
> Domain PR: **[#596](https://github.com/sierra-research/tau2-bench/pull/596)** · 数据集：**[ZitrackHF/tau2-zh-campus](https://huggingface.co/datasets/ZitrackHF/tau2-zh-campus)** · 上游 README：[`main` 分支](https://github.com/sierra-research/tau2-bench)

完整的域文档位于 [`src/tau2/domains/campus/README.md`](src/tau2/domains/campus/README.md)，本页为项目展示主页。

## 项目简介

τ²-bench 让工具调用型对话 Agent 面对政策文档、工具 API 与 LLM 模拟用户。Tau2-ZH 为其新增第一个**原生中文**域 `campus`——高校教务办事服务场景：

- **政策工程**：36 条中文教务规程，埋 14 类规则陷阱（时间窗 / 前置条件 / 例外 / 条款互引 / 维护窗口 / 学期额度）；
- **双控环境**：模拟*学生*本人在自己的"教务 App"上执行操作（上传材料 / 确认签署），Agent 只能**引导**——正对应 τ² 论文"引导用户比自己动手更难"的核心发现；
- **50 道分层任务**（15 易 / 20 中 / 15 难，含 17 道零写拒绝题）+ 14 表种子数据库 + 15 个 Agent 工具与 4 个学生工具，全中文错误信息；
- **程序化判分**：Agent/学生双侧数据库终态双哈希 + 实体串逐字命中，奖励路径无 LLM 裁判；
- **141 项测试**：覆盖错误文案目录、状态机、deadline 守卫矩阵，以及 **50 题全量金标重放 CI**（任何异常或不变量破坏即失败；对齐上游 #499 的反制措施）。

## 榜单 — 5 个大模型 × 50 题 × 4 次（每模型 200 场模拟）

| # | 模型（被测 agent） | pass^1 | pass^4 | 平均轮次 | GOAT credits |
|---|---|---|---|---|---|
| 1 | **DeepSeek V4.1-Flash**（锚点） | 0.975 | 0.900 | 6.07 | —（官方 API） |
| 2 | Qwen3.8-Flash | 0.860 | 0.720 | 5.41 | 3.780 |
| 3 | GLM-5.3 | 0.805 | 0.680 | 5.17 | 23.195 |
| 4 | GLM-5.3-Flash | 0.790 | 0.680 | 5.12 | 2.192 |
| 5 | MiMo-V2.6-Pro | 0.855 | 0.660 | 5.19 | 1.816 |

- **v1.1.1 补丁（2026-10-05/06）**：一致性整改（政策↔代码↔金标）——H01（因病缓考双材料）与 H06（特别通道十工作日窗，重锚）两题修复后，经 40 sims overlay 对全部 5 行重跑重锚；各行 pre-patch 原值保留。pass^4 同为 0.680 的第 3/4 名按 pass^1 排序互换。详见域 [变更记录](https://github.com/Zitrack/tau2-bench/blob/dev/campus/src/tau2/domains/campus/README.md#8-变更记录) 与 PR #596 Updates（part 1–3）。
- user simulator 与 NL judge 每行钉在 **DeepSeek V4.1-Flash**（`deepseek-flash`）；temperature=0；seed=20261004；max_steps=60。
- **E14 t1 为上游基础设施故障**（4 波重试，`provider temporarily unavailable`）：剔除该 trial，MiMo 修复前 0.840/0.660、现行 v1.1.1 overlay 0.860/0.680——两种口径均已披露。
- GOAT credits 含 prompt 缓存收益（GLM-5.3 无缓存收益 1.63 cr/M；MiMo 98.9% 命中 0.12 cr/M）——13× 计费差异如实披露。

完整协议、判分校准（132 条人工审计）与失败类型学：[`src/tau2/domains/campus/README.md`](src/tau2/domains/campus/README.md) 与 [#596](https://github.com/sierra-research/tau2-bench/pull/596) 的 PR 描述。

## 复现

```bash
uv sync
pytest tests/test_domains/test_campus          # 141 项测试
uv run tau2 run --domain campus --agent llm_agent \
  --agent-llm <provider>/<model> \
  --user user_simulator --user-llm deepseek/deepseek-flash \
  --task-split-name base
```

数据集（任务集 / 政策 / 种子库）：[huggingface.co/datasets/ZitrackHF/tau2-zh-campus](https://huggingface.co/datasets/ZitrackHF/tau2-zh-campus)

## 仓库结构（本 fork）

| 分支 / 路径 | 内容 |
|---|---|
| `main` | 上游 `sierra-research/tau2-bench` 的纯净镜像 |
| **`tau2-zh`**（默认） | **本页 + 完整 campus 域**——项目展示 |
| `dev/campus` | 上游 PR #596 的确切来源分支 |
| `src/tau2/domains/campus/` | 域代码：`data_model / user_data_model / tools / user_tools / environment` |
| `data/tau2/domains/campus/` | `policy.md` + `db.json` + `user_db.json` + `tasks.json`（50）+ `split_tasks.json` |
| `tests/test_domains/test_campus/` | 141 项测试 |

## 许可与致谢

代码与域内容遵循上游 **MIT 许可**。τ²-bench 由 Sierra Research 开发（[上游仓库](https://github.com/sierra-research/tau2-bench)，论文：[*τ²-Bench: Evaluating Conversational Agents in a Dual-Control Environment*](https://arxiv.org/abs/2506.07982)）。campus 域中的全部机构、人名与记录均为虚构（"青川大学 / Qingchuan University"）；政策素材改写自公开法规并脱敏。
