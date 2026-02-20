# Incident Log Correlation Engine (ILCE)
## 12-Week Contained Build Plan

**Project Start Date:** February 16, 2026  
**Target Completion Date:** May 10, 2026  
**Scope:** Contained v1 Prototype

---

# Guiding Principles

1. Containment over expansion  
2. Finish before improving  
3. No feature creep  
4. Validate before monetizing  
5. Weekly review and adjustment

---

# Week 1 – Discovery & Pain Validation

Objectives:
- Send targeted outreach to current manufacturing professionals
- Conduct at least 3 diagnostic conversations
- Identify recurring pain themes
- Document how root cause isolation is currently performed
- Confirm whether cross-system log correlation remains manual and time-consuming

Deliverable:
- One-page Validated Pain Summary

---

# Week 2 – Architecture Lock

Objectives:
- Define supported log schema (v1 format)
- Define internal event model structure
- Define timestamp normalization logic
- Define anomaly detection method (event clustering)
- Define correlation scoring methodology
- Define probability ranking normalization
- Define synthetic scenario set (3 controlled scenarios)

Deliverable:
- Architecture Specification Document
- Data Model Definition

Architecture frozen after this week.

---

# Weeks 3–4 – Log Ingestion & Normalization

Objectives:
- Build log parser for CSV/structured logs
- Implement timestamp normalization
- Build unified event timeline representation
- Implement event window extraction

Deliverable:
- Working CLI-based ingestion engine
- Sample synthetic log bundles processed successfully

---

# Weeks 5–6 – Correlation & Scoring Engine

Objectives:
- Implement event density spike detection
- Implement cross-system temporal proximity scoring
- Develop weighted heuristic scoring model
- Normalize scores into probability distribution
- Output ranked probable originating systems

Deliverable:
- Engine produces defensible probability rankings on synthetic scenarios

---

# Weeks 7–8 – Evidence Layer & Explainability

Objectives:
- Extract supporting log evidence for ranked results
- Build event chain summary generator
- Create correlation summary output
- Ensure transparency of scoring logic

Deliverable:
- Clear evidence-backed diagnostic summary output

---

# Weeks 9–10 – Web Interface Development

Objectives:
- Build lightweight web UI (Flask/FastAPI)
- Implement log upload interface
- Add scenario selector for demo mode
- Display timeline visualization
- Display ranked probabilities with supporting evidence

Deliverable:
- Functional web-based diagnostic interface

---

# Week 11 – Hardening & Validation

Objectives:
- Run repeated test scenarios
- Adjust scoring weights
- Improve output clarity
- Remove fragile logic
- Document system behavior

Deliverable:
- Stable demo-ready prototype

---

# Week 12 – External Review & Assessment

Objectives:
- Demo to 2–3 manufacturing professionals
- Gather structured feedback
- Evaluate perceived usefulness
- Document monetization pathway

Deliverable:
- Feedback Summary Report
- Decision on next iteration or pilot engagement

---

# Weekly Review Protocol

At the end of each week:
- Confirm milestone completion
- Confirm scope has not expanded
- Log lessons learned
- Adjust following week if needed

No scope expansion without explicit review.

---

# Success Criteria

By Week 12:

- A working prototype exists
- Multi-system log bundles can be processed
- Ranked probabilistic root cause output is generated
- Demo is stable and defensible
- At least 2 professionals have reviewed it

Completion itself represents a significant milestone and a finished system foundation.

---

**Commitment:** Build, finish, demonstrate.

