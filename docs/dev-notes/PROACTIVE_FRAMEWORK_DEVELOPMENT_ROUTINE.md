# Proactive Sales Framework - Development Routine

**Project:** Replace Passive Chat Flow with Proactive Sales Framework
**Duration:** 14 days (2 weeks)
**Start Date:** TBD
**Developer:** [Your Name]

---

## 📊 Project Overview

### Current State:
- ❌ Passive conversation flow
- ❌ Low engagement and conversion rates
- ❌ No proactive sales guidance

### Target State:
- ✅ Proactive 5-step sales framework
- ✅ Pain point detection and targeted recommendations
- ✅ Objection handling and flexible booking

### Success Metrics:
- Engagement rate increase (customer responds after opening)
- Conversion rate increase (bookings per conversation)
- Customer satisfaction (reduce "too pushy" complaints)

---

## 🎯 Goals & Priority Framework

| Goal | Description | Priority | Days |
|------|-------------|----------|------|
| **GOAL 1** | Foundation - Core Proactive Flow | P0 (Critical) | Day 1-5 |
| **GOAL 2** | Edge Cases & Customer Experience | P1 (High) | Day 6-9 |
| **GOAL 3** | Advanced Features & Optimization | P2 (Medium) | Day 10-12 |
| **GOAL 4** | Testing & Refinement | P1 (High) | Day 13-14 |

---

## 📅 WEEK 1: Foundation & Core Implementation

### 🎯 GOAL 1: Foundation - Core Proactive Flow (P0 - Critical)
**Days:** 1-5 | **Priority:** Must complete before Week 2

---

### **DAY 1** - Framework Preparation & Analysis

**Goal:** Understand current system and prepare for implementation

**Daily Deliverables:**
1. ✅ Read and analyze complete `chat_flow_comparison.md`
2. ✅ Review current prompt file structure
3. ✅ Identify all sections that need modification
4. ✅ Create backup of current prompt file
5. ✅ Set up development environment (test branch if using git)
6. ✅ Document current prompt structure (sections, line numbers)
7. ✅ Create implementation checklist

**Deliverable:** `IMPLEMENTATION_CHECKLIST.md` with all changes documented

**Time Estimate:** 4-6 hours

**Blocker Check:** None (preparation phase)

---

### **DAY 2** - STEP 1: Proactive Opening Implementation

**Goal:** Replace passive greeting with proactive opening questions

**Daily Deliverables:**
1. ✅ Remove "Hi boss" only rule (Line 636-640)
2. ✅ Add proactive opening templates:
   - New customer: "Hi boss! 今天想来放松一下吗？😊"
   - Returning customer: "Hi boss! 跟上次一样吗？还是想试别的？😊"
3. ✅ Add returning customer detection logic
4. ✅ Update communication style rules (resolve Issue #7)
5. ✅ Add "fast track" detection (customer who knows what they want)
6. ✅ Test opening with 10 sample conversations
7. ✅ Document changes in changelog

**Deliverable:** Updated prompt with proactive opening section

**Time Estimate:** 5-7 hours

**Dependencies:** None

**Testing:** Test greetings in different scenarios:
- New customer says "Hi"
- Returning customer says "Hi"
- Customer says "明天8点90分钟身体按摩" (direct booking)

---

### **DAY 3** - STEP 2: Pain Point Detection & Discovery

**Goal:** Implement need discovery and pain point detection system

**Daily Deliverables:**
1. ✅ Add pain point keyword detection section:
   - 身体部位痛点: 肩颈, 腰, 背, 脚, etc.
   - 状态痛点: 累, 压力大, 睡不好, etc.
   - 职业痛点: 久坐, 久站, 运动后, etc.
2. ✅ Add discovery question templates
3. ✅ Add "just browsing" mode detection (Issue #1)
4. ✅ Add "generic relaxation" path (Issue #9)
5. ✅ Add multi-pain point handling (Issue #2)
6. ✅ Add discovery loop prevention (max 2 questions rule)
7. ✅ Test with 15 sample pain point scenarios

**Deliverable:** Pain point detection and discovery section in prompt

**Time Estimate:** 6-8 hours

**Dependencies:** Day 2 (opening must be done first)

**Testing:** Test scenarios:
- Customer: "肩颈很酸"
- Customer: "全身都累"
- Customer: "肩颈酸，脚也累" (multi-pain)
- Customer: "只是问问价格" (just browsing)
- Customer: "就想放松" (no specific pain)

---

### **DAY 4** - STEP 3 & 4: Targeted Recommendations + Value

**Goal:** Implement pain point → service mapping and value explanation

**Daily Deliverables:**
1. ✅ Create targeted recommendation mapping table:
   - 肩颈酸 → 90/120分钟身体按摩 + 拔罐
   - 全身累 → 120分钟身体按摩
   - 脚酸 → 90分钟足部按摩
   - 压力大 → 90/120分钟身体按摩
   - 睡不好 → 90/120分钟身体按摩
   - Multi-pain point combinations
2. ✅ Add value explanation templates for each pain point
3. ✅ Optimize price anchoring (Issue #6)
4. ✅ Update 3-package recommendation with better value framing
5. ✅ Add social proof phrases ("很多客人都说...")
6. ✅ Test recommendations with 20 pain point scenarios

**Deliverable:** Targeted recommendation and value section

**Time Estimate:** 7-9 hours

**Dependencies:** Day 3 (pain point detection must work first)

**Testing:** Verify each pain point maps to correct service with proper value explanation

---

### **DAY 5** - STEP 5: Proactive Booking Guidance

**Goal:** Implement proactive closing and objection handling

**Daily Deliverables:**
1. ✅ Add proactive booking guidance after recommendations:
   - "您想预约今天还是明天？"
   - "要帮您预约吗？"
2. ✅ Add objection handling section:
   - "太贵了" → member price + shorter package
   - "再考虑" → membership registration hook
   - "没时间" → late hours availability
   - "下次吧" → soft close
3. ✅ Add "back-off" detection (Issue #5 - CRITICAL):
   - If customer declines 2x → stop pushing
4. ✅ Add call-to-action templates
5. ✅ Update booking template trigger logic
6. ✅ Test full flow: opening → discovery → recommend → close
7. ✅ Week 1 integration test

**Deliverable:** Complete STEP 1-5 proactive flow implementation

**Time Estimate:** 6-8 hours

**Dependencies:** Day 2, 3, 4 (all previous steps)

**Testing:** End-to-end conversation flow tests (at least 30 scenarios)

---

### **📋 WEEK 1 CHECKLIST** (Review Friday EOD)

- [ ] Proactive opening implemented and tested
- [ ] Pain point detection working correctly
- [ ] Targeted recommendations mapping correctly
- [ ] Value explanations connecting to pain points
- [ ] Proactive booking guidance active
- [ ] Objection handling in place
- [ ] "Back-off" logic working (not too pushy)
- [ ] All Day 1-5 tests passing
- [ ] Changelog updated with all changes
- [ ] No regressions in existing booking flow

**Weekly Deliverable:** Functional proactive framework (STEP 1-5) ready for testing

---

## 📅 WEEK 2: Edge Cases, Advanced Features & Testing

### 🎯 GOAL 2: Edge Cases & Customer Experience (P1 - High)
**Days:** 6-9 | **Priority:** Important for good UX

---

### **DAY 6** - Flexible Booking & "Difficult Customer" Handling

**Goal:** Implement Problem #2 from comparison doc (booking template issues)

**Daily Deliverables:**
1. ✅ Add "troublesome template" detection:
   - Keywords: "麻烦", "懒得填", "可以打电话吗", "不想填"
2. ✅ Remove "DO NOT provide phone number" restriction (Line 752)
3. ✅ Add phone booking alternative:
   - "您可以直接拨打我们店的电话 03-1234 5678"
4. ✅ Add simplified verbal booking flow:
   - Just collect: name + time + service
5. ✅ Add "difficult customer" detection logic:
   - Explicit complaints about template
   - Multiple failed attempts to fill template
   - Repeated questions after template sent
6. ✅ Test booking flexibility with 15 scenarios

**Deliverable:** Flexible booking section with phone alternative

**Time Estimate:** 5-7 hours

**Dependencies:** Week 1 completion (booking flow must be working)

**Testing:** Scenarios:
- Customer: "好麻烦啊"
- Customer: "可以打电话吗？"
- Customer: "不想填这么多东西"

---

### **DAY 7** - Message Length Balance & Communication Style

**Goal:** Resolve Issue #7 - balance between short and proactive

**Daily Deliverables:**
1. ✅ Update communication style rules:
   - Discovery questions: SHORT (3-7 words)
   - Recommendations: MEDIUM (value explanation allowed)
   - Confirmations: Standard template
   - Quick responses: SHORT
2. ✅ Add examples for each message type
3. ✅ Review all templates for length optimization
4. ✅ Ensure messages don't feel too long or too short
5. ✅ Add emoji usage guidelines (moderate, not excessive)
6. ✅ Test communication style consistency

**Deliverable:** Updated communication style guide in prompt

**Time Estimate:** 4-5 hours

**Dependencies:** Day 5 (all message templates must exist)

**Testing:** Review 50 conversation samples for style consistency

---

### **DAY 8** - Returning Customer Flow & Memory Usage

**Goal:** Optimize experience for returning customers (Issue #3)

**Daily Deliverables:**
1. ✅ Add returning customer detection:
   - Check if customer has booking history in memory
2. ✅ Add customized opening for regulars:
   - "Hi boss! 跟上次一样吗？还是想试试别的？😊"
3. ✅ Add memory usage rules:
   - ❌ Don't say "I remember you"
   - ✅ Use memory silently (pre-fill name/phone)
   - ✅ Reference past bookings only if relevant
4. ✅ Add "same as last time" quick booking:
   - Customer says "一样" → skip discovery
5. ✅ Update memory usage guidelines
6. ✅ Test with returning customer scenarios

**Deliverable:** Returning customer flow section

**Time Estimate:** 5-6 hours

**Dependencies:** Customer memory system must be available

**Testing:**
- New customer flow still works
- Returning customer gets personalized opening
- "Same as last time" booking works

---

### **DAY 9** - Information-Only Mode & Soft Close

**Goal:** Handle customers who just want information (Issue #1)

**Daily Deliverables:**
1. ✅ Add "just browsing" mode detection:
   - Keywords: "只是问问", "just asking", "先了解一下"
2. ✅ Add information-only response templates:
   - Provide info without pushing too hard
3. ✅ Add soft close techniques:
   - "了解了吗？有兴趣的话随时联系我😊"
   - "好的～有问题随时问我😊"
4. ✅ Add conversion attempt (gentle):
   - After info provided: "要不要试试？😊"
5. ✅ Test info-only scenarios
6. ✅ Review all edge cases from Issue list

**Deliverable:** Information-only mode and soft close section

**Time Estimate:** 4-5 hours

**Dependencies:** Day 5 (objection handling must be ready)

**Testing:**
- Customer: "只是问问价格"
- Customer: "先了解一下有什么服务"
- Verify agent doesn't push too hard

---

### **📋 WEEK 2 DAYS 6-9 CHECKLIST** (Review Tuesday EOD)

- [ ] Flexible booking alternatives working
- [ ] Phone number option available for difficult customers
- [ ] Communication style balanced (not too short, not too long)
- [ ] Returning customer flow optimized
- [ ] Information-only mode working
- [ ] No "too pushy" behavior detected
- [ ] All edge cases from Issue list addressed

---

### 🎯 GOAL 3: Advanced Features & Optimization (P2 - Medium)
**Days:** 10-12 | **Priority:** Enhancements

---

### **DAY 10** - English Language Support & Bilingual Testing

**Goal:** Ensure framework works for English-speaking customers (Issue #10)

**Daily Deliverables:**
1. ✅ Review all Chinese templates
2. ✅ Create complete English translations for:
   - Opening questions
   - Discovery questions
   - Pain point keywords (English)
   - Recommendations
   - Value explanations
   - Objection handling
   - Closing questions
3. ✅ Test bilingual switching (customer mixes Chinese/English)
4. ✅ Test Malaysian English patterns ("Got slot?", etc.)
5. ✅ Verify emoji usage appropriate for both languages

**Deliverable:** Complete bilingual template set

**Time Estimate:** 6-7 hours

**Dependencies:** All Chinese templates must be finalized

**Testing:**
- Full English conversation flow
- Mixed language conversation
- Malaysian English colloquialisms

---

### **DAY 11** - Conversation State Management & Flow Control

**Goal:** Ensure smooth transitions between framework steps

**Daily Deliverables:**
1. ✅ Add conversation state tracking:
   - State 1: Opening/Greeting
   - State 2: Discovery/Need finding
   - State 3: Recommendation
   - State 4: Closing/Booking
2. ✅ Add transition rules between states
3. ✅ Add "jump" logic (customer skips steps):
   - Example: Direct booking request → skip to booking
   - Example: Customer says pain point in greeting → skip discovery
4. ✅ Add conversation flow validation
5. ✅ Test state transitions with complex scenarios

**Deliverable:** Conversation state management section

**Time Estimate:** 5-6 hours

**Dependencies:** All STEP 1-5 must be working

**Testing:**
- Linear flow: Step 1 → 2 → 3 → 4 → 5
- Skip scenarios: Direct to booking
- Back-and-forth: Customer changes mind mid-conversation

---

### **DAY 12** - Documentation & Knowledge Transfer

**Goal:** Document everything for future maintenance

**Daily Deliverables:**
1. ✅ Create complete prompt documentation:
   - Section index with line numbers
   - What each section does
   - How to modify each section
2. ✅ Create conversation flow diagrams
3. ✅ Document all edge cases and how they're handled
4. ✅ Create troubleshooting guide:
   - "Agent too pushy" → Check back-off logic
   - "Agent not proactive enough" → Check opening
   - "Wrong recommendations" → Check pain point mapping
5. ✅ Create example conversation library (30+ examples)
6. ✅ Document testing procedures

**Deliverable:** Complete documentation package

**Time Estimate:** 6-8 hours

**Dependencies:** All implementation must be complete

---

### **📋 WEEK 2 DAYS 10-12 CHECKLIST** (Review Thursday EOD)

- [ ] Bilingual support complete and tested
- [ ] Conversation state management working smoothly
- [ ] Flow transitions handle all scenarios
- [ ] Documentation complete and clear
- [ ] Example library comprehensive
- [ ] Troubleshooting guide ready

---

### 🎯 GOAL 4: Testing & Refinement (P1 - High)
**Days:** 13-14 | **Priority:** Critical for launch readiness

---

### **DAY 13** - Comprehensive Testing & Bug Fixes

**Goal:** Test all scenarios and fix any bugs found

**Daily Deliverables:**
1. ✅ Run comprehensive test suite:
   - 50+ conversation scenarios
   - All pain point mappings
   - All objection types
   - All edge cases
   - Bilingual scenarios
2. ✅ Test for regressions:
   - Existing booking flow still works
   - Gender policy enforcement still works
   - Membership registration still works
3. ✅ Load testing (if applicable):
   - Multiple concurrent conversations
4. ✅ Create bug tracking document
5. ✅ Fix all P0 (critical) bugs
6. ✅ Fix all P1 (high priority) bugs
7. ✅ Document P2 bugs for future sprints

**Deliverable:** Bug-free proactive framework + Bug report

**Time Estimate:** 8-10 hours (full day)

**Dependencies:** All features implemented (Day 1-12)

**Testing Categories:**
- Happy path (everything works)
- Unhappy path (customer resistance)
- Edge cases (unusual scenarios)
- Regression tests (old features still work)

---

### **DAY 14** - Final Review, Optimization & Launch Prep

**Goal:** Final polish and prepare for production deployment

**Daily Deliverables:**
1. ✅ Final review of entire prompt:
   - Check for typos
   - Verify all templates are consistent
   - Ensure no contradictions
2. ✅ Performance optimization:
   - Remove redundant instructions
   - Optimize prompt length if needed
3. ✅ Create deployment checklist:
   - [ ] Backup current production prompt
   - [ ] Update prompt file
   - [ ] Test in staging environment
   - [ ] Monitor first 10 conversations
   - [ ] Rollback plan ready
4. ✅ Create monitoring plan:
   - Track engagement rate
   - Track conversion rate
   - Track customer complaints
5. ✅ Final stakeholder review
6. ✅ Deploy to production (or stage for approval)

**Deliverable:** Production-ready proactive framework + Deployment package

**Time Estimate:** 6-8 hours

**Dependencies:** All testing complete (Day 13)

**Launch Checklist:**
- [ ] All tests passing
- [ ] Documentation complete
- [ ] Deployment plan ready
- [ ] Rollback plan ready
- [ ] Monitoring in place
- [ ] Stakeholder approval obtained

---

### **📋 WEEK 2 DAYS 13-14 CHECKLIST** (Review Friday EOD)

- [ ] All bugs fixed
- [ ] Comprehensive testing complete
- [ ] Regression tests passing
- [ ] Documentation finalized
- [ ] Deployment checklist ready
- [ ] Monitoring plan in place
- [ ] **READY FOR PRODUCTION DEPLOYMENT**

---

## 📊 Weekly Task Summary

### **WEEK 1** (Days 1-5)
**Focus:** Core proactive framework implementation

| Day | Focus Area | Deliverable | Priority |
|-----|------------|-------------|----------|
| 1 | Preparation | Implementation checklist | P0 |
| 2 | STEP 1: Opening | Proactive greeting | P0 |
| 3 | STEP 2: Discovery | Pain point detection | P0 |
| 4 | STEP 3-4: Recommend + Value | Targeted recommendations | P0 |
| 5 | STEP 5: Close | Booking guidance + objection handling | P0 |

**Week 1 Goal:** Working proactive framework (STEP 1-5)

---

### **WEEK 2** (Days 6-14)
**Focus:** Edge cases, advanced features, and testing

| Day | Focus Area | Deliverable | Priority |
|-----|------------|-------------|----------|
| 6 | Flexible Booking | Phone alternative + verbal booking | P1 |
| 7 | Communication Style | Message length balance | P1 |
| 8 | Returning Customers | Personalized flow | P1 |
| 9 | Info-Only Mode | Soft close handling | P1 |
| 10 | Bilingual Support | English templates | P2 |
| 11 | State Management | Flow control | P2 |
| 12 | Documentation | Complete docs + examples | P2 |
| 13 | Testing | Comprehensive test + bug fixes | P1 |
| 14 | Launch Prep | Final review + deployment | P1 |

**Week 2 Goal:** Production-ready, fully-tested framework

---

## 🚨 Critical Path (Must Complete)

These tasks are BLOCKERS - if not done, launch is not possible:

1. **Day 2:** Proactive opening (without this, framework doesn't start)
2. **Day 3:** Pain point detection (core of proactive approach)
3. **Day 4:** Targeted recommendations (differentiator from current system)
4. **Day 5:** Proactive booking + back-off logic (conversion + safety)
5. **Day 6:** Flexible booking (customer experience)
6. **Day 13:** Comprehensive testing (quality assurance)
7. **Day 14:** Deployment (launch)

**If timeline is tight:** Focus on Days 1-6 and 13-14. Days 7-12 can be done post-launch.

---

## ⚠️ Risk Management

### High-Risk Items:
1. **Risk:** Agent becomes too pushy
   - **Mitigation:** Day 5 includes "back-off" logic
   - **Testing:** Day 13 includes pushiness tests

2. **Risk:** Breaking existing booking flow
   - **Mitigation:** Regression tests on Day 13
   - **Rollback:** Keep backup of current prompt

3. **Risk:** Message length increases token usage
   - **Mitigation:** Day 7 optimizes message length
   - **Monitoring:** Track token usage post-launch

4. **Risk:** Edge cases not covered
   - **Mitigation:** Days 6-9 focus on edge cases
   - **Testing:** Day 13 comprehensive scenarios

---

## 📈 Success Metrics (Track Post-Launch)

### Week 1 After Launch:
- Engagement rate (customers who respond after opening)
- Conversation length (number of messages)
- Booking conversion rate
- Customer complaints about "pushy" behavior

### Week 2 After Launch:
- Compare conversion rate: new vs old flow
- Track objection handling success rate
- Monitor flexible booking usage
- Collect customer feedback

### Month 1 After Launch:
- Overall sales increase
- Customer retention
- Average booking value
- Customer satisfaction scores

---

## 🛠️ Tools & Resources Needed

- **Development Environment:** Text editor for prompt editing
- **Testing Tool:** Conversation simulator (or manual testing)
- **Version Control:** Git (recommended) or manual backups
- **Documentation:** Markdown editor
- **Tracking:** Spreadsheet for test scenarios and results

---

## 📝 Daily Work Template

Use this template each day:

```markdown
# DAY [X] - [Focus Area] - [Date]

## Morning (Start of Day)
- [ ] Review yesterday's deliverables
- [ ] Review today's task list
- [ ] Set up environment

## Work Session
- [ ] Task 1: [Description]
- [ ] Task 2: [Description]
...

## Testing
- [ ] Test scenario 1
- [ ] Test scenario 2
...

## End of Day
- [ ] All deliverables complete?
- [ ] Tests passing?
- [ ] Documentation updated?
- [ ] Ready for tomorrow?

## Notes / Blockers
- [Any issues encountered]
- [Decisions made]
- [Questions for discussion]
```

---

## 📞 Escalation Path

If you encounter blockers:

1. **Technical Issue:** Review documentation, check examples
2. **Logic Issue:** Refer to `FRAMEWORK_ANALYSIS_AND_ISSUES.md`
3. **Unclear Requirement:** Check `chat_flow_comparison.md`
4. **Major Blocker:** Flag for discussion immediately (don't wait)

---

## ✅ Final Checklist (Before Production)

- [ ] All 14 days completed
- [ ] All deliverables reviewed and approved
- [ ] All tests passing (no regressions)
- [ ] Documentation complete
- [ ] Deployment plan ready
- [ ] Rollback plan tested
- [ ] Monitoring in place
- [ ] Stakeholder sign-off obtained
- [ ] **READY FOR LAUNCH** 🚀

---

**END OF DEVELOPMENT ROUTINE**

Good luck! Remember: Quality over speed. It's better to take an extra day to fix issues than to launch with bugs.
