# campus — University Academic-Affairs Service Domain (τ²-bench first native Chinese domain)

> Domain package for [τ²-bench](https://github.com/sierra-research/tau2-bench) (MIT), pinned to **v1.0.1** scoring.
> All institutions, people, and records in this domain are **fictional** (the university is "Qingchuan University", a made-up school); policy material is rewritten and de-identified from public regulations. No real personal data exists anywhere in this package.

## 1. Domain overview

`campus` is a natively designed **Chinese** domain for university academic-affairs service (course add/drop, exam deferrals, grade review & appeals, scholarships and aid, certificate issuing, student-status and tickets). It is *not* a translation: policy, database, tasks, and user personas are all written for the Chinese higher-education setting, while the scoring protocol stays exactly on the official τ²-bench v1.0.1 track (`reward_basis = [DB, COMMUNICATE]` + `env_assertions`; `RewardType.ACTION` not used), so results read directly against the official leaderboard conventions.

- **Policy**: `data/tau2/domains/campus/policy.md` — a 36-article service regulation for the fictional university, deliberately packed with time-boundary traps (the add-drop window, deferral deadlines, the maintenance window, month-end settlement, tiered appeals…).
- **Tasks**: 50 tasks (`tasks.json` + `split_tasks.json`, splits `base` / `easy` / `medium` / `hard`), difficulty 15 / 20 / 15; **17 refusal tasks** (privacy, skipping appeal levels, out-of-scope requests); every task carries scripted user personas with non-cooperative behavior.
- **Data**: `db.json` (14 tables) + `user_db.json` (students act through their own app).
- **Tests**: `tests/test_domains/test_campus/` — 146 pytest cases (tools, replay, contract, full 50-task gold-replay CI, deadline-guard matrix, state-machine invariants).

## 2. Dual-control design

Following the τ²-bench dual-control protocol, **both** sides hold tools:

| Side | Tools | Role |
|---|---|---|
| Agent (customer-service) | **15** tools (`tools.py`) | look up, apply, withdraw, create tickets… must guide the student to complete multi-step procedures |
| Student (simulated user) | **4** user tools (`user_tools.py`) | upload materials, confirm/sign, and **refuse** — the agent cannot do these *for* the student |

Hard tasks are multi-chain: the student must perform 3–4 actions in their own app while the agent keeps the procedure consistent (e.g. withdrawal requires agent request + student signature). The user simulator is driven by per-task scripted personas (six archetypes + a compliance dimension, non-cooperative by design), so an over-cooperative user cannot silently complete the task for the agent.

## 3. Leaderboard (5 rows / 4 vendors, by pass^4)

Pass^1 = share of passing trials (of 200); pass^4 = tasks passing **4/4** (of 50); 4 trials/task, seed=20261004, temperature=0, max_steps=60; user simulator + NL justification model = DeepSeek-V4.1-Flash.

| # | Model | pass^1 | pass^4 | avg turns | easy / medium / hard |
|---|---|---|---|---|---|
| 1 | DeepSeek V4.1-Flash (anchor) | 0.975 | 0.900 | 6.07 | 1.000 / 0.963 / 0.967 |
| 2 | Qwen3.8-Flash | 0.860 | 0.720 | 5.41 | 0.967 / 0.800 / 0.833 |
| 3 | GLM-5.3 | 0.805 | 0.680 | 5.17 | 0.833 / 0.825 / 0.750 |
| 4 | GLM-5.3-Flash | 0.790 | 0.680 | 5.12 | 0.783 / 0.813 / 0.767 |
| 5 | MiMo-V2.6-Pro | 0.855 | 0.660 | 5.19 | 0.883 / 0.875 / 0.800 |

> **v1.1.1 patch (2026-10-05)**: tasks H01 (two-document illness deferrals, art. 12(2)) and H06 (special-channel 10-workday submission window, re-anchored to 2026-03-20) were updated for policy↔code↔gold consistency and re-run on all rows (40-sim overlay; per-row pre-patch values are preserved in `leaderboard-final.json`). Rows 3/4 swap places at equal pass^4 (0.680), decided by pass^1. See §8 Changelog.

All numbers are recomputed programmatically from `results.json` (never hand-copied). Row 5 includes 1 infrastructure-failed trial in the pre-patch as-run (upstream outage): excluding it gives 0.840 / 0.660 pre-patch and 0.860 / 0.680 on the current v1.1.1 overlay — both calibers are documented. Closed-source flagship models were intentionally not run (cost vs. information gain); the anchor row carries the ceiling reference.

## 4. Protocol & grading declarations

1. Tasks with multi-chain procedures open with the user stating their student ID (hard beat; omitting it provokes ID hallucination).
2. Free-text tickets (M20) are graded on exact DB hashes — rewording loses points; single-trial variance is disclosed as-is.
3. Anchor row and user/NL-justification backend are the same DeepSeek-V4.1-Flash (legacy alias `deepseek-chat` vs canonical `deepseek-flash`, same `system_fingerprint`).
4. Agents occasionally answer in English and "translate away" Chinese policy strings → COMMUNICATE misses; assertion strings are tool-guaranteed entities, but the mechanism is disclosed.
5. Non-cooperative personas are fixed across all tested models (per-task scripted in `tasks.json` + `personas`).
6. seed=20261004, temperature=0 (agent/user/judge), max_steps=60 for every run.

Scoring-contract note: all 50 tasks ship `reward_basis=[DB, COMMUNICATE]` (the upstream default); the 53 `env_assertions` across 25 tasks are diagnostic outputs (reported in `RewardInfo.env_assertions`) and do not gate the reward, per the official v1.0.1 contract (docs/evaluation.md).

**Grading (judge) statement**: COMMUNICATE items use **deterministic substring matching** against the agent's full reply text (no whitespace/full-width normalization); DB items use terminal-state hash comparison; both must pass. The `deepseek-flash` model only writes justification text — the met/not-met decision is fully reproducible by rule (530/530 in calibration). Paraphrases may therefore score as misses; ~60% of misses in the audited population are such string-level engineering noise rather than capability failures.

## 5. Reproduce

> Pin a revision: the default branch (`tau2-zh`) is a showcase snapshot, not the benchmark code.

```sh
git clone --branch campus-v1.1.4 https://github.com/Zitrack/tau2-bench
cd tau2-bench

# install (Python >=3.12,<3.14)
uv sync

# domain tests (146 cases)
uv run pytest tests/test_domains/test_campus

# validate data
uv run tau2 check-data

# run the domain with any OpenAI-compatible agent
uv run tau2 run --domain campus --agent-llm <model> --user-llm deepseek/deepseek-flash \
  --num-trials 4 --task-split-name base

# re-score an existing trajectory dump against current tasks
uv run tau2 evaluate-trajs <results.json> --fresh-tasks
```

Leaderboard rows were produced with a dual-channel harness (agent on an OpenAI-compatible endpoint, user simulator + justification model pinned to `deepseek-flash`) writing `results.json` + `meta.json` per model; full protocol notes, cost disclosures, and the row-addition guide live in the project's `leaderboard-page.md`.

## 6. Citation

```bibtex
@misc{tau2-zh-campus,
  title        = {Tau2-ZH: A Native Chinese Campus Domain for $\tau^2$-bench},
  author       = {{Tau2-ZH Project}},
  year         = {2026},
  howpublished = {\url{https://github.com/Zitrack/tau2-bench} (dev/campus branch)},
  note         = {50 tasks; scoring pinned to tau2-bench v1.0.1}
}
```

Please also cite the benchmark itself: τ²-bench — Si et al., arXiv:2506.07982.

## 7. Known limitations (modeling boundaries)

- **Subject authorization is a policy-compliance test surface, same as upstream**: agent-side tools accept an arbitrary `student_id` (the upstream retail domain behaves identically); campus goes one step further on the student side with `bind_student` initialization binding and upload ownership checks ("records not belonging to you", policy art. 4). An audit-log / authorization-violation dimension is listed as future work.
- **Not modeled**: cross-college approval routing, status propagation after a leave of absence, the major-change workflow, scholarship ranking tables (rank-based eligibility is not tool-verifiable), and statutory public holidays (aligned in policy v1.4: no holiday adjustments in deadline calculations).
- **Certificate / medical field notes**: the certificate progress query (`get_service_requests`) returns `deadline_at` and a detail string but not `ready_at` or proxy-authorization remaining validity (the apply response does carry `ready_at`); `hospital_level` accepts only the canonical values "top-tier" (三甲) and "campus-hospital designated clinic" (校医院指定门诊) — variant spellings are not normalized.

## 8. Changelog

- **v1.1.4 (2026-10-06) — review-round-4 follow-up (art. 33 closure details).** Validity of the proxy-pickup authorization code now anchors to the **signing time** (`auth_sig.acted_at + 30d`), not the later document-upload time, when the "sign first, upload later" path completes the loop; `get_service_requests` distinguishes the two causes of pending-signature — unsigned → 缺签署（代领授权书）, signed-but-missing-ID → 缺受托人证件影像（第 33 条）— so agents are no longer steered to re-sign. Zero gold impact (no gold task contains the affected strings or the sign-first path); gold-replay CI 50/50, 146 tests green. Fix commit lands after tag `campus-v1.1.3`; use tag `campus-v1.1.4` for the corrected pin.
- **v1.1.3 (2026-10-06) — proxy-pickup closure & ticket field slimming (art. 33 / art. 16).** `confirm_action` on a proxy-pickup authorization now requires a bound validly-uploaded proxy ID document before the certificate enters production (art. 33: signature + valid document, in either order — a later valid upload completes the loop once the signature is confirmed); confirming without the document holds the certificate at pending-signature instead of silently entering production. `create_ticket`'s optional `target_grade_id` (art. 16 appeal window) is now window-input only, no longer persisted on the ticket row — agents passing it explicitly get byte-identical terminal states to the default path. Zero impact on the published suite: H07's gold actions already upload the proxy document before confirming, and no gold task passes `target_grade_id`. Gold-replay CI 50/50, 144 tests green.
- **v1.1.2 (2026-10-06) — review follow-up (art. 12).** A medical document uploaded without declaring `hospital_level` (empty or "none") is now marked **returned-for-supplement** instead of invalid; only a declared other-institution (or other non-canonical value) constitutes invalid material → rejection per art. 12, so an incomplete illness-deferral set settles back to pending-materials instead of being rejected and discarding already-valid documents. Zero impact on the published suite: all medical uploads among the 50 tasks declare compliant levels (M05/H01 = top-tier; M16/H07 are non-medical), gold-replay CI 50/50, 141 tests green. Follow-up: `confirm_action` now decides "enter pending-materials" by usable (non-returned) uploads, so a confirmation receipt no longer misreports submitted-for-review when only returned materials exist — response and settled state agree. Variant-level normalization remains disclosed future work.
- **v1.1.1 (2026-10-06) — hardening.** Pre-settle before every tool call (agent & user sides); user-side deadline guards on signature confirmation and material upload (art. 8/12); special-channel stuck-state terminal transition (confirmed-but-overdue → revert + expire); monotonic waitlist positions (max+1, no position reuse after abandonment). Zero live-impact on the published suite proven by the 50-task gold-replay CI (per-task DB/user-DB hashes byte-identical before/after the change).
- **v1.1 (2026-10-05) — consistency fixes (PR #596 updates, part 1/2).** Full gold-replay CI (exceptions-as-failures + terminal-state invariants; countermeasure aligned with upstream issue #499); optional `target_grade_id` appeal binding (art. 16); deferral↔enrollment binding (art. 12/10); illness deferrals restricted to post-exam filing (art. 12); waitlist ACTIVE-status / suspended-offering guards (art. 10/8); `copy_count ≥ 1` (art. 32); authoritative `enrolled_count` recount in special-channel settlement; illness two-document requirement + H01 gold update (art. 12(2)); special-channel 10-workday submission window + H06 re-anchor (art. 9); policy v1.4 (art. 2/13). Scoring-contract note: `env_assertions` are diagnostic outputs and do not gate the reward. Leaderboard re-anchored via a 40-sim overlay rerun (H01/H06, all 5 rows).
- **v1.0.1 (2026-10-03) — initial release.** Campus domain, 50 tasks (easy 15 / medium 20 / hard 15, incl. 17 refusal tasks), dual-control, policy v1.3, 5-row leaderboard.

---

# campus — 高校教务办事域（τ²-bench 首个原生中文域）

> [τ²-bench](https://github.com/sierra-research/tau2-bench)（MIT 许可）的域扩展，计分钉死官方 **v1.0.1**。
> 本域全部机构、人物、记录均**虚构**（学校为"青川大学"，虚构校名）；政策文本由公开规章改写脱敏，包内不含任何真实个人数据。

## 1. 域概要

`campus` 是为中文高校教务场景**原生设计**（非翻译）的域：选课/补退选、考试缓考、成绩查分与申诉、奖助学金、证明开具、学籍与工单。政策（36 条，含补退选窗口、缓考时限、维护窗口、月末结账、逐级申诉等时限坑）、数据库（14 表）、50 题任务（easy 15 / medium 20 / hard 15，含 17 道拒绝题）与 persona 全部中文原生；判分口径与官方同构（`[DB, COMMUNICATE]` + `env_assertions`，不用 ACTION），结果可与官方榜单同读。

## 2. 双控设计

遵循 τ²-bench 双控协议，**两侧**都有工具：

| 侧 | 工具 | 职责 |
|---|---|---|
| Agent（客服侧） | **15** 个工具（`tools.py`） | 查询/申请/撤回/建单……必须引导学生走完多步流程 |
| 学生（模拟用户） | **4** 个用户工具（`user_tools.py`） | 上传材料、确认签署、**拒绝**——这些动作 agent 无法代做 |

难题为多链并发：学生须在自己的 App 里完成 3–4 个动作，同时 agent 保持流程一致（如撤回＝agent 发起＋学生签署）。user simulator 由逐题钉死脚本（六型 persona＋顺从维度，非合作设计）驱动，防止过度合作的模拟用户替 agent 悄悄完成任务。

## 3. 榜单（5 行 / 4 家厂商，按 pass^4 降序）

Pass^1＝通过 trial 占比（共 200）；pass^4＝4/4 全过的题数（共 50）；每题 4 trials、seed=20261004、temperature=0、max_steps=60；user simulator 与 NL 判定模型钉在 DeepSeek-V4.1-Flash。

| # | 模型 | pass^1 | pass^4 | 平均轮次 | 易 / 中 / 难 |
|---|---|---|---|---|---|
| 1 | DeepSeek V4.1-Flash（锚点） | 0.975 | 0.900 | 6.07 | 1.000 / 0.963 / 0.967 |
| 2 | Qwen3.8-Flash | 0.860 | 0.720 | 5.41 | 0.967 / 0.800 / 0.833 |
| 3 | GLM-5.3 | 0.805 | 0.680 | 5.17 | 0.833 / 0.825 / 0.750 |
| 4 | GLM-5.3-Flash | 0.790 | 0.680 | 5.12 | 0.783 / 0.813 / 0.767 |
| 5 | MiMo-V2.6-Pro | 0.855 | 0.660 | 5.19 | 0.883 / 0.875 / 0.800 |

> **v1.1.1 补丁（2026-10-05）**：H01（因病缓考双材料，第 12 条二）与 H06（特别通道十工作日提交窗，重锚至 2026-03-20）为政策↔代码↔金标一致性而更新，并对全部 5 行重跑（40 sims overlay；各行 pre-patch 原值保留于 `leaderboard-final.json`）。pass^4 同为 0.680 的第 3/4 名按 pass^1 排序互换。详见 §8 变更记录。

全部数字均由 `results.json` 程序化重算（绝不手抄）。第 5 行在修复前 as-run 中含 1 个基础设施故障 trial（上游故障）：剔除后修复前为 0.840 / 0.660、现行 v1.1.1 overlay 为 0.860 / 0.680——两种口径均已披露。闭源旗舰模型有意未跑（成本 vs 信息增益）；锚点行承担天花板参照。

## 4. 协议与判分声明

1. 多链程序任务以用户报学号开场（硬节拍；省略会诱发学号幻觉）。
2. 自由文本工单（M20）按精确 DB 哈希判分——改述即失分；单 trial 方差如实披露。
3. 锚点行与 user/判定后端为同一 DeepSeek-V4.1-Flash（遗留别名 `deepseek-chat` 与 canonical `deepseek-flash` 同一 `system_fingerprint`）。
4. Agent 偶尔以英文作答并把中文政策串"翻译掉"→ COMMUNICATE MISS；断言串均为工具必现实体，该机理已披露。
5. 非合作 persona 在全部被测模型间固定（`tasks.json` + persona 逐题脚本）。
6. 每次运行均为 seed=20261004、temperature=0（agent/user/judge）、max_steps=60。

判分契约说明：50 题 reward_basis 均为 [DB, COMMUNICATE]（上游默认）；25 题的 53 条 env_assertions 为诊断性输出（见 RewardInfo.env_assertions），不计入 reward 判分，与官方 v1.0.1 文档契约一致。

**判分（judge）声明**：COMMUNICATE 项对 agent 全程回复文本做**确定性子串匹配**（空格/全半角不归一化）；DB 项为终态哈希比对；两项须同时通过。deepseek-flash 只产出判定文本——met/not-met 完全可由规则复现（校准 530/530）。改述因此可能记 MISS；母体约 60% MISS 属字面工程噪声而非能力失败。

## 5. 复现

> 请基于钉定修订跑基准：默认分支（tau2-zh）为展示快照，非基准代码。

```sh
git clone --branch campus-v1.1.4 https://github.com/Zitrack/tau2-bench
cd tau2-bench

# 安装（Python >=3.12,<3.14）
uv sync

# 域测试（146 项）
uv run pytest tests/test_domains/test_campus

# 数据校验
uv run tau2 check-data

# 以任意 OpenAI 兼容 agent 运行本域
uv run tau2 run --domain campus --agent-llm <model> --user-llm deepseek/deepseek-flash \
  --num-trials 4 --task-split-name base

# 对既有轨迹结果按现行任务重新判分
uv run tau2 evaluate-trajs <results.json> --fresh-tasks
```

榜单各行由双通道 harness 产出（agent 走 OpenAI 兼容端点，user simulator＋判定模型钉在 `deepseek-flash`），逐模型落盘 `results.json`＋`meta.json`；完整协议说明、成本披露与加行指南见项目 `leaderboard-page.md`。

## 6. 引用格式

```bibtex
@misc{tau2-zh-campus,
  title        = {Tau2-ZH: A Native Chinese Campus Domain for $\tau^2$-bench},
  author       = {{Tau2-ZH Project}},
  year         = {2026},
  howpublished = {\url{https://github.com/Zitrack/tau2-bench} (dev/campus branch)},
  note         = {50 tasks; scoring pinned to tau2-bench v1.0.1}
}
```

同时请引用基准本体：τ²-bench — Si et al., arXiv:2506.07982。

## 7. 已知限制（建模边界）

- **主体授权＝政策遵从测试面，与上游同构**：agent 侧工具接受任意 `student_id`（上游 retail 同构行为）；campus 的差异化在学生端——`bind_student` 初始化绑定 + 上传属主校验（"记录不属于本人"，政策第 4 条）。audit-log / 越权维度列为 future work。
- **未建模清单**：跨学院审批流转、休学后的状态传播、转专业工作流、奖学金排名表（排名类资格不经工具校验）。法定节假日已随政策 v1.4 对齐口径（时限计算不引入节假日调整），不再是待建模项。
- **证书 / 医院字段说明**：证书进度查询（`get_service_requests`）返回 `deadline_at` 与明细串，但不返回 `ready_at` 与代领授权余期（申请响应含 `ready_at`）；`hospital_level` 仅收 `三甲` / `校医院指定门诊` canonical 值，变体写法不归一。

## 8. 变更记录

- **v1.1.4（2026-10-06）——第四轮评审跟进（第 33 条闭环细节）**：先签后传路径闭环推进时，代领授权码有效期锚定为**签署时刻**（`auth_sig.acted_at + 30 日`），不再按后置上传时刻起算；`get_service_requests` 对"待签署"按成因分流——未签署 → 缺签署（代领授权书），已签署缺证件 → 缺受托人证件影像（第 33 条）——不再误导 agent 重新签署。对金标零影响（受影响字符串与先签后传路径均不在金标中）；金标重放 CI 50/50，146 项测试全绿。修复提交位于 tag `campus-v1.1.3` 之后，修正版请用 tag `campus-v1.1.4`。
- **v1.1.3（2026-10-06）——代领闭环与工单字段瘦身（第 33 条 / 第 16 条）**：代领授权的 `confirm_action` 现要求已绑定有效受托人证件影像方可让证明进入制作（第 33 条：签署＋有效证件，两序皆达——后传的有效证件在上传侧闭环推进）；无证件的签署确认将证明保持在"待签署"，不再静默进入制作。`create_ticket` 的可选 `target_grade_id`（第 16 条申诉窗）改为仅作判窗输入、不再写入工单行——显式传参的 agent 终态与缺省路径逐字节一致。对现役 50 题零影响（H07 金标本就先传证件后签署；金标零传参）。金标重放 CI 50/50，144 项测试全绿。
- **v1.1.2（2026-10-06）——评审跟进（第 12 条）**：医疗类材料未申报医院等级（空串/"无"）改为"已退回补报"而非"无效材料"；仅声明"其他机构"（或其他非 canonical 声明值）才构成无效驳回（第 12 条原文）；`confirm_action` 按可用材料（非退回）判定"进入待材料"，回执不再误报"已提交待审"。对现役 50 题零影响（金标重放 CI 50/50，141 项测试全绿）。变体等级归一化仍为已披露 future work。
- **v1.1.1（2026-10-06）——加固**：所有工具调用前置结算（pre-settle，agent/学生两侧）；用户侧签署确认与材料上传 deadline 守卫（第 8/12 条）；特别通道"已确认但逾期"终态迁移（回退＋过期）；候补位次单调（max+1，放弃后不复用位次）。50 题双库哈希逐字节一致证明零现役影响。
- **v1.1（2026-10-05）——一致性修复（PR #596 Updates part 1/2）**：50 题全量金标重放 CI（异常即失败＋终态不变量，对齐上游 #499）；申诉可选绑定目标成绩（第 16 条）；缓考↔选课绑定（第 12/10 条）；因病限考后补办（第 12 条）；候补在读/停开守卫（第 10/8 条）；开具份数≥1（第 32 条）；特别通道结算计数权威重算；因病双材料＋H01 金标更新（第 12 条二）；特别通道十工作日提交窗＋H06 重锚（第 9 条）；政策 v1.4（第 2/13 条）。判分契约说明：`env_assertions` 为诊断性输出、不计入 reward。榜单经 40 sims overlay 重跑重锚（H01/H06，全部 5 行）。
- **v1.0.1（2026-10-03）——首次发布**：campus 域、50 题（易 15/中 20/难 15，含 17 道拒绝题）、双控、政策 v1.3、5 行榜单。
