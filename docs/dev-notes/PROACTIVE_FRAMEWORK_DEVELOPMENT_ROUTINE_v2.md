# Proactive Sales Framework - Development Routine (v2)
## Task-Focused Daily Breakdown

**Project:** Replace Passive Chat Flow with Proactive Sales Framework
**Total Duration:** 14 days (2 weeks)
**Format:** 1 Goal = Multiple Daily Tasks
**Start Date:** TBD

---

## 📊 Project Goals Overview

| Goal | Description | Days | Task Count | Priority |
|------|-------------|------|------------|----------|
| **GOAL 1** | Core 5-Step Proactive Framework | Day 1-4 | 33 tasks | P0 - Critical |
| **GOAL 2** | Edge Cases & Customer Experience | Day 5-8 | 28 tasks | P1 - High |
| **GOAL 3** | Advanced Features & Polish | Day 9-11 | 22 tasks | P2 - Medium |
| **GOAL 4** | Testing & Production Launch | Day 12-14 | 27 tasks | P1 - Critical |

**Total Tasks:** 110 tasks across 14 days

---

# 🎯 GOAL 1: Core 5-Step Proactive Framework (P0)
**Duration:** Day 1-4
**Objective:** Implement STEP 1-5 of proactive sales flow
**Priority:** P0 - MUST COMPLETE (Critical Path)

---

## DAY 1 - Foundation & STEP 1 (Opening)
**Total Tasks:** 10 tasks
**Focus:** Preparation + Proactive Opening Implementation

### Tasks:
1. ✅ **[P0]** Read complete `chat_flow_comparison.md` and `FRAMEWORK_ANALYSIS_AND_ISSUES.md`
2. ✅ **[P0]** Locate and backup current prompt file (`config/prompts.yaml`)
3. ✅ **[P0]** Document current prompt structure (sections, line numbers)
4. ✅ **[P0]** Set up development environment (create test branch)
5. ✅ **[P0]** Remove passive "Hi boss" only rule (current Line 636-640)
6. ✅ **[P0]** Add proactive opening templates:
   - New customer: "Hi boss! 今天想来放松一下吗？😊"
   - Returning customer: "Hi boss! 跟上次一样吗？还是想试别的？😊"
7. ✅ **[P0]** Add returning customer detection logic
8. ✅ **[P1]** Add "fast track" detection (Issue #4 - customer knows what they want)
9. ✅ **[P0]** Test opening with 10 sample conversations
10. ✅ **[P0]** Document Day 1 changes in changelog

**Deliverable:** Proactive opening section implemented
**Blocker Risk:** None (preparation phase)

---

## DAY 2 - STEP 2 (Discovery) + Pain Point Detection
**Total Tasks:** 12 tasks
**Focus:** Need discovery and pain point detection system

### Tasks:
1. ✅ **[P0]** Add pain point keyword detection - 身体部位痛点 (肩颈, 腰, 背, 脚)
2. ✅ **[P0]** Add pain point keyword detection - 状态痛点 (累, 压力大, 睡不好)
3. ✅ **[P0]** Add pain point keyword detection - 职业痛点 (久坐, 久站, 运动后)
4. ✅ **[P0]** Add discovery question templates (通用探需问题)
5. ✅ **[P0]** Add targeted discovery questions (针对性探需问题)
6. ✅ **[P1]** Add "just browsing" mode detection (Issue #1)
7. ✅ **[P1]** Add "generic relaxation" path (Issue #9 - no specific pain)
8. ✅ **[P1]** Add multi-pain point handling logic (Issue #2)
9. ✅ **[P1]** Add discovery loop prevention (max 2 questions rule - Issue #9)
10. ✅ **[P1]** Resolve message length conflict (Issue #7 - update style rules)
11. ✅ **[P0]** Test with 15 pain point scenarios
12. ✅ **[P0]** Document Day 2 changes

**Deliverable:** Pain point detection and discovery section
**Blocker Risk:** Low (depends on Day 1 opening)

---

## DAY 3 - STEP 3 (Recommend) + STEP 4 (Value)
**Total Tasks:** 11 tasks
**Focus:** Pain point → service mapping + value explanation

### Tasks:
1. ✅ **[P0]** Create targeted recommendation mapping: 肩颈酸 → 90/120分钟身体按摩 + 拔罐
2. ✅ **[P0]** Create recommendation mapping: 全身累 → 120分钟身体按摩
3. ✅ **[P0]** Create recommendation mapping: 脚酸 → 90分钟足部按摩
4. ✅ **[P0]** Create recommendation mapping: 压力大/睡不好 → 90/120分钟身体按摩
5. ✅ **[P1]** Create multi-pain point combination recommendations (Issue #2)
6. ✅ **[P0]** Add value explanation templates for each pain point
7. ✅ **[P1]** Optimize price anchoring (Issue #6 - value before price)
8. ✅ **[P0]** Update 3-package recommendation with value framing
9. ✅ **[P0]** Add social proof phrases ("很多客人都说...")
10. ✅ **[P0]** Test recommendations with 20 pain point scenarios
11. ✅ **[P0]** Document Day 3 changes

**Deliverable:** Targeted recommendation and value sections
**Blocker Risk:** Medium (requires Day 2 pain point detection)

---

## DAY 4 - STEP 5 (Close) + Objection Handling
**Total Tasks:** 10 tasks (includes Goal 1 integration test)
**Focus:** Proactive booking guidance + objection handling

### Tasks:
1. ✅ **[P0]** Add proactive booking questions: "您想预约今天还是明天？"
2. ✅ **[P0]** Add call-to-action templates (二选一法, 假设成交法)
3. ✅ **[P0]** Add objection handling: "太贵了" → member price + shorter package
4. ✅ **[P0]** Add objection handling: "再考虑" → membership registration hook
5. ✅ **[P0]** Add objection handling: "没时间" → late hours availability
6. ✅ **[P0]** Add objection handling: "下次吧" → soft close
7. ✅ **[P0 CRITICAL]** Add "back-off" detection (Issue #5 - not too pushy)
8. ✅ **[P0]** Test full flow: opening → discovery → recommend → close (30 scenarios)
9. ✅ **[P0]** Goal 1 integration test - verify all STEP 1-5 working together
10. ✅ **[P0]** Document Day 4 changes + create Goal 1 completion report

**Deliverable:** Complete STEP 1-5 proactive flow
**Blocker Risk:** High (critical path - must work before continuing)

**✅ GOAL 1 COMPLETION CHECKPOINT:**
- [ ] Proactive opening works
- [ ] Pain point detection accurate
- [ ] Recommendations targeted
- [ ] Value explanations clear
- [ ] Proactive booking active
- [ ] Objection handling in place
- [ ] "Back-off" logic prevents pushiness
- [ ] All 30+ test scenarios passing

---

# 🎯 GOAL 2: Edge Cases & Customer Experience (P1)
**Duration:** Day 5-8
**Objective:** Handle edge cases and optimize customer experience
**Priority:** P1 - HIGH (Critical for good UX)

---

## DAY 5 - Flexible Booking & Phone Alternative
**Total Tasks:** 8 tasks
**Focus:** Problem #2 from framework doc (booking template issues)

### Tasks:
1. ✅ **[P1]** Add "troublesome template" keyword detection:
   - "麻烦", "好麻烦", "太麻烦了"
   - "懒得填", "不想填", "can't fill"
   - "可以打电话吗", "phone number", "call instead"
2. ✅ **[P1]** Remove "DO NOT provide phone number" restriction (current Line 752)
3. ✅ **[P1]** Add phone booking alternative response template (中英文)
4. ✅ **[P1]** Add "difficult customer" detection logic (6 types from doc)
5. ✅ **[P1]** Add simplified verbal booking flow (name + time + service only)
6. ✅ **[P1]** Add detection for multiple failed template attempts
7. ✅ **[P1]** Test booking flexibility with 15 scenarios
8. ✅ **[P1]** Document Day 5 changes

**Deliverable:** Flexible booking section with phone alternative
**Blocker Risk:** Low (independent feature)

---

## DAY 6 - Returning Customer Optimization
**Total Tasks:** 8 tasks
**Focus:** Issue #3 - Returning customer flow

### Tasks:
1. ✅ **[P1]** Add returning customer detection (check booking history in memory)
2. ✅ **[P1]** Add customized opening for regulars: "跟上次一样吗？"
3. ✅ **[P1]** Add "same as last time" quick booking logic
4. ✅ **[P1]** Add memory usage rules:
   - ❌ Don't say "I remember you"
   - ✅ Use memory silently (pre-fill fields)
   - ✅ Reference past bookings only if relevant
5. ✅ **[P1]** Update memory usage guidelines in prompt
6. ✅ **[P1]** Test new customer flow (ensure not broken)
7. ✅ **[P1]** Test returning customer flow (10 scenarios)
8. ✅ **[P1]** Document Day 6 changes

**Deliverable:** Returning customer flow section
**Blocker Risk:** Medium (requires memory system access)

---

## DAY 7 - Communication Style Balance
**Total Tasks:** 7 tasks
**Focus:** Issue #7 - Message length balance

### Tasks:
1. ✅ **[P1]** Define message length rules by message type:
   - Discovery questions: SHORT (3-7 words)
   - Recommendations: MEDIUM (value explanation allowed)
   - Confirmations: Standard template
   - Quick responses: SHORT
2. ✅ **[P1]** Add examples for each message type
3. ✅ **[P1]** Review all templates for length optimization
4. ✅ **[P1]** Add emoji usage guidelines (moderate, not excessive)
5. ✅ **[P1]** Test communication style consistency (50 conversation samples)
6. ✅ **[P1]** Update communication style guide section
7. ✅ **[P1]** Document Day 7 changes

**Deliverable:** Updated communication style guide
**Blocker Risk:** Low (optimization task)

---

## DAY 8 - Information-Only Mode & Soft Close
**Total Tasks:** 5 tasks (includes Goal 2 integration test)
**Focus:** Issue #1 - "Just browsing" customers

### Tasks:
1. ✅ **[P1]** Add "just browsing" keyword detection (只是问问, just asking, 先了解一下)
2. ✅ **[P1]** Add information-only response templates (provide info without pushing)
3. ✅ **[P1]** Add soft close techniques: "了解了吗？有兴趣的话随时联系我😊"
4. ✅ **[P1]** Add gentle conversion attempt: "要不要试试？😊" (after info provided)
5. ✅ **[P1]** Goal 2 integration test + document Day 8 changes

**Deliverable:** Information-only mode section
**Blocker Risk:** Low (edge case handling)

**✅ GOAL 2 COMPLETION CHECKPOINT:**
- [ ] Flexible booking alternatives working
- [ ] Phone booking option available
- [ ] Returning customer flow optimized
- [ ] Message length balanced
- [ ] Information-only mode working
- [ ] No "too pushy" behavior
- [ ] All edge cases from Issue list addressed

---

# 🎯 GOAL 3: Advanced Features & Polish (P2)
**Duration:** Day 9-11
**Objective:** Bilingual support, state management, documentation
**Priority:** P2 - MEDIUM (Enhancements)

---

## DAY 9 - English Language Support
**Total Tasks:** 8 tasks
**Focus:** Issue #10 - Complete English translations

### Tasks:
1. ✅ **[P2]** Review all Chinese templates (compile complete list)
2. ✅ **[P2]** Create English translations - Opening questions
3. ✅ **[P2]** Create English translations - Discovery questions + pain point keywords
4. ✅ **[P2]** Create English translations - Recommendations + value explanations
5. ✅ **[P2]** Create English translations - Objection handling + closing questions
6. ✅ **[P2]** Test bilingual switching (customer mixes Chinese/English)
7. ✅ **[P2]** Test Malaysian English patterns ("Got slot?", "Can anot?")
8. ✅ **[P2]** Document Day 9 changes

**Deliverable:** Complete bilingual template set
**Blocker Risk:** Low (enhancement)

---

## DAY 10 - Conversation State Management
**Total Tasks:** 7 tasks
**Focus:** Smooth transitions between framework steps

### Tasks:
1. ✅ **[P2]** Add conversation state tracking (Opening, Discovery, Recommendation, Closing)
2. ✅ **[P2]** Add transition rules between states
3. ✅ **[P2]** Add "jump" logic - Direct booking request → skip to booking
4. ✅ **[P2]** Add "jump" logic - Customer says pain point in greeting → skip discovery
5. ✅ **[P2]** Add conversation flow validation
6. ✅ **[P2]** Test state transitions with complex scenarios (20 scenarios)
7. ✅ **[P2]** Document Day 10 changes

**Deliverable:** Conversation state management section
**Blocker Risk:** Low (optimization)

---

## DAY 11 - Documentation & Knowledge Transfer
**Total Tasks:** 7 tasks (includes Goal 3 completion)
**Focus:** Complete documentation for maintainability

### Tasks:
1. ✅ **[P2]** Create complete prompt documentation:
   - Section index with line numbers
   - What each section does
   - How to modify each section
2. ✅ **[P2]** Create conversation flow diagrams
3. ✅ **[P2]** Document all edge cases and handling strategies
4. ✅ **[P2]** Create troubleshooting guide
5. ✅ **[P2]** Create example conversation library (30+ examples)
6. ✅ **[P2]** Document testing procedures
7. ✅ **[P2]** Goal 3 completion report + Day 11 documentation

**Deliverable:** Complete documentation package
**Blocker Risk:** None (documentation)

**✅ GOAL 3 COMPLETION CHECKPOINT:**
- [ ] Bilingual support complete
- [ ] Conversation state management working
- [ ] Flow transitions smooth
- [ ] Documentation complete
- [ ] Example library comprehensive
- [ ] Troubleshooting guide ready

---

# 🎯 GOAL 4: Testing & Production Launch (P1)
**Duration:** Day 12-14
**Objective:** Comprehensive testing and production deployment
**Priority:** P1 - CRITICAL (Launch Readiness)

---

## DAY 12 - Comprehensive Testing Phase 1
**Total Tasks:** 10 tasks
**Focus:** Test all scenarios + bug identification

### Tasks:
1. ✅ **[P1]** Test Suite: 20 pain point mapping scenarios
2. ✅ **[P1]** Test Suite: 10 objection handling scenarios
3. ✅ **[P1]** Test Suite: 15 edge case scenarios
4. ✅ **[P1]** Test Suite: 10 bilingual scenarios
5. ✅ **[P1]** Test Suite: 5 returning customer scenarios
6. ✅ **[P1]** Regression test: Existing booking flow still works
7. ✅ **[P1]** Regression test: Gender policy enforcement still works
8. ✅ **[P1]** Regression test: Membership registration still works
9. ✅ **[P1]** Create bug tracking document + categorize bugs (P0/P1/P2)
10. ✅ **[P1]** Document Day 12 test results

**Deliverable:** Bug report + Test results
**Blocker Risk:** High (bugs may delay launch)

---

## DAY 13 - Bug Fixes & Testing Phase 2
**Total Tasks:** 8 tasks
**Focus:** Fix all critical bugs + retest

### Tasks:
1. ✅ **[P0 CRITICAL]** Fix all P0 (critical) bugs found on Day 12
2. ✅ **[P1]** Fix all P1 (high priority) bugs
3. ✅ **[P2]** Document P2 bugs for future sprints (don't fix yet)
4. ✅ **[P1]** Retest all scenarios that had bugs
5. ✅ **[P1]** Run full regression test suite
6. ✅ **[P1]** Verify all 10 issues from analysis are resolved
7. ✅ **[P1]** Load testing (if applicable - multiple concurrent conversations)
8. ✅ **[P1]** Document Day 13 bug fixes + final test results

**Deliverable:** Bug-free proactive framework
**Blocker Risk:** Critical (must be bug-free for launch)

---

## DAY 14 - Final Review & Production Launch
**Total Tasks:** 9 tasks
**Focus:** Final polish + deployment

### Tasks:
1. ✅ **[P1]** Final review of entire prompt (check for typos, contradictions)
2. ✅ **[P1]** Verify all templates are consistent
3. ✅ **[P2]** Performance optimization (remove redundant instructions)
4. ✅ **[P1]** Create deployment checklist (backup, update, test, monitor, rollback plan)
5. ✅ **[P1]** Create monitoring plan (engagement rate, conversion rate, complaints)
6. ✅ **[P1]** Final stakeholder review and approval
7. ✅ **[P1]** Deploy to staging environment + test first 10 conversations
8. ✅ **[P1]** Deploy to production (or await final approval)
9. ✅ **[P1]** Create Goal 4 completion report + project handover document

**Deliverable:** Production-ready framework deployed
**Blocker Risk:** Critical (requires stakeholder approval)

**✅ GOAL 4 COMPLETION CHECKPOINT:**
- [ ] All bugs fixed
- [ ] All tests passing
- [ ] Regression tests passing
- [ ] Documentation finalized
- [ ] Deployment checklist complete
- [ ] Monitoring plan active
- [ ] Stakeholder approval obtained
- [ ] **PRODUCTION DEPLOYMENT COMPLETE** 🚀

---

# 📅 WEEKLY TASK SUMMARY

## WEEK 1: Core Implementation + Edge Cases
**Days:** 1-7
**Total Tasks:** 61 tasks

| Day | Goal | Focus | Task Count | Priority |
|-----|------|-------|------------|----------|
| **Day 1** | Goal 1 | Foundation + STEP 1 Opening | 10 tasks | P0 |
| **Day 2** | Goal 1 | STEP 2 Discovery + Pain Points | 12 tasks | P0 |
| **Day 3** | Goal 1 | STEP 3-4 Recommend + Value | 11 tasks | P0 |
| **Day 4** | Goal 1 | STEP 5 Close + Objection Handling | 10 tasks | P0 |
| **Day 5** | Goal 2 | Flexible Booking + Phone Alternative | 8 tasks | P1 |
| **Day 6** | Goal 2 | Returning Customer Optimization | 8 tasks | P1 |
| **Day 7** | Goal 2 | Communication Style Balance | 7 tasks | P1 |

**Week 1 Deliverable:** Complete proactive framework (STEP 1-5) + major edge cases handled

---

## WEEK 2: Advanced Features + Testing + Launch
**Days:** 8-14
**Total Tasks:** 49 tasks

| Day | Goal | Focus | Task Count | Priority |
|-----|------|-------|------------|----------|
| **Day 8** | Goal 2 | Information-Only Mode | 5 tasks | P1 |
| **Day 9** | Goal 3 | English Language Support | 8 tasks | P2 |
| **Day 10** | Goal 3 | Conversation State Management | 7 tasks | P2 |
| **Day 11** | Goal 3 | Documentation & Knowledge Transfer | 7 tasks | P2 |
| **Day 12** | Goal 4 | Comprehensive Testing Phase 1 | 10 tasks | P1 |
| **Day 13** | Goal 4 | Bug Fixes + Testing Phase 2 | 8 tasks | P0 |
| **Day 14** | Goal 4 | Final Review + Production Launch | 9 tasks | P1 |

**Week 2 Deliverable:** Production-ready, fully-tested framework deployed

---

# 🚨 CRITICAL PATH (Must Complete for Launch)

| Day | Milestone | Why Critical | Blocker if Skipped |
|-----|-----------|--------------|-------------------|
| **Day 1** | Proactive opening | Framework doesn't start without it | YES - Total blocker |
| **Day 2** | Pain point detection | Core of proactive approach | YES - Total blocker |
| **Day 3** | Targeted recommendations | Differentiator from current system | YES - Total blocker |
| **Day 4** | Proactive booking + back-off logic | Conversion + safety from pushiness | YES - Total blocker |
| **Day 5** | Flexible booking | Customer experience essential | YES - UX blocker |
| **Day 13** | Bug fixes | Quality assurance | YES - Quality blocker |
| **Day 14** | Deployment | Launch | YES - Cannot go live |

**If timeline is tight:** Days 9-11 (Goal 3) can be done post-launch. Focus on Days 1-8, 12-14.

---

# 📊 PRIORITY BREAKDOWN

| Priority | Task Count | Description | Can Skip? |
|----------|------------|-------------|-----------|
| **P0** | 56 tasks | Critical - Core framework | ❌ NO |
| **P1** | 32 tasks | High - UX and edge cases | ❌ NO |
| **P2** | 22 tasks | Medium - Enhancements | ✅ Can defer post-launch |

**Total:** 110 tasks

---

# 🛠️ DAILY WORK ROUTINE

Use this template each day:

```markdown
# DAY [X] - [Goal] - [Focus Area] - [Date]

## Morning Standup (15 min)
- [ ] Review yesterday's deliverables
- [ ] Review today's [N] tasks
- [ ] Identify any blockers

## Work Session 1 (2-3 hours)
- [ ] Task 1: [Description]
- [ ] Task 2: [Description]
...

## Lunch Break

## Work Session 2 (2-3 hours)
- [ ] Task [N-2]: [Description]
- [ ] Task [N-1]: [Description]
- [ ] Task [N]: [Description]

## Testing Session (1-2 hours)
- [ ] Test scenario 1
- [ ] Test scenario 2
...

## End of Day Review (15 min)
- [ ] All [N] tasks complete? (Y/N)
- [ ] Tests passing? (Y/N)
- [ ] Documentation updated? (Y/N)
- [ ] Ready for tomorrow? (Y/N)

## Notes / Blockers
- [Any issues encountered]
- [Decisions made]
- [Questions for discussion]
```

---

# ⚠️ RISK MANAGEMENT

| Risk | Probability | Impact | Mitigation | Day to Address |
|------|------------|--------|------------|---------------|
| Agent too pushy | Medium | High | Implement back-off logic | Day 4 |
| Breaking existing booking | Low | Critical | Regression tests | Day 12-13 |
| Message length increases tokens | Medium | Medium | Optimize on Day 7 | Day 7 |
| Edge cases not covered | Medium | High | Dedicated days 5-8 | Day 5-8 |
| Bugs found late | Medium | High | Early testing on Day 12 | Day 12-13 |

---

# 📈 SUCCESS METRICS (Post-Launch Tracking)

### Week 1 After Launch:
- Engagement rate (% customers respond after opening)
- Conversation length (avg messages per conversation)
- Booking conversion rate
- Customer complaints about "pushy" behavior (should be <5%)

### Week 2-4 After Launch:
- Conversion rate: new vs old flow (target: +20%)
- Objection handling success rate
- Flexible booking usage rate
- Customer satisfaction scores

### Month 1-3 After Launch:
- Overall sales increase (target: +15-25%)
- Customer retention rate
- Average booking value
- Repeat customer rate

---

# ✅ PRE-LAUNCH FINAL CHECKLIST

Before deploying to production, verify:

- [ ] All 110 tasks completed
- [ ] All Goal 1-4 completion checkpoints passed
- [ ] All 10 framework issues resolved
- [ ] All P0 and P1 bugs fixed
- [ ] All regression tests passing
- [ ] Documentation complete
- [ ] Deployment checklist ready
- [ ] Rollback plan tested
- [ ] Monitoring plan active
- [ ] Stakeholder sign-off obtained
- [ ] **READY FOR PRODUCTION LAUNCH** 🚀

---

**END OF DEVELOPMENT ROUTINE v2**

Good luck! Remember:
- Quality > Speed
- Test thoroughly
- Document everything
- Ask questions early
- Don't skip the critical path
