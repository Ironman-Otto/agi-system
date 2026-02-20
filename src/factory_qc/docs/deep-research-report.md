# CONNECT and ILCE Competitive Strategy Canvas

## CONNECT status, ownership, and objective

**CONNECT is an AVEVA-developed industrial intelligence platform** that AVEVA describes as “open,” “vendor-neutral,” and “cloud-based,” designed to integrate industrial data, models, applications, and AI/analytics using a set of shared software services. citeturn7view0

AVEVA’s public messaging frames CONNECT’s **objective** as reducing information silos and enabling collaboration and decision-making by creating a shared foundation for industrial intelligence. citeturn7view0

Several signals indicate CONNECT is **actively evolving through at least 2026**:

- AVEVA explicitly describes a brand transition where “AVEVA Connect is now CONNECT” (March 2024), positioning CONNECT as a broadened “unified experience” spanning data services, visualization, modeling/analytics, and application development services. citeturn7view4  
- AVEVA renamed **AVEVA Data Hub** → **CONNECT data services** (July 2024), describing it as the “foundation” of CONNECT and the “data management layer” for aggregation, enrichment, analysis, and secure sharing of real-time industrial data. citeturn7view3  
- AVEVA publishes “vision and roadmap” sessions/materials for CONNECT, including a 2025 roadmap deck and a 2026 roadmap session listing, implying ongoing investment and delivery cadence beyond a static product release. citeturn5view0turn0search11  

For corporate context (relevant mainly to “will they out-execute us?”): AVEVA’s site states that **entity["company","Schneider Electric","energy management firm"] completed its acquisition of **entity["company","AVEVA","industrial software vendor"] and AVEVA is now part of the Schneider Electric group. citeturn8view3

## CONNECT functionality that matters for your “race” question

CONNECT’s capabilities most relevant to an incident/root-cause product fall into two buckets: **data platform primitives** and **AI-assisted interrogation of published data**.

On the data platform side, AVEVA describes CONNECT’s data management as cloud-native storage and contextualization of near-real-time operational data, with features including ingestion from AVEVA-native sources (PI System, Historian, Edge Data Store), data views, and mechanisms for sharing curated datasets. citeturn8view3 AVEVA also emphasizes integration pathways for external tools, explicitly calling out a **Power BI connector and REST APIs** to connect third-party analytics tools and custom applications. citeturn8view3

On the AI side, AVEVA states that **Industrial AI Assistant** (inside CONNECT) became available to all CONNECT visualization users as of July 2025. AVEVA describes it as a generative AI chat interface that answers natural-language questions by retrieving relevant data from your CONNECT account and then formatting a response. citeturn7view1

Key implementation details AVEVA discloses about Industrial AI Assistant are strategically important for you:

- It uses a **retrieval augmented generation (RAG)** pattern (no “model training on your data” prerequisite), and AVEVA describes it as a **search-based tool** that finds and summarizes information from a defined set of data sources. citeturn7view1  
- The Assistant’s supported sources include **CONNECT data services** (streams, assets) and explicitly **“events from AVEVA Manufacturing Execution System.”** citeturn7view1  
- AVEVA states a constraint that is central to your opportunity framing: **if the needed information isn’t in CONNECT, the assistant can’t answer** (“If there’s no data, there’s no answer”). citeturn7view1  
- AVEVA also notes that if answering requires significant “tribal knowledge” or “complex inferences,” the assistant “may have difficulty finding the right information.” citeturn7view1  
- AVEVA explicitly signals continued evolution: it says improvements will roll out via CONNECT visualization updates and references adding “agentic capabilities” and “Generative Analytics” in the coming year. citeturn7view1  

The 2025 CONNECT roadmap deck further reinforces the direction of travel: it calls out recent additions like **integration with entity["company","Databricks","data platform company"]**, a “new Industrial AI Assistant,” and roadmap themes including “system of record for industrial data,” “powerful analytics and AI models,” and “visually relate data in context and expedite analysis with an AI Assistant,” alongside explicit mentions of **Events** and **MES** in the platform stack. citeturn5view0

## Race assessment: where CONNECT overlaps with ILCE and where it likely doesn’t

Your “race” intuition is justified in a specific way:

CONNECT is not a side project. AVEVA’s product messaging and roadmaps show a deliberate effort to build a cloud platform that integrates industrial data and adds AI-mediated access to that data, including MES events. citeturn7view0turn7view1turn5view0

However, the overlap with your **Incident Log Correlation Engine (ILCE)** depends on whether your target job-to-be-done is:

- **A) “Help me query published industrial data fast”** (CONNECT already does this), or  
- **B) “Turn messy, low-level diagnostic evidence into probabilistic root-cause hypotheses”** (CONNECT may enable this, but is not the same thing today).

What the public materials suggest—carefully, without over-claiming:

CONNECT’s Industrial AI Assistant is positioned as a **retrieval + summarization interface over data already present in CONNECT**, not as a deterministic engine purpose-built to ingest raw multi-system log bundles and compute a ranked set of causal hypotheses. AVEVA’s own phrasing emphasizes it as “search-based,” reliant on what data is available and discoverable, and potentially challenged by “tribal knowledge” and complex inference needs. citeturn7view1

This implies a plausible gap where ILCE can still be valuable:

- If incident evidence lives in **exported service logs, middleware traces, Windows event logs, database/SP call traces, or vendor-specific diagnostic files** that are *not routinely published into CONNECT as structured data*, Industrial AI Assistant cannot operate on them unless the customer first builds ingestion pipelines and normalization. AVEVA’s “if there’s no data, there’s no answer” framing makes this dependency explicit. citeturn7view1  
- Even when data is present, AVEVA acknowledges limitations when successful answering requires “tribal knowledge” or “complex inferences.” If ILCE’s value proposition is encoding the diagnostic heuristics that senior engineers use (signal isolation, responsibility assignment, causal ordering) and producing ranked hypotheses with evidence trails, that is directionally aligned with what AVEVA flags as challenging. citeturn7view1  

So, the “race” is real in the sense that AVEVA is expanding AI-assisted operational insight capability quickly, and their platform direction is adjacent to your vision. citeturn5view0turn7view1  
But ILCE can remain viable if it stays narrowly focused on evidence types and workflows that CONNECT is not (yet) solving end-to-end—especially **offline/on-prem incident packages** and **low-level diagnostic artifact correlation**.

## Complementary product options that fit “AV E VA-first now, portability later”

If you treat CONNECT as a platform you may need to coexist with (or optionally integrate into), three complementary product patterns emerge directly from AVEVA’s published architecture and constraints:

**Incident Package Builder + ILCE Engine (on-prem/offline by default)**  
CONNECT data services is explicitly “cloud” and positioned as the aggregation and management layer in CONNECT. citeturn7view3turn8view3  
A complementary product can live one step earlier: an on-prem tool that helps engineers collect/export diagnostic artifacts, normalize them into a stable schema, and run probabilistic correlation locally. Only the *derived summary* (timeline, hypotheses, key events) would optionally be published into CONNECT.

This is compatible with AVEVA’s own statement that the AI assistant depends on what data is published in CONNECT; your tool becomes the mechanism that turns raw evidence into publishable “events.” citeturn7view1turn7view3

**“Enrichment Publisher” back into CONNECT (optional integration, not required for MVP)**  
AV E VA highlights REST APIs and custom application connectivity as a core data-management feature, alongside data views and integration to third-party BI/AI tools. citeturn8view3  
So ILCE can produce outputs designed to map into CONNECT-friendly constructs (events, assets, annotations) in a later phase—without forcing you into “live integration” during the first 12 weeks.

**A narrow, AV E VA-shaped ingestion adapter that becomes the first of many adapters**  
AV E VA’s messaging explicitly suggests CONNECT is intended to be an ecosystem: data services + visualization + analytics + application development services. citeturn7view4turn7view0  
That ecosystem orientation means you can rationally build ILCE ingestion as **adapter-based** from day one: “AV E VA adapter v1” first, then reuse the normalized schema and engine for other MES/historians later. This closely matches your Virtual COBOL “platform-first, portability later” thinking—but with the important difference that the *target* platform here is not a single operating system; it’s a family of industrial data patterns.

## Virtual COBOL from Advanced Software Products: what the public record shows

You asked for “anything we can find” about “Virtual COBOL from ASP” (Advanced Software Products) and what happened to it. Publicly searchable material is limited, but there are several strong primary artifacts showing what it was and how it was positioned.

A 1980 issue of **entity["organization","Computerworld","IT news magazine"]** contains an advertisement for **Virtual COBOL** from **entity["company","Advanced Software Products","Delray Beach software firm 1980"]. The ad claims Virtual COBOL could run a large COBOL application on an **IBM Series/1** “without segmentation,” and that both procedure division and working storage can be larger than real memory. It states conformance with the **1974 ANSI COBOL** standard and references “Virtual COBOL for Control Program Support (5798-ZZB)” while directing readers to ask IBM for manual **SB30-1280**. citeturn2search1

A 1981 Computerworld letter by a vice president at Advanced Software Products discusses **IBM Control Program Support (CPS) Virtual COBOL**, clarifying that it runs on any Series/1 processor and asserting that CPS Virtual COBOL (ANSI 1974 level) could be migrated from Series/1 to a larger system that supports ANSI 1974 COBOL—directly emphasizing portability and migration, consistent with your retelling of “move from Series/1 to PC” as a strategic arc. citeturn2search0

IBM’s own pricing directory material from 1984 lists “5798‑ZZB Virtual COBOL – Control Program Support S/1” alongside other Series/1 software feature numbers, suggesting the product was available through IBM’s software channels at that time (and not merely a niche third-party sold independently). citeturn5view2

Beyond these references (1980–1984), I did not find easily accessible public sources that reliably document “what happened next” (acquisition, retirement story, or the specific downstream commercial outcomes you described). The accessible record supports that it existed, was marketed publicly, and appeared in IBM pricing materials; it does **not** provide clean public visibility into later business events.

The key strategic lesson you’re drawing—“a smaller builder can ship earlier, but the platform owner can later out-market/out-distribute”—is consistent with the general risk profile implied by how Virtual COBOL was tied to IBM channels and identifiers (manual number, feature number, IBM rep distribution). citeturn2search1turn5view2

## Canvas: research questions and system-design implications

This canvas is written to match your framing: “I’m the engineer assigned to reduce root-cause determination time in our AVEVA environment, and I want to know what I have to work with.”

**Platform reality check: what exactly is CONNECT solving today (versus enabling)?**  
CONNECT’s AI assistant is explicitly described as search-based and dependent on what data is present in CONNECT, using a RAG pattern rather than training on plant data. citeturn7view1  
Research question: Is CONNECT (today) only accelerating *retrieval and summarization of known data*, or is it reliably producing *causal hypotheses* using multi-source evidence? The difference is the entire company thesis.

**Roadmap risk: will AVEVA close the gap quickly?**  
AV E VA explicitly signals future “agentic capabilities” and “Generative Analytics,” and the roadmap deck frames the aim as expediting analysis with an AI assistant while expanding events and MES integrations. citeturn7view1turn5view0  
Research question: Which incident categories (software integration faults vs process anomalies vs equipment degradation) will AVEVA prioritize? If their focus is process/anomaly/root-cause in time-series space, ILCE can differentiate by owning the “messy diagnostic artifacts” space.

**Data-surface definition: what evidence can an engineer realistically export today?**  
Industrial AI Assistant supports streams, assets, and *events from AVEVA MES* when those are published into CONNECT. citeturn7view1  
CONNECT data services is positioned as the cloud gateway for aggregation and enrichment, with REST APIs and broad integration claims. citeturn7view3turn8view3  
Research question: For real customers, what fraction of root-cause-relevant evidence is already in (or routinely published to) CONNECT versus residing in local logs/traces that never leave the plant network?

**Schema design: can your normalized model align with CONNECT’s primitives without becoming “CONNECT-specific”?**  
CONNECT’s platform language repeatedly uses the primitives **assets, streams, and events**, plus contextualization (“add context”) as a core design goal. citeturn8view3turn7view1  
Design implication: A portable ILCE schema can adopt these primitives at the top layer (asset/entity, event, measurement/stream) while still preserving low-level fields (component name, severity, correlation keys) in source-specific payloads.

**Where the “tribal knowledge” lives—and how to encode it**  
AV E VA itself warns that if answering requires “tribal knowledge” or “complex inferences,” Industrial AI Assistant may have difficulty. citeturn7view1  
Research question: What is the smallest set of universally applicable incident reasoning heuristics that can be encoded across factories and MES deployments? Candidate categories include:
- evidence windowing (time-bound clustering),
- responsibility inference (which subsystem initiated the cascade),
- correlation keys (session/job/work-order/transaction relationships),
- symptom-to-failure-node mapping (turning “the line slowed” into a structured fault hypothesis).

**Form factor and deployment: cloud app, on-prem app, or appliance?**  
CONNECT and CONNECT data services are explicitly cloud-oriented. citeturn7view0turn7view3turn8view3  
Design implication: “Appliance with web UI + engine” is not just a sales psychology idea; it is also a technical strategy for customers who are not ready to publish sensitive diagnostic evidence into a cloud platform. A complementary posture is: on-prem analysis first, optional publishing of derived insight/events into CONNECT afterward.

**AV E VA-first build strategy under limited hands-on access**  
AV E VA publicly documents the MES Web API V3 as a supported interface providing access to the MES database, and AVEVA provides partner/developer materials for cloud data services development environments (for design/testing, not production). citeturn9search0turn9search10  
Research question: Can an ILCE “AV E VA adapter v1” be built using public documentation + synthetic incident packages while deferring full in-environment validation until a pilot customer provides real exports? This is the same “portability-first” lens that showed up in the Virtual COBOL advertising: ability to improve outcomes without requiring the platform owner’s internal roadmap or privileged access. citeturn2search1turn7view1