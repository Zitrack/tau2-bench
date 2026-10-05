"""Campus domain tool tests (S2A T10).

Two layers:
1. Error catalog table-driven: every tools-spec §4 code triggered on seed data,
   message compared against the §4 template text (措辞即判分变量，逐字).
2. State-machine transition tables: the 5 dual-control chains of tools-spec §5
   plus withdraw/expiry branches, asserted end-state-only (env_assertions 口径).

Data targets are hardcoded against contract db.json seed (baseline ea7ec13);
regenerating seeds must keep these anchors or update this file in the same commit.
"""

import pytest

from tau2.domains.campus.environment import get_environment


@pytest.fixture
def env():
    return get_environment()


def set_now(env, ts):
    env.tools.db.env.current_time = ts


# ------------------------------------------------------------------ 错误目录逐条触发

class TestErrorCatalog:
    def test_e_maintenance_blocks_agent_and_user_writes(self, env):
        set_now(env, "2026-06-15 02:00")  # 周一 02:00，维护窗内
        with pytest.raises(ValueError, match="当前处于系统维护时段（周日23:00–周一06:00，第3条）"):
            env.tools.create_ticket("S20230103", "咨询", "其他", "x", "y")
        env.user_tools.bind_student("S20230103")
        with pytest.raises(ValueError, match="写操作暂停，查询不受影响"):
            env.user_tools.upload_material("deferral_requests", "DF-006", "诊断证明", "a.pdf", "三甲")
        # 读不受影响
        assert env.tools.get_student_details("S20230103").student_status == "在读"

    def test_e_window_closed_enroll_and_drop(self, env):
        with pytest.raises(ValueError, match="补退选已于 2026-03-15 23:59 截止（政策第7条）"):
            env.tools.enroll_course("S20250401", "OF-2026SP-301-1")
        # 窗口外非毕业班退课
        en = next(e for e in env.tools.db.enrollments.values()
                  if e.student_id == "S20230103" and e.term == "2026SP" and e.status == "已选")
        with pytest.raises(ValueError, match="本学期不再受理退课；如为毕业班学生可走特别通道（第9条）"):
            env.tools.drop_course("S20230103", en.enrollment_id)

    def test_e_prereq_missing(self, env):
        set_now(env, "2026-03-04 10:00")  # 窗口内
        with pytest.raises(ValueError, match="要求先修《高等数学A\\(上\\)》合格或正在修读（政策第6条）"):
            env.tools.enroll_course("S20250401", "OF-2026SP-102-1")

    def test_e_capacity_full(self, env):
        set_now(env, "2026-03-04 10:00")
        with pytest.raises(ValueError, match="该课已满，可加入候补（第8条）"):
            env.tools.enroll_course("S20250401", "OF-2026SP-402-1")

    def test_e_time_conflict(self, env):
        set_now(env, "2026-03-04 10:00")
        # S20230103 已选 OF-2026SP-403-1（周二10:00），302 同时段
        with pytest.raises(ValueError, match="上课时间冲突（星期二 10:00-11:40）"):
            env.tools.enroll_course("S20230103", "OF-2026SP-302-1")

    def test_e_deferral_expired(self, env):
        # 2025FA 804 的考试 2026-01-15，考后3工作日早已过
        with pytest.raises(ValueError, match="该场考试已过补办时限（考后3个工作日，政策第12条）"):
            env.tools.submit_deferral("S20230303", "OF-2025FA-804-1", "EX-0014", "因病", "考后补办")

    def test_e_deferral_used(self, env):
        # S20250403 对 OF-2026SP-702-1 已有 DF-006（待签署，未撤回）→ 不占则拦
        with pytest.raises(ValueError, match="本学期已申请过缓考（第13条：仅一次）"):
            env.tools.submit_deferral("S20250403", "OF-2026SP-702-1", "EX-0039", "冲突", "考前正常")

    def test_e_approval_pending(self, env):
        # EN-0014 (S20220101) 已是特别通道审核中
        with pytest.raises(ValueError, match="毕业班特别通道申请仍在学院/教务处双重审核中（第9条）"):
            env.tools.drop_course("S20220101", "EN-0014")

    def test_e_aid_pool(self, env):
        with pytest.raises(ValueError, match="国家助学金/励志奖学金要求已认定入库（第27条）"):
            env.tools.submit_scholarship_app("S20230103", "AW-002")

    def test_e_record_uneligible(self, env):
        # S20230301 评定学年(2025-2026)有 F/缺 → 人民奖学金 no_fail_this_year
        with pytest.raises(ValueError, match="评定学年存在不及格记录（含'缺'）（第24条）.*重修通过不消除当学年记录（第19条）"):
            env.tools.submit_scholarship_app("S20230301", "AW-003")

    def test_e_stack_conflict(self, env):
        # S20230401 已获 AW-007 国助（APP-006 通过），AW-001/AW-007 互斥
        with pytest.raises(ValueError, match="与已申请/已获国家助学金构成兼得限制（第25条），请撤回其一"):
            env.tools.submit_scholarship_app("S20230401", "AW-001")

    def test_e_review_expired_only_appeal_grade(self, env):
        with pytest.raises(ValueError, match="成绩公布已超5个工作日，查分不受理（第16条）；申诉通道不适用于替代查分"):
            env.tools.create_ticket("S20230103", "申诉", "成绩", "复核", "学号S20230103")
        # v1.1-F2：咨询类成绩工单不触发
        t = env.tools.create_ticket("S20230103", "咨询", "成绩", "了解", "学号S20230103")
        assert t.ticket_id == "TK-006"

    def test_e_level_skip_appeal(self, env):
        # parent 挂他人/状态不符 → 越级拦截
        with pytest.raises(ValueError, match="复核须先经学院处理（第34条）"):
            env.tools.create_ticket("S20250401", "申诉", "选课", "复核选课", "学号S20250401",
                                    parent_ticket_id="TK-001")

    def test_e_waitlist_frozen(self, env):
        set_now(env, "2026-03-04 10:00")
        env.tools.db.students["S20250401"].waitlist_abandon_count = 3
        with pytest.raises(ValueError, match="本学期候补放弃已累计3次（政策第8条）"):
            env.tools.join_waitlist("S20250401", "OF-2026SP-402-1")

    def test_waitlist_cutoff_48h(self, env):
        # 锚 6-12 已过 adddrop_deadline-48h（3-13 23:59）
        with pytest.raises(ValueError, match="候补申请已于 2026-03-13 23:59 截止"):
            env.tools.join_waitlist("S20250401", "OF-2026SP-402-1")

    def test_e_cert_batch_defers_application(self, env):
        set_now(env, "2026-06-30 18:00")  # 6月最后工作日（周二）结账窗内
        r = env.tools.request_certificate("S20230103", "在读证明")
        assert r.status == "顺延结账"
        assert "证明系统月末结账中（最后工作日17:00–22:00，第31条），申请已顺延" in r.message

    def test_no_data_boundary_interception(self, env):
        """v1.1-F5：读工具对代查不拦截（E-DATA-BOUNDARY 不注册运行时）。"""
        d = env.tools.get_student_details("S20230103")
        assert d.server_time == "2026-06-12 10:00"


# ------------------------------------------------------------------ 状态机转移表

class TestDeferralChain:
    def test_conflict_full_chain_approve(self, env):
        t, u = env.tools, env.user_tools
        r = t.submit_deferral("S20230103", "OF-2026SP-203-1", "EX-0049", "冲突", "考前正常")
        assert r.status == "待签署"
        u.bind_student("S20230103")
        c = u.confirm_action(r.sig_id)
        assert c.business_status == "已提交待审"
        env.sync_tools()
        df = t.db.deferral_requests[r.request_id]
        assert (df.status, df.review_stage) == ("通过", "完成")
        assert t.db.exam_arrangements["EX-0049"].status == "已缓考"
        todo = t.user_db.app_todos[[k for k, v in t.user_db.app_todos.items() if v.ref_id == r.request_id][0]]
        assert todo.status == "已完成"

    def test_illness_invalid_material_reject(self, env):
        t, u = env.tools, env.user_tools
        r = t.submit_deferral("S20230103", "OF-2026SP-203-1", "EX-0049", "因病", "考后补办")
        u.bind_student("S20230103")
        u.confirm_action(r.sig_id)  # 无材料 → 待材料
        df = t.db.deferral_requests[r.request_id]
        assert df.status == "待材料"
        up = u.upload_material("deferral_requests", r.request_id, "诊断证明", "私人诊所.pdf", "其他机构")
        assert up.status == "无效材料"
        assert df.status == "驳回"
        assert "无效材料" in df.reject_reason

    def test_illness_valid_material_approve(self, env):
        t, u = env.tools, env.user_tools
        r = t.submit_deferral("S20230103", "OF-2026SP-203-1", "EX-0049", "因病", "考后补办")
        u.bind_student("S20230103")
        u.confirm_action(r.sig_id)
        up = u.upload_material("deferral_requests", r.request_id, "诊断证明", "市一院.pdf", "三甲")
        assert t.db.deferral_requests[r.request_id].status == "已提交待审"
        env.sync_tools()
        assert t.db.deferral_requests[r.request_id].status == "通过"
        assert t.user_db.uploads[up.upload_id].status == "已核验"

    def test_upload_before_sign_completes_upload_todo(self, env):
        """D-S3A-3：签署前上传有效材料，材料上传待办即完成，业务行仍待签署。
        M1-A3 适配：场景从 504/EX-0050（该生无选课行，绑定守卫后非法）改为本人已选的 203/EX-0049，断言不变。"""
        t, u = env.tools, env.user_tools
        r = t.submit_deferral("S20230103", "OF-2026SP-203-1", "EX-0049", "因病", "考后补办")
        u.bind_student("S20230103")
        up = u.upload_material("deferral_requests", r.request_id, "诊断证明", "诊断证明.pdf", "三甲")
        df = t.db.deferral_requests[r.request_id]
        assert df.status == "待签署"
        todo = next(v for v in t.user_db.app_todos.values()
                    if v.ref_id == r.request_id and v.type == "缓考材料上传")
        assert todo.status == "已完成"
        # 后续签署一路走到通过（材料已齐，不再进入待材料）
        u.confirm_action(r.sig_id)
        env.sync_tools()
        assert t.db.deferral_requests[r.request_id].status == "通过"

    def test_pending_sign_expiry_by_advance_time(self, env):
        t, u = env.tools, env.user_tools
        r = t.submit_deferral("S20230103", "OF-2026SP-203-1", "EX-0049", "冲突", "考前正常")
        u.bind_student("S20230103")
        t.advance_time(days=15)  # 过 deadline（EX-0049 6/26 前一日 23:59）
        env.sync_tools()
        df = t.db.deferral_requests[r.request_id]
        assert df.status == "逾期"
        sig = t.user_db.pending_signatures[r.sig_id]
        assert sig.status == "已过期"

    def test_withdraw_before_sign_restores_quota(self, env):
        t, u = env.tools, env.user_tools
        r = t.submit_deferral("S20230103", "OF-2026SP-203-1", "EX-0049", "冲突", "考前正常")
        u.bind_student("S20230103")
        w = t.withdraw_application("S20230103", "deferral", r.request_id)
        assert w.new_status == "已撤回"
        assert t.user_db.pending_signatures[r.sig_id].status == "已过期"
        # P13 额度恢复：重新申请成功
        r2 = t.submit_deferral("S20230103", "OF-2026SP-203-1", "EX-0049", "冲突", "考前正常")
        assert r2.status == "待签署"
        # 已提交待审阶段不可撤回
        u.confirm_action(r2.sig_id)
        with pytest.raises(ValueError, match="签署确认前方可主动撤回"):
            t.withdraw_application("S20230103", "deferral", r2.request_id)


class TestAwardAndCertificate:
    def test_fast_track_full_flow(self, env):
        t, u = env.tools, env.user_tools
        r = t.submit_scholarship_app("S20220101", "AW-008", "突发快速通道")
        assert t.db.students["S20220101"].temp_aid_used_this_year is True
        u.bind_student("S20220101")
        u.upload_material("scholarship_apps", r.app_id, "事故证明", "山火.pdf")
        u.confirm_action(r.sig_id)
        assert t.db.scholarship_apps[r.app_id].status == "待学院审"
        env.sync_tools()
        app = t.db.scholarship_apps[r.app_id]
        assert app.status == "公示中" and app.publicized_until is not None
        t.advance_time(hours=360)  # +15天，过公示
        env.sync_tools()
        assert t.db.scholarship_apps[r.app_id].status == "通过"

    def test_award_sign_pending_seed_confirm(self, env):
        t, u = env.tools, env.user_tools
        u.bind_student("S20240202")
        c = u.confirm_action("SIG-004")  # 种子待签署：APP-004 人民奖学金一等
        assert c.business_status == "待学院审"
        env.sync_tools()
        assert t.db.scholarship_apps["APP-004"].status in ("公示中", "驳回")

    def test_english_transcript_notes_unpublished(self, env):
        r = env.tools.request_certificate("S20240101", "英文成绩单", language="英")
        assert "英文成绩单仅含已正式记载成绩（第32条）" in r.message

    def test_cert_proxy_authorize_chain(self, env):
        t, u = env.tools, env.user_tools
        r = t.request_certificate("S20230103", "在读证明", delivery="委托代领",
                                  proxy_name="李受托", proxy_id_masked="****5678")
        assert r.status == "待签署"
        u.bind_student("S20230103")
        u.upload_material("certificates", r.cert_id, "身份证件影像", "id.jpg")
        u.confirm_action(r.sig_id)
        ce = t.db.certificates[r.cert_id]
        assert ce.status == "制作中"
        assert ce.proxy_info.valid_until == "2026-07-12 10:00"
        t.advance_time(hours=96)  # 6-16 10:00，未过 ready_at(6-17 10:00)
        env.sync_tools()
        assert ce.status == "制作中"
        t.advance_time(hours=48)  # 6-18 → 过 ready_at
        env.sync_tools()
        assert ce.status == "可领取" and ce.verify_code
        # 出具后不可撤回
        with pytest.raises(ValueError, match="出具前方可撤回（第30条）"):
            t.withdraw_application("S20230103", "certificate", r.cert_id)

    def test_cert_withdraw_before_issue(self, env):
        r = env.tools.request_certificate("S20230103", "中文成绩单")
        w = env.tools.withdraw_application("S20230103", "certificate", r.cert_id)
        assert w.new_status == "已撤回"
        assert env.tools.db.certificates[r.cert_id].ready_at is not None  # 留行标注


class TestWaitlistAndSpecialChannel:
    def test_drop_promotes_and_confirm(self, env):
        t, u = env.tools, env.user_tools
        set_now(env, "2026-03-04 10:00")
        r = t.drop_course("S20230101", "EN-0027")  # 402 空出一位
        assert r.status == "已退课"
        # 队列头 EN-0070 种子确认单 SIG-015 未过期 → 不为后序抢跑发新单
        assert t.db.course_offerings["OF-2026SP-402-1"].enrolled_count == 3
        sig159 = [s for s in t.user_db.pending_signatures.values()
                  if s.doc_type == "候补递补确认单" and s.ref_id == "EN-0159"]
        assert sig159 == []
        u.bind_student("S20230104")
        c = u.confirm_action("SIG-015")
        assert c.business_status == "已选"
        assert t.db.enrollments["EN-0070"].source == "候补递补"
        off = t.db.course_offerings["OF-2026SP-402-1"]
        assert off.enrolled_count == 4 and off.status == "满员"
        # 再退一位 → 队列下一位 EN-0159 收到新确认单
        t.drop_course("S20230102", "EN-0041")
        sig2 = [s for s in t.user_db.pending_signatures.values()
                if s.doc_type == "候补递补确认单" and s.ref_id == "EN-0159" and s.status == "待确认"]
        assert len(sig2) == 1
        assert t.db.enrollments["EN-0159"].promote_sig_id == sig2[0].sig_id

    def test_waitlist_reject_counts_abandon(self, env):
        t, u = env.tools, env.user_tools
        u.bind_student("S20230104")
        r = u.reject_suggestion("SIG-015", reason="已选别的课")
        assert r.business_status == "失效"
        assert t.db.students["S20230104"].waitlist_abandon_count == 1
        assert t.db.course_offerings["OF-2026SP-402-1"].waitlist_count == 1

    def test_waitlist_expiry_by_advance(self, env):
        t, u = env.tools, env.user_tools
        set_now(env, "2026-03-04 10:00")
        t.drop_course("S20230101", "EN-0027")  # 先空出一位（前序 SIG-015 未过期，不为 0159 抢跑）
        set_now(env, "2026-06-12 19:00")       # SIG-015 deadline 18:00 已过
        env.sync_tools()
        assert t.db.enrollments["EN-0070"].status == "失效"
        assert t.db.students["S20230104"].waitlist_abandon_count == 1
        # 空位顺延递补：EN-0159 生成新确认单
        sig = [s for s in t.user_db.pending_signatures.values()
               if s.doc_type == "候补递补确认单" and s.ref_id == "EN-0159" and s.status == "待确认"]
        assert len(sig) == 1

    def test_special_channel_confirm_approve(self, env):
        t, u = env.tools, env.user_tools
        # S20220101 唯一开课 805 → 无替代 → 双重程序通过
        en = next(e for e in t.db.enrollments.values()
                  if e.student_id == "S20220101" and e.offering_id == "OF-2026SP-805-1" and e.status == "已选")
        r = t.drop_course("S20220101", en.enrollment_id)
        assert r.status == "特别通道审核中"
        u.bind_student("S20220101")
        u.confirm_action(r.special_sig_id)
        env.sync_tools()
        row = t.db.enrollments[en.enrollment_id]
        assert row.status == "已退课" and row.drop_channel == "特别通道"

    def test_special_channel_reject_when_alternative(self, env):
        t, u = env.tools, env.user_tools
        # 造替代开课：CRS-805 另一门 2026SP 开放有余位
        from tau2.domains.campus.data_model import OfferingRow
        src = t.db.course_offerings["OF-2026SP-805-1"]
        alt = src.model_copy(update={"offering_id": "OF-2026SP-805-2", "enrolled_count": 10,
                                      "capacity": 40, "status": "开放"})
        t.db.course_offerings["OF-2026SP-805-2"] = alt
        en = next(e for e in t.db.enrollments.values()
                  if e.student_id == "S20220101" and e.offering_id == "OF-2026SP-805-1" and e.status == "已选")
        r = t.drop_course("S20220101", en.enrollment_id)
        u.bind_student("S20220101")
        u.confirm_action(r.special_sig_id)
        env.sync_tools()
        assert t.db.enrollments[en.enrollment_id].status == "已选"  # 有替代 → 维持原状

    def test_special_channel_student_rejects(self, env):
        t, u = env.tools, env.user_tools
        en = next(e for e in t.db.enrollments.values()
                  if e.student_id == "S20220101" and e.offering_id == "OF-2026SP-805-1" and e.status == "已选")
        r = t.drop_course("S20220101", en.enrollment_id)
        u.bind_student("S20220101")
        u.reject_suggestion(r.special_sig_id, reason="再想想")
        assert t.db.enrollments[en.enrollment_id].status == "已选"


class TestDualControlBoundary:
    def test_agent_cannot_flip_signature(self, env):
        # Agent 侧不存在任何能翻转 SIG 状态的工具（工具面清点）
        names = {t.name for t in env.get_tools()}
        assert all(not n.startswith(("confirm", "reject", "sign")) for n in names)
        r = env.tools.submit_deferral("S20230103", "OF-2026SP-203-1", "EX-0049", "冲突", "考前正常")
        assert env.tools.user_db.pending_signatures[r.sig_id].status == "待确认"

    def test_user_cannot_operate_others(self, env):
        u = env.user_tools
        u.bind_student("S20230103")
        with pytest.raises(ValueError, match="不属于本人"):
            u.upload_material("deferral_requests", "DF-006", "诊断证明", "x.pdf", "三甲")
        with pytest.raises(ValueError, match="或不属于本人"):
            u.confirm_action("SIG-013")  # DF-006 的签署单属 S20250403


class TestReadTools:
    def test_server_time_first_on_every_tool(self, env):
        results = {
            "student": env.tools.get_student_details("S20230103"),
            "offerings": env.tools.get_course_offerings("2026SP", keyword="算法"),
            "enrollments": env.tools.get_enrollments("S20230103", "2026SP"),
            "grades": env.tools.get_grades("S20230103"),
            "exams": env.tools.get_exam_arrangements("S20230103", "2026SP"),
            "requests": env.tools.get_service_requests("S20250403", "deferral"),
            "policy": env.tools.search_policy("维护"),
        }
        for name, res in results.items():
            first = list(res.model_dump().keys())[0]
            assert first == "server_time", f"{name} first field is {first}"

    def test_get_grades_semantic_annotations(self, env):
        g = env.tools.get_grades("S20240101")
        huang = [x for x in g.grades if x.grade_level == "缓"]
        assert huang and "不属于通过成绩" in huang[0].note
        g2 = env.tools.get_grades("S20230303")
        que = [x for x in g2.grades if x.grade_level == "缺"]
        assert que and "放弃课程" in que[0].note

    def test_get_grades_retake_relation_marked(self, env):
        # 种子含重修行（replaces_grade_id）
        from tau2.domains.campus.data_model import GradeRow
        retakes = [g for g in env.tools.db.grades.values() if g.is_retake and g.replaces_grade_id]
        assert retakes
        g = env.tools.get_grades(retakes[0].student_id)
        assert any(retakes[0].replaces_grade_id in x.note for x in g.grades)

    def test_exam_publish_gate(self, env):
        ex = env.tools.get_exam_arrangements("S20230103", "2026SP")
        assert all(x.scheduled_at != "" for x in ex.exams)
        # 未公布（published_at 未到）→ 掩码显示
        set_now(env, "2026-06-01 10:00")
        ex2 = env.tools.get_exam_arrangements("S20230103", "2026SP")
        assert all(x.scheduled_at == "未公布" for x in ex2.exams)

    def test_search_policy_chapters_and_full_text(self, env):
        allc = env.tools.search_policy("", section="")
        assert len(allc.clauses) == 36  # 六章36条一字不动的回归锚
        maint = env.tools.search_policy("例行维护", section="总则")
        assert [c.clause_no for c in maint.clauses] == [3]
        assert "周日 23:00 至周一 06:00" in maint.clauses[0].text
        sel = env.tools.search_policy("", section="选课")
        assert [c.clause_no for c in sel.clauses] == [5, 6, 7, 8, 9, 10]

    def test_service_requests_missing_flags(self, env):
        rs = env.tools.get_service_requests("S20250403", "deferral")
        df6 = [x for x in rs.requests if x.request_id == "DF-006"][0]
        assert "缺签署" in " ".join(df6.missing)


# ------------------------------------------------------------------ M1 一致性守卫（A2–A7，R10 P1-3/5/6/8/9、P2-9）

class TestM1ConsistencyGuards:
    def test_appeal_target_grade_in_window_succeeds(self, env):
        # GR-0033 公布 2026-01-23 09:00（周五）→ 5 工作日窗至 2026-01-30 23:59
        set_now(env, "2026-01-26 10:00")
        r = env.tools.create_ticket("S20230103", "申诉", "成绩", "复核", "学号S20230103",
                                    target_grade_id="GR-0033")
        assert env.tools.db.tickets[r.ticket_id].target_grade_id == "GR-0033"

    def test_appeal_target_grade_expired_rejected(self, env):
        # 种子时点 2026-06-12：GR-0033（2026-01-23 公布）早已越 5 工作日窗
        with pytest.raises(ValueError, match="成绩公布已超5个工作日"):
            env.tools.create_ticket("S20230103", "申诉", "成绩", "复核", "学号S20230103",
                                    target_grade_id="GR-0033")

    def test_appeal_target_overrides_any_grade_scan(self, env):
        """P1-3 修复核心语义：指定目标按该成绩判窗——其他成绩在窗也救不了越窗的目标。"""
        set_now(env, "2026-01-26 10:00")  # GR-0033 在窗；GR-0028（2025-01-24 公布）越窗
        with pytest.raises(ValueError, match="成绩公布已超5个工作日"):
            env.tools.create_ticket("S20230103", "申诉", "成绩", "复核", "学号S20230103",
                                    target_grade_id="GR-0028")

    def test_appeal_target_grade_missing_or_not_own(self, env):
        with pytest.raises(ValueError, match="未找到成绩记录 GR-9999（或不属于该学号）"):
            env.tools.create_ticket("S20230103", "申诉", "成绩", "复核", "学号S20230103",
                                    target_grade_id="GR-9999")
        other = next(g.grade_id for g in env.tools.db.grades.values() if g.student_id != "S20230103")
        with pytest.raises(ValueError, match="未找到成绩记录 .*（或不属于该学号）"):
            env.tools.create_ticket("S20230103", "申诉", "成绩", "复核", "学号S20230103",
                                    target_grade_id=other)

    def test_appeal_without_target_unchanged(self, env):
        """不传 target_grade_id：判窗行为与修前完全一致（种子时点拒、窗内过、行不带 target）。"""
        with pytest.raises(ValueError, match="成绩公布已超5个工作日"):
            env.tools.create_ticket("S20230103", "申诉", "成绩", "复核", "学号S20230103")
        set_now(env, "2026-01-26 10:00")
        r = env.tools.create_ticket("S20230103", "申诉", "成绩", "复核", "学号S20230103")
        assert env.tools.db.tickets[r.ticket_id].target_grade_id is None

    def test_deferral_requires_own_enrollment(self, env):
        # S20250401 在读但未选 OF-2026SP-203-1 → 缓考绑定守卫拒绝（第12/10条）
        with pytest.raises(ValueError, match="未找到该课程的在读选课记录，无法申请缓考（政策第12/10条）"):
            env.tools.submit_deferral("S20250401", "OF-2026SP-203-1", "EX-0049", "冲突", "考前正常")

    def test_illness_requires_post_exam_filing(self, env):
        # 因病 + 考前正常 → 拒（第12条二）；因病主路径由 test_illness_* 与 A1 金标重放钉住
        with pytest.raises(ValueError, match="因病缓考属考后补办（第12条二）"):
            env.tools.submit_deferral("S20230103", "OF-2026SP-203-1", "EX-0049", "因病", "考前正常")

    def test_waitlist_requires_active_status(self, env):
        # S20240105 休学 → 学籍守卫先于窗口/容量检查触发（第10条）
        with pytest.raises(ValueError, match="当前学籍状态为'休学'（政策第10条）：非在读状态不享受选课服务（含候补）"):
            env.tools.join_waitlist("S20240105", "OF-2026SP-402-1")

    def test_waitlist_rejects_suspended_offering(self, env):
        # OF-2026SP-401-1 已停开 → 停开守卫先于 48h 截止检查触发（第9条相关）
        with pytest.raises(ValueError, match="本学期已停开（第9条相关）：不可加入候补"):
            env.tools.join_waitlist("S20250401", "OF-2026SP-401-1")

    def test_cert_copy_count_lower_bound(self, env):
        with pytest.raises(ValueError, match="开具份数至少为 1 份（政策第32条）"):
            env.tools.request_certificate("S20230103", "在读证明", copy_count=0)
