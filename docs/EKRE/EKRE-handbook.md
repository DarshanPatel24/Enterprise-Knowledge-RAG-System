# EKRE — Enterprise Knowledge Retrieval Engine
## Enterprise Architecture Handbook

> **Version:** 1.0
> **Status:** Approved
> **Owner:** Product Management
> **Architecture Owner:** Principal Architect

---

## Table of Contents

- [Chapter 1 - Product Vision](#chapter-1-product-vision)
- [Chapter 2 - Product Requirements Specification (PRS)](#chapter-2-product-requirements-specification-prs)
- [Chapter 3 - Personas, Enterprise Retrieval Scenarios & Use Cases](#chapter-3-personas-enterprise-retrieval-scenarios-use-cases)
- [Chapter 4 - Functional Requirements Specification (FRS)](#chapter-4-functional-requirements-specification-frs)
- [Chapter 5 - Non-Functional Requirements (NFR)](#chapter-5-non-functional-requirements-nfr)
- [Chapter 6 - Enterprise Retrieval Architecture Overview](#chapter-6-enterprise-retrieval-architecture-overview)
- [Chapter 7 - End-to-End Query Lifecycle](#chapter-7-end-to-end-query-lifecycle)
- [Chapter 8 - Query Intelligence Domain](#chapter-8-query-intelligence-domain)
- [Chapter 9 - Query Understanding Engine](#chapter-9-query-understanding-engine)
- [Chapter 10 - Intent Classification Engine](#chapter-10-intent-classification-engine)
- [Chapter 11 - Query Enrichment Engine](#chapter-11-query-enrichment-engine)
- [Chapter 12 - Knowledge Awareness Engine (KAE)](#chapter-12-knowledge-awareness-engine-kae)
- [Chapter 13 - Query Planner](#chapter-13-query-planner)
- [Chapter 14 - Retrieval Execution Domain Overview](#chapter-14-retrieval-execution-domain-overview)
- [Chapter 15 - Retrieval Orchestrator](#chapter-15-retrieval-orchestrator)
- [Chapter 16 - Execution Runtime](#chapter-16-execution-runtime)
- [Chapter 17 - Execution Scheduler](#chapter-17-execution-scheduler)
- [Chapter 18 - Retrieval Worker Framework](#chapter-18-retrieval-worker-framework)
- [Chapter 19 - Vector Retrieval Worker](#chapter-19-vector-retrieval-worker)
- [Chapter 20 - Keyword Retrieval Worker](#chapter-20-keyword-retrieval-worker)
- [Chapter 21 - Metadata Retrieval Worker](#chapter-21-metadata-retrieval-worker)
- [Chapter 22 - Repository Connector Framework](#chapter-22-repository-connector-framework)
- [Chapter 23 - Unified Candidate Collection Framework](#chapter-23-unified-candidate-collection-framework)
- [Chapter 24 - Candidate Fusion Framework](#chapter-24-candidate-fusion-framework)
- [Chapter 25 - Ranking Engine](#chapter-25-ranking-engine)
- [Chapter 26 - Context Assembly Engine](#chapter-26-context-assembly-engine)
- [Chapter 27 - Response Packaging & Handoff](#chapter-27-response-packaging-handoff)
- [Chapter 28 - End-to-End Observability & Traceability](#chapter-28-end-to-end-observability-traceability)
- [Chapter 29 - Security, Governance & Compliance](#chapter-29-security-governance-compliance)
- [Chapter 30 - Deployment Architecture & Scalability](#chapter-30-deployment-architecture-scalability)

---

# Chapter 1 - Product Vision

## 1.1 Introduction

Enterprise organizations possess enormous amounts of information
distributed across multiple repositories such as SharePoint, Confluence,
Git repositories, engineering documentation, operating manuals,
policies, contracts, knowledge bases, emails, and structured databases.

Although modern AI systems promise intelligent knowledge discovery, most
organizations struggle because the information available to Large
Language Models is fragmented, duplicated, outdated, poorly indexed, and
difficult to retrieve accurately.

Traditional search engines primarily rely on lexical matching, while
modern vector databases focus on semantic similarity. Neither approach
alone satisfies enterprise requirements such as:

\- High precision

\- Explainability

\- Security enforcement

\- Metadata awareness

\- Version awareness

\- Governance

\- Deterministic behavior

EKRE (Enterprise Knowledge Retrieval Engine) is designed to solve this
problem.

Rather than functioning as another search engine, EKRE provides an
intelligent retrieval platform that understands enterprise knowledge and
returns the most relevant, explainable, and policy-compliant context for
downstream AI systems.

\-\--

## 1.2 Product Definition

EKRE is an enterprise retrieval platform responsible for discovering,
ranking, filtering, and assembling knowledge assets produced by EKIE.

Its primary objective is to transform user queries into structured
retrieval results that are:

\- Relevant

\- Explainable

\- Deterministic

\- Secure

\- Traceable

\- Ready for downstream consumption

EKRE does not generate answers.

EKRE does not summarize.

EKRE does not interact with conversational memory.

EKRE does not execute AI agents.

Its responsibility ends when the optimal retrieval context has been
produced.

\-\--

## 1.3 Product Mission

Deliver enterprise-grade retrieval capabilities that maximize relevance
while preserving governance, security, explainability, and deterministic
behavior.

\-\--

## 1.4 Product Vision

Become the enterprise standard retrieval platform capable of serving
every downstream AI application through a unified retrieval interface.

Instead of every AI product implementing its own retrieval logic,
organizations deploy one centralized retrieval platform.

All AI systems consume knowledge through EKRE.

\-\--

## 1.5 Product Scope

EKRE is responsible for:

✓ Query Understanding

✓ Query Planning

✓ Query Optimization

✓ Hybrid Retrieval

✓ Metadata Filtering

✓ Security Filtering

✓ Candidate Fusion

✓ Ranking

✓ Re-ranking

✓ Context Assembly

✓ Retrieval Explainability

✓ Retrieval APIs

✓ Retrieval Observability

✓ Retrieval Performance

✓ Retrieval Governance

\-\--

EKRE is NOT responsible for:

✗ Prompt Engineering

✗ Chat Interfaces

✗ Conversation Management

✗ AI Agents

✗ LLM Response Generation

✗ Tool Calling

✗ Workflow Automation

✗ Knowledge Ingestion

✗ Embedding Generation

✗ Repository Synchronization

Those responsibilities belong to other enterprise platforms.

\-\--

## 1.6 Product Position

Enterprise AI Platform

│

├── EKIE

│ Enterprise Knowledge Ingestion Engine

│ (Knowledge Creation)

│

├── EKRE

│ Enterprise Knowledge Retrieval Engine

│ (Knowledge Discovery)

│

└── EKCP

Enterprise Knowledge Chat Platform

(Knowledge Consumption)

Each platform owns an independent responsibility.

Each platform evolves independently.

Each platform exposes well-defined APIs.

\-\--

## 1.7 Core Architectural Principle

The most important architectural decision for EKRE is:

\> Retrieval must remain completely independent from response
generation.

This separation ensures:

• Independent scaling

• Independent deployment

• Independent optimization

• Independent testing

• Independent evolution

The retrieval platform should remain valuable even if no Large Language
Model is attached.

\-\--

## 1.8 Target Consumers

EKRE is designed for multiple enterprise consumers.

### AI Chat Applications

Enterprise copilots

Knowledge assistants

Support bots

\-\--

### Intelligent Agents

Planning agents

Research agents

Automation agents

\-\--

### Search Applications

Enterprise search portals

Engineering search

Knowledge portals

\-\--

### APIs

Internal services

Business applications

Workflow engines

Analytics systems

\-\--

## 1.9 Product Objectives

The success of EKRE will be measured by six objectives.

### Objective 1

Highest possible retrieval precision.

\-\--

### Objective 2

Deterministic retrieval.

The same query executed against the same knowledge state should always
produce identical results.

\-\--

### Objective 3

Enterprise governance.

Every returned result must satisfy:

\- Security policies

\- Metadata policies

\- Version policies

\- Compliance policies

\-\--

### Objective 4

Explainability.

Every retrieved document should include the reason it was selected.

\-\--

### Objective 5

Performance.

Retrieval latency should support interactive enterprise AI applications.

\-\--

### Objective 6

Scalability.

The platform should support millions of knowledge chunks distributed
across multiple repositories and vector indexes.

\-\--

## 1.10 Success Metrics

The platform will be evaluated using measurable KPIs.

Examples include:

\- Retrieval Precision@K

\- Recall@K

\- Mean Reciprocal Rank (MRR)

\- NDCG

\- Average retrieval latency

\- Query throughput

\- Retrieval success rate

\- Security policy compliance

\- Explainability coverage

These metrics become the official product KPIs.

\-\--

## 1.11 Guiding Principles

Every future architecture decision should satisfy these principles.

### Principle 1

Knowledge remains immutable.

EKRE never modifies knowledge.

\-\--

### Principle 2

Retrieval is deterministic.

\-\--

### Principle 3

Security before relevance.

Unauthorized information should never participate in ranking.

\-\--

### Principle 4

Hybrid retrieval is mandatory.

No single retrieval algorithm is sufficient for enterprise environments.

\-\--

### Principle 5

Every retrieval decision should be explainable.

\-\--

### Principle 6

Every retrieval operation should be observable.

\-\--

### Principle 7

Ranking is a separate concern from retrieval.

\-\--

### Principle 8

Retrieval should remain model-independent.

The retrieval platform should not depend on a specific LLM vendor.

\-\--

## 1.12 Product Boundaries

The following diagram defines the official product boundary.

User Query

│

▼

Query Understanding

│

▼

Query Planning

│

▼

Retrieval Execution

│

▼

Candidate Fusion

│

▼

Ranking

│

▼

Context Assembly

│

▼

Structured Retrieval Result

│

▼

────────────────────────────────────────

END OF EKRE RESPONSIBILITY

────────────────────────────────────────

│

▼

External Consumer (EKCP)

Everything below the boundary belongs to another product.

\-\--

## 1.13 Product Philosophy

EKRE should become for enterprise retrieval what SQL databases became
for enterprise transactions.

Applications should not build retrieval themselves.

Applications should ask EKRE.

EKRE becomes the organization\'s retrieval platform.

\-\--

# End of Chapter 1

------------------------------------------------------------------------

**🏗️ Principal Architect Review**

As both Product Manager and Principal Architect, I would make **one
enhancement before we freeze Chapter 1**.

**Introduce the \"Enterprise Retrieval Contract (ERC)\"**

This becomes the **constitutional contract** of EKRE.

Every feature added in the future must satisfy these five promises:

1.  **Correctness** -- Results faithfully represent the indexed
    knowledge.

2.  **Relevance** -- The most useful information is ranked highest.

3.  **Governance** -- Security, metadata, and policy enforcement are
    mandatory.

4.  **Explainability** -- Every ranking decision is traceable and
    understandable.

5.  **Performance** -- Retrieval remains interactive at enterprise
    scale.

This ERC will act exactly like the **architecture principles** in EKIE
and prevent future feature requests from violating the product\'s core
mission.

------------------------------------------------------------------------

**📋 Progress Tracker**

We\'ll build the handbook sequentially:

- ✅ **Volume I -- Chapter 1: Product Vision & Foundation** *(Complete)*

- ⏳ **Chapter 2: Business Requirements & Product Requirements
  Specification (PRS)** *(Next)*

- ⏳ Chapter 3: Personas & Retrieval Use Cases

- ⏳ Chapter 4: Functional Requirements

- ⏳ Chapter 5: Non-Functional Requirements

- ⏳ Then we\'ll freeze **Volume I** before moving into the retrieval
  architecture itself.

I recommend we continue in this order so that, just like EKIE, every
technical decision in EKRE is anchored to clearly defined product
requirements rather than emerging ad hoc.

Excellent. This is exactly where a real product starts.

One thing I want to improve compared to EKIE is that before we start
designing the architecture, we should completely freeze **what problem
EKRE solves** and **what capabilities the product must deliver**.

As a Product Manager, **Chapter 2 is the most important chapter in the
entire handbook** because every future epic, sprint, architecture
decision, and acceptance criterion will originate from these
requirements.

This chapter will serve as the **Product Requirements Specification
(PRS)**.

------------------------------------------------------------------------

# Chapter 2 - Product Requirements Specification (PRS)

\-\--

# 2.1 Purpose

The Product Requirements Specification (PRS) defines the business
objectives, functional capabilities, constraints, success criteria, and
product boundaries of the Enterprise Knowledge Retrieval Engine (EKRE).

Unlike implementation documentation, this chapter answers one
fundamental question:

\> \*\*What problem must EKRE solve?\*\*

Every future architectural decision, API, workflow, and engineering task
must satisfy the requirements defined in this chapter.

This document acts as the contractual agreement between Product
Management, Architecture, Engineering, QA, Security, and Operations.

\-\--

# 2.2 Business Problem Statement

Modern enterprises have invested heavily in knowledge management systems
such as:

\- SharePoint

\- Confluence

\- Git Repositories

\- Wikis

\- Engineering Documentation

\- SOP Libraries

\- Technical Manuals

\- Knowledge Bases

\- Policy Repositories

Although these systems contain valuable information, they present
several challenges:

• Information exists in multiple disconnected repositories.

• Search quality varies significantly across systems.

• Traditional keyword search misses semantic meaning.

• Pure vector search ignores enterprise metadata.

• Security trimming is inconsistent.

• Multiple document versions create ambiguity.

• Duplicate information reduces trust.

• AI systems receive incomplete or irrelevant context.

As organizations adopt Generative AI, retrieval quality becomes the
limiting factor.

Poor retrieval results in hallucinations, inaccurate answers, and
reduced user confidence.

The enterprise therefore requires a centralized retrieval platform
capable of delivering trusted, explainable, and policy-compliant
knowledge.

EKRE fulfills this requirement.

\-\--

# 2.3 Product Problem Statement

Current retrieval systems suffer from several limitations.

## Traditional Enterprise Search

Strengths

✓ Fast keyword matching

Weaknesses

✗ Cannot understand semantic intent

✗ Sensitive to wording

✗ Poor ranking quality

✗ Weak contextual understanding

\-\--

## Pure Vector Search

Strengths

✓ Semantic similarity

Weaknesses

✗ Weak filtering

✗ Limited explainability

✗ Difficult governance

✗ No business context

✗ Metadata often ignored

\-\--

## AI Applications

Most enterprise AI applications implement their own retrieval logic.

This causes:

• duplicated engineering effort

• inconsistent retrieval behavior

• multiple security implementations

• different ranking algorithms

• inconsistent governance

The organization loses a single source of retrieval truth.

\-\--

# 2.4 Product Opportunity

Instead of every AI application implementing retrieval independently,
the enterprise deploys one centralized retrieval platform.

Every consumer requests knowledge through EKRE.

Benefits include:

\- Consistent retrieval

\- Centralized governance

\- Unified security enforcement

\- Shared ranking algorithms

\- Standard APIs

\- Better observability

\- Lower operational cost

\-\--

# 2.5 Product Vision Statement

Provide a unified enterprise retrieval platform that delivers the most
relevant, secure, explainable, and deterministic knowledge for every AI
application.

\-\--

# 2.6 Product Goals

EKRE has seven primary goals.

\-\--

## Goal 1

Deliver highly relevant enterprise knowledge.

Success means:

Users consistently receive the information they actually need.

\-\--

## Goal 2

Support hybrid retrieval.

Every query should leverage multiple retrieval strategies rather than
relying on a single search technique.

\-\--

## Goal 3

Provide deterministic retrieval.

Given:

\- identical query

\- identical indexes

\- identical policies

the system should always produce identical ranked results.

\-\--

## Goal 4

Enterprise governance.

Every retrieved result must satisfy:

\- security

\- metadata

\- compliance

\- versioning

\- lifecycle policies

\-\--

## Goal 5

Explainability.

Every ranking decision should be explainable.

The platform should answer:

\"Why was this result returned?\"

\-\--

## Goal 6

Performance.

Interactive retrieval should support enterprise AI systems without
introducing unacceptable latency.

\-\--

## Goal 7

Scalability.

Support:

\- millions of documents

\- hundreds of millions of chunks

\- multiple repositories

\- multiple vector databases

\- distributed deployments

\-\--

# 2.7 Product Objectives

The product objectives translate business goals into measurable
outcomes.

\| Objective \| Description \|

\|\-\-\-\-\-\-\-\-\-\-\--\|\-\-\-\-\-\-\-\-\-\-\-\--\|

\| Improve retrieval precision \| Return the most relevant results \|

\| Reduce hallucinations \| Supply higher quality context to downstream
consumers \|

\| Centralize retrieval \| One retrieval engine for all enterprise AI \|

\| Improve governance \| Uniform enforcement of enterprise policies \|

\| Increase transparency \| Every retrieval decision is traceable \|

\| Simplify integration \| Standard retrieval APIs \|

\-\--

# 2.8 Primary Stakeholders

The success of EKRE depends on multiple stakeholder groups.

### Executive Sponsors

Interested in:

\- enterprise AI adoption

\- governance

\- operational efficiency

\-\--

### Business Users

Need:

\- accurate search

\- trusted information

\- fast retrieval

\-\--

### AI Platform Teams

Require:

\- reusable retrieval APIs

\- stable interfaces

\- predictable latency

\-\--

### Security Teams

Require:

\- policy enforcement

\- access control

\- auditability

\-\--

### Knowledge Managers

Require:

\- metadata-aware retrieval

\- document lifecycle awareness

\- version management

\-\--

### Developers

Need:

\- SDKs

\- APIs

\- documentation

\- observability

\-\--

# 2.9 User Personas

The initial product supports several personas.

\| Persona \| Objective \|

\|\-\-\-\-\-\-\-\-\--\|\-\-\-\-\-\-\-\-\-\--\|

\| Enterprise Employee \| Find trusted information \|

\| AI Assistant \| Retrieve context for reasoning \|

\| Software Application \| Integrate retrieval through APIs \|

\| Research Agent \| Discover related enterprise knowledge \|

\| Knowledge Manager \| Validate retrieval quality \|

\| Security Auditor \| Verify policy enforcement \|

Detailed persona analysis will be documented in Chapter 3.

\-\--

# 2.10 Product Scope

The following capabilities are included in Version 1.0.

### Included

✓ Query Understanding

✓ Query Planning

✓ Hybrid Retrieval

✓ Vector Search

✓ Metadata Search

✓ Candidate Fusion

✓ Ranking

✓ Re-ranking

✓ Context Assembly

✓ Security Filtering

✓ Retrieval APIs

✓ Explainability

✓ Observability

✓ Performance Optimization

\-\--

### Excluded

✗ Chat Applications

✗ Prompt Engineering

✗ LLM Responses

✗ Agent Frameworks

✗ Memory

✗ Knowledge Creation

✗ Embedding Generation

✗ Repository Synchronization

✗ Workflow Automation

These capabilities belong to other products.

\-\--

# 2.11 Business Capabilities

EKRE provides the following business capabilities.

Capability 1

Unified Retrieval

One retrieval interface for all enterprise applications.

\-\--

Capability 2

Hybrid Search

Semantic

\+

Keyword

\+

Metadata

\+

Governance

\-\--

Capability 3

Policy-aware Retrieval

Every query respects:

\- permissions

\- security labels

\- compliance

\- document lifecycle

\-\--

Capability 4

Retrieval Explainability

The platform explains why every result was selected.

\-\--

Capability 5

Context Preparation

Produce retrieval context optimized for downstream AI systems.

\-\--

# 2.12 Product Constraints

The product operates under several architectural constraints.

Constraint 1

EKRE never modifies enterprise knowledge.

\-\--

Constraint 2

EKRE consumes knowledge assets produced by EKIE.

\-\--

Constraint 3

Retrieval must remain vendor-independent.

\-\--

Constraint 4

Ranking algorithms must be replaceable.

\-\--

Constraint 5

All retrieval decisions must be observable.

\-\--

Constraint 6

Security enforcement is mandatory.

No bypass mechanisms are permitted.

\-\--

# 2.13 Assumptions

The following assumptions apply.

\- Knowledge has already been indexed.

\- Embeddings already exist.

\- Metadata is available.

\- Security labels exist.

\- Vector indexes are synchronized.

\- Control Plane is available.

\-\--

# 2.14 Success Criteria

EKRE will be considered successful if it achieves:

• High retrieval precision

• Low retrieval latency

• Consistent ranking

• Explainable decisions

• Enterprise-scale performance

• Full policy compliance

• Stable APIs

• High availability

\-\--

# 2.15 Product KPIs

Recommended product KPIs.

Business KPIs

\- Search success rate

\- User satisfaction

\- Adoption rate

Technical KPIs

\- Precision@K

\- Recall@K

\- Mean Reciprocal Rank

\- NDCG

Operational KPIs

\- Average query latency

\- Queries per second

\- Error rate

\- Cache hit ratio

Governance KPIs

\- Security compliance

\- Explainability coverage

\- Policy enforcement accuracy

\-\--

# 2.16 Product Risks

Potential risks include:

\- Poor metadata quality

\- Weak chunk quality from ingestion

\- Embedding model drift

\- Large-scale indexing delays

\- Security misconfiguration

\- Query ambiguity

\- Performance bottlenecks

Mitigation strategies will be defined in later architecture chapters.

\-\--

# 2.17 Product Success Definition

EKRE succeeds when enterprise applications no longer need to implement
retrieval themselves.

Instead they rely entirely on EKRE to provide:

\- trusted retrieval

\- consistent ranking

\- secure filtering

\- explainable context

through a standardized enterprise retrieval platform.

\-\--

# End of Chapter 2

------------------------------------------------------------------------

**📐 Principal Architect Review (Before Freezing Chapter 2)**

As the Principal Architect, I would add one strategic enhancement that
will influence the rest of the handbook.

**Introduce Product Quality Attributes (Architecturally Significant
Requirements)**

Before any architecture is designed, we should explicitly prioritize the
non-functional qualities that drive architectural decisions.

**Proposed Quality Attribute Priorities**

  ---------------------------------------------------------------------------------
  **Priority**   **Attribute**    **Why It Matters**
  -------------- ---------------- -------------------------------------------------
  P1             Retrieval        The core value proposition of EKRE.
                 Accuracy         

  P1             Security         No unauthorized information may be retrieved.

  P1             Performance      Interactive AI systems require low-latency
                                  retrieval.

  P1             Scalability      Must support enterprise-scale repositories and
                                  indexes.

  P2             Explainability   Essential for trust, auditing, and debugging.

  P2             Availability     Retrieval should remain resilient under failures.

  P2             Observability    Every query path must be traceable.

  P3             Extensibility    New ranking algorithms and retrieval strategies
                                  should be pluggable.

  P3             Portability      Avoid lock-in to a specific vector database or
                                  cloud provider.
  ---------------------------------------------------------------------------------

These quality attributes should become the architectural drivers for
every design decision in the subsequent chapters.

------------------------------------------------------------------------

**📖 Handbook Progress**

**Volume I --- Product Foundation**

- ✅ Chapter 1 --- Product Vision

- ✅ Chapter 2 --- Product Requirements Specification (PRS)

- ⏳ Chapter 3 --- Personas, Enterprise Retrieval Scenarios & Use Cases
  *(next)*

- ⏳ Chapter 4 --- Functional Requirements

- ⏳ Chapter 5 --- Non-Functional Requirements

**Product Manager Assessment:** We are building the foundation
correctly. By fully freezing the product requirements before discussing
implementation, we ensure that every architectural component in EKRE can
be traced back to an explicit business requirement, resulting in a more
cohesive and maintainable platform.

Excellent. This is where EKRE starts becoming a true product rather than
just a search engine.

One thing I learned while designing EKIE is that we should **fully
understand the users and retrieval scenarios before designing the
architecture**.

Many retrieval systems fail because they optimize for a generic
\"search\" use case. Enterprise retrieval is much broader. Different
users expect different retrieval behavior.

For example:

- A software engineer searches differently from a legal officer.

- An AI agent retrieves differently from a human.

- A dashboard requesting top-5 documents has different needs than a
  research assistant requesting exhaustive evidence.

This chapter will freeze those requirements.

------------------------------------------------------------------------

# Chapter 3 - Personas, Enterprise Retrieval Scenarios & Use Cases

\-\--

# 3.1 Purpose

The purpose of this chapter is to identify the users, systems,
workflows, and retrieval scenarios that EKRE must support.

Rather than designing retrieval around technology, EKRE is designed
around enterprise retrieval behavior.

This chapter establishes:

\- Product personas

\- Consumer types

\- Retrieval patterns

\- Query categories

\- Enterprise use cases

\- Success expectations

Every future retrieval strategy, ranking algorithm, and optimization
must satisfy at least one use case defined here.

\-\--

# 3.2 Consumer Categories

EKRE serves two broad consumer categories.

## Human Consumers

Users interact through applications built on top of EKRE.

Examples include:

\- Enterprise Search Portals

\- Knowledge Portals

\- Internal AI Assistants

\- Engineering Documentation Systems

\- Operations Dashboards

These consumers require:

\- Fast responses

\- High precision

\- Explainability

\- Interactive performance

\-\--

## Machine Consumers

Software systems consume EKRE through APIs.

Examples include:

\- AI Chat Platforms

\- Enterprise Agents

\- Workflow Automation

\- Recommendation Systems

\- Analytics Platforms

Machine consumers require:

\- Deterministic APIs

\- Stable contracts

\- Structured responses

\- Rich metadata

\- High throughput

\-\--

# 3.3 Enterprise Personas

EKRE supports multiple enterprise personas.

\-\--

## Persona 1 --- Enterprise Employee

Objective:

Find trusted enterprise information quickly.

Typical Questions

\- Where is the latest SOP?

\- What is the leave policy?

\- Which architecture document is current?

Success Criteria

\- Accurate answers

\- Latest version

\- Easy discovery

\-\--

## Persona 2 --- Software Engineer

Objective

Locate technical documentation.

Typical Queries

\- API specifications

\- Design documents

\- Deployment guides

\- Coding standards

Important Ranking Factors

\- Latest version

\- Technical relevance

\- Repository trust

\- Architecture level

\-\--

## Persona 3 --- Knowledge Manager

Objective

Validate enterprise knowledge quality.

Typical Tasks

\- Detect duplicate content

\- Review document versions

\- Verify metadata

\- Analyze retrieval quality

Important Factors

\- Metadata

\- Lineage

\- Version history

\-\--

## Persona 4 --- AI Assistant

Objective

Retrieve context before reasoning.

Characteristics

\- High frequency

\- Low latency

\- Structured output

\- Deterministic behavior

Consumes

JSON APIs

Never human-readable interfaces.

\-\--

## Persona 5 --- Enterprise Research Agent

Objective

Collect evidence across multiple repositories.

Requirements

\- High recall

\- Source diversity

\- Citation quality

\- Relationship discovery

\-\--

## Persona 6 --- Security Auditor

Objective

Validate policy enforcement.

Typical Queries

\- Which confidential documents were retrieved?

\- Why was access denied?

\- Which policy filtered this document?

Priority

Governance over relevance.

\-\--

# 3.4 Query Categories

Not every query is the same.

EKRE classifies queries into retrieval categories.

\-\--

## Category A --- Lookup

Simple retrieval.

Examples

\"Travel policy\"

\"Expense form\"

Expected Behavior

Highest precision.

Low latency.

\-\--

## Category B --- Exploratory Search

Examples

\"Architecture for knowledge ingestion\"

Expected Behavior

Multiple relevant documents.

Topic diversity.

\-\--

## Category C --- Research

Examples

\"Everything related to refinery shutdown procedures\"

Expected Behavior

High recall.

Cross-repository retrieval.

Relationship discovery.

\-\--

## Category D --- Navigation

Examples

\"Open latest deployment guide\"

Expected Behavior

Locate exact document.

Prefer newest approved version.

\-\--

## Category E --- Comparison

Examples

\"Compare EKIE and EKRE\"

Expected Behavior

Retrieve documents from multiple domains.

Balanced context.

\-\--

## Category F --- Compliance

Examples

\"Policies related to GDPR\"

Expected Behavior

Strict metadata filtering.

Version awareness.

\-\--

## Category G --- AI Context Retrieval

Examples

Generated internally by downstream AI systems.

Expected Behavior

Token-efficient.

Highly ranked.

Structured output.

\-\--

# 3.5 Retrieval Intent Matrix

Every query belongs to one primary intent.

\| Intent \| Goal \| Ranking Priority \|

\|\-\-\-\-\-\-\-\-\--\|\-\-\-\-\--\|\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\--\|

\| Lookup \| Find exact information \| Precision \|

\| Explore \| Learn topic \| Diversity \|

\| Research \| Gather evidence \| Recall \|

\| Compare \| Multiple viewpoints \| Coverage \|

\| Navigate \| Find document \| Exact Match \|

\| AI Context \| Feed downstream AI \| Context Quality \|

Intent detection becomes the responsibility of the Query Understanding
Engine.

\-\--

# 3.6 Enterprise Retrieval Scenarios

Scenario 1

Employee searches company policy.

↓

Metadata filtering

↓

Keyword + semantic search

↓

Latest approved document returned.

\-\--

Scenario 2

AI assistant requests context.

↓

Semantic retrieval

↓

Hybrid ranking

↓

Context assembly

↓

JSON response.

\-\--

Scenario 3

Research agent searches five repositories.

↓

Parallel retrieval

↓

Fusion

↓

Deduplication

↓

Evidence package.

\-\--

Scenario 4

Engineering application requests API specification.

↓

Metadata filter

↓

Architecture ranking

↓

Latest version.

\-\--

Scenario 5

Compliance application requests documents.

↓

Security filtering

↓

Classification filtering

↓

Policy-aware ranking.

\-\--

# 3.7 Retrieval Expectations

Enterprise users expect:

\- Fast responses

\- Latest versions

\- No duplicates

\- Secure information

\- Explainable ranking

\- Stable ordering

Failure in any expectation reduces trust.

\-\--

# 3.8 Retrieval Modes

EKRE supports multiple retrieval modes.

Mode 1

Top-K Retrieval

Return best ranked chunks.

\-\--

Mode 2

Exhaustive Retrieval

Return all matching evidence.

\-\--

Mode 3

Filtered Retrieval

Return results satisfying metadata constraints.

\-\--

Mode 4

Semantic Retrieval

Embedding similarity.

\-\--

Mode 5

Hybrid Retrieval

Vector

\+

Keyword

\+

Metadata

\+

Policy

\-\--

Mode 6

Relationship Retrieval (Future)

Use lineage and knowledge graphs.

\-\--

# 3.9 API Consumption Patterns

Synchronous

Interactive search.

Low latency.

\-\--

Asynchronous

Large research tasks.

Batch retrieval.

\-\--

Streaming (Future)

Large context delivery.

Incremental retrieval.

\-\--

# 3.10 Enterprise Retrieval Journey

User Query

↓

Intent Detection

↓

Query Understanding

↓

Query Planning

↓

Retrieval

↓

Fusion

↓

Ranking

↓

Context Assembly

↓

API Response

This becomes the official retrieval lifecycle.

\-\--

# 3.11 Success Definition

A successful retrieval session satisfies all of the following:

✓ Correct information

✓ Correct version

✓ Authorized access

✓ High relevance

✓ Explainable ranking

✓ Acceptable latency

\-\--

# End of Chapter 3

------------------------------------------------------------------------

**🏛 Principal Architect Review (Before Freezing Chapter 3)**

This chapter is strong, but I would introduce one concept now rather
than later because it influences almost every architectural decision
that follows.

**Introduce Retrieval Profiles**

Instead of having a single retrieval pipeline for all requests, define
**Retrieval Profiles** that encapsulate different retrieval behaviors.

Examples:

  ----------------------------------------------------------
  **Profile**       **Optimized For** **Typical Consumer**
  ----------------- ----------------- ----------------------
  **Precision       Exactness, low    Employees, search
  Profile**         noise             portals

  **Recall          Maximum coverage  Research agents
  Profile**                           

  **Balanced        Precision +       AI assistants
  Profile**         recall            

  **Compliance      Policy            Auditors, legal teams
  Profile**         enforcement       

  **Performance     Lowest latency    High-QPS applications
  Profile**                           
  ----------------------------------------------------------

Each profile controls:

- Query expansion strategy

- Hybrid search weights

- Number of retrieved candidates

- Re-ranking model

- Context assembly rules

- Caching behavior

This is a major architectural improvement because it avoids hardcoding
one retrieval strategy for every scenario. Instead, the Query Planner
can select or override a profile based on intent, consumer type, or
explicit API parameters.

------------------------------------------------------------------------

**📚 Handbook Progress**

**Volume I -- Product Foundation**

- ✅ Chapter 1 --- Product Vision

- ✅ Chapter 2 --- Product Requirements Specification

- ✅ Chapter 3 --- Personas, Enterprise Retrieval Scenarios & Use Cases

- ⏳ **Chapter 4 --- Functional Requirements Specification (FRS)**
  *(Next)*

- ⏳ Chapter 5 --- Non-Functional Requirements (NFR)

- ⏳ Chapter 6 --- Enterprise Retrieval Principles & ADRs

**Product Manager Decision**

Before we move into the architecture (Volume II), I want to **fully
freeze Volume I**. Chapter 4 will be one of the most detailed chapters
because it will enumerate every functional capability that EKRE must
provide. Those requirements will later map directly to architecture
components, epics, APIs, test cases, and acceptance criteria, giving us
complete traceability from business need to implementation.

Excellent. This is one of the most important chapters in the entire
handbook.

As the **Product Manager**, I consider the **Functional Requirements
Specification (FRS)** to be the contract between Product and
Engineering.

Unlike the PRS, which explains *why* the product exists, the FRS defines
**exactly what EKRE must do**.

Every architecture component, API, database schema, workflow, sprint,
and test case will trace back to one or more functional requirements
defined here.

I also want to improve something compared to EKIE.

Instead of writing generic functional requirements, we will assign each
one a **Requirement ID (FR-XXX)**. These IDs will later map directly to:

- Architecture Components

- APIs

- User Stories

- Test Cases

- Acceptance Criteria

- Traceability Matrix

This is how enterprise products are built.

------------------------------------------------------------------------

# Chapter 4 - Functional Requirements Specification (FRS)

\-\--

# 4.1 Purpose

This chapter defines the functional capabilities that the Enterprise
Knowledge Retrieval Engine (EKRE) shall provide.

Each requirement is uniquely identified and traceable throughout the
product lifecycle.

Every implementation, architecture decision, and validation test must
reference one or more functional requirements documented here.

\-\--

# 4.2 Functional Requirement Categories

The functional requirements are organized into the following domains.

FR-100 Query Management

FR-200 Query Understanding

FR-300 Query Planning

FR-400 Retrieval Execution

FR-500 Hybrid Search

FR-600 Candidate Fusion

FR-700 Ranking & Re-ranking

FR-800 Context Assembly

FR-900 Explainability

FR-1000 Security & Governance

FR-1100 APIs

FR-1200 Administration

FR-1300 Observability

FR-1400 Performance

FR-1500 Extensibility

\-\--

# FR-100 Query Management

\-\--

## FR-101

The system shall accept structured retrieval requests through a standard
retrieval API.

\-\--

## FR-102

The system shall support both natural language queries and structured
query requests.

\-\--

## FR-103

Each query shall receive a globally unique Query ID.

\-\--

## FR-104

Every query shall be timestamped.

\-\--

## FR-105

Every query shall generate a complete execution trace.

\-\--

## FR-106

Every query shall execute independently.

\-\--

## FR-107

The system shall support query cancellation.

\-\--

## FR-108

The system shall support configurable request timeout policies.

\-\--

# FR-200 Query Understanding

\-\--

## FR-201

The system shall normalize incoming queries.

Examples:

\- whitespace normalization

\- punctuation normalization

\- language normalization

\-\--

## FR-202

The system shall detect retrieval intent.

Supported intents include:

\- lookup

\- exploration

\- research

\- comparison

\- navigation

\- compliance

\- AI context retrieval

\-\--

## FR-203

The system shall extract entities from user queries.

Examples:

\- projects

\- products

\- repositories

\- document types

\- versions

\- dates

\-\--

## FR-204

The system shall identify metadata filters contained within the query.

\-\--

## FR-205

The system shall support configurable query expansion.

Expansion techniques may include:

\- synonym expansion

\- ontology expansion

\- acronym resolution

\-\--

## FR-206

Query expansion shall be optional.

\-\--

## FR-207

Every transformation performed during query understanding shall be
recorded for explainability.

\-\--

# FR-300 Query Planning

\-\--

## FR-301

The system shall generate an execution plan before retrieval begins.

\-\--

## FR-302

The execution plan shall identify which retrieval engines participate.

\-\--

## FR-303

The planner shall determine whether hybrid retrieval is required.

\-\--

## FR-304

The planner shall determine retrieval profile selection.

Examples:

\- Precision

\- Recall

\- Balanced

\- Compliance

\- Performance

\-\--

## FR-305

The planner shall support configurable retrieval strategies.

\-\--

## FR-306

Execution plans shall be observable.

\-\--

## FR-307

Execution plans shall be versioned.

\-\--

# FR-400 Retrieval Execution

\-\--

## FR-401

The system shall support vector retrieval.

\-\--

## FR-402

The system shall support lexical retrieval.

\-\--

## FR-403

The system shall support metadata retrieval.

\-\--

## FR-404

The system shall support repository-level filtering.

\-\--

## FR-405

The system shall support version-aware retrieval.

\-\--

## FR-406

The system shall support cross-repository retrieval.

\-\--

## FR-407

Retrieval engines shall execute in parallel whenever possible.

\-\--

## FR-408

Partial failures shall not terminate the entire retrieval session.

\-\--

## FR-409

Every retrieval engine shall produce standardized candidate results.

\-\--

# FR-500 Hybrid Search

\-\--

## FR-501

The system shall combine multiple retrieval engines.

\-\--

## FR-502

Hybrid retrieval weights shall be configurable.

\-\--

## FR-503

Hybrid strategies shall support future retrieval engines.

\-\--

## FR-504

Hybrid retrieval shall support profile-specific weighting.

\-\--

## FR-505

Candidate normalization shall occur before fusion.

\-\--

# FR-600 Candidate Fusion

\-\--

## FR-601

Candidate results shall be merged into a unified candidate pool.

\-\--

## FR-602

Duplicate candidates shall be detected.

\-\--

## FR-603

Duplicate candidates shall be consolidated.

\-\--

## FR-604

Candidate provenance shall be preserved.

\-\--

## FR-605

Fusion decisions shall be observable.

\-\--

# FR-700 Ranking & Re-ranking

\-\--

## FR-701

Every candidate shall receive a ranking score.

\-\--

## FR-702

Ranking algorithms shall be replaceable.

\-\--

## FR-703

Ranking shall support configurable weighting.

\-\--

## FR-704

Re-ranking shall be optional.

\-\--

## FR-705

Cross-encoder re-ranking shall be supported.

\-\--

## FR-706

Ranking explanations shall be generated.

\-\--

## FR-707

Ranking shall consider:

\- semantic similarity

\- keyword relevance

\- metadata

\- document freshness

\- repository trust

\- retrieval profile

\-\--

# FR-800 Context Assembly

\-\--

## FR-801

The system shall assemble retrieved chunks into structured context
packages.

\-\--

## FR-802

Context assembly shall preserve source order where required.

\-\--

## FR-803

Chunk relationships shall be preserved.

\-\--

## FR-804

Token budgets shall be configurable.

\-\--

## FR-805

Context assembly shall preserve citations.

\-\--

## FR-806

Context shall include metadata.

\-\--

## FR-807

Context shall be consumable by downstream applications.

\-\--

# FR-900 Explainability

\-\--

## FR-901

Every retrieved result shall include an explanation.

\-\--

## FR-902

Every ranking decision shall be traceable.

\-\--

## FR-903

Every retrieval engine contribution shall be recorded.

\-\--

## FR-904

Execution plans shall be available for diagnostics.

\-\--

## FR-905

Retrieval profiles shall be reported.

\-\--

# FR-1000 Security & Governance

\-\--

## FR-1001

Security filtering shall occur before ranking.

\-\--

## FR-1002

Unauthorized documents shall never enter the candidate pool.

\-\--

## FR-1003

Metadata policies shall be enforced.

\-\--

## FR-1004

Version policies shall be enforced.

\-\--

## FR-1005

Compliance rules shall be configurable.

\-\--

# FR-1100 APIs

\-\--

## FR-1101

The platform shall expose versioned retrieval APIs.

\-\--

## FR-1102

API contracts shall remain backward compatible.

\-\--

## FR-1103

Structured JSON responses shall be returned.

\-\--

## FR-1104

Streaming responses shall be supported in future versions.

\-\--

# FR-1200 Administration

\-\--

## FR-1201

Retrieval profiles shall be configurable.

\-\--

## FR-1202

Ranking policies shall be configurable.

\-\--

## FR-1203

Query planners shall support configuration.

\-\--

## FR-1204

Administrators shall configure retrieval strategies without
recompilation.

\-\--

# FR-1300 Observability

\-\--

## FR-1301

Every query shall emit structured logs.

\-\--

## FR-1302

Every query shall expose metrics.

\-\--

## FR-1303

Distributed tracing shall be supported.

\-\--

## FR-1304

Every query shall expose latency breakdowns.

\-\--

## FR-1305

Observability shall integrate with enterprise monitoring platforms.

\-\--

# FR-1400 Performance

\-\--

## FR-1401

Parallel retrieval shall be supported.

\-\--

## FR-1402

Caching shall be supported.

\-\--

## FR-1403

Retrieval shall support configurable timeout policies.

\-\--

## FR-1404

Large-scale repositories shall be supported.

\-\--

# FR-1500 Extensibility

\-\--

## FR-1501

New retrieval engines shall be pluggable.

\-\--

## FR-1502

New ranking algorithms shall be pluggable.

\-\--

## FR-1503

New query planners shall be pluggable.

\-\--

## FR-1504

Future retrieval strategies shall require no modification to the Core
Engine.

\-\--

# 4.3 Functional Traceability

Every functional requirement defined in this chapter shall be traceable
to:

• Product Goals (Chapter 2)

• Architecture Components (Volume II)

• APIs (Volume III)

• Test Cases (Volume V)

• Acceptance Criteria

• Release Notes

This traceability ensures complete lifecycle governance.

\-\--

# End of Chapter 4

------------------------------------------------------------------------

**🏛 Principal Architect Review (Before Freezing Chapter 4)**

This chapter is much stronger than a traditional FRS, but after
reviewing it I would make **one major architectural enhancement** that
will save us significant effort later.

**Introduce Capability IDs Alongside Requirement IDs**

Right now we have **Functional Requirements (FRs)**, but we don\'t yet
have **Product Capabilities**.

I recommend introducing a capability layer:

  ------------------------------------------------
  **Capability   **Capability**    **Related FRs**
  ID**                             
  -------------- ----------------- ---------------
  **CAP-01**     Query Management  FR-101 → FR-108

  **CAP-02**     Query             FR-201 → FR-207
                 Understanding     

  **CAP-03**     Query Planning    FR-301 → FR-307

  **CAP-04**     Retrieval         FR-401 → FR-409
                 Execution         

  **CAP-05**     Hybrid Retrieval  FR-501 → FR-505

  **CAP-06**     Candidate Fusion  FR-601 → FR-605

  **CAP-07**     Ranking           FR-701 → FR-707

  **CAP-08**     Context Assembly  FR-801 → FR-807

  **CAP-09**     Explainability    FR-901 → FR-905

  **CAP-10**     Governance        FR-1001 →
                                   FR-1005

  **CAP-11**     APIs              FR-1101 →
                                   FR-1104

  **CAP-12**     Administration    FR-1201 →
                                   FR-1204

  **CAP-13**     Observability     FR-1301 →
                                   FR-1305

  **CAP-14**     Performance       FR-1401 →
                                   FR-1404

  **CAP-15**     Extensibility     FR-1501 →
                                   FR-1504
  ------------------------------------------------

This gives us three levels of traceability:

- **Business Goal** → Why are we building it?

- **Capability** → What business capability are we delivering?

- **Functional Requirement** → What exactly must the system do?

This structure will make the later implementation roadmap, sprint
planning, and testing significantly more manageable.

------------------------------------------------------------------------

**📚 Handbook Progress**

**Volume I -- Product Foundation**

- ✅ Chapter 1 --- Product Vision

- ✅ Chapter 2 --- Product Requirements Specification (PRS)

- ✅ Chapter 3 --- Personas, Enterprise Retrieval Scenarios & Use Cases

- ✅ Chapter 4 --- Functional Requirements Specification (FRS)

- ⏳ **Chapter 5 --- Non-Functional Requirements (NFR)** *(Next and
  final chapter of Volume I)*

After Chapter 5, we will **freeze Volume I** and move into **Volume II
--- Retrieval Architecture**, where we begin designing the core of EKRE:
the Query Lifecycle, Query Understanding Engine, Query Planner,
Retrieval Orchestrator, Hybrid Retrieval Framework, Ranking Engine, and
Context Assembly Engine. This ensures the architecture is built on a
complete, stable, and traceable product foundation.

Excellent. Now we reach what I consider the **architectural driver** of
the entire product.

In most software projects, Non-Functional Requirements (NFRs) are
treated as an afterthought. For EKRE, they are **first-class citizens**
because retrieval systems are judged less by *whether they work* and
more by *how well they work*.

For example:

- Returning the correct document in **30 seconds** is a failure.

- Returning unauthorized documents is a failure.

- Returning inconsistent results for the same query is a failure.

- Returning correct documents without explainability is a failure in
  many regulated enterprises.

This chapter defines the **Architecturally Significant Requirements
(ASRs)** that will drive every design decision in Volume II.

------------------------------------------------------------------------

# Chapter 5 - Non-Functional Requirements (NFR)

\-\--

# 5.1 Purpose

This chapter defines the quality attributes and operational
characteristics required for the Enterprise Knowledge Retrieval Engine
(EKRE).

Unlike functional requirements, which describe \*what\* the platform
must do, non-functional requirements define \*how well\* it must perform
those functions.

Every architectural decision in EKRE must be justified against one or
more non-functional requirements documented here.

\-\--

# 5.2 Architectural Quality Attributes

The architecture shall optimize for the following quality attributes,
ordered by priority.

\| Priority \| Quality Attribute \| Importance \|

\|\-\-\-\-\-\-\-\-\-\--\|\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\--\|\-\-\-\-\-\-\-\-\-\-\--\|

\| P1 \| Retrieval Accuracy \| Critical \|

\| P1 \| Security \| Critical \|

\| P1 \| Performance \| Critical \|

\| P1 \| Scalability \| Critical \|

\| P2 \| Explainability \| High \|

\| P2 \| Reliability \| High \|

\| P2 \| Availability \| High \|

\| P2 \| Observability \| High \|

\| P3 \| Extensibility \| Medium \|

\| P3 \| Maintainability \| Medium \|

\| P3 \| Portability \| Medium \|

These priorities guide architecture trade-offs throughout the product
lifecycle.

\-\--

# 5.3 Retrieval Accuracy

## Objective

Deliver highly relevant retrieval results with minimal false positives
and false negatives.

### Requirements

\- Ranking must prioritize the most relevant content.

\- Duplicate results shall be minimized.

\- Hybrid retrieval shall improve precision over individual retrieval
methods.

\- Query understanding shall improve intent detection.

\- Re-ranking shall improve final candidate quality.

### Target Metrics

\- Precision@10

\- Recall@10

\- Mean Reciprocal Rank (MRR)

\- NDCG

\- Success Rate

Accuracy is the primary value proposition of EKRE.

\-\--

# 5.4 Performance

## Objective

Support interactive enterprise retrieval with predictable latency.

### Requirements

\- Retrieval pipelines shall execute in parallel whenever possible.

\- Candidate fusion shall avoid unnecessary blocking operations.

\- Ranking shall scale with configurable candidate limits.

\- Context assembly shall minimize token processing overhead.

### Performance Targets

Average latency targets (illustrative):

\| Operation \| Target \|

\|\-\-\-\-\-\-\-\-\-\-\--\|\-\-\-\-\-\-\-\--\|

\| Query Understanding \| \<20 ms \|

\| Query Planning \| \<10 ms \|

\| Metadata Retrieval \| \<50 ms \|

\| Vector Retrieval \| \<150 ms \|

\| Candidate Fusion \| \<20 ms \|

\| Ranking \| \<100 ms \|

\| Context Assembly \| \<50 ms \|

End-to-end latency target:

≤ 500 ms for standard enterprise queries under normal operating
conditions.

\-\--

# 5.5 Scalability

## Objective

Scale horizontally as enterprise knowledge grows.

### Requirements

The platform shall support:

\- Millions of enterprise documents.

\- Hundreds of millions of chunks.

\- Multiple repositories.

\- Multiple vector databases.

\- Distributed deployments.

\- Concurrent users.

\- Concurrent AI systems.

Scaling shall not require architectural redesign.

\-\--

# 5.6 Reliability

## Objective

Provide predictable retrieval under expected operating conditions.

### Requirements

\- Partial failures shall degrade gracefully.

\- Failed retrieval engines shall not terminate entire queries.

\- Retry policies shall be configurable.

\- Recovery mechanisms shall be automatic where appropriate.

Reliability includes deterministic behavior as well as resilience to
component failures.

\-\--

# 5.7 Availability

## Objective

Support enterprise-grade uptime.

### Requirements

\- Retrieval APIs shall remain available during component failures where
feasible.

\- Planned maintenance should minimize disruption.

\- Health monitoring shall detect degraded services promptly.

Illustrative availability target:

≥ 99.9% service availability.

\-\--

# 5.8 Security

## Objective

Ensure retrieval never exposes unauthorized knowledge.

### Requirements

\- Authorization shall be enforced before ranking.

\- Unauthorized candidates shall never enter the candidate pool.

\- Security policies shall be centrally managed.

\- Audit logs shall capture security-relevant events.

\- Sensitive metadata shall be protected.

Security is a mandatory architectural constraint and cannot be bypassed.

\-\--

# 5.9 Explainability

## Objective

Every retrieval decision shall be understandable.

### Requirements

The platform shall explain:

\- Why a document was retrieved.

\- Which retrieval engines contributed.

\- Which ranking factors influenced the score.

\- Which metadata filters were applied.

\- Which security policies affected visibility.

Explainability supports user trust, debugging, and compliance.

\-\--

# 5.10 Observability

## Objective

Every retrieval workflow shall be measurable.

### Requirements

Each query shall expose:

\- Query ID

\- Trace ID

\- Execution timeline

\- Retrieval stages

\- Ranking metrics

\- Latency breakdown

\- Error information

\- Selected retrieval profile

Observability is mandatory for production operations.

\-\--

# 5.11 Maintainability

## Objective

Allow rapid evolution with minimal operational risk.

### Requirements

\- Components shall be modular.

\- Interfaces shall be stable.

\- Configuration shall be externalized.

\- Documentation shall accompany architectural changes.

\- Architecture Decision Records (ADRs) shall be maintained.

\-\--

# 5.12 Extensibility

## Objective

Support future retrieval innovations without modifying the Core Engine.

### Requirements

The architecture shall support pluggable:

\- Retrieval engines

\- Ranking algorithms

\- Query planners

\- Re-ranking models

\- Query expansion strategies

\- Context assemblers

Future extensions should require configuration rather than core code
changes.

\-\--

# 5.13 Portability

## Objective

Avoid dependence on specific infrastructure vendors.

### Requirements

The architecture should support replacing:

\- Vector databases

\- Search engines

\- Embedding providers

\- Identity providers

\- Cloud platforms

through abstraction layers and well-defined interfaces.

\-\--

# 5.14 Compliance

## Objective

Support enterprise governance requirements.

### Requirements

The platform shall support:

\- Auditability

\- Data lineage integration

\- Policy enforcement

\- Access reviews

\- Version-aware retrieval

\- Regulatory compliance workflows

Compliance requirements shall integrate with enterprise governance
processes.

\-\--

# 5.15 Usability

## Objective

Provide a predictable and consistent developer experience.

### Requirements

\- Stable APIs

\- Comprehensive documentation

\- Clear error messages

\- Versioned contracts

\- SDK support

\- Consistent response structures

Although end users interact through downstream applications, developer
usability remains a key success factor.

\-\--

# 5.16 Disaster Recovery

## Objective

Recover retrieval services with minimal interruption.

### Requirements

\- Configuration backups.

\- Recovery procedures.

\- Index reconstruction support.

\- Service restart automation.

\- Operational runbooks.

Recovery objectives will be finalized during deployment planning.

\-\--

# 5.17 Quality Attribute Scenarios

Each quality attribute should be validated through measurable scenarios.

### Example: Performance

Scenario:

An AI application submits a retrieval request against 50 million indexed
chunks.

Expected Result:

The platform returns the top-ranked context within the defined latency
target.

\-\--

### Example: Security

Scenario:

A user requests confidential documentation without appropriate
permissions.

Expected Result:

No unauthorized documents appear in the candidate pool or final results.

\-\--

### Example: Explainability

Scenario:

A user asks why a specific document ranked first.

Expected Result:

The platform returns the contributing retrieval engines, ranking
factors, metadata filters, and scoring rationale.

\-\--

### Example: Reliability

Scenario:

The vector database becomes temporarily unavailable.

Expected Result:

The retrieval pipeline degrades gracefully, executes remaining retrieval
strategies where appropriate, and reports the degraded state in the
execution trace.

\-\--

# 5.18 Architectural Decision Drivers

The following quality attributes are considered Architecturally
Significant Requirements (ASRs):

1\. Retrieval Accuracy

2\. Security

3\. Performance

4\. Scalability

5\. Explainability

6\. Reliability

7\. Availability

8\. Observability

Every architecture decision documented in subsequent volumes shall
explicitly reference one or more of these ASRs.

\-\--

# End of Chapter 5

------------------------------------------------------------------------

**🏛 Principal Architect Review (Before Freezing Volume I)**

After reviewing Chapters 1--5, I would make **one significant
improvement** that I wish we had incorporated earlier in EKIE.

**Introduce a Product Traceability Matrix**

Before moving into architecture, define a traceability model that
connects every layer of the product.

  ------------------------------------------------------
  **Layer**            **Example**
  -------------------- ---------------------------------
  Business Goal        Deliver trusted enterprise
                       retrieval

  Product Capability   Hybrid Retrieval

  Functional           FR-501
  Requirement          

  Quality Attribute    Performance

  Architecture         Retrieval Orchestrator
  Component            

  API                  /retrieve

  Test Suite           Integration Test -- Hybrid Search

  Acceptance Criteria  Top-10 results meet Precision@10
                       target
  ------------------------------------------------------

This creates **end-to-end traceability** from business vision to
implementation and testing. It also makes impact analysis
straightforward: if a requirement changes, you can immediately identify
the affected components, APIs, and tests.

------------------------------------------------------------------------

**📘 Volume I Status --- Complete**

With Chapter 5 complete, **Volume I is now frozen**.

**Volume I --- Product Foundation**

- ✅ Chapter 1 --- Product Vision

- ✅ Chapter 2 --- Product Requirements Specification (PRS)

- ✅ Chapter 3 --- Personas, Enterprise Retrieval Scenarios & Use Cases

- ✅ Chapter 4 --- Functional Requirements Specification (FRS)

- ✅ Chapter 5 --- Non-Functional Requirements (NFR)

------------------------------------------------------------------------

**🚀 Next Phase: Volume II --- Enterprise Retrieval Architecture**

This is where EKRE transitions from **product definition** to **system
design**.

Unlike EKIE, where the architecture began with repository
synchronization, EKRE begins with the **query lifecycle** because
everything in the retrieval platform revolves around how a query is
transformed into a ranked, explainable, policy-compliant context.

The proposed sequence for Volume II is:

1.  **Chapter 6** --- Enterprise Retrieval Architecture Overview

2.  **Chapter 7** --- End-to-End Query Lifecycle

3.  **Chapter 8** --- Query Understanding Engine

4.  **Chapter 9** --- Query Planner

5.  **Chapter 10** --- Retrieval Orchestrator

6.  **Chapter 11** --- Hybrid Retrieval Framework

7.  **Chapter 12** --- Candidate Fusion Engine

8.  **Chapter 13** --- Ranking & Re-ranking Framework

9.  **Chapter 14** --- Context Assembly Engine

From this point onward, the handbook shifts from **\"what EKRE should
do\"** to **\"how EKRE is architected to do it.\"** This is where the
platform\'s core technical design begins.

Excellent. Now we begin what I consider the **heart of EKRE**.

Everything before this point defined **why the product exists**.

From this chapter onward, we define **how the product works**.

As Principal Architect, I want to make one improvement over EKIE.

**We are NOT going to start with individual components like the Query
Understanding Engine.**

Instead, we\'re first going to define the **Enterprise Retrieval
Architecture** as a whole.

This is exactly how TOGAF, Microsoft, Google, AWS and large enterprise
architecture teams work.

First define the **system**.

Then define the **subsystems**.

Then define the **components**.

Then define the **classes**.

This prevents architectural drift later.

------------------------------------------------------------------------

# Volume II

# Enterprise Retrieval Architecture

\-\--

# Chapter 6 - Enterprise Retrieval Architecture Overview

\-\--

# 6.1 Purpose

This chapter establishes the architectural blueprint of the Enterprise
Knowledge Retrieval Engine (EKRE).

It defines:

\- System boundaries

\- Architectural layers

\- Core subsystems

\- Component responsibilities

\- Runtime interactions

\- Design principles

Rather than describing implementation details, this chapter defines how
the entire retrieval platform is organized.

Every architecture component described in subsequent chapters inherits
its responsibilities from this chapter.

\-\--

# 6.2 Architecture Philosophy

EKRE is designed as a layered enterprise retrieval platform.

The architecture follows five principles.

## Principle 1

Single Responsibility

Every subsystem owns exactly one business capability.

\-\--

## Principle 2

Separation of Concerns

Understanding a query is different from retrieving knowledge.

Retrieving knowledge is different from ranking.

Ranking is different from assembling context.

Each responsibility becomes an independent subsystem.

\-\--

## Principle 3

Pipeline Architecture

Queries move through a deterministic pipeline.

Each stage transforms the query.

No stage skips another stage.

\-\--

## Principle 4

Composable Retrieval

Retrieval strategies should be composable rather than hardcoded.

Future retrieval engines should plug into existing workflows.

\-\--

## Principle 5

Deterministic Execution

Given

\- same query

\- same indexes

\- same configuration

EKRE should produce identical execution plans and ranked results.

\-\--

# 6.3 Architectural Goals

The architecture must satisfy the following goals.

✓ High Retrieval Accuracy

✓ Low Latency

✓ Enterprise Governance

✓ Explainability

✓ Horizontal Scalability

✓ Vendor Independence

✓ Component Replaceability

✓ Operational Visibility

\-\--

# 6.4 Enterprise Architecture Layers

EKRE is organized into eight logical layers.

\`\`\`

┌──────────────────────────────┐

│ Client Applications │

└──────────────────────────────┘

│

┌──────────────────────────────┐

│ API Gateway │

└──────────────────────────────┘

│

┌──────────────────────────────┐

│ Query Processing Layer │

└──────────────────────────────┘

│

┌──────────────────────────────┐

│ Retrieval Execution │

└──────────────────────────────┘

│

┌──────────────────────────────┐

│ Fusion & Ranking │

└──────────────────────────────┘

│

┌──────────────────────────────┐

│ Context Assembly │

└──────────────────────────────┘

│

┌──────────────────────────────┐

│ Data Access Layer │

└──────────────────────────────┘

│

┌──────────────────────────────┐

│ Enterprise Knowledge Assets │

└──────────────────────────────┘

\`\`\`

\-\--

# 6.5 Architectural Building Blocks

The platform is composed of independent subsystems.

Each subsystem owns one capability.

\| Layer \| Subsystem \|

\|\-\-\-\-\-\-\-\--\|\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\--\|

\| API \| Retrieval API \|

\| Query \| Query Understanding Engine \|

\| Query \| Query Planner \|

\| Execution \| Retrieval Orchestrator \|

\| Execution \| Retrieval Engines \|

\| Ranking \| Candidate Fusion Engine \|

\| Ranking \| Ranking Framework \|

\| Context \| Context Assembly Engine \|

\| Runtime \| Policy Engine \|

\| Runtime \| Cache Manager \|

\| Runtime \| Observability Framework \|

These become the major chapters of Volume II.

\-\--

# 6.6 Core Runtime Flow

Every request follows the same lifecycle.

\`\`\`

Incoming Query

↓

Authentication

↓

Authorization

↓

Query Understanding

↓

Query Planning

↓

Retrieval Execution

↓

Candidate Fusion

↓

Ranking

↓

Context Assembly

↓

Response Generation

↓

API Response

\`\`\`

Every query must follow this pipeline.

No component bypasses another.

\-\--

# 6.7 Enterprise Component Model

The platform consists of independent services.

\`\`\`

Retrieval API

│

┌──────────────┼──────────────┐

▼ ▼ ▼

Query Understanding Planner Observability

│

▼

Retrieval Orchestrator

│

┌──────┼───────────┬────────────┐

▼ ▼ ▼ ▼

Vector Keyword Metadata Relationship

Engine Engine Engine Engine(Future)

│

▼

Candidate Fusion

│

▼

Ranking Engine

│

▼

Context Assembly

│

▼

Structured Retrieval Result

\`\`\`

Each subsystem can evolve independently.

\-\--

# 6.8 Architectural Dependencies

EKRE depends upon several enterprise services.

Mandatory

• EKIE Knowledge Assets

• Vector Database

• Metadata Store

• Security Provider

• Configuration Service

Optional

• Ontology Service

• Enterprise Search Index

• Graph Database

• External Re-ranking Models

The architecture remains modular regardless of which optional services
are enabled.

\-\--

# 6.9 Architecture Characteristics

The architecture is intentionally:

Stateless

Modular

Event-aware

Pipeline-oriented

Configuration-driven

Extensible

Observable

Explainable

Deterministic

Vendor Neutral

These characteristics influence every implementation decision.

\-\--

# 6.10 Data Ownership

An important architectural rule:

EKRE owns retrieval.

EKRE does NOT own knowledge.

Knowledge ownership remains within EKIE.

This separation prevents duplication of responsibility.

\-\--

# 6.11 Component Responsibilities

Query Understanding

↓

Transforms user language into structured retrieval intent.

\-\--

Query Planner

↓

Determines execution strategy.

\-\--

Retrieval Orchestrator

↓

Coordinates retrieval engines.

\-\--

Retrieval Engines

↓

Collect candidate knowledge.

\-\--

Candidate Fusion

↓

Merge all candidates.

\-\--

Ranking Framework

↓

Prioritize candidates.

\-\--

Context Assembly

↓

Prepare enterprise context packages.

\-\--

Observability

↓

Capture execution telemetry.

\-\--

Policy Engine

↓

Enforce enterprise governance.

\-\--

# 6.12 Enterprise Design Principles

Every subsystem shall satisfy:

Loose coupling

High cohesion

Dependency inversion

Plugin architecture

Configuration over code

Deterministic execution

No shared mutable state

Asynchronous execution where appropriate

\-\--

# 6.13 Architectural Boundaries

The following responsibilities are explicitly outside EKRE.

✗ Knowledge ingestion

✗ Embedding generation

✗ Prompt construction

✗ LLM inference

✗ Conversation memory

✗ AI agent execution

✗ Response generation

These responsibilities belong to other enterprise platforms.

\-\--

# 6.14 Architectural Success Criteria

The architecture is considered successful when:

Every component has a single responsibility.

Every pipeline stage is observable.

Every retrieval decision is explainable.

Every subsystem can evolve independently.

Every retrieval workflow remains deterministic.

Every enterprise policy is enforced.

Every consumer receives a stable API.

\-\--

# End of Chapter 6

------------------------------------------------------------------------

**🏛 Principal Architect Review (Critical Improvement)**

Now that we have the architecture overview, I want to introduce
something that I believe will become **the defining feature of EKRE**.

**The Retrieval Pipeline is Not Enough**

Most RAG systems stop here:

Query

↓

Retriever

↓

Ranking

↓

LLM

Even sophisticated enterprise systems often extend it only slightly:

Query

↓

Query Understanding

↓

Retriever

↓

Ranking

↓

Context

**I recommend a richer, enterprise-grade retrieval lifecycle.**

Instead of treating retrieval as a single pipeline, define **four
architectural domains**, each with a distinct responsibility:

┌───────────────────────────────────────────┐

│ DOMAIN 1 │

│ Query Intelligence │

│\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\--│

│ Query Understanding │

│ Query Planning │

│ Query Expansion │

│ Retrieval Profile Selection │

└───────────────────────────────────────────┘

│

▼

┌───────────────────────────────────────────┐

│ DOMAIN 2 │

│ Retrieval Execution │

│\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\--│

│ Vector Search │

│ Keyword Search │

│ Metadata Search │

│ Repository Search │

│ Future Graph Search │

└───────────────────────────────────────────┘

│

▼

┌───────────────────────────────────────────┐

│ DOMAIN 3 │

│ Retrieval Intelligence │

│\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\--│

│ Candidate Fusion │

│ Ranking │

│ Re-ranking │

│ Explainability │

│ Diversity Optimization │

└───────────────────────────────────────────┘

│

▼

┌───────────────────────────────────────────┐

│ DOMAIN 4 │

│ Context Engineering │

│\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\--│

│ Context Assembly │

│ Token Budgeting │

│ Citation Mapping │

│ Provenance │

│ Output Packaging │

└───────────────────────────────────────────┘

**Why This Is Better**

This domain-driven architecture provides several advantages:

- It maps directly to product capabilities, making ownership and
  evolution clearer.

- New retrieval methods (graph search, multimodal search, SQL search)
  fit naturally into the **Retrieval Execution** domain without
  affecting Query Intelligence or Context Engineering.

- Advanced ranking techniques, explainability, and personalization can
  evolve within the **Retrieval Intelligence** domain independently.

- Context packaging becomes a dedicated engineering concern, allowing
  optimization for different downstream consumers while still remaining
  within EKRE\'s responsibility.

------------------------------------------------------------------------

**📘 Handbook Status**

We have now completed:

**Volume I --- Product Foundation**

- ✅ Chapters 1--5

**Volume II --- Enterprise Retrieval Architecture**

- ✅ Chapter 6 --- Enterprise Retrieval Architecture Overview

**Next Chapters**

1.  **Chapter 7 --- End-to-End Query Lifecycle** *(the single most
    important workflow in EKRE)*

2.  Chapter 8 --- Query Intelligence Domain

3.  Chapter 9 --- Query Understanding Engine

4.  Chapter 10 --- Query Planner

5.  Chapter 11 --- Retrieval Execution Domain

**Product Manager Decision**

I recommend we adopt the **four-domain architecture** as the official
EKRE structure before designing any individual engine. It provides a
cleaner separation of responsibilities than a simple pipeline, scales
well for enterprise features, and gives us a robust foundation for the
rest of the handbook. This will make the subsequent chapters more
coherent and extensible.

Excellent. We have now reached what I believe is **the most important
chapter in the entire EKRE handbook**.

As the Product Manager and Principal Architect, I would say:

**If Chapter 7 is designed correctly, almost every remaining chapter
becomes straightforward.**

Everything in EKRE revolves around one concept:

**The Query Lifecycle**

Unlike EKIE, where the lifecycle was **Document → Markdown → Chunk →
Embedding → Publish**, EKRE transforms a **query** into a **trusted
retrieval context**.

This chapter becomes the **reference workflow** for the entire product.
Every subsystem, API, metric, log, and test case will trace back to this
lifecycle.

One improvement over our earlier outline: instead of a simple sequence,
we\'ll model the lifecycle as a **state machine**. This is more suitable
for retries, observability, distributed execution, and debugging.

------------------------------------------------------------------------

# Chapter 7 - End-to-End Query Lifecycle

\-\--

# 7.1 Purpose

The Query Lifecycle defines the canonical execution flow of every
retrieval request processed by the Enterprise Knowledge Retrieval Engine
(EKRE).

Regardless of:

\- Consumer

\- Query Type

\- Retrieval Strategy

\- Repository

\- Ranking Algorithm

\- Deployment Model

every retrieval request shall follow the lifecycle defined in this
chapter.

This lifecycle becomes the architectural backbone of EKRE.

\-\--

# 7.2 Design Philosophy

A retrieval request is not a database query.

It is a workflow.

Each stage progressively transforms an unstructured request into an
explainable, policy-compliant, and optimized retrieval result.

Each stage has:

\- Defined input

\- Defined output

\- Defined responsibilities

\- Observable metrics

\- Failure handling

\- Retry policy

No stage performs responsibilities owned by another stage.

\-\--

# 7.3 Canonical Query Lifecycle

\`\`\`

Client Request

↓

Authentication

↓

Authorization

↓

Query Registration

↓

Query Understanding

↓

Query Planning

↓

Retrieval Strategy Selection

↓

Parallel Retrieval Execution

↓

Candidate Collection

↓

Candidate Normalization

↓

Candidate Fusion

↓

Policy Validation

↓

Ranking

↓

Re-ranking (Optional)

↓

Context Assembly

↓

Response Packaging

↓

Observability Finalization

↓

API Response

\`\`\`

This becomes the official retrieval workflow for EKRE Version 1.0.

\-\--

# 7.4 Lifecycle State Machine

Every query transitions through well-defined execution states.

\`\`\`

NEW

↓

REGISTERED

↓

UNDERSTANDING

↓

PLANNED

↓

EXECUTING

↓

COLLECTING

↓

FUSING

↓

RANKING

↓

ASSEMBLING

↓

COMPLETED

\`\`\`

Failure transitions:

\`\`\`

EXECUTING

↓

PARTIAL_FAILURE

↓

DEGRADED

↓

COMPLETED

\`\`\`

or

\`\`\`

ANY STATE

↓

FAILED

\`\`\`

This state machine enables deterministic execution, replay, and
diagnostics.

\-\--

# 7.5 Stage 1 --- Query Registration

Purpose:

Create an immutable record for every retrieval request.

Responsibilities:

\- Generate Query ID

\- Capture timestamp

\- Identify requesting consumer

\- Record API version

\- Initialize execution trace

Output:

Query Context Object (QCO)

\-\--

# 7.6 Query Context Object (QCO)

The Query Context Object is the internal data structure that accompanies
the query throughout its lifecycle.

It contains:

\`\`\`

Query ID

Original Query

Normalized Query

Consumer Information

Identity

Retrieval Profile

Execution Plan

Candidate Set

Ranking Scores

Retrieval Context Package

Trace Information

Timing Information

Errors

Warnings

\`\`\`

Every stage enriches the same Query Context Object rather than creating
isolated structures.

This provides complete lifecycle traceability.

\-\--

# 7.7 Stage 2 --- Query Understanding

Input:

Original query.

Responsibilities:

\- Normalize text

\- Detect language

\- Detect intent

\- Extract entities

\- Identify filters

\- Expand terminology

\- Resolve acronyms

Output:

Structured Query Model (SQM)

No retrieval occurs at this stage.

\-\--

# 7.8 Stage 3 --- Query Planning

Input:

Structured Query Model.

Responsibilities:

\- Select Retrieval Profile

\- Select Retrieval Engines

\- Configure search parameters

\- Determine candidate limits

\- Configure ranking policy

Output:

Execution Plan

The execution plan becomes immutable after approval.

\-\--

# 7.9 Stage 4 --- Retrieval Strategy Selection

The planner determines which retrieval mechanisms participate.

Possible strategies:

\- Vector Search

\- Keyword Search

\- Metadata Search

\- Repository Search

\- Graph Search (Future)

\- Domain-specific plugins

Not every query requires every strategy.

\-\--

# 7.10 Stage 5 --- Parallel Retrieval Execution

Selected retrieval engines execute concurrently.

Each engine is isolated.

Each engine returns standardized candidate objects.

Failures remain isolated.

The orchestrator continues whenever possible.

\-\--

# 7.11 Standard Candidate Object (SCO)

Every retrieval engine produces the same output contract.

\`\`\`

Candidate ID

Document ID

Chunk ID

Repository

Retrieval Source

Raw Score

Metadata

Security Labels

Version

Language

Provenance

\`\`\`

This standardization allows downstream components to remain
engine-agnostic.

\-\--

# 7.12 Stage 6 --- Candidate Collection

Responsibilities:

\- Aggregate candidates

\- Preserve provenance

\- Record retrieval engine

\- Maintain retrieval statistics

No ranking occurs here.

Collection simply aggregates results.

\-\--

# 7.13 Stage 7 --- Candidate Normalization

Different retrieval engines produce different scoring systems.

Normalization converts all scores into a common scale.

Examples:

\- Cosine similarity

\- BM25

\- Metadata confidence

\- Rule-based confidence

After normalization:

Every candidate becomes comparable.

\-\--

# 7.14 Stage 8 --- Candidate Fusion

Multiple engines may return identical knowledge.

Fusion responsibilities:

\- Merge duplicates

\- Preserve provenance

\- Combine confidence

\- Preserve engine contributions

\- Record fusion decisions

No ranking logic belongs here.

Fusion produces a unified candidate pool.

\-\--

# 7.15 Stage 9 --- Policy Validation

Before ranking begins:

Every candidate undergoes policy evaluation.

Policies include:

\- Security

\- Repository permissions

\- Metadata restrictions

\- Document lifecycle

\- Compliance

Unauthorized candidates are removed.

They never participate in ranking.

\-\--

# 7.16 Stage 10 --- Ranking

Input:

Validated candidate pool.

Ranking evaluates:

\- Semantic similarity

\- Keyword relevance

\- Metadata relevance

\- Freshness

\- Repository trust

\- Retrieval profile

\- Business rules

Output:

Ordered candidate list.

\-\--

# 7.17 Stage 11 --- Re-ranking

Optional stage.

Applied when:

\- Cross-encoder models

\- LLM rerankers

\- Domain-specific ranking

\- Learning-to-rank

are enabled.

This stage improves ordering but never introduces new candidates.

\-\--

# 7.18 Stage 12 --- Context Assembly

Responsibilities:

\- Select final chunks

\- Preserve logical ordering

\- Maintain citations

\- Build token-aware context

\- Group related chunks

\- Preserve provenance

Output:

Enterprise Retrieval Context Package (ECP)

\-\--

# 7.19 Enterprise Retrieval Context Package (ECP)

This is the official output of EKRE.

Contents include:

\`\`\`

Query Metadata

Retrieved Context

Chunk References

Document References

Citations

Retrieval Scores

Ranking Explanations

Security Metadata

Execution Summary

\`\`\`

This package is intentionally model-agnostic.

EKRE produces retrieval context, not prompts.

\-\--

# 7.20 Stage 13 --- Response Packaging

Transform the Enterprise Retrieval Context Package into the response format
requested by the consumer.

Examples:

\- JSON

\- Streaming payload

\- REST response

\- gRPC message

Packaging never modifies retrieval decisions.

\-\--

# 7.21 Stage 14 --- Observability Finalization

Finalize execution telemetry.

Capture:

\- Total latency

\- Stage latency

\- Retrieval engines used

\- Candidate counts

\- Ranking metrics

\- Errors

\- Warnings

\- Execution trace

This enables complete operational visibility.

\-\--

# 7.22 Failure Handling

Every stage defines failure behavior.

Possible outcomes:

COMPLETE_SUCCESS

PARTIAL_SUCCESS

DEGRADED_SUCCESS

FAILED

Partial failures should degrade gracefully whenever possible.

\-\--

# 7.23 Lifecycle Guarantees

Every completed query guarantees:

✓ Traceable execution

✓ Deterministic workflow

✓ Policy-compliant retrieval

✓ Explainable ranking

✓ Standardized output

✓ Observable execution

\-\--

# 7.24 Architecture Rules

The lifecycle enforces several architectural rules:

\- No stage may skip another mandatory stage.

\- Every stage receives and returns the Query Context Object.

\- Every mutation to the Query Context Object must be versioned within
the execution trace.

\- Retrieval engines must never modify ranking results directly.

\- Ranking engines must never bypass policy validation.

\- Context Assembly must never change candidate ordering.

\- Response Packaging must never alter retrieval semantics.

These rules preserve architectural integrity and make the execution
pipeline predictable and testable.

\-\--

# End of Chapter 7

------------------------------------------------------------------------

**🏛 Principal Architect Review (Major Architectural Enhancement)**

This chapter is already strong, but before freezing it I would introduce
**three foundational runtime objects** that will become the canonical
data contracts throughout EKRE.

Instead of relying on loosely defined structures, every subsystem should
exchange these immutable domain objects:

  ------------------------------------------------------------------------
  **Object**           **Owner**      **Purpose**
  -------------------- -------------- ------------------------------------
  **Query Context      Runtime        The evolving execution context
  Object (QCO)**                      carried through the entire
                                      lifecycle.

  **Structured Query   Query          The normalized, intent-aware
  Model (SQM)**        Intelligence   representation of the incoming
                                      query.

  **Enterprise Context Context        The final retrieval artifact
  Package (ECP)**      Engineering    returned to consumers.
  ------------------------------------------------------------------------

This gives EKRE a clean **Domain-Driven Design (DDD)** foundation. Every
subsequent chapter can now define its inputs and outputs using these
three contracts, making interfaces explicit and reducing coupling.

------------------------------------------------------------------------

**📚 Handbook Progress**

**Volume I --- Product Foundation**

- ✅ Chapters 1--5

**Volume II --- Enterprise Retrieval Architecture**

- ✅ Chapter 6 --- Enterprise Retrieval Architecture Overview

- ✅ **Chapter 7 --- End-to-End Query Lifecycle**

**Next Chapters**

We now begin designing the actual subsystems, one domain at a time:

1.  **Chapter 8 --- Query Intelligence Domain** *(domain architecture)*

2.  Chapter 9 --- Query Understanding Engine

3.  Chapter 10 --- Query Planner

4.  Chapter 11 --- Retrieval Profile Manager *(new, extracted from the
    planner)*

5.  Chapter 12 --- Retrieval Execution Domain

**Product Manager Recommendation**

Compared to our initial plan, I recommend introducing a dedicated
**Retrieval Profile Manager** as its own subsystem rather than embedding
profile selection entirely within the Query Planner. This keeps the
planner focused on execution strategy while allowing retrieval profiles
(Precision, Recall, Compliance, Balanced, Performance, and future custom
profiles) to evolve independently through configuration and policy,
without changing planning logic. This separation will make EKRE more
extensible for enterprise deployments.

Excellent. This is exactly where EKRE starts becoming an enterprise
platform instead of a traditional RAG retriever.

Before writing Chapter 8, I want to make one architectural improvement.

# Chapter 8 - Query Intelligence Domain

\-\--

# 8.1 Purpose

The Query Intelligence Domain is responsible for transforming an
unstructured retrieval request into an optimized execution plan.

It represents the \"brain\" of EKRE.

Unlike retrieval engines, which search knowledge repositories, the Query
Intelligence Domain determines \*\*how\*\* retrieval should occur.

It performs no retrieval itself.

Instead, it prepares the query for downstream execution.

\-\--

# 8.2 Responsibilities

The Query Intelligence Domain owns five major capabilities.

1\. Query Understanding

2\. Intent Classification

3\. Query Enrichment

4\. Retrieval Profile Selection

5\. Query Planning

Collectively these capabilities convert raw user input into an optimized
retrieval strategy.

\-\--

# 8.3 Design Principles

The Query Intelligence Domain follows several architectural principles.

### Principle 1

No retrieval occurs inside this domain.

\-\--

### Principle 2

Every component is deterministic.

\-\--

### Principle 3

Each engine has a single responsibility.

\-\--

### Principle 4

Outputs are immutable.

Each engine produces a new version of the Structured Query Model (SQM)
rather than modifying previous stages in place.

\-\--

### Principle 5

Execution decisions are explainable.

Every transformation performed within the domain must be recorded.

\-\--

# 8.4 Domain Architecture

\`\`\`

Raw Query

│

▼

Query Understanding

│

▼

Intent Classification

│

▼

Query Enrichment

│

▼

Retrieval Profile Manager

│

▼

Query Planner

│

▼

Execution Plan

\`\`\`

\-\--

# 8.5 Component Responsibilities

## Query Understanding

Responsible for:

\- Normalization

\- Language detection

\- Token cleanup

\- Acronym expansion

\- Entity extraction

Produces:

Structured Query Model v1

\-\--

## Intent Classification

Responsible for:

\- Detecting retrieval intent

\- Determining search behavior

\- Estimating recall vs precision needs

Produces:

Structured Query Model v2

\-\--

## Query Enrichment

Responsible for:

\- Synonym expansion

\- Ontology expansion

\- Business vocabulary mapping

\- Domain terminology resolution

Produces:

Structured Query Model v3

\-\--

## Retrieval Profile Manager

Responsible for selecting:

\- Precision Profile

\- Recall Profile

\- Balanced Profile

\- Compliance Profile

\- Performance Profile

\- Custom Enterprise Profiles

Produces:

Retrieval Configuration

\-\--

## Query Planner

Responsible for:

\- Selecting retrieval engines

\- Building execution graphs

\- Configuring retrieval limits

\- Determining parallel execution

\- Selecting ranking policies

Produces:

Execution Plan

\-\--

# 8.6 Domain Inputs

The domain accepts:

\- Raw Query

\- Consumer Identity

\- User Context

\- Metadata Filters

\- Configuration

\- Enterprise Policies

\-\--

# 8.7 Domain Outputs

The domain produces:

\- Structured Query Model

\- Retrieval Profile

\- Execution Plan

\- Explainability Metadata

No retrieval results are produced here.

\-\--

# 8.8 Structured Query Model Evolution

The Structured Query Model evolves through multiple stages.

Version 0

Raw Query

↓

Version 1

Normalized Query

↓

Version 2

Intent-Aware Query

↓

Version 3

Enriched Query

↓

Version 4

Retrieval Configuration

↓

Version 5

Execution Plan

Each version is immutable and traceable.

\-\--

# 8.9 Explainability

Every transformation must be recorded.

Example:

Original Query

↓

Normalization Applied

↓

Intent Classified

↓

Ontology Expanded

↓

Profile Selected

↓

Planner Decision

This chain becomes part of the execution trace.

\-\--

# 8.10 Failure Handling

Failures within one engine should not necessarily terminate the
pipeline.

Examples:

Ontology unavailable

↓

Continue without enrichment

Intent confidence low

↓

Use Balanced Profile

Language detection fails

↓

Default language

Graceful degradation is preferred.

\-\--

# 8.11 Performance Objectives

Illustrative latency targets:

\| Component \| Target \|

\|\-\-\-\-\-\-\-\-\-\--\|\-\-\-\-\-\-\--\|

\| Query Understanding \| \<20 ms \|

\| Intent Classification \| \<15 ms \|

\| Query Enrichment \| \<30 ms \|

\| Profile Selection \| \<5 ms \|

\| Query Planner \| \<10 ms \|

Total Query Intelligence latency target:

\<80 ms

\-\--

# 8.12 Design Rules

The Query Intelligence Domain must never:

\- Access vector databases

\- Rank candidates

\- Assemble context

\- Retrieve documents

Its sole responsibility is deciding \*\*how\*\* retrieval should be
executed.

\-\--

# 8.13 Success Criteria

The Query Intelligence Domain is successful when:

✓ Queries are correctly interpreted.

✓ Retrieval intent is accurately classified.

✓ Domain terminology is understood.

✓ Appropriate retrieval profiles are selected.

✓ Execution plans are deterministic.

✓ Decisions are explainable.

\-\--

# End of Chapter 8

------------------------------------------------------------------------

**🏛 Principal Architect Review (Major Improvement)**

Before freezing Chapter 8, I would introduce an additional concept that
elevates EKRE beyond most enterprise RAG systems:

**Add a Knowledge Awareness Engine (KAE)**

Between **Query Enrichment** and **Retrieval Profile Manager**, insert a
lightweight decision component that consults metadata about the indexed
knowledge---not the content itself.

Its responsibilities would include:

- Determining which repositories are likely relevant.

- Detecting document domains (engineering, HR, legal, finance).

- Applying tenant, region, or business-unit constraints.

- Estimating repository confidence and freshness.

- Recommending retrieval strategies before execution.

Revised flow:

Query Understanding

↓

Intent Classification

↓

Query Enrichment

↓

Knowledge Awareness Engine

↓

Retrieval Profile Manager

↓

Query Planner

**Why this matters**

Most RAG pipelines become inefficient because they search *everything*.
By consulting lightweight knowledge metadata first, EKRE can narrow the
search space before any expensive retrieval begins. This improves
latency, reduces cost, and often increases precision without sacrificing
modularity.

------------------------------------------------------------------------

**📚 Handbook Progress**

**Volume II --- Enterprise Retrieval Architecture**

- ✅ Chapter 6 --- Enterprise Retrieval Architecture Overview

- ✅ Chapter 7 --- End-to-End Query Lifecycle

- ✅ Chapter 8 --- Query Intelligence Domain

**Next Chapters**

We now move from the domain level to the engine level:

1.  **Chapter 9 --- Query Understanding Engine** (deep technical design)

2.  Chapter 10 --- Intent Classification Engine

3.  Chapter 11 --- Query Enrichment Engine

4.  Chapter 12 --- Knowledge Awareness Engine

5.  Chapter 13 --- Retrieval Profile Manager

6.  Chapter 14 --- Query Planner

**Product Manager Recommendation**

I recommend expanding the original plan to include the **Knowledge
Awareness Engine** and splitting the Query Intelligence Domain into
dedicated engines. This gives EKRE a cleaner, domain-driven
architecture, improves extensibility, and creates clear ownership
boundaries for engineering teams while keeping retrieval decisions
explainable and performant.

Excellent. We are now entering the component-level architecture.

This is where I want to change our methodology compared to most RAG
documentation.

**Product Manager + Principal Architect Review**

Most documentation says:

Query

↓

Normalize

↓

Remove Stopwords

↓

Embedding

↓

Search

That is **far too simplistic** for an enterprise retrieval engine.

Instead, every engine should be documented like a micro-product.

For every engine we should define:

1.  Purpose

2.  Responsibilities

3.  Inputs

4.  Outputs

5.  Internal Pipeline

6.  State Changes

7.  Data Contracts

8.  Configuration

9.  Extension Points

10. Failure Handling

11. Performance Targets

12. Observability

13. APIs

14. Sequence Diagram

15. Future Roadmap

This means every engine becomes independently implementable.

------------------------------------------------------------------------

# Chapter 9 - Query Understanding Engine

\-\--

# 9.1 Purpose

The Query Understanding Engine (QUE) is the first execution engine
within the Query Intelligence Domain.

Its responsibility is to transform an unstructured user query into a
clean, normalized, structured representation suitable for downstream
semantic interpretation.

The engine does \*\*not\*\* determine retrieval intent.

The engine does \*\*not\*\* select retrieval strategies.

The engine performs linguistic and structural preprocessing only.

\-\--

# 9.2 Objectives

The Query Understanding Engine shall:

✓ Normalize user input

✓ Detect language

✓ Correct malformed text

✓ Resolve enterprise abbreviations

✓ Extract entities

✓ Extract metadata constraints

✓ Produce deterministic outputs

\-\--

# 9.3 Responsibilities

The engine owns only the following responsibilities:

• Query normalization

• Unicode normalization

• Character cleanup

• Language identification

• Enterprise acronym resolution

• Entity extraction

• Metadata extraction

• Date extraction

• Numeric extraction

• Basic syntax validation

Everything else belongs to downstream engines.

\-\--

# 9.4 Inputs

The engine receives:

Raw Query

Consumer Metadata

Identity Context

Tenant Information

Optional User Locale

Optional Preferred Language

Configuration

Enterprise Dictionary

Ontology Cache

\-\--

# 9.5 Outputs

The engine produces:

Structured Query Model (SQM v1)

The SQM contains:

\`\`\`

query_id

original_query

normalized_query

detected_language

detected_entities

metadata_filters

enterprise_terms

dates

numbers

warnings

confidence_scores

\`\`\`

\-\--

# 9.6 Internal Processing Pipeline

The Query Understanding Engine executes the following pipeline.

\`\`\`

Raw Query

↓

Input Validation

↓

Unicode Normalization

↓

Whitespace Normalization

↓

Character Cleanup

↓

Language Detection

↓

Spell Correction

↓

Enterprise Dictionary Resolution

↓

Acronym Expansion

↓

Entity Recognition

↓

Metadata Extraction

↓

Date Recognition

↓

Number Recognition

↓

SQM Construction

\`\`\`

Each stage performs exactly one transformation.

\-\--

# 9.7 Processing Stage Details

\-\--

## Stage 1

Input Validation

Responsibilities

• Empty query detection

• Maximum length validation

• Illegal character detection

Output

Validated query

\-\--

## Stage 2

Unicode Normalization

Purpose

Normalize Unicode representations.

Examples

Curly quotes

↓

Standard quotes

Unicode variants

↓

Canonical representation

\-\--

## Stage 3

Whitespace Normalization

Examples

Multiple spaces

↓

Single spaces

Tabs

↓

Spaces

Newlines

↓

Normalized separators

\-\--

## Stage 4

Character Cleanup

Remove

Invisible characters

Control characters

Unsupported Unicode

Repeated punctuation

Normalize punctuation

\-\--

## Stage 5

Language Detection

Supported languages configurable.

Produces

Language Code

Confidence

Fallback Language

\-\--

## Stage 6

Spell Correction

Optional.

Configuration driven.

Enterprise dictionary preferred over general dictionary.

Example

\"Kubernets\"

↓

\"Kubernetes\"

\-\--

## Stage 7

Enterprise Dictionary Resolution

Enterprise terminology

Examples

HRMS

↓

Human Resource Management System

EKIE

↓

Enterprise Knowledge Ingestion Engine

\-\--

## Stage 8

Acronym Expansion

Enterprise-specific abbreviations.

Examples

SOP

API

IAM

RAG

Each expansion recorded.

\-\--

## Stage 9

Named Entity Recognition

Detect

Products

Projects

Teams

Repositories

Applications

Departments

Document Types

Versions

Regions

Organizations

\-\--

## Stage 10

Metadata Extraction

Recognize filters embedded in natural language.

Examples

\"latest\"

↓

Document Version

\"finance\"

↓

Department

\"after 2024\"

↓

Date Filter

\"approved\"

↓

Approval Status

\-\--

## Stage 11

Temporal Understanding

Extract

Dates

Ranges

Relative dates

Fiscal periods

\-\--

## Stage 12

Numeric Extraction

Examples

Top 10

Version 2

ISO 9001

RFC 9110

\-\--

## Stage 13

SQM Construction

Build immutable Structured Query Model.

Version:

SQM v1

\-\--

# 9.8 Internal State Machine

\`\`\`

RECEIVED

↓

VALIDATED

↓

NORMALIZED

↓

LANGUAGE_IDENTIFIED

↓

ENRICHED

↓

STRUCTURED

↓

COMPLETED

\`\`\`

Failure

↓

FAILED

\-\--

# 9.9 Configuration

Configuration options include:

Enable Spell Correction

Enable Acronym Expansion

Enable Entity Extraction

Enable Metadata Extraction

Supported Languages

Enterprise Dictionary Version

Confidence Thresholds

Fallback Language

\-\--

# 9.10 Explainability

Every transformation produces an audit record.

Example

\`\`\`

Original Query

↓

Removed Extra Spaces

↓

Expanded Acronym

↓

Detected Language

↓

Extracted Entity

↓

Extracted Metadata

↓

Generated SQM

\`\`\`

This chain becomes part of the Query Trace.

\-\--

# 9.11 Failure Handling

Examples

Dictionary unavailable

↓

Continue

NER unavailable

↓

Continue

Language detection fails

↓

Default language

Spell correction timeout

↓

Continue

The engine prefers graceful degradation.

\-\--

# 9.12 Performance Targets

Illustrative targets:

Input Validation

\<2 ms

Normalization

\<5 ms

Language Detection

\<10 ms

Entity Recognition

\<20 ms

Metadata Extraction

\<10 ms

Total Engine

\<50 ms

\-\--

# 9.13 Observability

Metrics

Normalization Time

NER Time

Language Detection Time

Dictionary Lookup Time

SQM Generation Time

Trace

Every stage emits structured events.

\-\--

# 9.14 Extension Points

Future plugins may include:

OCR Query Cleanup

Voice Query Normalization

Multilingual Translation

Domain-specific NER Models

PII Detection

Medical Terminology Packs

Legal Terminology Packs

\-\--

# 9.15 API Contract

Input

Raw Query Context Object

Output

Structured Query Model v1

The engine exposes only internal service interfaces.

External consumers never invoke this engine directly.

\-\--

# 9.16 Sequence Diagram

\`\`\`

Client

↓

Query Intelligence

↓

Query Understanding Engine

↓

SQM v1

↓

Intent Engine

\`\`\`

\-\--

# 9.17 Architecture Rules

The Query Understanding Engine SHALL NOT:

Perform retrieval

Access vector databases

Rank candidates

Select retrieval profiles

Build execution plans

Assemble context

Generate prompts

Call LLMs for response generation

Its responsibility ends with producing a high-quality SQM v1.

\-\--

# End of Chapter 9

------------------------------------------------------------------------

**🏛 Principal Architect Review (Important Design Improvement)**

This is where I would introduce a concept that very few enterprise RAG
systems implement, but which will significantly improve EKRE.

**Split the Structured Query Model (SQM)**

Instead of a single evolving object, define two separate models:

**1. Linguistic Query Model (LQM)**

Owned by the Query Understanding Engine.

Contains:

- Original query

- Normalized query

- Language

- Entities

- Dates

- Numbers

- Metadata candidates

- Confidence scores

This model represents **what the user said**.

**2. Retrieval Query Model (RQM)**

Produced after the Intent Engine, Query Enrichment Engine, and Retrieval
Profile Manager.

Contains:

- Retrieval intent

- Selected profile

- Expanded terms

- Filters

- Repository hints

- Execution preferences

This model represents **how EKRE intends to retrieve information**.

**Why this separation matters**

It avoids mixing linguistic analysis with retrieval decisions, resulting
in:

- Cleaner boundaries

- Easier testing

- Better explainability

- Reusable linguistic processing

- Independent evolution of retrieval strategies

This is the type of separation commonly seen in large-scale compiler
design and enterprise workflow engines, and it fits naturally into
EKRE\'s domain-driven architecture.

------------------------------------------------------------------------

**📚 Updated Roadmap**

We now have:

**Query Intelligence Domain**

- ✅ Chapter 8 --- Domain Architecture

- ✅ Chapter 9 --- Query Understanding Engine

**Remaining Components**

- ⏳ Chapter 10 --- Intent Classification Engine

- ⏳ Chapter 11 --- Query Enrichment Engine

- ⏳ Chapter 12 --- Knowledge Awareness Engine

- ⏳ Chapter 13 --- Retrieval Profile Manager

- ⏳ Chapter 14 --- Query Planner

At this point, the Query Intelligence Domain will be fully specified,
providing a complete blueprint before we move into the Retrieval
Execution Domain. This disciplined approach ensures each subsystem has a
well-defined responsibility, clear interfaces, and complete
traceability.

Excellent. Before continuing, I want to make a product architecture
decision.

------------------------------------------------------------------------

**🏛 Principal Architect Review**

After reviewing Chapter 9, I think we should **slightly redesign the
Query Intelligence Domain** before moving forward.

Originally we had:

Query Understanding

↓

Intent Classification

↓

Query Enrichment

↓

Knowledge Awareness

↓

Retrieval Profile

↓

Query Planner

After designing the Query Understanding Engine in detail, I think we are
still missing an important enterprise capability.

**Missing Component**

**Query Validation Engine**

Most enterprise retrieval failures occur **before retrieval begins**.

Examples:

Empty query

\"show\"

\"latest\"

\"policy\"

\"asdfgh\"

\"!!!!!!\"

\"\.....\"

Traditional RAG systems simply send these to retrieval.

Instead, EKRE should determine:

- Is the query meaningful?

- Is clarification needed?

- Is there enough information?

- Should we continue?

- Should we recommend query expansion?

- Should we reject the request?

Therefore the architecture becomes:

Query Intelligence Domain

Raw Query

↓

Query Validation

↓

Query Understanding

↓

Intent Classification

↓

Query Enrichment

↓

Knowledge Awareness

↓

Retrieval Profile

↓

Query Planner

↓

Execution Plan

This dramatically improves retrieval quality.

------------------------------------------------------------------------

### 9.X Expected EKIE Publishing Schema (Dependency)

**Integration Contract:** EKRE assumes all knowledge vectors consumed from the vector database strictly adhere to the EKIE Publishing Payload Schema. If EKIE changes this schema without coordination, EKRE hybrid retrieval and metadata filtering will fail.

Required fields from EKIE: `document_id`, `chunk_id`, `content`, `classification`, `tenant_id`.

### 9.Y Embedding Model Dependency

**Integration Contract:** The embedding model used by EKRE for Query Vectorization must perfectly match the model used by EKIE for Document Vectorization. EKRE relies on the `EmbeddingModelChanged` and `EmbeddingReprocessingCompleted` events from EKIE's Control Plane to manage transition states.

# Chapter 10 - Intent Classification Engine

\-\--

# 10.1 Purpose

The Intent Classification Engine (ICE) determines \*\*why\*\* the user
is performing a retrieval.

Unlike the Query Understanding Engine, which analyzes the linguistic
structure of the query, the Intent Classification Engine analyzes the
user\'s objective.

The output of this engine influences every downstream architectural
decision.

It determines:

\- Retrieval strategy

\- Candidate limits

\- Ranking strategy

\- Context size

\- Retrieval profile

\- Future query optimization

The engine never performs retrieval.

\-\--

# 10.2 Objectives

The Intent Classification Engine shall:

✓ Identify retrieval intent

✓ Estimate search complexity

✓ Predict retrieval behavior

✓ Recommend retrieval profile

✓ Estimate recall requirements

✓ Estimate precision requirements

✓ Produce deterministic classifications

\-\--

# 10.3 Responsibilities

The engine is responsible for:

• Intent Classification

• Query Complexity Estimation

• Search Behavior Prediction

• Confidence Estimation

• Multi-intent Detection

• Intent Explainability

It is NOT responsible for retrieval planning.

\-\--

# 10.4 Inputs

Input:

Linguistic Query Model (LQM)

Containing:

\- Normalized Query

\- Language

\- Entities

\- Metadata

\- Dates

\- Numbers

\- Enterprise Terms

\-\--

# 10.5 Outputs

Retrieval Query Model (RQM v1)

Containing:

Intent

Intent Confidence

Complexity

Retrieval Objective

Expected Recall

Expected Precision

Suggested Retrieval Profile

Suggested Candidate Count

Warnings

\-\--

# 10.6 Supported Retrieval Intents

The engine supports the following enterprise intents.

\-\--

Intent 1

Exact Lookup

Examples

\"Travel Policy\"

\"VPN Guide\"

Goal

Locate one document.

\-\--

Intent 2

Navigation

Examples

\"Open latest EKIE architecture\"

Goal

Locate known artifact.

\-\--

Intent 3

Research

Examples

\"Everything related to refinery shutdown\"

Goal

Maximum coverage.

\-\--

Intent 4

Comparison

Examples

Compare EKIE and EKRE.

Goal

Retrieve balanced evidence.

\-\--

Intent 5

Discovery

Examples

Best practices for retrieval architecture.

Goal

Topic exploration.

\-\--

Intent 6

Compliance

Examples

Policies regarding GDPR.

Goal

Metadata-heavy retrieval.

\-\--

Intent 7

Analytical

Examples

Architecture changes between versions.

Goal

Relationship-aware retrieval.

\-\--

Intent 8

AI Context Retrieval

Generated internally.

Goal

Context preparation.

\-\--

# 10.7 Intent Classification Pipeline

\`\`\`

LQM

↓

Feature Extraction

↓

Intent Detection

↓

Complexity Analysis

↓

Confidence Scoring

↓

Multi-intent Resolution

↓

RQM Construction

\`\`\`

\-\--

# 10.8 Feature Extraction

Features include:

Query Length

Entity Count

Metadata Count

Question Type

Action Verbs

Temporal References

Comparative Words

Repository References

Business Vocabulary

Document Types

\-\--

# 10.9 Query Complexity Estimation

Every query receives a complexity score.

Levels:

LOW

MEDIUM

HIGH

VERY HIGH

Factors:

Number of entities

Number of filters

Cross-domain references

Repository diversity

Semantic ambiguity

Expected retrieval breadth

\-\--

# 10.10 Confidence Scoring

Intent confidence ranges:

0.0 → 1.0

Example

Lookup

0.97

Research

0.82

Comparison

0.76

Low confidence may trigger:

Balanced Profile

or downstream clarification policies.

\-\--

# 10.11 Multi-intent Detection

Example

\"Compare EKIE ingestion architecture with latest EKRE retrieval
design.\"

Contains:

Comparison

\+

Navigation

\+

Research

The engine produces:

Primary Intent

Secondary Intent(s)

Priority Order

Confidence

\-\--

# 10.12 Explainability

Every decision records:

Detected features

Classification model version

Confidence

Alternative intents

Reason selected

Rejected intents

\-\--

# 10.13 Failure Handling

If intent classification fails:

↓

Balanced Profile

↓

Continue execution

If confidence is below configured threshold:

↓

Mark query as ambiguous

↓

Allow downstream planner to apply conservative defaults

The engine should fail gracefully rather than block retrieval.

\-\--

# 10.14 Performance Targets

Illustrative targets:

Feature Extraction

\<5 ms

Intent Detection

\<10 ms

Complexity Estimation

\<5 ms

Confidence Scoring

\<5 ms

Total Engine

\<25 ms

\-\--

# 10.15 Configuration

Configurable parameters include:

Supported Intent Types

Confidence Thresholds

Default Intent

Fallback Retrieval Profile

Feature Weights

Complexity Thresholds

Custom Enterprise Intents

\-\--

# 10.16 Observability

Metrics emitted:

Intent Distribution

Intent Confidence

Ambiguous Query Rate

Multi-intent Rate

Classification Latency

Fallback Rate

These metrics help product teams continuously improve retrieval
behavior.

\-\--

# 10.17 Extension Points

Future enhancements:

Learning-to-Classify

Domain-specific Intent Models

Industry Packs

Multilingual Intent Models

User Behavior Feedback

Personalized Intent Prediction

\-\--

# 10.18 Architecture Rules

The Intent Classification Engine SHALL NOT:

Perform retrieval

Expand queries

Select repositories

Rank candidates

Build execution plans

Access vector databases

Its responsibility ends with producing Retrieval Query Model v1.

\-\--

# End of Chapter 10

------------------------------------------------------------------------

**🏛 Principal Architect Review (Major Improvement)**

After completing this chapter, I would introduce another concept that is
rarely implemented but extremely valuable in enterprise retrieval.

**Intent Taxonomy**

Instead of using only **one intent label**, define **three orthogonal
dimensions**.

**Dimension 1 --- Retrieval Objective**

- Lookup

- Research

- Discovery

- Comparison

- Navigation

**Dimension 2 --- Retrieval Breadth**

- Narrow

- Focused

- Broad

- Exhaustive

**Dimension 3 --- Retrieval Urgency**

- Interactive

- Background

- Batch

This multidimensional taxonomy is more expressive than a single intent
label.

For example:

  ------------------------------------------------------------------------------------
  **Query**                                **Objective**   **Breadth**   **Urgency**
  ---------------------------------------- --------------- ------------- -------------
  \"Open VPN policy\"                      Navigation      Narrow        Interactive

  \"Compare EKIE vs EKRE\"                 Comparison      Focused       Interactive

  \"Find every refinery shutdown document  Research        Exhaustive    Background
  from 2020--2025\"                                                      
  ------------------------------------------------------------------------------------

The **Query Planner** can then make more informed decisions:

- Parallelism

- Candidate limits

- Cache usage

- Timeout policies

- Ranking strategies

- Retrieval profile selection

------------------------------------------------------------------------

**📚 Progress**

**Query Intelligence Domain**

- ✅ Chapter 8 --- Query Intelligence Domain

- ✅ Chapter 9 --- Query Understanding Engine

- ✅ Chapter 10 --- Intent Classification Engine

**Remaining**

- ⏳ Chapter 11 --- Query Enrichment Engine

- ⏳ Chapter 12 --- Knowledge Awareness Engine

- ⏳ Chapter 13 --- Retrieval Profile Manager

- ⏳ Chapter 14 --- Query Planner

At this point, the Query Intelligence Domain is evolving into a
fully-fledged enterprise subsystem rather than a simple preprocessing
stage. By the time we complete Chapter 14, it will provide a
comprehensive blueprint that engineering teams can implement as
independent, testable services with well-defined interfaces.

Excellent. Now we are moving into what I consider **the intelligence
multiplier** of EKRE.

If the **Query Understanding Engine** understands **what the user
typed**, and the **Intent Classification Engine** understands **why the
user is asking**, then the next question is:

**\"How can we improve this query before searching?\"**

This is the responsibility of the **Query Enrichment Engine (QEE).**

------------------------------------------------------------------------

**🏛 Principal Architect Review (Before Chapter 11)**

Before writing the chapter, I want to improve the architecture.

Most RAG systems perform something like this:

Query

↓

Embedding

↓

Search

Slightly better systems do:

Query

↓

Synonym Expansion

↓

Embedding

Enterprise retrieval is much richer.

A query can be enriched using **multiple independent knowledge
sources**, each contributing a different perspective.

Instead of one monolithic enrichment step, I recommend modeling
enrichment as a **pipeline of pluggable enrichers**.

Query Enrichment Engine

LQM + Intent

│

┌──────────────┬────────────┬──────────────┬──────────────┐

▼ ▼ ▼ ▼

Enterprise Ontology Synonym Acronym

Dictionary Resolver Expander Resolver

│ │ │ │

└──────────────┼────────────┼──────────────┘

▼

Domain Terminology

Enrichment

▼

Repository Hints

▼

Metadata Expansion

▼

Retrieval Query Model v2

Each enricher:

- Has one responsibility.

- Can be enabled or disabled.

- Can execute in parallel.

- Can be replaced independently.

This is significantly more scalable than a single enrichment module.

------------------------------------------------------------------------

# Chapter 11 - Query Enrichment Engine

\-\--

# 11.1 Purpose

The Query Enrichment Engine (QEE) enhances the Retrieval Query Model by
incorporating enterprise knowledge, domain semantics, repository
metadata, and configurable enrichment strategies.

Unlike the Query Understanding Engine, which interprets the user\'s
language, and the Intent Classification Engine, which determines the
retrieval objective, the Query Enrichment Engine improves the query to
maximize retrieval quality.

The engine does not retrieve documents.

Its responsibility is to produce a richer and more retrieval-aware
query.

\-\--

# 11.2 Objectives

The Query Enrichment Engine shall:

✓ Improve semantic understanding.

✓ Expand enterprise terminology.

✓ Resolve domain-specific vocabulary.

✓ Add repository intelligence.

✓ Improve retrieval precision.

✓ Improve retrieval recall.

✓ Preserve explainability.

\-\--

# 11.3 Responsibilities

The engine is responsible for:

• Synonym expansion

• Ontology expansion

• Enterprise dictionary lookup

• Acronym resolution

• Domain terminology enrichment

• Metadata enrichment

• Repository hint generation

• Semantic keyword expansion

• Controlled vocabulary mapping

It shall never perform retrieval.

\-\--

# 11.4 Inputs

Input:

Retrieval Query Model (RQM v1)

Containing:

\- Intent

\- Entities

\- Metadata

\- Enterprise Terms

\- Language

\- Dates

\- Numbers

\- Retrieval Objective

\-\--

# 11.5 Outputs

Retrieval Query Model (RQM v2)

New fields include:

Expanded Terms

Resolved Synonyms

Ontology Concepts

Repository Hints

Metadata Hints

Business Vocabulary

Expansion Confidence

Enrichment Trace

\-\--

# 11.6 Internal Architecture

The engine consists of independent enrichment modules.

\`\`\`

RQM v1

│

▼

Enrichment Orchestrator

│

┌─────────────┼─────────────────────────────┐

▼ ▼ ▼ ▼

Enterprise Synonym Ontology Acronym

Dictionary Expander Resolver Resolver

│ │ │ │

└─────────────┼─────────────┼───────────────┘

▼

Metadata Enricher

▼

Repository Hint Generator

▼

RQM v2

\`\`\`

The orchestrator coordinates all enrichment plugins and merges their
outputs into a single immutable Retrieval Query Model.

\-\--

# 11.7 Enrichment Modules

## Enterprise Dictionary Resolver

Purpose:

Translate organization-specific terminology into canonical enterprise
concepts.

Example:

\`\`\`

EKIE

↓

Enterprise Knowledge Ingestion Engine

RAG

↓

Retrieval-Augmented Generation

\`\`\`

\-\--

## Synonym Expander

Purpose:

Expand terms using configurable synonym dictionaries.

Example:

\`\`\`

Manual

↓

Guide

Documentation

Instruction

\`\`\`

Expansion rules are configurable and domain-aware.

\-\--

## Ontology Resolver

Purpose:

Map query terms to concepts within an enterprise ontology.

Example:

\`\`\`

Pump

↓

Equipment

↓

Mechanical Asset

↓

Maintenance

\`\`\`

This enables semantic relationships that keyword search alone cannot
capture.

\-\--

## Acronym Resolver

Purpose:

Resolve enterprise and industry abbreviations.

Examples:

\- SOP

\- IAM

\- PLC

\- DCS

\- ERP

Each expansion is recorded for explainability.

\-\--

## Metadata Enricher

Purpose:

Infer metadata filters from the query.

Examples:

\`\`\`

Latest

↓

Version = Current

Approved

↓

Status = Approved

Engineering

↓

Department = Engineering

\`\`\`

\-\--

## Repository Hint Generator

Purpose:

Recommend repositories likely to contain relevant information.

Examples:

\`\`\`

API Specification

↓

Git Repository

Architecture Guide

↓

Confluence

HR Policy

↓

SharePoint

\`\`\`

These are hints only; the Query Planner makes the final decision.

\-\--

# 11.8 Enrichment Pipeline

\`\`\`

RQM v1

↓

Enterprise Dictionary

↓

Synonym Expansion

↓

Ontology Resolution

↓

Metadata Enrichment

↓

Repository Hints

↓

Semantic Expansion

↓

RQM v2

\`\`\`

Each stage produces a new immutable version of the Retrieval Query
Model.

\-\--

# 11.9 Explainability

Every enrichment operation records:

\- Source module

\- Original term

\- Expanded term

\- Confidence

\- Knowledge source

\- Timestamp

Example trace:

\`\`\`

\"PLC\"

↓

Enterprise Dictionary

↓

Programmable Logic Controller

↓

Ontology

↓

Industrial Automation Equipment

↓

Repository Hint

↓

Engineering Documentation

\`\`\`

\-\--

# 11.10 Failure Handling

Examples:

Ontology unavailable

↓

Continue with synonyms.

Enterprise dictionary unavailable

↓

Continue with ontology.

Repository hint service unavailable

↓

Continue without hints.

The engine degrades gracefully whenever possible.

\-\--

# 11.11 Configuration

Administrators may configure:

\- Enabled enrichers

\- Synonym dictionaries

\- Enterprise dictionaries

\- Ontology providers

\- Maximum expansion count

\- Confidence thresholds

\- Repository hint rules

Configuration changes require no code modifications.

\-\--

# 11.12 Performance Targets

Illustrative latency goals:

Enterprise Dictionary

\<10 ms

Synonym Expansion

\<5 ms

Ontology Resolution

\<20 ms

Metadata Enrichment

\<5 ms

Repository Hint Generation

\<10 ms

Total Engine

\<40 ms

\-\--

# 11.13 Observability

Metrics:

Expansion Count

Ontology Hits

Dictionary Hits

Average Confidence

Repository Hint Distribution

Enrichment Latency

Plugin Failures

These metrics support continuous tuning and optimization.

\-\--

# 11.14 Extension Points

Future plugins may include:

\- Knowledge Graph Expansion

\- Vector-based Query Expansion

\- LLM-assisted Expansion

\- Industry-specific Ontology Packs

\- Regulatory Terminology Packs

\- Personalized Vocabulary Models

Each plugin adheres to the common Enricher interface.

\-\--

# 11.15 Architecture Rules

The Query Enrichment Engine SHALL NOT:

\- Retrieve documents

\- Select retrieval engines

\- Rank candidates

\- Execute searches

\- Build execution plans

\- Modify security policies

Its responsibility ends with producing Retrieval Query Model v2.

\-\--

# End of Chapter 11

------------------------------------------------------------------------

**🏛 Principal Architect Review (Major Architectural Improvement)**

After completing this chapter, I would introduce a key abstraction that
will simplify the rest of the architecture.

**Introduce the Enrichment Plugin Framework**

Instead of embedding enrichment logic directly into the engine, define a
common interface:

interface QueryEnricher {

String name();

boolean supports(RetrievalQueryModel query);

EnrichmentResult enrich(RetrievalQueryModel query);

int priority();

}

The **Enrichment Orchestrator** becomes responsible for:

- Discovering plugins.

- Executing independent enrichers in parallel where possible.

- Respecting dependencies between enrichers (e.g., Acronym Resolution
  before Ontology Resolution).

- Merging enrichment outputs.

- Recording provenance and confidence.

- Applying conflict resolution policies.

This architecture provides several advantages:

- **Open/Closed Principle**: New enrichers can be added without
  modifying the engine.

- **Enterprise customization**: Different business units can enable
  different enrichment plugins.

- **Testing**: Each enricher can be validated independently.

- **Scalability**: Plugins can evolve separately and even be deployed
  independently in the future.

------------------------------------------------------------------------

**📚 Updated Progress**

**Query Intelligence Domain**

- ✅ Chapter 8 --- Query Intelligence Domain

- ✅ Chapter 9 --- Query Understanding Engine

- ✅ Chapter 10 --- Intent Classification Engine

- ✅ **Chapter 11 --- Query Enrichment Engine**

**Remaining**

- ⏳ Chapter 12 --- Knowledge Awareness Engine

- ⏳ Chapter 13 --- Retrieval Profile Manager

- ⏳ Chapter 14 --- Query Planner

**Product Manager Recommendation**

I recommend treating the **Enrichment Plugin Framework** as one of
EKRE\'s core extension mechanisms, alongside pluggable retrieval engines
and ranking algorithms. This design will allow enterprise customers to
incorporate organization-specific vocabularies, taxonomies, and business
rules without altering the core platform, making EKRE significantly more
adaptable and maintainable over time.

Excellent. Now we reach what I believe is **the biggest differentiator
between an enterprise retrieval platform and a traditional RAG
retriever.**

Everything we have built so far is preparing the query.

Now we need to answer another question:

**\"Before we search, what do we already know about our enterprise
knowledge?\"**

This is **NOT retrieval.**

This is **Knowledge Awareness**.

------------------------------------------------------------------------

**🏛 Principal Architect Review**

Before writing Chapter 12, I want to introduce a major architectural
refinement.

Most RAG architectures look like this:

Query

↓

Retriever

↓

Vector DB

Even enterprise RAG systems often do:

Query

↓

Metadata Filter

↓

Retriever

I don\'t think this is sufficient.

Instead, EKRE should maintain **Knowledge Intelligence** about the
indexed enterprise.

Notice the difference.

We are NOT querying documents.

We are querying **knowledge about the knowledge**.

Think of it as the equivalent of PostgreSQL\'s Query Planner reading
statistics before executing SQL.

------------------------------------------------------------------------

**Knowledge Awareness Model**

Enterprise Knowledge

↓

Knowledge Catalog

↓

Knowledge Statistics

↓

Knowledge Awareness Engine

↓

Query Planner

Instead of scanning repositories blindly, the planner first asks:

- Which repositories contain this topic?

- Which repositories are authoritative?

- Which repositories are stale?

- Which repositories are restricted?

- Which repositories have low confidence?

- Which repositories are currently unavailable?

- Which repositories contain the newest versions?

This dramatically improves performance.

------------------------------------------------------------------------

# Chapter 12 - Knowledge Awareness Engine (KAE)

\-\--

# 12.1 Purpose

The Knowledge Awareness Engine (KAE) provides enterprise-wide
intelligence about indexed knowledge assets.

Unlike retrieval engines, the KAE never retrieves document content.

Instead, it provides metadata-driven recommendations that help the Query
Planner make optimal retrieval decisions.

The KAE transforms enterprise knowledge statistics into retrieval
intelligence.

\-\--

# 12.2 Why the Knowledge Awareness Engine Exists

Enterprise repositories are heterogeneous.

Example:

SharePoint

Confluence

Git

Engineering DMS

Wiki

Policies

Drawing Repository

ERP Documents

Searching every repository for every query is:

• Expensive

• Slow

• Redundant

• Difficult to scale

Instead,

EKRE should understand its own knowledge landscape before retrieval
begins.

\-\--

# 12.3 Responsibilities

The Knowledge Awareness Engine is responsible for:

✓ Repository Awareness

✓ Knowledge Domain Awareness

✓ Document Distribution Awareness

✓ Metadata Awareness

✓ Freshness Awareness

✓ Repository Health Awareness

✓ Repository Confidence Estimation

✓ Search Scope Recommendation

It never retrieves document content.

\-\--

# 12.4 Inputs

The engine consumes:

Retrieval Query Model (RQM v2)

Enterprise Knowledge Catalog

Repository Statistics

Metadata Catalog

Repository Health

Governance Policies

\-\--

# 12.5 Outputs

Knowledge Awareness Report (KAR)

Containing:

Recommended Repositories

Repository Confidence

Repository Freshness

Repository Availability

Recommended Search Scope

Repository Priority

Estimated Candidate Volume

Expected Retrieval Cost

Knowledge Domain

Confidence

\-\--

# 12.6 Internal Architecture

\`\`\`

RQM v2

│

▼

Knowledge Awareness Engine

│

┌────────────────┼──────────────────┐

▼ ▼ ▼

Repository Metadata Knowledge

Profiler Analyzer Catalog

│ │ │

└────────────────┼──────────────────┘

▼

Repository Intelligence

▼

Search Scope Optimizer

▼

KAR

\`\`\`

\-\--

# 12.7 Repository Profiler

Maintains statistics for each repository.

Examples

Repository Name

Document Count

Chunk Count

Embedding Coverage

Average Freshness

Last Synchronization

Health Status

Average Retrieval Latency

Security Classification

Repository Trust Score

These statistics are continuously updated by EKIE.

\-\--

# 12.8 Knowledge Catalog

The catalog contains knowledge metadata.

Examples

Domains

Engineering

Finance

Legal

HR

Operations

Products

Applications

Projects

Business Units

Languages

Regions

Versions

The catalog contains metadata only.

Never document content.

\-\--

# 12.9 Metadata Analyzer

Responsible for understanding:

Available Metadata

Metadata Completeness

Metadata Quality

Metadata Distribution

Metadata Confidence

This allows the planner to determine whether metadata search is
worthwhile.

\-\--

# 12.10 Repository Health

Repository health influences retrieval.

Health Levels

Healthy

Degraded

Offline

Maintenance

Recovery

The planner can avoid degraded repositories.

\-\--

# 12.11 Repository Confidence

Each repository receives a confidence score.

Factors include

Freshness

Metadata Quality

Synchronization Status

Repository Trust

Document Quality

Duplicate Ratio

Historical Reliability

Confidence Score

0.0

↓

1.0

\-\--

# 12.12 Knowledge Domain Detection

The engine determines likely business domains.

Examples

Query

\"Shutdown procedure\"

↓

Operations

Engineering

Maintenance

Example

\"Expense reimbursement\"

↓

Finance

HR

\-\--

# 12.13 Search Scope Optimization

Instead of searching:

\`\`\`

All Repositories

\`\`\`

The engine recommends

\`\`\`

Engineering Wiki

\+

Maintenance Manuals

\+

Operations SOPs

\`\`\`

This reduces retrieval cost significantly.

\-\--

# 12.14 Repository Prioritization

Example

Git

Priority 0.95

Confluence

Priority 0.91

SharePoint

Priority 0.72

Old Archive

Priority 0.21

These priorities guide retrieval execution.

\-\--

# 12.15 Search Cost Estimation

The engine estimates

Expected Candidate Count

Expected Latency

Expected Cost

Expected Recall

Expected Precision

The planner uses these estimates.

\-\--

# 12.16 Explainability

Example

Repository Selected

↓

Engineering Wiki

Reason

Highest confidence

Latest synchronization

Relevant knowledge domain

Healthy status

Every recommendation records its rationale.

\-\--

# 12.17 Failure Handling

Knowledge Catalog unavailable

↓

Search all repositories.

Repository statistics unavailable

↓

Fallback priorities.

Health service unavailable

↓

Ignore health optimization.

The engine should never block retrieval.

\-\--

# 12.18 Performance Targets

Illustrative targets:

Repository Profiling

\<5 ms

Metadata Analysis

\<10 ms

Scope Optimization

\<5 ms

Cost Estimation

\<5 ms

Total Engine

\<25 ms

\-\--

# 12.19 Observability

Metrics:

Repository Recommendation Rate

Repository Confidence Distribution

Scope Reduction Percentage

Average Estimated Cost

Recommendation Accuracy

Knowledge Domain Distribution

These metrics help improve planning over time.

\-\--

# 12.20 Extension Points

Future enhancements:

Knowledge Graph Statistics

Repository Learning Models

Adaptive Repository Ranking

Domain Popularity Analytics

Semantic Repository Clustering

Real-time Repository Telemetry

\-\--

# 12.21 Architecture Rules

The Knowledge Awareness Engine SHALL NOT:

Retrieve documents

Access vector embeddings

Perform ranking

Build execution plans

Modify metadata

Change security policies

Its responsibility ends with producing the Knowledge Awareness Report
(KAR).

\-\--

# End of Chapter 12

**🏛 Principal Architect Review (Major Improvement)**

I think we can make EKRE even more enterprise-grade by introducing
another core concept.

**Introduce the Knowledge Catalog Service (KCS)**

Right now, the Knowledge Awareness Engine depends on multiple metadata
sources.

Instead, create a dedicated service maintained by EKIE.

EKIE

↓

Knowledge Catalog Service

↓

Knowledge Awareness Engine

↓

Query Planner

The **Knowledge Catalog Service** becomes the authoritative registry
for:

- Repository inventory

- Document statistics

- Domain taxonomy

- Repository capabilities

- Synchronization status

- Freshness metrics

- Trust scores

- Metadata schemas

- Language coverage

- Security classifications

This gives us a clean separation:

  -----------------------------------------------------------------------
  **Component**              **Responsibility**
  -------------------------- --------------------------------------------
  **EKIE**                   Create and maintain enterprise knowledge

  **Knowledge Catalog        Publish knowledge metadata and statistics
  Service (KCS)**            

  **Knowledge Awareness      Consume catalog data and generate retrieval
  Engine (KAE)**             recommendations

  **Query Planner**          Make execution decisions
  -----------------------------------------------------------------------

This separation avoids coupling the Query Intelligence Domain directly
to EKIE internals.

------------------------------------------------------------------------

**📚 Updated Progress**

**Query Intelligence Domain**

- ✅ Chapter 8 --- Query Intelligence Domain

- ✅ Chapter 9 --- Query Understanding Engine

- ✅ Chapter 10 --- Intent Classification Engine

- ✅ Chapter 11 --- Query Enrichment Engine

- ✅ **Chapter 12 --- Knowledge Awareness Engine**

**Remaining**

- ⏳ Chapter 13 --- Retrieval Profile Manager

- ⏳ Chapter 14 --- Query Planner

------------------------------------------------------------------------

**🚀 Product Manager Recommendation (Strategic)**

At this point, I would make one strategic change to the overall
enterprise platform.

Instead of thinking about **EKIE** and **EKRE** as isolated systems, we
should define a **shared platform layer** that both products use:

Enterprise Knowledge Platform

┌──────────────────────────────────────────┐

│ Shared Platform Services │

│\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\--│

│ Knowledge Catalog Service (KCS) │

│ Metadata Registry │

│ Schema Registry │

│ Configuration Service │

│ Policy Service │

│ Observability Platform │

└──────────────────────────────────────────┘

▲ ▲

│ │

EKIE (Ingestion) EKRE (Retrieval)

This gives the entire ecosystem cleaner boundaries, reduces duplication,
and allows future products (such as EKCP) to consume the same shared
services without tightly coupling them to either ingestion or retrieval.
This architectural refinement will make the overall platform
significantly more scalable and maintainable as it grows.

Excellent. We have now reached what I consider **the brain of the entire
EKRE system**.

Everything we\'ve designed so far exists to support one component:

**The Query Planner (QP)**

If the Ingestion Engine was the brain of EKIE, then the **Query Planner
is the brain of EKRE**.

It is **not** a retriever.

It is **not** a search engine.

It is an **execution planner**, very similar to how PostgreSQL, Spark
SQL, Presto, Snowflake, and distributed databases create execution plans
before touching data.

This is where I want EKRE to be different from nearly every RAG
framework.

------------------------------------------------------------------------

**🏛 Principal Architect Review (Critical Architecture Improvement)**

Most RAG systems do this:

Query

↓

Retriever

Slightly better ones do:

Query

↓

Hybrid Retriever

Enterprise systems should instead create an **Execution Graph**.

Instead of saying:

Search Vector DB

the planner should generate something like:

Execution Plan

Step 1

Search Engineering Repository

↓

Step 2

Search Vector Index

↓

Step 3

Search Metadata

↓

Step 4

Merge

↓

Step 5

Rank

↓

Step 6

Build Context

This is a huge difference.

The planner is no longer selecting a retriever.

It is orchestrating a workflow.

------------------------------------------------------------------------

# Chapter 13 - Query Planner

\-\--

# 13.1 Purpose

The Query Planner (QP) is responsible for transforming retrieval intent
into a deterministic execution workflow.

It is the central orchestration component of the Query Intelligence
Domain.

The Query Planner does not execute retrieval.

Instead, it constructs an optimized Retrieval Execution Plan (REP)
describing how retrieval should occur.

\-\--

# 13.2 Why a Query Planner Exists

Enterprise retrieval involves multiple dimensions:

\- Multiple repositories

\- Multiple retrieval engines

\- Security policies

\- Metadata filtering

\- Cost constraints

\- Latency objectives

\- Business priorities

Rather than hardcoding retrieval logic, EKRE creates an execution plan
for every query.

This allows retrieval behavior to evolve independently from retrieval
implementation.

\-\--

# 13.3 Responsibilities

The Query Planner is responsible for:

✓ Selecting retrieval engines

✓ Determining execution order

✓ Configuring parallel execution

✓ Applying retrieval profiles

✓ Defining candidate limits

✓ Applying timeout policies

✓ Configuring ranking strategy

✓ Generating deterministic execution plans

The planner never retrieves content.

\-\--

# 13.4 Inputs

The planner receives:

Retrieval Query Model (RQM v2)

Knowledge Awareness Report (KAR)

Retrieval Profile

Enterprise Policies

Runtime Configuration

Repository Health

Consumer Requirements

\-\--

# 13.5 Outputs

Retrieval Execution Plan (REP)

Containing:

Execution ID

Selected Engines

Execution Graph

Repository Order

Candidate Limits

Timeouts

Ranking Strategy

Fallback Strategy

Expected Cost

Expected Latency

Observability Metadata

\-\--

# 13.6 Internal Architecture

\`\`\`

RQM v2

│

▼

Query Planner

│

┌──────────────────┼──────────────────┐

▼ ▼ ▼

Policy Cost-Based Strategy

Engine Optimizer Builder

│ │ │

└──────────────────┼──────────────────┘

▼

Execution Graph Builder

▼

Retrieval Execution Plan

\`\`\`

\-\--

# 13.7 Planning Pipeline

\`\`\`

Input Validation

↓

Policy Evaluation

↓

Repository Selection

↓

Retrieval Strategy Selection

↓

Execution Optimization

↓

Execution Graph Construction

↓

Cost Estimation

↓

Plan Validation

↓

Execution Plan Generation

\`\`\`

\-\--

# 13.8 Policy Evaluation

The planner applies enterprise rules.

Examples:

Security restrictions

Region restrictions

Compliance rules

Tenant isolation

Maximum latency

Maximum candidate count

Business policies

Policies constrain the execution plan before retrieval begins.

\-\--

# 13.9 Repository Selection

Uses the Knowledge Awareness Report.

Example:

Engineering Wiki

Priority 0.96

Git Repository

Priority 0.94

Archive

Ignored

Selection is metadata-driven.

\-\--

# 13.10 Retrieval Strategy Selection

Possible retrieval engines:

Vector Search

Keyword Search

Metadata Search

Repository Search

Knowledge Graph Search (Future)

SQL Search (Future)

Each engine is selected based on query characteristics rather than
static configuration.

\-\--

# 13.11 Parallel Execution Planning

The planner identifies independent retrieval tasks.

Example:

\`\`\`

Query

│

┌────────┴────────┐

▼ ▼

Vector Search Metadata Search

│ │

└────────┬────────┘

▼

Candidate Fusion

\`\`\`

Independent branches execute concurrently.

\-\--

# 13.12 Candidate Planning

The planner determines:

Maximum candidates

Minimum candidates

Repository quotas

Recall objectives

Precision objectives

This prevents unnecessary retrieval work.

\-\--

# 13.13 Timeout Planning

Different engines receive different budgets.

Example:

Vector Search

150 ms

Keyword Search

80 ms

Metadata Search

40 ms

Overall Budget

300 ms

\-\--

# 13.14 Cost-Based Optimization

The planner estimates:

Retrieval cost

Repository cost

Expected latency

Expected recall

Expected precision

Execution complexity

The least expensive plan satisfying quality objectives is preferred.

\-\--

# 13.15 Execution Graph

The planner produces a directed acyclic graph (DAG).

Example

\`\`\`

Repositories

↓

Retrieval Engines

↓

Candidate Collection

↓

Fusion

↓

Ranking

↓

Context Assembly

\`\`\`

The graph becomes the contract for the Retrieval Orchestrator.

\-\--

# 13.16 Retrieval Execution Plan (REP)

REP includes:

Execution ID

Planner Version

Selected Engines

Execution Graph

Policies Applied

Repository Order

Ranking Configuration

Timeouts

Candidate Limits

Fallback Rules

Expected Metrics

The REP is immutable.

\-\--

# 13.17 Explainability

Every planning decision records:

Decision

Reason

Input

Alternative Considered

Confidence

Policy Applied

Example:

Repository:

Engineering Wiki

Reason:

Highest freshness

Highest trust

Relevant domain

\-\--

# 13.18 Failure Handling

Repository unavailable

↓

Re-plan using alternatives.

Policy conflict

↓

Reject plan.

Optimization timeout

↓

Use default execution plan.

The planner should degrade gracefully whenever safe.

\-\--

# 13.19 Configuration

Administrators may configure:

Planning strategies

Optimization weights

Cost models

Latency objectives

Default retrieval profiles

Fallback policies

Parallelism limits

Candidate budgets

\-\--

# 13.20 Performance Targets

Illustrative goals:

Policy Evaluation

\<5 ms

Repository Selection

\<5 ms

Optimization

\<10 ms

Execution Graph

\<5 ms

Total Planning

\<30 ms

\-\--

# 13.21 Observability

Metrics:

Planning Latency

Optimization Success Rate

Fallback Plan Rate

Average Candidate Budget

Average Execution Cost

Repository Selection Accuracy

Plan Cache Hit Rate

\-\--

# 13.22 Extension Points

Future enhancements:

Adaptive Planning

Learning-based Planning

Feedback-driven Optimization

Cost Prediction Models

Dynamic Repository Ranking

Context-aware Planning

\-\--

# 13.23 Architecture Rules

The Query Planner SHALL NOT:

Execute retrieval

Rank candidates

Access document content

Generate embeddings

Modify repository metadata

Assemble context

The planner produces only the Retrieval Execution Plan.

\-\--

# End of Chapter 13

------------------------------------------------------------------------

**🏛 Principal Architect Review (Major Improvement)**

After designing the planner, I think EKRE can adopt a concept inspired
by mature database systems.

**Introduce a Plan Cache**

Many enterprise queries are repetitive:

- \"Travel Policy\"

- \"VPN Setup Guide\"

- \"Latest Architecture\"

- \"Expense Policy\"

For these, we can cache the **Retrieval Execution Plan (REP)** itself.

The flow becomes:

Incoming Query

│

▼

Query Fingerprinting

│

▼

Plan Cache Lookup

│ │

Hit Miss

│ │

▼ ▼

Reuse REP Generate REP

**Benefits**

- Reduces planning latency.

- Ensures deterministic behavior for recurring queries.

- Improves consistency in execution.

- Lowers CPU usage for high-volume enterprise environments.

The cache key should be based on:

- Normalized query.

- Retrieval profile.

- Tenant.

- Repository version.

- Policy version.

This ensures cached plans remain valid when enterprise knowledge or
policies change.

------------------------------------------------------------------------

**📚 Updated Handbook Progress**

**Query Intelligence Domain**

- ✅ Chapter 8 --- Query Intelligence Domain

- ✅ Chapter 9 --- Query Understanding Engine

- ✅ Chapter 10 --- Intent Classification Engine

- ✅ Chapter 11 --- Query Enrichment Engine

- ✅ Chapter 12 --- Knowledge Awareness Engine

- ✅ **Chapter 13 --- Query Planner**

**Next Major Volume**

With the Query Intelligence Domain fully specified, the next volume
should shift from **decision-making** to **execution**:

**Volume III --- Retrieval Execution Domain**

Proposed chapters:

- **Chapter 14 --- Retrieval Execution Domain Overview**

- Chapter 15 --- Retrieval Orchestrator

- Chapter 16 --- Vector Retrieval Engine

- Chapter 17 --- Keyword Retrieval Engine

- Chapter 18 --- Metadata Retrieval Engine

- Chapter 19 --- Repository Connector Framework

- Chapter 20 --- Candidate Collection Framework

**Product Manager Recommendation**

Before implementing any retrieval engine, I recommend designing the
**Retrieval Execution Domain** as a standalone subsystem, just as we did
for Query Intelligence. This maintains strict separation between
*planning* (\"what should be done\") and *execution* (\"doing it\"),
which is a core principle of scalable enterprise systems and will keep
EKRE extensible as new retrieval technologies are added.

Excellent. We have now completed what I call the **Decision Phase** of
EKRE.

Let\'s pause and look at what we\'ve built architecturally.

QUERY INTELLIGENCE DOMAIN

Query Validation (Future)

│

▼

Query Understanding Engine

│

▼

Intent Classification Engine

│

▼

Query Enrichment Engine

│

▼

Knowledge Awareness Engine

│

▼

Retrieval Profile Manager

│

▼

Query Planner

│

▼

Retrieval Execution Plan (REP)

Notice something important.

Everything above has produced **zero search results**.

That is intentional.

This entire subsystem exists to answer one question:

**\"How should retrieval happen?\"**

Now we begin answering the second question:

**\"Execute the plan.\"**

This is the beginning of the actual Retrieval Engine.

------------------------------------------------------------------------

**🏛 Principal Architect Review**

Before writing Volume III, I want to redesign something that almost
every RAG framework gets wrong.

Most systems execute retrieval like this:

Planner

↓

Retriever

↓

Results

This creates a massive bottleneck.

Instead, EKRE should introduce a **Retrieval Orchestrator** that behaves
like a workflow engine.

Think of:

- Apache Airflow

- Temporal

- Netflix Conductor

- Kubernetes Scheduler

The planner generates the workflow.

The orchestrator executes the workflow.

Huge difference.

------------------------------------------------------------------------

**Proposed Runtime**

Query Planner

↓

Retrieval Execution Plan

↓

Retrieval Orchestrator

↓

Execution Graph

↓

Parallel Retrieval Engines

↓

Candidate Collection

↓

Fusion

The planner never touches retrieval.

The retrieval engines never make planning decisions.

This separation makes EKRE horizontally scalable.

------------------------------------------------------------------------

**Volume III --- Retrieval Execution Domain**

# Volume III

# Retrieval Execution Domain

\-\--

# Chapter 14 - Retrieval Execution Domain Overview

\-\--

# 14.1 Purpose

The Retrieval Execution Domain is responsible for executing Retrieval
Execution Plans (REP) generated by the Query Planner.

Unlike the Query Intelligence Domain, which decides \*how\* retrieval
should occur, the Retrieval Execution Domain performs the retrieval
itself.

It is responsible for coordinating retrieval engines, collecting
candidates, handling execution failures, and delivering standardized
retrieval results.

\-\--

# 14.2 Mission

Convert

\`\`\`

Retrieval Execution Plan

\`\`\`

into

\`\`\`

Candidate Collection

\`\`\`

efficiently,

deterministically,

and observably.

\-\--

# 14.3 Responsibilities

The Retrieval Execution Domain owns:

✓ Execution orchestration

✓ Repository communication

✓ Retrieval engine execution

✓ Parallel processing

✓ Candidate collection

✓ Failure isolation

✓ Retry policies

✓ Execution telemetry

It never performs ranking.

It never assembles context.

\-\--

# 14.4 Architectural Layers

\`\`\`

Retrieval Execution Domain

┌────────────────────────────────────────────┐

│ Retrieval Orchestrator │

├────────────────────────────────────────────┤

│ Execution Scheduler │

├────────────────────────────────────────────┤

│ Retrieval Engine Framework │

├────────────────────────────────────────────┤

│ Repository Connector Framework │

├────────────────────────────────────────────┤

│ Candidate Collection Framework │

└────────────────────────────────────────────┘

\`\`\`

Each layer owns one responsibility.

\-\--

# 14.5 Core Components

The Retrieval Execution Domain consists of:

• Retrieval Orchestrator

• Execution Scheduler

• Vector Retrieval Engine

• Keyword Retrieval Engine

• Metadata Retrieval Engine

• Repository Connector Framework

• Candidate Collection Framework

Future components include:

• Graph Retrieval Engine

• SQL Retrieval Engine

• Image Retrieval Engine

• Audio Retrieval Engine

• Video Retrieval Engine

\-\--

# 14.6 Execution Flow

\`\`\`

Retrieval Execution Plan

↓

Execution Scheduler

↓

Retrieval Orchestrator

↓

Parallel Retrieval Engines

↓

Repository Connectors

↓

Candidate Collection

↓

Candidate Set

\`\`\`

Every execution follows this lifecycle.

\-\--

# 14.7 Execution Model

Retrieval tasks execute independently.

Example

\`\`\`

REP

│

┌───────────┼─────────────┐

▼ ▼ ▼

Vector Engine Metadata Engine Keyword Engine

│ │ │

└───────────┼─────────────┘

▼

Candidate Collector

\`\`\`

No retrieval engine depends upon another.

\-\--

# 14.8 Repository Connectors

Retrieval engines never communicate directly with repositories.

Instead,

all repository communication passes through standardized connectors.

Benefits:

Repository independence

Connection pooling

Retry handling

Authentication isolation

Vendor abstraction

\-\--

# 14.9 Candidate Collection

Every retrieval engine produces standardized candidates.

Candidate Collection merges them into:

Unified Candidate Set (UCS)

No ranking occurs.

No duplicate removal occurs.

Collection only aggregates.

\-\--

# 14.10 Failure Isolation

Repository failures are isolated.

Example

Git Offline

↓

Continue

SharePoint Timeout

↓

Continue

Metadata Engine Failure

↓

Continue

Retrieval should degrade gracefully whenever possible.

\-\--

# 14.11 Retry Strategy

Supported retry policies:

No Retry

Immediate Retry

Exponential Backoff

Repository-specific Retry

Adaptive Retry

Policy is configurable.

\-\--

# 14.12 Parallelism

Independent retrieval tasks execute concurrently.

The scheduler determines:

Maximum parallel workers

Maximum repository concurrency

CPU budgets

Memory budgets

Timeout budgets

\-\--

# 14.13 Observability

Execution metrics include:

Execution latency

Repository latency

Engine latency

Candidate count

Failure rate

Retry rate

Repository availability

Execution graph duration

\-\--

# 14.14 Architecture Rules

The Retrieval Execution Domain SHALL NOT:

Rank candidates

Modify execution plans

Generate embeddings

Understand user intent

Perform query enrichment

Assemble context

Generate prompts

Its responsibility ends after producing a Unified Candidate Set.

\-\--

# 14.15 Success Criteria

The Retrieval Execution Domain succeeds when:

✓ Every execution follows the REP.

✓ Retrieval engines execute independently.

✓ Failures remain isolated.

✓ Candidate collection is deterministic.

✓ Execution is observable.

✓ Performance objectives are satisfied.

\-\--

# End of Chapter 14

------------------------------------------------------------------------

**🏛 Principal Architect Review (Critical Improvement)**

Now I want to introduce what I believe will become one of EKRE\'s
defining architectural patterns.

**Replace \"Retrieval Engines\" with Retrieval Workers**

Instead of thinking of retrieval engines as monolithic services, think
of them as **workers** managed by the orchestrator.

Retrieval Orchestrator

↓

Task Queue

↓

Worker Pool

↓

Vector Worker

Keyword Worker

Metadata Worker

Graph Worker

SQL Worker

Repository Worker

Why?

Because workers provide:

- Better concurrency control.

- Horizontal scaling.

- Backpressure handling.

- Resource management.

- Dynamic load balancing.

- Easier autoscaling in Kubernetes.

Each worker executes a single retrieval task and returns standardized
candidates.

This aligns EKRE with distributed execution frameworks such as Spark,
Ray, and Temporal rather than traditional synchronous RAG pipelines.

------------------------------------------------------------------------

**📚 Handbook Status**

**Volume I**

- ✅ Product Foundation

**Volume II**

- ✅ Query Intelligence Domain

**Volume III**

- ✅ Chapter 14 --- Retrieval Execution Domain Overview

**Next Chapters**

The implementation sequence I recommend is:

1.  **Chapter 15 --- Retrieval Orchestrator** ⭐ *(the runtime brain of
    retrieval)*

2.  Chapter 16 --- Execution Scheduler

3.  Chapter 17 --- Retrieval Worker Framework

4.  Chapter 18 --- Vector Retrieval Worker

5.  Chapter 19 --- Keyword Retrieval Worker

6.  Chapter 20 --- Metadata Retrieval Worker

7.  Chapter 21 --- Repository Connector Framework

8.  Chapter 22 --- Unified Candidate Collection Framework

------------------------------------------------------------------------

**🚀 Product Manager Recommendation (Major Architectural Change)**

After reviewing the complete architecture, I recommend one final
refinement before implementation:

Introduce a **shared Execution Runtime** used by both EKIE and EKRE.

Enterprise Knowledge Platform

┌────────────────────────────────────────────────────┐

│ Shared Execution Runtime │

│\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\--│

│ Workflow Engine │

│ Task Queue │

│ Worker Framework │

│ Retry Manager │

│ Scheduler │

│ Observability Pipeline │

│ Configuration Service │

└────────────────────────────────────────────────────┘

▲ ▲

│ │

EKIE (Ingestion) EKRE (Retrieval)

This avoids building two different orchestration systems---one for
ingestion and another for retrieval. Instead, both products share the
same execution runtime while implementing different workflows. It
provides consistency, simplifies operations, and creates a strong
foundation for future components like EKCP, enabling the entire
Enterprise Knowledge Platform to evolve as a cohesive ecosystem rather
than isolated services.

Excellent.

Now we have entered what I consider **the Runtime Architecture** of
EKRE.

Up until now we designed the **brains** (Query Intelligence).

Now we are designing the **execution engine**.

This is also where I want to differentiate EKRE from LangChain,
LlamaIndex, Haystack, CrewAI, and most open-source RAG frameworks.

------------------------------------------------------------------------

**🏛 Principal Architect Review**

Before writing the Retrieval Orchestrator, I want to make a significant
architectural refinement.

Currently we have:

Query Planner

↓

Retrieval Execution Plan (REP)

↓

Retrieval Orchestrator

↓

Workers

I believe we\'re still missing a critical abstraction.

**Add an Execution Runtime Layer**

Instead of the Orchestrator directly managing workers, introduce an
**Execution Runtime** responsible for scheduling, concurrency, retries,
state management, and resource allocation.

Retrieval Execution Domain

REP

│

▼

Retrieval Orchestrator

│

▼

Execution Runtime

│

┌──────────────────┼───────────────────┐

▼ ▼ ▼

Scheduler Worker Manager State Manager

│ │ │

└──────────────────┼───────────────────┘

▼

Retrieval Workers

This separation keeps the orchestrator focused on **business workflow**,
while the runtime handles **execution mechanics**.

------------------------------------------------------------------------

**Volume III**

### 14.X Security Context Contract

**Integration Contract:** Any consumer (e.g., EKCP) calling the Retrieval Execution API must provide a strictly formed Security Context. EKRE will use this to enforce ABAC/RBAC on the Candidate Collection.

**Required Fields:**
- `user_id` (String)
- `tenant_id` (String)
- `roles` (List[String])
- `classification_clearance` (Enum: Public, Internal, Confidential, Restricted)

# Chapter 15 - Retrieval Orchestrator

\-\--

# 15.1 Purpose

The Retrieval Orchestrator (RO) is the central runtime coordinator
responsible for executing Retrieval Execution Plans (REP).

The orchestrator transforms an execution plan into a sequence of
executable retrieval tasks.

Unlike the Query Planner, which creates execution plans, the Retrieval
Orchestrator executes those plans.

It does not retrieve knowledge directly.

Instead, it coordinates retrieval workers.

\-\--

# 15.2 Responsibilities

The Retrieval Orchestrator is responsible for:

✓ Loading Retrieval Execution Plans

✓ Building execution sessions

✓ Creating retrieval tasks

✓ Coordinating worker execution

✓ Managing execution state

✓ Monitoring progress

✓ Handling execution failures

✓ Producing execution summaries

\-\--

# 15.3 Responsibilities NOT Owned

The orchestrator SHALL NOT:

\- Understand queries

\- Select repositories

\- Rank candidates

\- Assemble context

\- Generate prompts

\- Modify execution plans

Those responsibilities belong to other components.

\-\--

# 15.4 Inputs

The orchestrator receives:

Retrieval Execution Plan (REP)

Execution Configuration

Runtime Policies

Execution Context

Cancellation Tokens

Trace Context

\-\--

# 15.5 Outputs

Execution Session

Containing:

Session ID

Execution State

Task Graph

Worker Assignments

Candidate Streams

Execution Metrics

Execution Trace

Completion Status

\-\--

# 15.6 Internal Architecture

\`\`\`

REP

│

▼

Retrieval Orchestrator

│

┌───────────┼─────────────┐

▼ ▼ ▼

Session Task Progress

Manager Builder Monitor

│ │ │

└───────────┼─────────────┘

▼

Execution Runtime

\`\`\`

Each component owns one responsibility.

\-\--

# 15.7 Execution Session

Every retrieval request creates an Execution Session.

The session maintains:

Execution ID

Current State

Task Status

Worker Status

Candidate Streams

Execution Metrics

Errors

Warnings

Timing

The session exists only for the duration of execution.

\-\--

# 15.8 Task Builder

The Task Builder converts the Retrieval Execution Plan into executable
tasks.

Example:

REP

↓

Task A

Vector Retrieval

↓

Task B

Metadata Retrieval

↓

Task C

Keyword Retrieval

↓

Task D

Candidate Collection

Task dependencies are preserved.

\-\--

# 15.9 Execution Graph

Tasks are represented as a Directed Acyclic Graph (DAG).

Example:

\`\`\`

Start

↓

Vector Worker

↓

Candidate Collection

↓

Completed

\`\`\`

Parallel example:

\`\`\`

Start

│

┌──────┴──────┐

▼ ▼

Vector Worker Metadata Worker

│ │

└──────┬──────┘

▼

Candidate Collector

▼

Complete

\`\`\`

The orchestrator never executes tasks outside the graph.

\-\--

# 15.10 State Machine

Execution states:

CREATED

↓

INITIALIZED

↓

RUNNING

↓

WAITING

↓

COLLECTING

↓

COMPLETED

Failure states:

FAILED

CANCELLED

TIMED_OUT

DEGRADED

State transitions are immutable and recorded.

\-\--

# 15.11 Worker Coordination

The orchestrator assigns tasks to the Execution Runtime.

Responsibilities include:

Task dispatch

Dependency tracking

Completion monitoring

Failure notification

Cancellation propagation

Progress reporting

Worker implementation remains abstract.

\-\--

# 15.12 Candidate Streams

Workers return candidates as streams rather than waiting for all tasks
to complete.

Benefits:

Lower latency

Progressive retrieval

Early fusion

Adaptive stopping

Streaming metrics

The orchestrator aggregates these streams into the Unified Candidate
Set.

\-\--

# 15.13 Retry Handling

Retries follow policy.

Examples:

Repository Timeout

↓

Retry

Worker Failure

↓

Reassign

Permanent Failure

↓

Continue with degraded execution

Retry behavior is configurable.

\-\--

# 15.14 Cancellation

Execution may be cancelled by:

Client request

Timeout

Policy violation

System shutdown

Resource exhaustion

Cancellation propagates to all active tasks.

\-\--

# 15.15 Progress Monitoring

The orchestrator continuously tracks:

Completed Tasks

Running Tasks

Waiting Tasks

Candidate Count

Execution Latency

Repository Status

Worker Health

Progress is observable in real time.

\-\--

# 15.16 Failure Handling

Failures are isolated.

Example:

Metadata Worker fails.

↓

Vector Worker continues.

↓

Keyword Worker continues.

↓

Execution completes with partial results.

Only critical failures terminate the execution session.

\-\--

# 15.17 Configuration

Configurable options include:

Maximum Concurrent Tasks

Maximum Workers

Retry Policies

Execution Timeouts

Cancellation Behavior

Streaming Enabled

Task Queue Size

State Persistence

\-\--

# 15.18 Performance Targets

Illustrative targets:

Session Creation

\<5 ms

Task Graph Generation

\<5 ms

Worker Dispatch

\<5 ms

Progress Updates

\<1 ms

Total Orchestrator Overhead

\<15 ms

\-\--

# 15.19 Observability

Metrics emitted:

Execution Sessions

Task Completion Rate

Worker Utilization

Retry Count

Average Session Duration

Execution Failures

Cancellation Rate

Streaming Throughput

\-\--

# 15.20 Extension Points

Future enhancements:

Distributed Orchestration

Cross-region Execution

Priority Scheduling

Adaptive Execution

Dynamic Worker Scaling

Predictive Failure Recovery

Execution Replay

\-\--

# 15.21 Architecture Rules

The Retrieval Orchestrator SHALL NOT:

Perform retrieval

Interpret user queries

Rank candidates

Modify retrieval plans

Generate embeddings

Assemble context

Its responsibility ends after coordinating execution and producing the
Unified Candidate Set.

\-\--

# End of Chapter 15

------------------------------------------------------------------------

**🏛 Principal Architect Review (Enterprise-Level Improvement)**

After completing the Retrieval Orchestrator, I would introduce one of
the strongest architectural concepts in the entire Enterprise Knowledge
Platform.

**Introduce an Execution Context (EC)**

Right now, the orchestrator passes several objects between components.

Instead, define a single immutable runtime object:

Execution Context (EC)

The EC accompanies every task during execution and contains:

Execution ID

Session ID

Tenant ID

Trace ID

Retrieval Execution Plan

Cancellation Token

Execution Budget

Current State

Worker Assignments

Runtime Metrics

Security Context

Feature Flags

Configuration Snapshot

Policy Snapshot

Observability Context

Every worker receives the same Execution Context, ensuring:

- No hidden dependencies.

- Deterministic behavior.

- Consistent tracing.

- Simplified testing.

- Easier debugging.

- Distributed execution compatibility.

This mirrors mature execution frameworks such as Spark (TaskContext),
Kubernetes (PodSpec), and workflow engines like Temporal (Workflow
Context).

------------------------------------------------------------------------

**📚 Updated Handbook Progress**

**Volume I --- Product Foundation**

- ✅ Complete

**Volume II --- Query Intelligence Domain**

- ✅ Complete

**Volume III --- Retrieval Execution Domain**

- ✅ Chapter 14 --- Retrieval Execution Domain Overview

- ✅ **Chapter 15 --- Retrieval Orchestrator**

**Remaining Chapters**

- ⏳ Chapter 16 --- Execution Runtime

- ⏳ Chapter 17 --- Execution Scheduler

- ⏳ Chapter 18 --- Retrieval Worker Framework

- ⏳ Chapter 19 --- Vector Retrieval Worker

- ⏳ Chapter 20 --- Keyword Retrieval Worker

- ⏳ Chapter 21 --- Metadata Retrieval Worker

- ⏳ Chapter 22 --- Repository Connector Framework

- ⏳ Chapter 23 --- Unified Candidate Collection Framework

**🚀 Product Manager Recommendation (Architecture Refactoring)**

At this stage, I recommend a structural refinement that will improve the
maintainability of the entire Enterprise Knowledge Platform.

Instead of implementing the Retrieval Orchestrator as a standalone
service, position it as a specialized workflow running on a **shared
Execution Runtime** (introduced earlier). This allows EKIE (ingestion
workflows), EKRE (retrieval workflows), and future platform components
to share the same scheduling, task management, retry, observability, and
execution infrastructure.

The resulting layered architecture becomes:

Enterprise Knowledge Platform

│

├── Shared Platform Services

│ ├── Knowledge Catalog Service

│ ├── Policy Service

│ ├── Configuration Service

│ └── Observability Platform

│

├── Shared Execution Runtime

│ ├── Execution Scheduler

│ ├── Worker Manager

│ ├── State Manager

│ ├── Retry Manager

│ ├── Task Queue

│ └── Execution Context

│

├── EKIE (Knowledge Ingestion)

│ └── Ingestion Workflows

│

└── EKRE (Knowledge Retrieval)

└── Retrieval Workflows

This refinement creates a unified execution model across the platform,
minimizes duplicated infrastructure, and provides a scalable foundation
for future enterprise capabilities without coupling ingestion and
retrieval logic.

Excellent.

Now we are designing what I consider the **operating system of EKRE**.

Most RAG systems completely ignore this layer.

They have:

Retriever

↓

Vector DB

↓

Results

That\'s fine for demos.

It completely breaks in enterprise environments where you have:

- 100+ repositories

- Thousands of concurrent users

- Millions of chunks

- Multi-tenant isolation

- Retry policies

- Resource limits

- Backpressure

- Partial failures

This is why we introduced the **Execution Runtime**.

**🏛 Principal Architect Review**

Before writing Chapter 16, I want to make one of the biggest
improvements in the entire architecture.

Right now we have:

Retrieval Orchestrator

↓

Execution Runtime

But \"Execution Runtime\" is still too generic.

Let\'s model it exactly like a modern distributed execution engine
(Kubernetes, Spark, Ray, Temporal).

Instead of one runtime, split it into **five runtime services**.

Execution Runtime

│

┌────────────────┼────────────────┐

▼ ▼ ▼

Execution Scheduler Worker Manager State Manager

│ │ │

└────────────────┼────────────────┘

▼

Resource Manager

▼

Execution Monitor

Each service owns exactly one capability.

This keeps the runtime extremely scalable.

------------------------------------------------------------------------

# Chapter 16 - Execution Runtime

\-\--

# 16.1 Purpose

The Execution Runtime is the distributed execution platform responsible
for managing all retrieval workflows within EKRE.

Unlike the Retrieval Orchestrator, which coordinates business workflow
execution, the Execution Runtime manages the operational aspects of task
execution.

It provides:

\- Scheduling

\- Worker management

\- State management

\- Resource allocation

\- Failure recovery

\- Runtime observability

The Execution Runtime is shared infrastructure.

\-\--

# 16.2 Responsibilities

The Execution Runtime owns:

✓ Task Scheduling

✓ Worker Lifecycle

✓ Resource Management

✓ Execution State

✓ Retry Management

✓ Failure Recovery

✓ Runtime Metrics

✓ Distributed Coordination

It performs no retrieval logic.

\-\--

# 16.3 Runtime Components

The runtime consists of five services.

\`\`\`

Execution Runtime

│

├── Execution Scheduler

├── Worker Manager

├── State Manager

├── Resource Manager

└── Execution Monitor

\`\`\`

Each service is independently deployable.

\-\--

# 16.4 Execution Scheduler

Purpose:

Determine when tasks execute.

Responsibilities:

\- Queue management

\- Priority scheduling

\- Dependency resolution

\- Worker assignment

\- Backpressure

The scheduler never executes work itself.

\-\--

# 16.5 Worker Manager

Responsible for:

\- Worker registration

\- Worker discovery

\- Worker health

\- Worker scaling

\- Worker replacement

Workers remain stateless.

\-\--

# 16.6 State Manager

Maintains execution state.

Tracks:

Execution Sessions

Task States

Worker States

Retries

Timeouts

Progress

State transitions are immutable.

\-\--

# 16.7 Resource Manager

Controls runtime resources.

Examples:

CPU

Memory

Concurrent Workers

Repository Connections

Queue Capacity

Bandwidth

Resource limits prevent system overload.

\-\--

# 16.8 Execution Monitor

Provides runtime telemetry.

Collects:

Execution latency

Worker utilization

Queue depth

Task throughput

Error rates

Retry counts

Timeouts

Health status

\-\--

# 16.9 Runtime Lifecycle

\`\`\`

Task Submitted

↓

Queued

↓

Scheduled

↓

Assigned

↓

Running

↓

Completed

\`\`\`

Alternative paths:

\`\`\`

Running

↓

Retry

↓

Running

\`\`\`

or

\`\`\`

Running

↓

Failed

\`\`\`

\-\--

# 16.10 Runtime State Machine

Task states:

PENDING

READY

RUNNING

WAITING

RETRYING

COMPLETED

FAILED

CANCELLED

TIMED_OUT

State transitions are versioned.

\-\--

# 16.11 Scheduling Policies

Supported scheduling strategies:

FIFO

Priority

Weighted Priority

Deadline-based

Resource-aware

Adaptive Scheduling (Future)

Administrators may select policies at runtime.

\-\--

# 16.12 Worker Pools

Workers are organized into pools.

Examples:

Vector Pool

Keyword Pool

Metadata Pool

Repository Pool

Graph Pool (Future)

Each pool scales independently.

\-\--

# 16.13 Backpressure Management

When demand exceeds capacity:

Queue tasks.

Reduce concurrency.

Throttle workers.

Reject low-priority requests.

Protect high-priority workloads.

Backpressure prevents cascading failures.

\-\--

# 16.14 Failure Recovery

Runtime failures include:

Worker Crash

Node Failure

Repository Timeout

Queue Failure

Memory Exhaustion

Recovery actions:

Retry

Worker Replacement

Task Migration

Graceful Degradation

Abort

Recovery policies are configurable.

\-\--

# 16.15 Configuration

Administrators configure:

Maximum Workers

Queue Size

Scheduling Policy

Retry Policy

Resource Limits

Worker Timeout

Execution Timeout

Health Check Interval

\-\--

# 16.16 Performance Targets

Illustrative targets:

Task Scheduling

\<2 ms

Worker Assignment

\<2 ms

State Update

\<1 ms

Queue Latency

\<5 ms

Runtime Overhead

\<10 ms

\-\--

# 16.17 Observability

Runtime metrics include:

Worker Utilization

Queue Length

Average Wait Time

Task Throughput

Retry Rate

Failure Rate

CPU Usage

Memory Usage

Task Success Rate

\-\--

# 16.18 Extension Points

Future capabilities:

Distributed Scheduling

Multi-region Execution

GPU Workers

Priority Inheritance

Adaptive Scaling

Predictive Scheduling

Serverless Workers

\-\--

# 16.19 Architecture Rules

The Execution Runtime SHALL NOT:

Understand queries

Retrieve documents

Perform ranking

Modify execution plans

Generate embeddings

Assemble context

It exists solely to execute tasks efficiently and reliably.

\-\--

# End of Chapter 16

------------------------------------------------------------------------

**🏛 Principal Architect Review (Major Improvement)**

I believe we can elevate EKRE even further by introducing an **Execution
Contract**.

Instead of workers receiving arbitrary task payloads, every task should
conform to a standard interface.

interface RetrievalTask {

String taskId();

String executionId();

TaskType type();

TaskPriority priority();

TaskDependencies dependencies();

ExecutionBudget budget();

TaskResult execute(ExecutionContext context);

}

Every retrieval worker---whether it performs vector search, keyword
search, metadata search, or future graph retrieval---implements this
contract.

This gives us:

- Uniform task lifecycle.

- Pluggable worker implementations.

- Consistent scheduling.

- Simplified retries.

- Predictable observability.

- Strong typing between planner and runtime.

------------------------------------------------------------------------

**📚 Handbook Progress**

**Volume III --- Retrieval Execution Domain**

- ✅ Chapter 14 --- Retrieval Execution Domain Overview

- ✅ Chapter 15 --- Retrieval Orchestrator

- ✅ **Chapter 16 --- Execution Runtime**

**Remaining Chapters**

The next implementation order I recommend is:

1.  **Chapter 17 --- Execution Scheduler** *(deep dive into scheduling
    algorithms, priorities, fairness, and backpressure)*

2.  Chapter 18 --- Retrieval Worker Framework

3.  Chapter 19 --- Vector Retrieval Worker

4.  Chapter 20 --- Keyword Retrieval Worker

5.  Chapter 21 --- Metadata Retrieval Worker

6.  Chapter 22 --- Repository Connector Framework

7.  Chapter 23 --- Unified Candidate Collection Framework

8.  Chapter 24 --- Candidate Fusion Framework

------------------------------------------------------------------------

**🏆 Principal Architect Recommendation (One Important Refinement)**

One architectural decision I recommend making now---before
implementation---is to **avoid coupling the Execution Runtime to
retrieval-specific concepts**.

Instead of classes like:

- VectorWorker

- KeywordWorker

- MetadataWorker

define generic runtime concepts:

- Task

- Worker

- Queue

- Scheduler

- ExecutionContext

The retrieval-specific behavior belongs in **plugins** that implement
these contracts.

This gives you a reusable runtime that can power:

- **EKIE** (document ingestion workflows)

- **EKRE** (retrieval workflows)

- **EKCP** (knowledge processing pipelines)

- Any future enterprise workflow

This is a significant architectural investment, but it transforms the
runtime into a **platform capability** rather than an implementation
detail of EKRE. It aligns with the overall vision of building the
**Enterprise Knowledge Platform (EKP)** as a family of products sharing
common infrastructure while remaining independently evolvable.

Excellent.

Now we arrive at what I consider **one of the hardest problems in
Enterprise Retrieval**.

Not vector search.

Not embeddings.

Not hybrid search.

The hardest problem is **scheduling**.

If EKRE eventually serves an enterprise with:

- 500 repositories

- 50 million chunks

- 30 retrieval workers

- 10,000 concurrent users

- Multiple tenants

- Different SLAs

- Different priorities

then the scheduler becomes more important than the retrieval algorithm
itself.

This is exactly why Spark, Kubernetes, Ray, Flink, Dask and Temporal all
have sophisticated schedulers.

**EKRE deserves the same level of engineering.**

------------------------------------------------------------------------

**🏛 Principal Architect Review**

Before writing the Scheduler chapter, I think we should slightly
redesign the runtime.

Currently we have

Execution Runtime

↓

Execution Scheduler

I think we should split scheduling into **three phases**.

Incoming Tasks

↓

Admission Controller

↓

Task Scheduler

↓

Worker Allocator

↓

Worker Queue

Why?

Because scheduling is not simply:

Task

↓

Worker

Instead it should answer three different questions.

**Phase 1 --- Admission Control**

Should this task even enter the runtime?

Examples:

- Tenant quota exceeded

- Repository unavailable

- System overloaded

- Budget exhausted

- Invalid execution plan

If the answer is \"No\", we reject immediately.

------------------------------------------------------------------------

**Phase 2 --- Scheduling**

If accepted:

Which task should execute next?

Examples

Priority

Deadline

FIFO

Weighted Fair Queue

Cost-based

Latency-aware

**Phase 3 --- Worker Allocation**

Now choose:

Which worker?

Which node?

Which region?

Which CPU?

Which GPU?

Which repository connection?

Notice these are completely different problems.

This separation will make EKRE much more scalable.

------------------------------------------------------------------------

### 16.X API Contract: Security Processing & Context Lineage

The Execution Runtime API strictly requires the `security_context` object in the request payload and guarantees a `context_lineage` object in the response, mapping every retrieved chunk back to its source EKIE document and repository.


### 16.Y Cascading Failure Prevention (Backpressure)

**Integration Contract:** If the Retrieval Orchestrator detects that retrieval queues are saturated or the Vector DB is overwhelmed, the Execution Runtime must explicitly return an **HTTP 429 Too Many Requests** response with a `Retry-After` header to EKCP, rather than allowing connections to time out.


# Chapter 17 - Execution Scheduler

\-\--

# 17.1 Purpose

The Execution Scheduler is responsible for deciding when and where
retrieval tasks execute.

Unlike the Retrieval Orchestrator, which builds execution workflows, and
unlike workers, which execute retrieval logic, the scheduler determines
task ordering and resource assignment.

The scheduler is responsible for maximizing throughput while maintaining
fairness, latency objectives, and resource utilization.

\-\--

# 17.2 Responsibilities

The scheduler owns:

✓ Admission Control

✓ Task Prioritization

✓ Queue Management

✓ Worker Allocation

✓ Dependency Scheduling

✓ Fairness

✓ Deadline Management

✓ Backpressure

✓ Load Balancing

\-\--

# 17.3 Internal Architecture

\`\`\`

Incoming Tasks

↓

Admission Controller

↓

Priority Calculator

↓

Task Queue Manager

↓

Dependency Resolver

↓

Worker Allocator

↓

Worker Pool

\`\`\`

Each component owns a single scheduling responsibility.

\-\--

# 17.4 Admission Controller

Before a task enters execution, it is validated.

Checks include:

Tenant quota

Execution budget

Execution timeout

Repository availability

System load

Security policy

Feature flags

Only admitted tasks enter the scheduler.

\-\--

# 17.5 Priority Calculation

Every task receives a scheduling priority.

Factors include:

User Priority

Retrieval Profile

Execution Deadline

Repository Importance

Expected Cost

Business Criticality

Latency Objective

Priority is computed rather than hardcoded.

\-\--

# 17.6 Queue Manager

The Queue Manager maintains execution queues.

Supported queue types:

FIFO

Priority Queue

Weighted Queue

Tenant Queue

Repository Queue

Hybrid Queue

The scheduler may operate on multiple queues simultaneously.

\-\--

# 17.7 Dependency Resolution

Some tasks depend upon others.

Example

\`\`\`

Metadata Search

↓

Vector Search

↓

Candidate Collection

\`\`\`

The scheduler ensures that dependent tasks execute only after
prerequisite tasks complete.

Independent tasks are executed concurrently whenever possible.

\-\--

# 17.8 Worker Allocation

Worker selection considers:

Worker Type

Current Load

Worker Health

CPU Usage

Memory Usage

Repository Affinity

Data Locality

Network Latency

The objective is efficient execution rather than simple round-robin
assignment.

\-\--

# 17.9 Scheduling Policies

Supported policies:

First In First Out (FIFO)

Priority Scheduling

Weighted Fair Scheduling

Deadline Scheduling

Cost-aware Scheduling

Latency-aware Scheduling

Adaptive Scheduling (future)

Policies are configurable per tenant or workload.

\-\--

# 17.10 Load Balancing

Tasks are distributed across workers to:

Prevent hotspots

Maintain utilization

Reduce latency

Avoid starvation

Improve throughput

Load balancing operates continuously.

\-\--

# 17.11 Backpressure

When capacity is exceeded, the scheduler may:

Delay admission

Throttle execution

Reduce parallelism

Reject low-priority work

Preserve high-priority workloads

Backpressure is proactive rather than reactive.

\-\--

# 17.12 Starvation Prevention

High-priority tasks should not permanently block lower-priority tasks.

Mechanisms include:

Priority aging

Maximum wait thresholds

Fair-share scheduling

Queue balancing

This ensures predictable system behavior.

\-\--

# 17.13 Deadlines

Tasks may include execution deadlines.

Examples:

Interactive Retrieval

300 ms

Background Retrieval

5 seconds

Batch Retrieval

60 seconds

The scheduler attempts to satisfy these objectives while respecting
system constraints.

\-\--

# 17.14 Failure Handling

Scheduler failures include:

Worker unavailable

Queue corruption

Resource exhaustion

Admission timeout

Dependency deadlock

Recovery strategies:

Retry scheduling

Alternative worker selection

Task migration

Graceful degradation

Task cancellation

\-\--

# 17.15 Configuration

Administrators may configure:

Scheduling policy

Maximum queue size

Maximum parallel tasks

Admission thresholds

Priority weights

Fairness parameters

Worker affinity rules

Deadline policies

\-\--

# 17.16 Performance Targets

Illustrative goals:

Admission Decision

\<1 ms

Priority Calculation

\<1 ms

Queue Insertion

\<1 ms

Worker Allocation

\<2 ms

Scheduling Overhead

\<5 ms

\-\--

# 17.17 Observability

Metrics include:

Queue Depth

Average Wait Time

Scheduling Latency

Admission Reject Rate

Worker Utilization

Task Throughput

Starvation Events

Deadline Miss Rate

Load Distribution

These metrics are exported to the platform observability service.

\-\--

# 17.18 Extension Points

Future capabilities:

Predictive Scheduling

ML-based Worker Allocation

Dynamic Priority Adjustment

Cross-region Scheduling

Energy-aware Scheduling

SLA-aware Scheduling

GPU Scheduling

\-\--

# 17.19 Architecture Rules

The Execution Scheduler SHALL NOT:

Execute retrieval

Interpret user queries

Rank candidates

Modify execution plans

Generate embeddings

Retrieve documents

Its responsibility ends once a task has been assigned to an execution
worker.

\-\--

# End of Chapter 17

**🏛 Principal Architect Review (Major Architectural Improvement)**

I believe we can make EKRE significantly stronger by introducing one
more concept borrowed from modern distributed systems.

**Introduce the Execution Budget**

Today, execution plans specify *what* to do.

The scheduler should also know *what resources are allowed*.

Every Retrieval Execution Plan should carry an immutable **Execution
Budget**.

Execution Budget

Maximum Latency

Maximum Cost

Maximum CPU Time

Maximum Memory

Maximum Repository Calls

Maximum Candidate Count

Maximum Parallel Workers

Retry Budget

Timeout Budget

Instead of blindly executing tasks, the scheduler continuously tracks
budget consumption.

Execution Plan

↓

Execution Budget

↓

Scheduler

↓

Workers

If a task exceeds its budget:

- Stop additional retrieval branches.

- Reduce parallelism.

- Skip low-priority repositories.

- Switch to a degraded execution profile.

- Terminate execution if necessary.

This introduces **governance** directly into runtime execution and
prevents resource-intensive queries from monopolizing the platform.

------------------------------------------------------------------------

**📚 Updated Handbook Progress**

**Volume III --- Retrieval Execution Domain**

- ✅ Chapter 14 --- Retrieval Execution Domain Overview

- ✅ Chapter 15 --- Retrieval Orchestrator

- ✅ Chapter 16 --- Execution Runtime

- ✅ **Chapter 17 --- Execution Scheduler**

**Remaining Chapters**

- ⏳ Chapter 18 --- Retrieval Worker Framework

- ⏳ Chapter 19 --- Vector Retrieval Worker

- ⏳ Chapter 20 --- Keyword Retrieval Worker

- ⏳ Chapter 21 --- Metadata Retrieval Worker

- ⏳ Chapter 22 --- Repository Connector Framework

- ⏳ Chapter 23 --- Unified Candidate Collection Framework

- ⏳ Chapter 24 --- Candidate Fusion Framework

- ⏳ Chapter 25 --- Ranking Engine

- ⏳ Chapter 26 --- Context Assembly Engine

------------------------------------------------------------------------

**🏆 Product Manager Recommendation (Strategic Refinement)**

At this point, I would make one strategic adjustment to the overall
platform roadmap.

The **Execution Runtime** should not be treated as an internal
implementation detail of EKRE. Instead, it should be promoted to a
**first-class platform service** with its own versioning, APIs,
observability, and lifecycle. This allows EKIE, EKRE, EKCP, and future
platform components to execute workflows on the same runtime, ensuring
consistent scheduling, retry behavior, telemetry, and governance across
the Enterprise Knowledge Platform.

This decision will increase the initial implementation effort, but it
creates a durable foundation that scales with the platform rather than
requiring each product to build and maintain its own execution
infrastructure.

Excellent.

Now we are entering what I consider **the heart of the Retrieval
Execution Domain**.

Everything we\'ve designed so far exists to support one abstraction:

**The Retrieval Worker Framework**

This is where most RAG frameworks become tightly coupled.

Typically, they implement retrieval like this:

vector_search()

keyword_search()

metadata_search()

These are just functions.

That approach doesn\'t scale.

In EKRE, **retrieval is treated as a distributed workload**, where each
retrieval operation is a **worker** executing a standardized task.

This is inspired by:

- Kubernetes Pods

- Spark Executors

- Ray Workers

- Temporal Activities

- Apache Flink Operators

This architectural choice makes retrieval engines pluggable,
horizontally scalable, and independently deployable.

------------------------------------------------------------------------

**🏛 Principal Architect Review**

Before writing the Worker Framework, I think we are still missing one
important abstraction.

Currently we have:

Scheduler

↓

Worker

Instead, we should introduce a **Task Lifecycle Manager**.

Task

↓

Task Lifecycle Manager

↓

Worker

↓

Task Result

Why?

Every task should pass through the same lifecycle regardless of whether
it is:

- Vector Search

- Metadata Search

- Keyword Search

- Graph Search

- Future SQL Search

This keeps runtime behavior deterministic.

------------------------------------------------------------------------

### 17.X Event-Driven Cache Invalidation from EKIE

**Integration Contract:** EKRE Execution Scheduler subscribes directly to the EKIE Event Bus for cache invalidation.
- `DocumentDeleted`: Immediately purges associated vectors from EKRE active cache.
- `ClassificationChanged`: Immediately invalidates the security context cache for the affected document.
- `EmbeddingReprocessingCompleted`: Triggers a full cache flush and index swap.

# Chapter 18 - Retrieval Worker Framework

\-\--

# 18.1 Purpose

The Retrieval Worker Framework provides the execution abstraction for
all retrieval operations within EKRE.

Rather than embedding retrieval logic directly into the runtime,
retrieval capabilities are implemented as specialized workers that
execute standardized retrieval tasks.

This framework enables horizontal scalability, plugin extensibility, and
consistent execution semantics.

\-\--

# 18.2 Design Goals

The framework shall provide:

✓ Standard worker lifecycle

✓ Worker isolation

✓ Independent scaling

✓ Fault tolerance

✓ Pluggable implementations

✓ Deterministic execution

✓ Uniform observability

✓ Runtime independence

\-\--

# 18.3 Responsibilities

The Worker Framework is responsible for:

• Worker registration

• Worker discovery

• Task execution

• Task lifecycle

• Health reporting

• Capability advertisement

• Execution metrics

• Result standardization

The framework performs no planning.

\-\--

# 18.4 Worker Model

Every retrieval implementation is a Worker.

Examples

Vector Worker

Keyword Worker

Metadata Worker

Graph Worker

Repository Worker

Future AI Search Worker

Workers expose capabilities rather than implementation details.

\-\--

# 18.5 Internal Architecture

\`\`\`

Task

│

▼

Worker Dispatcher

│

┌──────────┼──────────┐

▼ ▼ ▼

Vector Worker Metadata Worker Keyword Worker

│ │ │

└──────────┼──────────┘

▼

Standard Result

\`\`\`

\-\--

# 18.6 Worker Lifecycle

Every worker follows the same lifecycle.

\`\`\`

CREATED

↓

INITIALIZED

↓

READY

↓

EXECUTING

↓

COMPLETED

\`\`\`

Failure paths:

\`\`\`

FAILED

TIMED_OUT

CANCELLED

DEGRADED

\`\`\`

Lifecycle transitions are recorded for every task.

\-\--

# 18.7 Worker Registration

Each worker registers with the Worker Manager.

Registration includes:

Worker ID

Capabilities

Supported Task Types

Version

Health Endpoint

Configuration

Resource Requirements

Registration is dynamic.

\-\--

# 18.8 Capability Discovery

Workers advertise capabilities.

Examples

Supports:

Vector Search

Embedding Model

Cosine Similarity

Hybrid Retrieval

Metadata Filtering

The scheduler assigns work based on capabilities rather than
implementation names.

\-\--

# 18.9 Worker Isolation

Each worker executes independently.

Isolation prevents:

Memory corruption

Shared mutable state

Cross-task interference

Repository coupling

Failures in one worker must not affect others.

\-\--

# 18.10 Task Execution Contract

Every worker receives:

Execution Context

↓

Retrieval Task

↓

Configuration Snapshot

↓

Cancellation Token

↓

Runtime Budget

Workers must treat all inputs as immutable.

\-\--

# 18.11 Standard Result Contract

Every worker returns:

Task ID

Execution ID

Worker ID

Candidate List

Execution Metrics

Warnings

Errors

Execution Duration

This standard contract simplifies downstream processing.

\-\--

# 18.12 Health Checks

Workers periodically report:

Availability

Queue Depth

Memory Usage

CPU Usage

Current Load

Error Rate

Version

The runtime uses these signals for scheduling decisions.

\-\--

# 18.13 Scaling

Workers support:

Horizontal scaling

Rolling upgrades

Graceful shutdown

Autoscaling

Canary deployments

Blue-green deployments

Scaling policies are managed by the Worker Manager.

\-\--

# 18.14 Failure Handling

Worker failures include:

Crash

Timeout

Repository failure

Network failure

Configuration error

Recovery actions:

Retry

Worker replacement

Task migration

Graceful degradation

Abort

\-\--

# 18.15 Configuration

Administrators configure:

Worker pools

Concurrency limits

Health check intervals

Retry policies

Timeouts

Scaling policies

Feature flags

\-\--

# 18.16 Performance Targets

Illustrative goals:

Worker Startup

\<100 ms

Task Initialization

\<2 ms

Execution Overhead

\<5 ms

Health Reporting

\<1 ms

Result Serialization

\<2 ms

\-\--

# 18.17 Observability

Metrics include:

Worker Utilization

Task Throughput

Execution Latency

Health Status

Failure Rate

Autoscaling Events

Queue Length

Average Task Duration

\-\--

# 18.18 Extension Points

Future worker types:

Graph Retrieval Worker

SQL Retrieval Worker

Image Retrieval Worker

Audio Retrieval Worker

Video Retrieval Worker

LLM Retrieval Worker

External Search Worker

The framework remains open for extension without modification.

\-\--

# 18.19 Architecture Rules

The Retrieval Worker Framework SHALL NOT:

Understand user intent

Generate execution plans

Rank candidates

Assemble context

Modify execution policies

Workers execute only assigned retrieval tasks.

\-\--

# End of Chapter 18

------------------------------------------------------------------------

**🏛 Principal Architect Review (Major Improvement)**

I think we can strengthen this framework further by introducing **Worker
Capabilities** as a first-class concept.

Instead of selecting workers by type:

VectorWorker

select them by advertised capabilities.

Example capability descriptor:

worker:

id: vector-worker-01

capabilities:

\- semantic-search

\- cosine-similarity

\- metadata-filtering

\- hybrid-search

supportedRepositories:

\- qdrant

\- pinecone

maxConcurrency: 32

priority: HIGH

health: HEALTHY

version: 2.1.0

The scheduler no longer asks:

\"Give me a Vector Worker.\"

Instead it asks:

\"Give me any worker that supports semantic-search with metadata
filtering against Qdrant.\"

This decouples the scheduler from concrete implementations and allows
new retrieval technologies to be introduced without changing scheduling
logic.

------------------------------------------------------------------------

**📚 Updated Handbook Progress**

**Volume III --- Retrieval Execution Domain**

- ✅ Chapter 14 --- Retrieval Execution Domain Overview

- ✅ Chapter 15 --- Retrieval Orchestrator

- ✅ Chapter 16 --- Execution Runtime

- ✅ Chapter 17 --- Execution Scheduler

- ✅ **Chapter 18 --- Retrieval Worker Framework**

**Remaining Chapters**

- ⏳ Chapter 19 --- Vector Retrieval Worker

- ⏳ Chapter 20 --- Keyword Retrieval Worker

- ⏳ Chapter 21 --- Metadata Retrieval Worker

- ⏳ Chapter 22 --- Repository Connector Framework

- ⏳ Chapter 23 --- Unified Candidate Collection Framework

- ⏳ Chapter 24 --- Candidate Fusion Framework

- ⏳ Chapter 25 --- Ranking Engine

- ⏳ Chapter 26 --- Context Assembly Engine

------------------------------------------------------------------------

**🏆 Principal Architect Recommendation (One Critical Improvement)**

Before implementing the first retrieval worker, I recommend introducing
a **Retrieval SDK** shared by all worker implementations.

Instead of each worker implementing runtime contracts independently,
provide a common SDK that includes:

- RetrievalTask interfaces

- ExecutionContext handling

- Standard result models

- Metrics instrumentation

- Logging and tracing

- Retry helpers

- Configuration loading

- Health check implementation

- Error classification

- Budget enforcement

This ensures every retrieval worker behaves consistently, dramatically
reducing implementation effort and operational complexity. It also
allows third-party or customer-developed retrieval workers to integrate
seamlessly with EKRE by conforming to a single, well-defined SDK rather
than reimplementing platform behavior. This is the same pattern used by
mature platforms such as Kubernetes Operators, Spark Connectors, and
Temporal SDKs, and it positions EKRE as an extensible enterprise
platform rather than a closed retrieval engine.

Excellent.

Now we begin implementing the **actual retrieval engines**.

Up until now, everything we\'ve built has been infrastructure:

- Planner

- Runtime

- Scheduler

- Workers

- Execution Context

- Execution Budget

- Worker SDK

Now we finally arrive at the first real retrieval engine.

And I want to make something very clear before we design it.

------------------------------------------------------------------------

**🏛 Principal Architect Review**

Most RAG systems think a Vector Retriever is simply this:

embedding = embed(query)

results = vectordb.search(

embedding,

top_k=10

)

This is **less than 10%** of what an enterprise Vector Retrieval Worker
should do.

In EKRE, the Vector Worker is **not responsible for finding documents.**

It is responsible for **executing semantic retrieval according to the
Execution Plan**.

That distinction changes everything.

------------------------------------------------------------------------

**The Vector Worker should never decide**

It should NEVER decide

- Top K

- Threshold

- Which collection

- Which embedding model

- Which repository

- Which reranking strategy

- Which filters

- Whether hybrid search is enabled

Those decisions were already made by the Planner.

Instead it simply executes.

Think SQL.

The Query Planner creates

SELECT \*

FROM Documents

WHERE Department=\'Engineering\'

LIMIT 20;

The Storage Engine executes it.

Exactly the same philosophy.

------------------------------------------------------------------------

**Proposed Runtime**

Query Planner

↓

Retrieval Execution Plan

↓

Vector Retrieval Task

↓

Vector Worker

↓

Repository Connector

↓

Vector Database

↓

Candidate Objects

Notice

The worker doesn\'t know anything about

- User

- Intent

- Planner

- Context

- LLM

It only executes semantic search.

That keeps responsibilities extremely clean.

------------------------------------------------------------------------

# Chapter 19 - Vector Retrieval Worker

\-\--

# 19.1 Purpose

The Vector Retrieval Worker (VRW) executes semantic retrieval tasks
against enterprise vector indexes.

Unlike traditional vector retrievers, the VRW never makes retrieval
decisions.

Its responsibility is to execute semantic search exactly as specified by
the Retrieval Execution Plan (REP).

The worker is deterministic, stateless, and execution-driven.

\-\--

# 19.2 Responsibilities

The Vector Retrieval Worker owns:

✓ Vector search execution

✓ Query embedding generation

✓ Filter application

✓ Candidate retrieval

✓ Result normalization

✓ Execution metrics

✓ Error reporting

✓ Budget enforcement

It performs no planning.

\-\--

# 19.3 Responsibilities NOT Owned

The worker SHALL NOT:

Interpret user intent

Choose embedding models dynamically

Determine Top-K

Select repositories

Choose ranking strategies

Merge candidate lists

Assemble context

Generate prompts

Those responsibilities belong to upstream components.

\-\--

# 19.4 Inputs

The worker receives:

Execution Context

Vector Retrieval Task

Configuration Snapshot

Repository Connection

Embedding Service

Cancellation Token

Execution Budget

\-\--

# 19.5 Outputs

Vector Retrieval Result

Containing:

Execution ID

Task ID

Worker ID

Repository ID

Candidate List

Similarity Scores

Execution Metrics

Warnings

Errors

\-\--

# 19.6 Internal Architecture

\`\`\`

Vector Retrieval Task

↓

Embedding Adapter

↓

Repository Connector

↓

Vector Database

↓

Candidate Normalizer

↓

Standard Result

\`\`\`

Each module owns one responsibility.

\-\--

# 19.7 Embedding Adapter

The worker delegates embedding generation to an Embedding Adapter.

Responsibilities:

Generate query embeddings

Support multiple embedding providers

Apply embedding normalization

Track embedding latency

Return embedding vectors

The adapter abstracts embedding implementations from the worker.

\-\--

# 19.8 Repository Connector

The worker never communicates directly with the vector database.

Instead it uses the Repository Connector Framework.

Benefits:

Vendor independence

Connection pooling

Retry management

Authentication isolation

Telemetry

Future migration support

\-\--

# 19.9 Search Execution

The search request includes:

Vector

Collection

Metadata Filters

Top-K

Similarity Metric

Search Threshold

Namespace

Execution Budget

All values originate from the Retrieval Execution Plan.

\-\--

# 19.10 Candidate Normalization

Repository-specific results are transformed into a common candidate
format.

Each candidate includes:

Document ID

Chunk ID

Repository ID

Similarity Score

Metadata

Security Labels

Source URI

Version

The normalization process is deterministic.

\-\--

# 19.11 Similarity Metrics

Supported metrics include:

Cosine Similarity

Dot Product

Euclidean Distance

Maximum Inner Product

The metric is specified by the execution plan and repository
capabilities.

\-\--

# 19.12 Filtering

The worker applies filters exactly as provided.

Examples:

Department

Language

Version

Security Classification

Document Type

Date Range

No additional filters are inferred.

\-\--

# 19.13 Budget Enforcement

During execution, the worker continuously checks:

Maximum latency

Maximum candidate count

Maximum retries

Repository call limits

If the execution budget is exceeded, the worker terminates gracefully
and reports partial progress where appropriate.

\-\--

# 19.14 Failure Handling

Potential failures include:

Embedding service unavailable

Repository timeout

Vector database unavailable

Authentication failure

Budget exceeded

Network interruption

Recovery follows runtime policies:

Retry

Failover

Graceful degradation

Abort

\-\--

# 19.15 Configuration

Administrators may configure:

Default embedding provider

Connection pools

Retry policies

Timeouts

Telemetry settings

Health checks

Worker concurrency

These settings influence execution mechanics, not retrieval strategy.

\-\--

# 19.16 Performance Targets

Illustrative goals:

Embedding Generation

\<20 ms

Repository Call

\<100 ms

Normalization

\<5 ms

Worker Overhead

\<5 ms

Total Target

\<150 ms

\-\--

# 19.17 Observability

Metrics include:

Embedding latency

Repository latency

Vector search latency

Candidate count

Similarity distribution

Retry count

Failure rate

Budget utilization

\-\--

# 19.18 Extension Points

Future enhancements:

Multi-vector retrieval

Sparse embeddings

Late interaction models

Vector compression

Approximate nearest-neighbor tuning

Adaptive search strategies

The worker remains compatible through the common Retrieval SDK.

\-\--

# 19.19 Architecture Rules

The Vector Retrieval Worker SHALL NOT:

Modify execution plans

Interpret user queries

Perform reranking

Merge candidates

Generate context

Call LLMs

Its responsibility ends after returning a normalized set of semantic
candidates.

\-\--

# End of Chapter 19

------------------------------------------------------------------------

**🏛 Principal Architect Review (Critical Architectural Improvement)**

I think we can improve the design even further.

**Introduce an Embedding Service as a Shared Platform Component**

Currently, the Vector Worker generates embeddings internally via an
adapter.

I recommend extracting this into a dedicated platform service.

Retrieval Worker

↓

Embedding Service

↓

Embedding Provider

↓

OpenAI

↓

Voyage

↓

Cohere

↓

BGE

↓

E5

↓

Local Models

**Why?**

Because embeddings are used across the entire Enterprise Knowledge
Platform:

- **EKIE** --- document chunk embeddings.

- **EKRE** --- query embeddings.

- **Future reranking** --- embedding-based similarity.

- **Clustering and analytics** --- semantic grouping.

- **Duplicate detection** --- embedding comparisons.

A shared Embedding Service provides:

- Model versioning.

- Embedding cache.

- Batch generation.

- Cost tracking.

- Model fallback.

- Telemetry.

- Consistent vector dimensions across the platform.

------------------------------------------------------------------------

**📚 Updated Handbook Progress**

**Volume III --- Retrieval Execution Domain**

- ✅ Chapter 14 --- Retrieval Execution Domain Overview

- ✅ Chapter 15 --- Retrieval Orchestrator

- ✅ Chapter 16 --- Execution Runtime

- ✅ Chapter 17 --- Execution Scheduler

- ✅ Chapter 18 --- Retrieval Worker Framework

- ✅ **Chapter 19 --- Vector Retrieval Worker**

**Remaining Chapters**

- ⏳ Chapter 20 --- Keyword Retrieval Worker

- ⏳ Chapter 21 --- Metadata Retrieval Worker

- ⏳ Chapter 22 --- Repository Connector Framework

- ⏳ Chapter 23 --- Unified Candidate Collection Framework

- ⏳ Chapter 24 --- Candidate Fusion Framework

- ⏳ Chapter 25 --- Ranking Engine

- ⏳ Chapter 26 --- Context Assembly Engine

------------------------------------------------------------------------

**🚀 Product Manager Recommendation (Important Product Decision)**

Before implementing any vector database integration (Qdrant, Pinecone,
Milvus, Weaviate, Elasticsearch, etc.), define a **Vector Repository
Abstraction** in the Repository Connector Framework.

Rather than allowing workers to depend on vendor-specific APIs, the
worker should interact with a capability-driven interface (e.g.,
search(), filter(), health(), capabilities()). This isolates
vendor-specific behavior inside connectors, making it possible to swap
vector databases, support multiple vendors simultaneously, or migrate
infrastructure without changing the worker implementation.

This design keeps the Vector Retrieval Worker focused solely on
executing semantic retrieval tasks while ensuring the Enterprise
Knowledge Platform remains portable, extensible, and resilient to
changes in the underlying vector technology stack.

Excellent.

Now we move to what I believe is one of the **most underestimated
retrieval engines** in enterprise RAG.

Most modern RAG systems focus almost exclusively on vector search.

That\'s a mistake.

In real enterprises, **keyword retrieval often outperforms semantic
retrieval** for:

- Product IDs

- Equipment IDs

- PLC Tags

- API Names

- Error Codes

- Document Numbers

- Version Numbers

- File Names

- Function Names

- Class Names

- Ticket Numbers

- Invoice IDs

- Standards (ISO, IEC, IEEE)

Example:

ABB-PLC-7X-1024

ISO-14224

API-GW-V2

ERR-5009

DOC-ENG-00241

A vector embedding is often **worse** than an inverted index for these
queries.

This is why Google, Elasticsearch, Lucene, Vespa, OpenSearch and Azure
AI Search all continue to invest heavily in keyword search.

EKRE should treat keyword retrieval as a **first-class retrieval
engine**, not a fallback.

------------------------------------------------------------------------

**🏛 Principal Architect Review**

Before writing the Keyword Worker, I think we should improve the overall
retrieval architecture.

Instead of thinking in terms of retrieval technologies:

Vector

Keyword

Metadata

Think in terms of **retrieval strategies**.

Retrieval Strategy

│

┌─────────┼─────────┐

▼ ▼ ▼

Semantic Lexical Structural

Where

Semantic

↓

Vector Worker

Lexical

↓

Keyword Worker

Structural

↓

Metadata Worker

Future

↓

Graph Worker

↓

SQL Worker

↓

Image Worker

↓

Audio Worker

↓

Video Worker

This abstraction is much more future-proof.

------------------------------------------------------------------------


### 19.X Distance Metric Synchronization

**Integration Contract:** The Vector Retrieval Worker must not hardcode the distance metric. It must dynamically query the EKIE registry (or vector database schema) to retrieve the exact `distance_metric` (Cosine, DotProduct) used during ingestion before executing the nearest-neighbor search.


# Chapter 20 - Keyword Retrieval Worker

\-\--

# 20.1 Purpose

The Keyword Retrieval Worker (KRW) executes lexical retrieval tasks
against enterprise search indexes.

Unlike semantic retrieval, lexical retrieval focuses on exact terms,
token matching, structured identifiers, and textual relevance.

The worker executes retrieval exactly as defined by the Retrieval
Execution Plan (REP).

It performs no planning.

\-\--

# 20.2 Why Keyword Retrieval Exists

Enterprise repositories contain many terms that should not be
interpreted semantically.

Examples:

Equipment IDs

API Names

Function Names

Error Codes

Product Codes

Version Numbers

Document IDs

Engineering Tags

Standards

Exact matching is often superior to vector similarity for these queries.

\-\--

# 20.3 Responsibilities

The Keyword Retrieval Worker owns:

✓ Lexical search execution

✓ Query tokenization

✓ Search expression generation

✓ Exact term matching

✓ Candidate retrieval

✓ Result normalization

✓ Execution metrics

✓ Budget enforcement

\-\--

# 20.4 Responsibilities NOT Owned

The worker SHALL NOT:

Interpret user intent

Expand synonyms

Choose search strategy

Determine repositories

Perform reranking

Merge candidate lists

Generate prompts

Those responsibilities belong to upstream components.

\-\--

# 20.5 Inputs

Execution Context

Keyword Retrieval Task

Configuration Snapshot

Repository Connector

Search Index

Cancellation Token

Execution Budget

\-\--

# 20.6 Outputs

Keyword Retrieval Result

Containing:

Execution ID

Task ID

Worker ID

Repository ID

Candidate List

Lexical Scores

Execution Metrics

Warnings

Errors

\-\--

# 20.7 Internal Architecture

\`\`\`

Keyword Retrieval Task

↓

Query Parser

↓

Search Expression Builder

↓

Repository Connector

↓

Search Index

↓

Candidate Normalizer

↓

Standard Result

\`\`\`

Each module owns one responsibility.

\-\--

# 20.8 Query Parser

The parser converts the retrieval task into a lexical query.

Examples:

Phrase Search

Boolean Search

Prefix Search

Wildcard Search

Exact Match

Field-specific Search

The parser never changes query intent.

\-\--

# 20.9 Search Expression Builder

Constructs repository-specific search syntax.

Example:

\`\`\`

status:approved

AND

department:engineering

AND

\"shutdown procedure\"

\`\`\`

Workers remain repository-independent through connector abstractions.

\-\--

# 20.10 Repository Connector

All communication occurs through the Repository Connector Framework.

Responsibilities:

Authentication

Connection Pooling

Retry Handling

Telemetry

Vendor Translation

No repository-specific logic exists inside the worker.

\-\--

# 20.11 Search Execution

Supported retrieval modes:

Exact Match

Boolean Search

Phrase Search

Field Search

Wildcard Search

Prefix Search

Fuzzy Search (optional)

The execution plan determines which modes are enabled.

\-\--

# 20.12 Candidate Normalization

Each result is normalized into the common candidate format.

Fields include:

Document ID

Chunk ID

Repository ID

Lexical Score

Matched Terms

Metadata

Security Labels

Source URI

Version

This ensures downstream components treat lexical and semantic candidates
uniformly.

\-\--

# 20.13 Scoring

Supported lexical scoring models include:

BM25

TF-IDF

Boolean Match

Repository-native Relevance

The scoring model is selected by the Query Planner and enforced by the
worker.

\-\--

# 20.14 Budget Enforcement

The worker monitors:

Latency budget

Candidate budget

Repository call budget

Retry budget

Timeout budget

Budget exhaustion results in graceful termination.

\-\--

# 20.15 Failure Handling

Examples:

Search index unavailable

Repository timeout

Authentication failure

Query parser error

Budget exceeded

Recovery follows runtime policy:

Retry

Failover

Graceful degradation

Abort

\-\--

# 20.16 Configuration

Configurable options:

Default analyzer

Search timeout

Retry policy

Connection pool size

Telemetry

Worker concurrency

Field mappings

Analyzer selection

\-\--

# 20.17 Performance Targets

Illustrative goals:

Query Parsing

\<2 ms

Search Expression Generation

\<2 ms

Repository Search

\<80 ms

Normalization

\<5 ms

Worker Overhead

\<5 ms

Total Target

\<100 ms

\-\--

# 20.18 Observability

Metrics include:

Search latency

Index latency

Candidate count

Query complexity

Analyzer usage

Retry count

Failure rate

Budget utilization

\-\--

# 20.19 Extension Points

Future capabilities:

Cross-index search

Distributed lexical search

Typo tolerance

Domain-specific analyzers

Custom tokenizers

Multilingual analyzers

Adaptive lexical ranking

\-\--

# 20.20 Architecture Rules

The Keyword Retrieval Worker SHALL NOT:

Modify execution plans

Interpret user intent

Perform semantic search

Merge candidates

Generate context

Call LLMs

Its responsibility ends after returning a normalized lexical candidate
set.

\-\--

# End of Chapter 20

------------------------------------------------------------------------

**🏛 Principal Architect Review (Major Architectural Improvement)**

I think we can improve both the Vector Worker and Keyword Worker by
introducing a **Retrieval Capability Matrix**.

Instead of hardcoding assumptions, each worker advertises supported
capabilities.

Example:

workerId: keyword-worker-01

strategy: lexical

capabilities:

exact-match: true

phrase-search: true

boolean-search: true

fuzzy-search: false

wildcard-search: true

prefix-search: true

regex-search: false

supportedIndexes:

\- Elasticsearch

\- OpenSearch

\- Lucene

supportedLanguages:

\- English

\- German

\- French

The Query Planner can use this matrix during planning to determine which
workers are eligible for a given retrieval task.

------------------------------------------------------------------------

**📚 Updated Handbook Progress**

**Volume III --- Retrieval Execution Domain**

- ✅ Chapter 14 --- Retrieval Execution Domain Overview

- ✅ Chapter 15 --- Retrieval Orchestrator

- ✅ Chapter 16 --- Execution Runtime

- ✅ Chapter 17 --- Execution Scheduler

- ✅ Chapter 18 --- Retrieval Worker Framework

- ✅ Chapter 19 --- Vector Retrieval Worker

- ✅ **Chapter 20 --- Keyword Retrieval Worker**

**Remaining Chapters**

- ⏳ Chapter 21 --- Metadata Retrieval Worker

- ⏳ Chapter 22 --- Repository Connector Framework

- ⏳ Chapter 23 --- Unified Candidate Collection Framework

- ⏳ Chapter 24 --- Candidate Fusion Framework

- ⏳ Chapter 25 --- Ranking Engine

- ⏳ Chapter 26 --- Context Assembly Engine

------------------------------------------------------------------------

**🚀 Principal Architect Recommendation (Critical Product Decision)**

Before implementing the remaining retrieval workers, I recommend
formalizing the concept of a **Retrieval Strategy Layer** as a
first-class abstraction across EKRE.

Retrieval Strategy Layer

┌──────────────────────────────────────────────────────┐

│ Semantic Strategy → Vector Worker │

│ Lexical Strategy → Keyword Worker │

│ Structural Strategy → Metadata Worker │

│ Graph Strategy → Graph Worker (Future) │

│ Relational Strategy → SQL Worker (Future) │

│ Multimodal Strategy → Image/Audio/Video Workers │

└──────────────────────────────────────────────────────┘

This separation ensures that the **Query Planner selects strategies**,
while the **Execution Runtime schedules workers** and the **workers
execute tasks**. It keeps planning, execution, and implementation
concerns cleanly separated and makes EKRE extensible as new retrieval
paradigms emerge without requiring changes to the runtime architecture.
This is the same architectural principle used in mature database
optimizers, distributed query engines, and modern workflow platforms.

Excellent.

Now we arrive at what I consider the **most overlooked retrieval
engine** in modern RAG systems.

Almost every framework supports:

- Vector Search ✅

- Keyword Search ✅

Very few properly support **Metadata Retrieval**.

This is surprising because in enterprise systems, metadata is often
**more reliable than semantic similarity**.

Examples:

- Department = Engineering

- Status = Approved

- Version = Latest

- Language = English

- Document Type = SOP

- Confidentiality = Internal

- Author = John Smith

- Project = EKRE

- Created After = 2025-01-01

Many enterprise queries are actually metadata queries disguised as
natural language.

Example:

\"Show me the latest approved shutdown SOPs from Operations.\"

This is **not primarily a semantic search problem**.

It is a **structured retrieval problem**.

This is why Metadata Retrieval deserves its own dedicated worker.

------------------------------------------------------------------------

**🏛 Principal Architect Review**

Before writing the Metadata Worker, I think we should refine the
retrieval strategy model.

Instead of only categorizing by search technology, categorize by
**information access pattern**.

Information Access

│

┌──────────────────┼───────────────────┐

▼ ▼ ▼

Semantic Lexical Structured

│ │ │

▼ ▼ ▼

Vector Worker Keyword Worker Metadata Worker

This abstraction is much cleaner because:

- **Semantic** → \"Find meaning.\"

- **Lexical** → \"Find matching text.\"

- **Structured** → \"Find matching attributes.\"

Future strategies can extend naturally:

- Graph

- Relational

- Multimodal

------------------------------------------------------------------------

# Chapter 21 - Metadata Retrieval Worker

\-\--

# 21.1 Purpose

The Metadata Retrieval Worker (MRW) executes structured retrieval tasks
using document metadata rather than document content.

Unlike semantic or lexical retrieval, metadata retrieval evaluates
structured attributes such as document properties, classifications,
governance information, and business metadata.

The worker executes metadata queries exactly as specified by the
Retrieval Execution Plan (REP).

\-\--

# 21.2 Why Metadata Retrieval Exists

Enterprise repositories contain rich metadata that can dramatically
reduce search scope before any content-based retrieval begins.

Examples:

Department

Author

Document Type

Business Unit

Project

Version

Language

Region

Confidentiality

Approval Status

Created Date

Modified Date

Retention Category

Repository

Metadata retrieval improves both precision and performance.

\-\--

# 21.3 Responsibilities

The Metadata Retrieval Worker owns:

✓ Metadata filter execution

✓ Attribute matching

✓ Repository metadata search

✓ Candidate retrieval

✓ Result normalization

✓ Execution metrics

✓ Budget enforcement

It performs no semantic interpretation.

\-\--

# 21.4 Responsibilities NOT Owned

The worker SHALL NOT:

Interpret user intent

Infer metadata

Expand metadata

Modify filters

Perform ranking

Merge candidates

Generate prompts

Those responsibilities belong to upstream components.

\-\--

# 21.5 Inputs

Execution Context

Metadata Retrieval Task

Configuration Snapshot

Repository Connector

Metadata Index

Cancellation Token

Execution Budget

\-\--

# 21.6 Outputs

Metadata Retrieval Result

Containing:

Execution ID

Task ID

Worker ID

Repository ID

Candidate List

Matched Metadata

Execution Metrics

Warnings

Errors

\-\--

# 21.7 Internal Architecture

\`\`\`

Metadata Retrieval Task

↓

Metadata Query Builder

↓

Repository Connector

↓

Metadata Index

↓

Candidate Normalizer

↓

Standard Result

\`\`\`

\-\--

# 21.8 Metadata Query Builder

The Query Builder converts structured constraints into repository-native
queries.

Examples:

\`\`\`

Department = Engineering

Status = Approved

Version = Latest

Language = English

\`\`\`

Complex predicates are supported.

Example:

\`\`\`

Department = Engineering

AND

Status = Approved

AND

CreatedDate \> 2025-01-01

\`\`\`

\-\--

# 21.9 Repository Connector

All metadata access occurs through the Repository Connector Framework.

Responsibilities include:

Connection Management

Authentication

Retry Handling

Vendor Translation

Telemetry

The worker remains repository-independent.

\-\--

# 21.10 Metadata Search

Supported operations:

Equality

Range Queries

Boolean Logic

Date Filters

Collection Membership

Existence Checks

Pattern Matching (optional)

The planner determines which operations are enabled.

\-\--

# 21.11 Candidate Normalization

Each retrieved document is normalized into the common candidate schema.

Fields include:

Document ID

Chunk ID

Repository ID

Matched Metadata

Security Labels

Version

Source URI

Metadata Confidence

Execution Metrics

\-\--

# 21.12 Metadata Validation

Before execution, metadata filters are validated.

Checks include:

Field Exists

Supported Type

Operator Validity

Value Compatibility

Repository Capability

Invalid filters are rejected before repository execution.

\-\--

# 21.13 Budget Enforcement

The worker monitors:

Latency budget

Repository calls

Candidate count

Retry budget

Execution timeout

Budget violations result in graceful termination.

\-\--

# 21.14 Failure Handling

Potential failures include:

Metadata index unavailable

Repository timeout

Authentication failure

Invalid metadata schema

Budget exceeded

Recovery follows runtime policy:

Retry

Failover

Graceful degradation

Abort

\-\--

# 21.15 Configuration

Configurable options:

Metadata schema registry

Field mappings

Supported operators

Timeouts

Retry policies

Concurrency limits

Telemetry

\-\--

# 21.16 Performance Targets

Illustrative goals:

Query Validation

\<2 ms

Query Generation

\<2 ms

Repository Search

\<40 ms

Normalization

\<5 ms

Worker Overhead

\<5 ms

Total Target

\<60 ms

\-\--

# 21.17 Observability

Metrics include:

Metadata Query Latency

Field Utilization

Operator Distribution

Candidate Count

Repository Latency

Failure Rate

Retry Count

Budget Utilization

\-\--

# 21.18 Extension Points

Future enhancements:

Dynamic Metadata Discovery

Schema Evolution

Metadata Caching

Cross-Repository Metadata Federation

Policy-Aware Metadata Search

Temporal Metadata Queries

\-\--

# 21.19 Architecture Rules

The Metadata Retrieval Worker SHALL NOT:

Interpret user intent

Generate metadata

Perform semantic search

Merge candidates

Rank candidates

Generate context

Its responsibility ends after returning normalized metadata candidates.

\-\--

# End of Chapter 21

------------------------------------------------------------------------

**🏛 Principal Architect Review (Major Improvement)**

Now I think we can significantly improve the retrieval architecture.

Right now, every worker independently communicates with repositories.

Instead, introduce a **Repository Capability Registry**.

Repository Registry

↓

SharePoint

Capabilities

• Metadata Search

• Full Text Search

• Versioning

• ACL Support

↓

Git

Capabilities

• File History

• Branch Metadata

↓

Qdrant

Capabilities

• Vector Search

• Payload Filtering

↓

Confluence

Capabilities

• Labels

• Spaces

• Attachments

Instead of assuming all repositories support the same operations, the
**Query Planner** consults this registry during planning.

Example:

Metadata Query

↓

Repository Capability Registry

↓

Can Repository X execute this filter?

↓

YES → Generate Task

NO → Skip Repository

This avoids generating retrieval tasks that are impossible to execute.

------------------------------------------------------------------------

**📚 Updated Handbook Progress**

**Volume III --- Retrieval Execution Domain**

- ✅ Chapter 14 --- Retrieval Execution Domain Overview

- ✅ Chapter 15 --- Retrieval Orchestrator

- ✅ Chapter 16 --- Execution Runtime

- ✅ Chapter 17 --- Execution Scheduler

- ✅ Chapter 18 --- Retrieval Worker Framework

- ✅ Chapter 19 --- Vector Retrieval Worker

- ✅ Chapter 20 --- Keyword Retrieval Worker

- ✅ **Chapter 21 --- Metadata Retrieval Worker**

**Remaining Chapters**

- ⏳ **Chapter 22 --- Repository Connector Framework** ⭐ *(one of the
  most important chapters)*

- ⏳ Chapter 23 --- Unified Candidate Collection Framework

- ⏳ Chapter 24 --- Candidate Fusion Framework

- ⏳ Chapter 25 --- Ranking Engine

- ⏳ Chapter 26 --- Context Assembly Engine

- ⏳ Chapter 27 --- Response Packaging & Handoff

------------------------------------------------------------------------

**🏆 Principal Architect Recommendation (Critical Design Decision)**

Before implementing any connector (SharePoint, Confluence, Qdrant, Git,
S3, Azure Blob, Elasticsearch, etc.), create a **Repository Connector
SDK** with standardized interfaces for:

- Authentication

- Connection lifecycle

- Health checks

- Capability discovery

- Query translation

- Pagination

- Retry policies

- Rate limiting

- Security context propagation

- Metrics and tracing

- Error normalization

Every repository-specific connector should implement this SDK rather
than exposing vendor-specific APIs to retrieval workers. This keeps the
Retrieval Workers completely vendor-agnostic, simplifies testing,
enables connector reuse across EKIE and EKRE, and allows new enterprise
repositories to be integrated without modifying the retrieval engine
itself. This connector abstraction will become one of the foundational
extension points of the entire Enterprise Knowledge Platform.

Excellent.

Now we reach what I consider **the architectural backbone of EKRE**.

Until now we\'ve designed:

Planner

↓

Execution Runtime

↓

Scheduler

↓

Workers

But the workers still need a way to communicate with enterprise
repositories.

This is where almost every RAG system becomes tightly coupled.

For example:

qdrant.search()

confluence.search()

sharepoint.search()

git.search()

Every worker ends up containing repository-specific logic.

This creates a maintenance nightmare.

Instead, **repository integrations should be treated as plugins**, not
retrieval engines.

This is one of the most important architectural decisions in the entire
Enterprise Knowledge Platform.

------------------------------------------------------------------------

**🏛 Principal Architect Review**

Before writing this chapter, I want to introduce a new architectural
pattern.

Instead of viewing connectors as simple API wrappers, treat them as
**Repository Drivers**, similar to database drivers.

Think of:

- JDBC

- ODBC

- ADO.NET

- Kubernetes CSI Drivers

This gives us a standardized contract while allowing repository-specific
implementations.

The architecture becomes:

Retrieval Worker

│

▼

Repository Connector SDK

│

┌─────────────────┼──────────────────┐

▼ ▼ ▼

Qdrant Driver SharePoint Driver Git Driver

▼ ▼ ▼

Repository API Repository API Repository API

The worker never knows which repository it is communicating with.

------------------------------------------------------------------------

# Chapter 22 - Repository Connector Framework

\-\--

# 22.1 Purpose

The Repository Connector Framework (RCF) provides a standardized
interface for interacting with enterprise knowledge repositories.

It abstracts repository-specific protocols, authentication mechanisms,
query languages, pagination models, and data formats behind a common
contract.

Retrieval Workers communicate exclusively with Repository Connectors.

They never interact directly with repository APIs.

\-\--

# 22.2 Design Goals

The Repository Connector Framework shall provide:

✓ Repository abstraction

✓ Vendor independence

✓ Standardized contracts

✓ Connection lifecycle management

✓ Authentication abstraction

✓ Capability discovery

✓ Retry management

✓ Rate limiting

✓ Security context propagation

✓ Unified telemetry

✓ Version compatibility

\-\--

# 22.3 Responsibilities

The Repository Connector Framework owns:

• Repository connection lifecycle

• Authentication

• Authorization context propagation

• Query translation

• Result translation

• Pagination

• Repository health monitoring

• Retry handling

• Rate limiting

• Metrics collection

• Error normalization

\-\--

# 22.4 Responsibilities NOT Owned

The Repository Connector Framework SHALL NOT:

Interpret user queries

Generate execution plans

Perform retrieval ranking

Merge candidates

Generate embeddings

Call LLMs

Modify retrieval policies

Business logic remains outside the connector layer.

\-\--

# 22.5 Architecture

\`\`\`

Retrieval Worker

│

▼

Repository Connector SDK

│

┌──────────────┼──────────────┐

▼ ▼ ▼

Qdrant Connector SharePoint Connector Git Connector

▼ ▼ ▼

Repository API Repository API Repository API

\`\`\`

Each connector implements the same interface.

\-\--

# 22.6 Repository Connector SDK

Every connector implements the following lifecycle:

Initialize

↓

Authenticate

↓

Validate Configuration

↓

Capability Discovery

↓

Execute Request

↓

Normalize Response

↓

Return Standard Result

↓

Shutdown

This lifecycle is identical across all repositories.

\-\--

# 22.7 Connector Contract

Each connector must expose standardized operations.

Core operations include:

connect()

disconnect()

health()

capabilities()

search()

metadata()

authenticate()

ping()

configuration()

No vendor-specific methods are exposed to workers.

\-\--

# 22.8 Capability Discovery

Every connector publishes supported capabilities.

Example:

Repository:

SharePoint

Capabilities:

✓ Full-text Search

✓ Metadata Search

✓ Version History

✓ ACL Enforcement

✗ Vector Search

Example:

Repository:

Qdrant

Capabilities:

✓ Vector Search

✓ Payload Filtering

✓ ANN Index

✗ Document Versioning

The Query Planner uses these capabilities during planning.

\-\--

# 22.9 Authentication

Supported authentication models:

API Key

OAuth2

Bearer Token

Basic Authentication

Client Certificate

Managed Identity

Custom Enterprise Authentication

Authentication details remain isolated within connectors.

\-\--

# 22.10 Query Translation

Workers submit standardized retrieval requests.

Connectors translate them into repository-native formats.

Example:

Standard Filter

↓

\`\`\`

Department = Engineering

\`\`\`

↓

SharePoint CAML Query

↓

or

Elasticsearch DSL

↓

or

SQL WHERE Clause

Workers never construct repository-specific queries.

\-\--

# 22.11 Result Translation

Repository responses vary significantly.

The connector converts repository-specific responses into a common
structure.

Each normalized response includes:

Document ID

Chunk ID

Repository ID

Metadata

Security Labels

Repository Version

Raw Repository Reference

Candidate Payload

Execution Metrics

\-\--

# 22.12 Pagination

The connector manages repository pagination.

Supported strategies:

Offset Pagination

Cursor Pagination

Token Pagination

Streaming

Chunked Responses

Pagination behavior is hidden from workers.

\-\--

# 22.13 Retry Management

Supported retry policies:

Immediate Retry

Exponential Backoff

Repository-specific Retry

Adaptive Retry

Circuit Breaker

Retries are transparent to workers.

\-\--

# 22.14 Rate Limiting

The connector respects repository limits.

Capabilities include:

Token Bucket

Fixed Window

Sliding Window

Adaptive Throttling

Repository Quotas

This prevents repository overload.

\-\--

# 22.15 Security Context Propagation

Every request propagates:

Tenant ID

User Identity

Access Token

Security Labels

Compliance Context

Audit Context

The connector never elevates permissions.

\-\--

# 22.16 Error Normalization

Repository-specific errors are translated into platform-standard errors.

Examples:

Authentication Failed

Repository Unavailable

Permission Denied

Rate Limited

Timeout

Schema Mismatch

Workers handle standardized errors rather than vendor-specific
exceptions.

\-\--

# 22.17 Health Monitoring

Each connector periodically reports:

Availability

Authentication Status

Connection Health

Latency

Rate Limit Status

Version

Capability Changes

These metrics feed the platform observability service.

\-\--

# 22.18 Configuration

Connector configuration includes:

Repository Endpoint

Authentication Provider

Timeouts

Retry Policies

Connection Pools

TLS Settings

Telemetry

Feature Flags

Configurations are externalized and version-controlled.

\-\--

# 22.19 Performance Targets

Illustrative goals:

Connection Reuse

\>95%

Authentication Overhead

\<5 ms

Query Translation

\<2 ms

Result Normalization

\<5 ms

Connector Overhead

\<10 ms

\-\--

# 22.20 Extension Points

Future connectors:

Microsoft Graph

Google Drive

Box

Dropbox

Jira

ServiceNow

Snowflake

SAP

Databricks

Neo4j

MongoDB

S3

Azure Blob Storage

No runtime modifications are required to support new connectors.

\-\--

# 22.21 Architecture Rules

The Repository Connector Framework SHALL NOT:

Interpret user intent

Perform retrieval planning

Execute ranking

Merge candidates

Generate embeddings

Call language models

Its sole responsibility is to provide standardized, secure, and
observable access to enterprise repositories.

\-\--

# End of Chapter 22

------------------------------------------------------------------------

**🏛 Principal Architect Review (One of the Biggest Improvements So
Far)**

I believe we can strengthen the connector architecture by introducing a
**Repository Registry Service** as a shared platform component.

Instead of hardcoding connector configurations, maintain a central
registry.

Repository Registry

│

┌───────────────────┼────────────────────┐

▼ ▼ ▼

Repository Catalog Capability Catalog Health Catalog

│ │ │

▼ ▼ ▼

SharePoint Metadata Search HEALTHY

Confluence Full Text Search DEGRADED

Qdrant Vector Search HEALTHY

Git Version History HEALTHY

S3 Object Storage HEALTHY

This service becomes the **source of truth** for repository metadata
across the Enterprise Knowledge Platform.

The **Query Planner** consults it during planning.

The **Execution Runtime** consults it during scheduling.

The **Repository Connectors** update it with health and capability
information.

------------------------------------------------------------------------

**📚 Updated Handbook Progress**

**Volume III --- Retrieval Execution Domain**

**Core Runtime**

- ✅ Chapter 14 --- Retrieval Execution Domain Overview

- ✅ Chapter 15 --- Retrieval Orchestrator

- ✅ Chapter 16 --- Execution Runtime

- ✅ Chapter 17 --- Execution Scheduler

**Worker Framework**

- ✅ Chapter 18 --- Retrieval Worker Framework

- ✅ Chapter 19 --- Vector Retrieval Worker

- ✅ Chapter 20 --- Keyword Retrieval Worker

- ✅ Chapter 21 --- Metadata Retrieval Worker

**Repository Layer**

- ✅ **Chapter 22 --- Repository Connector Framework**

**Remaining Chapters**

- ⏳ **Chapter 23 --- Unified Candidate Collection Framework** ⭐

- ⏳ Chapter 24 --- Candidate Fusion Framework

- ⏳ Chapter 25 --- Ranking Engine

- ⏳ Chapter 26 --- Context Assembly Engine

- ⏳ Chapter 27 --- Response Packaging & Handoff

------------------------------------------------------------------------

**🏆 Principal Architect Recommendation (Critical Architectural
Refinement)**

Before moving on to candidate collection, I recommend formalizing a
**Knowledge Object Model (KOM)** for the entire Enterprise Knowledge
Platform.

Today, every connector normalizes repository-specific responses into a
common candidate format. Instead of defining that format implicitly
within the connector layer, introduce a platform-wide **Knowledge Object
Model** that represents documents, chunks, metadata, security labels,
versions, provenance, and repository references.

Every component---from **EKIE** (ingestion) to **EKRE** (retrieval) and
future services like **EKCP**---should exchange knowledge through this
single canonical model. This eliminates repeated data transformations,
simplifies interoperability, and ensures every subsystem speaks the same
\"knowledge language.\" It is a foundational decision that will make the
platform easier to evolve as new repositories, retrieval strategies, and
downstream AI capabilities are added.

Excellent.

Now we arrive at what I consider **the convergence point of the entire
Retrieval Engine**.

Everything we have built so far produces one thing:

Candidate Lists

Vector Worker

↓

Candidate List A

Keyword Worker

↓

Candidate List B

Metadata Worker

↓

Candidate List C

But these lists are still completely independent.

The next subsystem is responsible for **collecting** them into one
unified representation.

Notice I said **collecting**, not **ranking**.

Those are two completely different responsibilities.

This separation is one of the biggest differences between EKRE and
traditional RAG systems.

------------------------------------------------------------------------

**🏛 Principal Architect Review**

Let\'s first redesign this part.

Most RAG systems do something like:

Vector Results

\+

Keyword Results

↓

Merge

↓

Rerank

That is actually mixing **three different responsibilities**:

- Collection

- Deduplication

- Ranking

These should never exist in the same component.

Instead we should build a **Candidate Pipeline**.

Workers

↓

Candidate Collector

↓

Candidate Normalizer

↓

Duplicate Resolver

↓

Candidate Store

↓

Fusion Engine

↓

Ranking Engine

Each stage has exactly one responsibility.

This is a much cleaner enterprise architecture.

------------------------------------------------------------------------

**Volume III**

# Chapter 23 - Unified Candidate Collection Framework

\-\--

# 23.1 Purpose

The Unified Candidate Collection Framework (UCCF) is responsible for
collecting candidate results produced by multiple retrieval workers into
a single standardized candidate set.

It does not perform ranking, deduplication, or context assembly.

Its responsibility is to create a deterministic, observable, and
immutable collection of retrieval candidates.

\-\--

# 23.2 Why Candidate Collection Exists

Retrieval workers execute independently.

Example:

\`\`\`

Vector Worker

↓

12 Candidates

\`\`\`

\`\`\`

Keyword Worker

↓

8 Candidates

\`\`\`

\`\`\`

Metadata Worker

↓

20 Candidates

\`\`\`

Without a standardized collection process:

\- Candidate formats differ.

\- Execution ordering becomes nondeterministic.

\- Observability becomes inconsistent.

\- Downstream ranking becomes difficult.

The UCCF solves this by producing a Unified Candidate Set (UCS).

\-\--

# 23.3 Responsibilities

The Unified Candidate Collection Framework owns:

✓ Candidate collection

✓ Candidate normalization validation

✓ Candidate aggregation

✓ Candidate provenance tracking

✓ Execution ordering

✓ Collection metrics

✓ Collection lifecycle

It performs no ranking.

\-\--

# 23.4 Responsibilities NOT Owned

The framework SHALL NOT:

Remove duplicates

Rank candidates

Fuse scores

Interpret metadata

Generate prompts

Assemble context

Call LLMs

\-\--

# 23.5 Inputs

The framework receives:

Execution Context

Candidate Streams

Worker Metadata

Execution Metrics

Collection Policy

Execution Budget

\-\--

# 23.6 Outputs

Unified Candidate Set (UCS)

Containing:

Execution ID

Collection ID

Candidate List

Worker Sources

Collection Metrics

Execution Trace

Warnings

Errors

The UCS becomes the canonical input for downstream processing.

\-\--

# 23.7 Internal Architecture

\`\`\`

Vector Candidates

↓

Keyword Candidates

↓

Metadata Candidates

↓

Candidate Collector

↓

Candidate Validator

↓

Provenance Recorder

↓

Unified Candidate Set

\`\`\`

Each stage owns a single responsibility.

\-\--

# 23.8 Candidate Collector

The collector receives candidate streams from retrieval workers.

Responsibilities:

Collect

Buffer

Order

Track source worker

Track repository

Preserve execution metadata

Collection does not alter candidate content.

\-\--

# 23.9 Candidate Validation

Before collection completes, every candidate is validated.

Checks include:

Required fields

Candidate schema

Repository ID

Document ID

Execution ID

Security labels

Malformed candidates are rejected and logged.

\-\--

# 23.10 Provenance Tracking

Every candidate maintains complete lineage.

Captured attributes include:

Worker ID

Repository ID

Retrieval Strategy

Execution Timestamp

Execution Duration

Similarity Score (if applicable)

Lexical Score (if applicable)

Metadata Match (if applicable)

Planner Task ID

Execution Session

This information is immutable.

\-\--

# 23.11 Collection Ordering

Candidate ordering during collection follows deterministic rules.

Default ordering:

Worker Completion Time

↓

Candidate Arrival Time

↓

Candidate Identifier

This ordering is temporary.

Ranking occurs later.

\-\--

# 23.12 Collection Policies

Supported policies include:

Complete Collection

Budget-limited Collection

Streaming Collection

Incremental Collection

Repository-aware Collection

Adaptive Collection (Future)

Policy selection is determined by the Query Planner.

\-\--

# 23.13 Streaming Support

The framework supports progressive collection.

Workers may stream candidates as they become available.

Benefits:

Reduced latency

Progressive ranking

Early termination

Interactive retrieval

Streaming is transparent to downstream components.

\-\--

# 23.14 Budget Enforcement

Collection respects:

Latency budget

Maximum candidates

Memory budget

Execution timeout

Streaming limits

Collection terminates gracefully when budgets are exhausted.

\-\--

# 23.15 Failure Handling

Possible failures:

Malformed candidate

Worker disconnect

Collection timeout

Memory exhaustion

Execution cancellation

Recovery:

Continue with remaining candidates

Record warning

Maintain execution trace

Never corrupt the Unified Candidate Set.

\-\--

# 23.16 Configuration

Administrators configure:

Maximum candidate count

Streaming buffer size

Validation rules

Collection policy

Memory limits

Telemetry

Timeouts

\-\--

# 23.17 Performance Targets

Illustrative goals:

Candidate Validation

\<1 ms per candidate

Collection Overhead

\<5 ms

Streaming Buffer

\<2 ms

Unified Candidate Set Generation

\<10 ms

\-\--

# 23.18 Observability

Metrics include:

Candidate Count

Candidates per Worker

Candidates per Repository

Collection Latency

Validation Failures

Streaming Throughput

Memory Usage

Collection Success Rate

\-\--

# 23.19 Extension Points

Future enhancements:

Distributed Collection

Cross-region Collection

Adaptive Buffers

Persistent Candidate Store

Collection Replay

Checkpoint Recovery

\-\--

# 23.20 Architecture Rules

The Unified Candidate Collection Framework SHALL NOT:

Perform ranking

Remove duplicates

Modify candidate scores

Generate context

Interpret queries

Call language models

Its responsibility ends after producing a valid Unified Candidate Set.

\-\--

# End of Chapter 23

------------------------------------------------------------------------

**🏛 Principal Architect Review (Major Improvement)**

Now I think we should introduce something that will become central to
the entire platform:

**Knowledge Object Model (KOM)**

Earlier I suggested a canonical knowledge model. Now it\'s time to
formalize it.

Instead of every component defining its own candidate schema, define one
immutable platform object.

Knowledge Object

├── Object ID

├── Document ID

├── Chunk ID

├── Repository ID

├── Repository Type

├── Retrieval Strategy

├── Retrieval Worker

├── Security Labels

├── Metadata

├── Version

├── Content

├── Embedding Reference

├── Source URI

├── Provenance

├── Scores

│ ├── Semantic Score

│ ├── Lexical Score

│ ├── Metadata Score

│ └── Future Scores\...

├── Audit Information

└── Execution Metadata

Every subsystem in the Enterprise Knowledge Platform exchanges
**Knowledge Objects**, not ad hoc JSON payloads.

Benefits:

- **EKIE** produces Knowledge Objects during ingestion.

- **EKRE** retrieves Knowledge Objects.

- Future rerankers enrich Knowledge Objects.

- Context Assembly consumes Knowledge Objects.

- Response Generation references Knowledge Objects for citations.

- Analytics, governance, and auditing all operate on the same canonical
  structure.

This single decision eliminates countless format conversions and creates
a stable contract across the platform.

------------------------------------------------------------------------

**📚 Updated Handbook Progress**

**Volume III --- Retrieval Execution Domain**

**Runtime**

- ✅ Chapter 14 --- Retrieval Execution Domain Overview

- ✅ Chapter 15 --- Retrieval Orchestrator

- ✅ Chapter 16 --- Execution Runtime

- ✅ Chapter 17 --- Execution Scheduler

**Workers**

- ✅ Chapter 18 --- Retrieval Worker Framework

- ✅ Chapter 19 --- Vector Retrieval Worker

- ✅ Chapter 20 --- Keyword Retrieval Worker

- ✅ Chapter 21 --- Metadata Retrieval Worker

**Repository Layer**

- ✅ Chapter 22 --- Repository Connector Framework

**Candidate Processing**

- ✅ **Chapter 23 --- Unified Candidate Collection Framework**

**Remaining Chapters**

- ⏳ **Chapter 24 --- Candidate Fusion Framework** ⭐ *(arguably the
  most technically sophisticated part of EKRE)*

- ⏳ Chapter 25 --- Ranking Engine

- ⏳ Chapter 26 --- Context Assembly Engine

- ⏳ Chapter 27 --- Response Packaging & Handoff

- ⏳ Chapter 28 --- Observability & End-to-End Traceability

- ⏳ Chapter 29 --- Security, Governance & Compliance

- ⏳ Chapter 30 --- Deployment Architecture & Scalability

------------------------------------------------------------------------

**🚀 Principal Architect Recommendation (Before Chapter 24)**

Before we design the Candidate Fusion Framework, I recommend making one
additional architectural distinction that will significantly improve
EKRE.

Introduce two separate concepts:

1.  **Candidate** --- the raw retrieval result returned by a worker. It
    is immutable and represents exactly what the repository returned
    after normalization.

2.  **Knowledge Object** --- the enriched platform entity built from one
    or more candidates. It can carry additional scores, provenance,
    governance metadata, policy decisions, and enrichment added by
    downstream components.

This distinction prevents retrieval from being coupled to later
enrichment stages. The Collection Framework should manage
**Candidates**, while the Fusion, Ranking, and Context Assembly stages
progressively transform them into **Knowledge Objects**. This layered
model keeps each stage focused, simplifies testing, and provides a clean
evolution path as the Enterprise Knowledge Platform grows in
sophistication.

Excellent.

Now we reach what I personally consider **the crown jewel of EKRE**.

Not Vector Search.

Not Hybrid Search.

Not Reranking.

The **Candidate Fusion Framework**.

------------------------------------------------------------------------

**🏛 Principal Architect Review**

Almost every RAG framework confuses these three concepts:

Hybrid Search

Fusion

Ranking

These are **not** the same.

Let\'s separate them.

  ---------------------------------------------------------------------
  **Stage**       **Responsibility**                **Output**
  --------------- --------------------------------- -------------------
  Retrieval       Retrieve independent candidate    Candidates
                  lists                             

  Collection      Aggregate candidates              Unified Candidate
                                                    Set

  Fusion          Identify equivalent knowledge and Fused Knowledge Set
                  enrich                            

  Ranking         Determine relevance ordering      Ranked Knowledge
                                                    Set

  Context         Build LLM context                 Retrieval Context Package
  Assembly                                          
  ---------------------------------------------------------------------

Notice something important.

**Fusion happens BEFORE Ranking.**

Most RAG systems do this incorrectly.

------------------------------------------------------------------------

**Why?**

Suppose we have

Vector Worker

↓

Document A

Score = 0.91

Keyword Worker

↓

Document A

Score = 12.4 BM25

Metadata Worker

↓

Document A

Status = Approved

Traditional RAG

Merge

↓

Rank

Wrong.

Because we actually have

**one document**

represented three different ways.

Instead we should first create

Knowledge Object

↓

Semantic Evidence

↓

Lexical Evidence

↓

Metadata Evidence

Then rank it.

This is how enterprise retrieval engines should work.

------------------------------------------------------------------------

**New Pipeline**

Workers

↓

Candidate Collection

↓

Candidate Fusion

↓

Knowledge Object

↓

Ranking

↓

Context Assembly

This is a major architectural improvement.

------------------------------------------------------------------------

# Chapter 24 - Candidate Fusion Framework

\-\--

# 24.1 Purpose

The Candidate Fusion Framework (CFF) transforms multiple retrieval
candidates representing the same underlying knowledge into a single
enriched Knowledge Object.

Unlike ranking, fusion does not determine relevance.

Instead, it combines complementary evidence from multiple retrieval
strategies into a unified representation.

\-\--

# 24.2 Why Fusion Exists

Multiple retrieval strategies frequently discover the same document.

Example

Vector Worker

↓

Engineering_SOP.pdf

Keyword Worker

↓

Engineering_SOP.pdf

Metadata Worker

↓

Engineering_SOP.pdf

These are not three independent results.

They are three observations of one knowledge asset.

Fusion consolidates them.

\-\--

# 24.3 Responsibilities

The Candidate Fusion Framework owns:

✓ Candidate identity resolution

✓ Candidate grouping

✓ Evidence aggregation

✓ Provenance preservation

✓ Score preservation

✓ Knowledge Object creation

✓ Fusion metrics

It performs no ranking.

\-\--

# 24.4 Responsibilities NOT Owned

The framework SHALL NOT:

Rank Knowledge Objects

Discard relevant information

Interpret user intent

Generate prompts

Assemble context

Call language models

\-\--

# 24.5 Inputs

Execution Context

Unified Candidate Set

Fusion Policy

Knowledge Object Model

Execution Budget

\-\--

# 24.6 Outputs

Fused Knowledge Set (FKS)

Containing:

Knowledge Objects

Fusion Metadata

Evidence Graph

Fusion Metrics

Execution Trace

\-\--

# 24.7 Internal Architecture

\`\`\`

Unified Candidate Set

↓

Identity Resolver

↓

Candidate Grouper

↓

Evidence Aggregator

↓

Knowledge Object Builder

↓

Fused Knowledge Set

\`\`\`

Each stage owns exactly one responsibility.

\-\--

# 24.8 Identity Resolution

Determine whether multiple candidates refer to the same knowledge asset.

Matching signals include:

Document ID

Chunk ID

Repository ID

Version

Checksum

Canonical URI

Repository-native identifiers

Identity rules are deterministic.

\-\--

# 24.9 Candidate Grouping

Candidates representing the same knowledge are grouped together.

Example

Knowledge Object A

├── Vector Candidate

├── Keyword Candidate

└── Metadata Candidate

Grouping never changes candidate content.

\-\--

# 24.10 Evidence Aggregation

Evidence from each candidate is preserved.

Examples:

Semantic Similarity

Lexical Relevance

Metadata Match

Repository Confidence

Security Labels

Version Information

Each evidence source remains independently traceable.

\-\--

# 24.11 Knowledge Object Builder

Creates immutable Knowledge Objects.

Each object contains:

Knowledge ID

Document Information

Chunk Information

Evidence Sources

Repository References

Metadata

Security Context

Version

Content Reference

Scores

Audit Information

Execution Metadata

Knowledge Objects become the canonical entities for downstream
processing.

\-\--

# 24.12 Provenance Preservation

Every Knowledge Object records:

Originating Worker

Originating Repository

Retrieval Strategy

Execution Timestamp

Execution Session

Candidate Lineage

Transformation History

No provenance information is discarded.

\-\--

# 24.13 Fusion Policies

Supported policies include:

Strict Identity

Repository Identity

Version-aware Identity

Chunk-aware Identity

Document-aware Identity

Custom Identity Rules

Policy selection is determined during planning.

\-\--

# 24.14 Streaming Fusion

Fusion supports streaming.

As candidates arrive:

↓

Identity Resolution

↓

Knowledge Object Update

↓

Streaming Output

Knowledge Objects evolve incrementally.

\-\--

# 24.15 Budget Enforcement

Fusion respects:

Latency budget

Memory budget

Maximum Knowledge Objects

Execution timeout

Streaming limits

Budget violations trigger graceful degradation.

\-\--

# 24.16 Failure Handling

Examples:

Identity conflict

Version mismatch

Missing metadata

Corrupted candidate

Budget exceeded

Recovery:

Skip conflicting evidence

Record warning

Continue processing

Maintain immutable audit trail

\-\--

# 24.17 Configuration

Administrators configure:

Identity rules

Version policy

Chunk policy

Fusion policy

Streaming

Memory limits

Telemetry

\-\--

# 24.18 Performance Targets

Illustrative goals:

Identity Resolution

\<2 ms

Candidate Grouping

\<5 ms

Knowledge Object Creation

\<5 ms

Fusion Overhead

\<10 ms

\-\--

# 24.19 Observability

Metrics include:

Fusion Rate

Duplicate Candidates

Knowledge Objects Created

Evidence Sources

Fusion Latency

Identity Conflicts

Memory Usage

Budget Utilization

\-\--

# 24.20 Extension Points

Future capabilities:

Cross-repository identity

Knowledge graph fusion

Entity resolution

Semantic deduplication

Ontology-aware fusion

Cross-language fusion

\-\--

# 24.21 Architecture Rules

The Candidate Fusion Framework SHALL NOT:

Rank Knowledge Objects

Modify retrieval plans

Generate prompts

Interpret user intent

Call LLMs

Its responsibility ends after producing immutable Knowledge Objects.

\-\--

# End of Chapter 24

------------------------------------------------------------------------

**🏛 Principal Architect Review (One of the Biggest Architectural
Improvements)**

I believe EKRE can go even further.

Instead of treating fusion as simple deduplication, introduce an
**Evidence Model**.

Today we have

Knowledge Object

↓

Scores

Instead we should model

Knowledge Object

│

├── Semantic Evidence

├── Lexical Evidence

├── Metadata Evidence

├── Repository Evidence

├── Governance Evidence

├── Temporal Evidence

├── Popularity Evidence

└── Future AI Evidence

Notice something important.

A Knowledge Object no longer has

One Score

It has

Multiple Evidence Sources

Ranking becomes much more explainable.

------------------------------------------------------------------------

**Example**

Instead of

Document A

Score = 0.91

We have

Knowledge Object A

Semantic Evidence

Similarity = 0.91

Lexical Evidence

BM25 = 17.2

Metadata Evidence

Department = Engineering

Repository Evidence

SharePoint

Governance Evidence

Approved

Temporal Evidence

Modified = Yesterday

Now the Ranking Engine has **rich evidence** instead of a single opaque
score.

This is a major architectural improvement for explainability, debugging,
governance, and future AI reasoning.

------------------------------------------------------------------------

**📚 Handbook Progress**

**Volume III --- Retrieval Execution Domain**

**Runtime**

- ✅ Chapter 14 --- Retrieval Execution Domain Overview

- ✅ Chapter 15 --- Retrieval Orchestrator

- ✅ Chapter 16 --- Execution Runtime

- ✅ Chapter 17 --- Execution Scheduler

**Workers**

- ✅ Chapter 18 --- Retrieval Worker Framework

- ✅ Chapter 19 --- Vector Retrieval Worker

- ✅ Chapter 20 --- Keyword Retrieval Worker

- ✅ Chapter 21 --- Metadata Retrieval Worker

**Repository Layer**

- ✅ Chapter 22 --- Repository Connector Framework

**Candidate Processing**

- ✅ Chapter 23 --- Unified Candidate Collection Framework

- ✅ **Chapter 24 --- Candidate Fusion Framework**

**Remaining Chapters**

- ⏳ **Chapter 25 --- Ranking Engine** ⭐ *(the intelligence layer that
  converts evidence into relevance)*

- ⏳ Chapter 26 --- Context Assembly Engine

- ⏳ Chapter 27 --- Response Packaging & Handoff

- ⏳ Chapter 28 --- Observability & End-to-End Traceability

- ⏳ Chapter 29 --- Security, Governance & Compliance

- ⏳ Chapter 30 --- Deployment Architecture & Scalability

------------------------------------------------------------------------

**🏆 Principal Architect Recommendation (Critical Architectural
Refinement)**

Before designing the Ranking Engine, I recommend introducing a formal
**Evidence Framework** as a platform-wide abstraction.

Instead of every ranking algorithm consuming raw scores, define
immutable evidence types with standardized schemas, confidence values,
provenance, timestamps, and quality indicators. The Candidate Fusion
Framework would produce these evidence objects, and the Ranking Engine
would consume them to compute relevance.

This approach provides several long-term advantages:

- **Explainability**: Every ranking decision can be traced back to
  specific evidence.

- **Extensibility**: New evidence sources (graph relationships, user
  feedback, document freshness, AI-generated quality signals) can be
  added without redesigning the ranking engine.

- **Governance**: Evidence can be audited independently of ranking
  logic.

- **Experimentation**: Different ranking algorithms can operate over the
  same evidence model.

- **Platform Reuse**: Future products in the Enterprise Knowledge
  Platform can consume the same evidence framework for recommendations,
  analytics, or knowledge discovery.

This moves EKRE beyond a traditional RAG pipeline into a **knowledge
reasoning platform**, where retrieval is no longer based on isolated
scores but on a rich, explainable body of evidence.

Excellent.

Now we reach what I consider the **brain of the Retrieval Execution
Domain**.

If the Query Intelligence Domain answered:

**\"How should retrieval happen?\"**

And the Retrieval Execution Domain answered:

**\"Execute retrieval.\"**

Then the Ranking Engine answers:

**\"Which knowledge is most valuable for answering the user\'s
question?\"**

This is a fundamentally different responsibility.

------------------------------------------------------------------------

**🏛 Principal Architect Review**

Before designing the Ranking Engine, I want to make one architectural
correction that I believe will significantly improve EKRE.

Most RAG systems have a single ranking step:

Candidates

↓

Cross Encoder

↓

Top 10

This works for demos.

It is insufficient for enterprise systems.

Instead, EKRE should use a **multi-stage ranking pipeline**, similar to
modern search engines like Google, Bing, and enterprise search
platforms.

The ranking process should progressively refine candidates.

Knowledge Objects

↓

Eligibility Filter

↓

Evidence Scoring

↓

Business Policy Ranking

↓

LLM Reranking (Optional)

↓

Final Ranking

Each stage answers a different question:

- **Eligibility** → Can this object be shown?

- **Evidence** → How relevant is it?

- **Business Policy** → Should governance or business rules adjust its
  position?

- **LLM Reranking** → Does deep semantic reasoning improve the order?

- **Final Ranking** → Produce the ordered knowledge set.

This architecture separates concerns and allows each stage to evolve
independently.

------------------------------------------------------------------------

# Chapter 25 - Ranking Engine

\-\--

# 25.1 Purpose

The Ranking Engine determines the relevance ordering of Knowledge
Objects produced by the Candidate Fusion Framework.

Unlike retrieval, which discovers knowledge, or fusion, which
consolidates knowledge, ranking evaluates the available evidence and
produces an ordered set of Knowledge Objects most suitable for
downstream context assembly.

Ranking is deterministic, explainable, configurable, and
evidence-driven.

\-\--

# 25.2 Responsibilities

The Ranking Engine owns:

✓ Eligibility evaluation

✓ Evidence scoring

✓ Score aggregation

✓ Policy-aware ranking

✓ Ranking explanations

✓ Final ordering

✓ Ranking metrics

✓ Budget enforcement

\-\--

# 25.3 Responsibilities NOT Owned

The Ranking Engine SHALL NOT:

Retrieve documents

Modify Knowledge Objects

Interpret user intent

Generate prompts

Assemble context

Call repositories

Perform document ingestion

\-\--

# 25.4 Inputs

Execution Context

Fused Knowledge Set

Evidence Objects

Ranking Policy

Execution Budget

Optional LLM Reranker

\-\--

# 25.5 Outputs

Ranked Knowledge Set (RKS)

Containing:

Execution ID

Knowledge Objects

Final Rank

Ranking Explanation

Evidence Summary

Ranking Metrics

Execution Trace

The Ranked Knowledge Set becomes the canonical input for Context
Assembly.

\-\--

# 25.6 Internal Architecture

\`\`\`

Fused Knowledge Set

↓

Eligibility Filter

↓

Evidence Scorer

↓

Policy Engine

↓

Optional LLM Reranker

↓

Final Rank Calculator

↓

Ranked Knowledge Set

\`\`\`

Each component owns a single responsibility.

\-\--

# 25.7 Eligibility Filter

Before scoring, Knowledge Objects are evaluated for eligibility.

Checks include:

Security permissions

Document visibility

Version validity

Retention status

Repository availability

Content completeness

Only eligible objects continue to ranking.

\-\--

# 25.8 Evidence Scoring

Each Knowledge Object contains multiple evidence sources.

Examples:

Semantic Evidence

Lexical Evidence

Metadata Evidence

Governance Evidence

Temporal Evidence

Repository Evidence

Popularity Evidence

Each evidence type contributes independently.

\-\--

# 25.9 Score Aggregation

Evidence is aggregated into a composite ranking score.

Illustrative formula:

Final Score =

Semantic Weight

\+

Lexical Weight

\+

Metadata Weight

\+

Freshness Weight

\+

Business Weight

\+

Repository Trust Weight

Weights are configurable.

The aggregation strategy is versioned and auditable.

\-\--

# 25.10 Policy Engine

Business policies may adjust rankings.

Examples:

Boost approved documents

Demote archived versions

Prefer official documentation

Boost tenant-specific repositories

Penalize stale documents

Policies modify ranking---not underlying evidence.

\-\--

# 25.11 Optional LLM Reranking

For high-value or complex queries, an LLM-based reranker may refine
ordering.

Responsibilities:

Deep semantic comparison

Intent-sensitive ordering

Context-aware prioritization

Explainability metadata

The reranker operates only within the execution budget.

\-\--

# 25.12 Final Rank Calculator

Assigns final positions.

Output includes:

Rank

Composite Score

Evidence Breakdown

Applied Policies

Ranking Confidence

No Knowledge Object content is modified.

\-\--

# 25.13 Ranking Policies

Supported policies:

Evidence-weighted

Freshness-first

Governance-first

Repository-priority

Business-priority

Hybrid

Custom enterprise policy

Policies are configurable per tenant or workload.

\-\--

# 25.14 Budget Enforcement

Ranking respects:

Latency budget

Maximum reranking candidates

LLM token budget

Memory budget

Execution timeout

When budgets are exceeded:

Skip optional reranking

Reduce candidate set

Fall back to deterministic ranking

Graceful degradation is preferred.

\-\--

# 25.15 Failure Handling

Examples:

Policy evaluation failure

Evidence inconsistency

LLM unavailable

Budget exceeded

Ranking timeout

Recovery:

Fallback ranking

Partial ranking

Record warnings

Continue execution

\-\--

# 25.16 Configuration

Administrators configure:

Evidence weights

Policy sets

Maximum rerank candidates

LLM provider

Latency thresholds

Confidence thresholds

Feature flags

\-\--

# 25.17 Performance Targets

Illustrative goals:

Eligibility Filter

\<5 ms

Evidence Aggregation

\<10 ms

Policy Evaluation

\<5 ms

LLM Reranking (optional)

\<150 ms

Total Deterministic Ranking

\<25 ms

\-\--

# 25.18 Observability

Metrics include:

Ranking latency

Evidence utilization

Policy applications

Ranking confidence

LLM rerank usage

Budget utilization

Ranking consistency

Top-K stability

\-\--

# 25.19 Extension Points

Future enhancements:

Learning-to-Rank

Personalized ranking

Graph-aware ranking

Behavioral ranking

Federated ranking

Neural ranking

Domain-specific ranking models

\-\--

# 25.20 Architecture Rules

The Ranking Engine SHALL NOT:

Retrieve knowledge

Modify evidence

Assemble context

Generate prompts

Call enterprise repositories

Its responsibility ends after producing the Ranked Knowledge Set.

\-\--

# End of Chapter 25

------------------------------------------------------------------------

**🏛 Principal Architect Review (Major Architectural Improvement)**

Now I think we can make EKRE even more powerful by introducing the
concept of a **Ranking Pipeline**.

Instead of treating ranking as a monolithic algorithm, define it as a
configurable pipeline of stages.

Ranking Pipeline

↓

Eligibility Stage

↓

Evidence Aggregation Stage

↓

Policy Stage

↓

Deterministic Ranking Stage

↓

Optional LLM Reranking Stage

↓

Confidence Evaluation Stage

↓

Final Ranking

This architecture provides several advantages:

- **Modularity**: Each stage can evolve independently.

- **Configurability**: Different workloads can enable or disable stages.

- **Performance**: Optional stages (such as LLM reranking) can be
  skipped when latency budgets are tight.

- **Explainability**: Every stage contributes traceable information to
  the final ranking decision.

- **Experimentation**: New ranking techniques can be inserted without
  redesigning the engine.

------------------------------------------------------------------------

**📚 Updated Handbook Progress**

**Volume III --- Retrieval Execution Domain**

**Runtime**

- ✅ Chapter 14 --- Retrieval Execution Domain Overview

- ✅ Chapter 15 --- Retrieval Orchestrator

- ✅ Chapter 16 --- Execution Runtime

- ✅ Chapter 17 --- Execution Scheduler

**Worker Framework**

- ✅ Chapter 18 --- Retrieval Worker Framework

- ✅ Chapter 19 --- Vector Retrieval Worker

- ✅ Chapter 20 --- Keyword Retrieval Worker

- ✅ Chapter 21 --- Metadata Retrieval Worker

**Repository Layer**

- ✅ Chapter 22 --- Repository Connector Framework

**Candidate Processing**

- ✅ Chapter 23 --- Unified Candidate Collection Framework

- ✅ Chapter 24 --- Candidate Fusion Framework

**Ranking**

- ✅ **Chapter 25 --- Ranking Engine**

**Remaining Chapters**

- ⏳ **Chapter 26 --- Context Assembly Engine** ⭐ *(the bridge between
  retrieval and the LLM)*

- ⏳ Chapter 27 --- Response Packaging & Handoff

- ⏳ Chapter 28 --- Observability & End-to-End Traceability

- ⏳ Chapter 29 --- Security, Governance & Compliance

- ⏳ Chapter 30 --- Deployment Architecture & Scalability

------------------------------------------------------------------------

**🏆 Principal Architect Recommendation (One Critical Refinement)**

Before proceeding to Context Assembly, I recommend introducing a formal
**Retrieval Confidence Model**.

The Ranking Engine should not only output an ordered list of Knowledge
Objects but also produce an **overall retrieval confidence assessment**
based on evidence quality, agreement across retrieval strategies,
governance status, repository trust, and ranking stability.

This confidence score can be consumed by downstream components to decide
whether to:

- Proceed with response generation.

- Trigger additional retrieval strategies.

- Request clarification from the user.

- Apply stricter guardrails.

- Surface confidence indicators in enterprise applications.

By separating **confidence** from **relevance**, EKRE becomes capable of
reasoning not only about *which knowledge is most relevant*, but also
*how trustworthy and complete the retrieved knowledge is*. This is an
essential capability for enterprise-grade AI systems operating in
regulated, safety-critical, or high-stakes environments.

Excellent.

Now we arrive at what I consider the **most important chapter in the
entire Retrieval Engine**.

Not because it is technically the most difficult.

But because it is the **boundary between Retrieval and Generative AI.**

Everything before this chapter is about **finding knowledge**.

Everything after this chapter is about **using knowledge.**

This boundary must be extremely clean.

------------------------------------------------------------------------

**🏛 Principal Architect Review**

Most RAG systems do this:

Retriever

↓

Top 10 Chunks

↓

Prompt

↓

LLM

This is where most hallucinations begin.

Why?

Because the retriever returns **ranked documents**, not **LLM-ready
context**.

Those are completely different things.

Instead, EKRE should introduce a dedicated **Context Assembly Domain**.

Ranked Knowledge Objects

↓

Context Assembly

↓

Retrieval Context Package

↓

LLM

Notice the difference.

The LLM **never sees Knowledge Objects.**

It only sees a carefully constructed **Retrieval Context Package**.

This separation is one of the biggest architectural improvements we can
make.

------------------------------------------------------------------------

**Why Context Assembly deserves its own Engine**

Retrieval answers

Which knowledge is relevant?

Context Assembly answers

How should this knowledge be presented to the LLM?

Those are different optimization problems.

Example

Knowledge Object

Engineering SOP

42 chunks

Should we send

42 chunks?

No.

Maybe

Chunks

4

5

6

Because

- they are consecutive

- same section

- token efficient

This decision belongs to Context Assembly.

NOT Retrieval.

NOT Ranking.

------------------------------------------------------------------------

**New Pipeline**

Retrieval

↓

Knowledge Objects

↓

Context Assembly

↓

Context Optimizer

↓

Prompt Package

↓

LLM

------------------------------------------------------------------------

**Volume III**

# Chapter 26 - Context Assembly Engine

\-\--

# 26.1 Purpose

The Context Assembly Engine (CAE) transforms Ranked Knowledge Objects
into an optimized Retrieval Context Package suitable for Large Language Models.

Unlike retrieval, which discovers knowledge, or ranking, which orders
knowledge, Context Assembly determines how knowledge should be
structured, compressed, and organized for effective LLM reasoning.

The Retrieval Context Package is the only artifact transferred to the Response
Generation domain.

\-\--

# 26.2 Responsibilities

The Context Assembly Engine owns:

✓ Context selection

✓ Chunk sequencing

✓ Neighbor expansion

✓ Token budgeting

✓ Context compression

✓ Citation preparation

✓ Context optimization

✓ Context metrics

It performs no retrieval or ranking.

\-\--

# 26.3 Responsibilities NOT Owned

The Context Assembly Engine SHALL NOT:

Retrieve documents

Rank Knowledge Objects

Interpret user intent

Generate answers

Call repositories

Modify Knowledge Objects

\-\--

# 26.4 Inputs

Execution Context

Ranked Knowledge Set

Context Policy

Token Budget

Model Capabilities

Execution Budget

\-\--

# 26.5 Outputs

Retrieval Context Package

Containing:

Execution ID

Selected Knowledge Objects

Ordered Chunks

Citation Map

Token Usage

Compression Metrics

Context Metadata

Execution Trace

The Retrieval Context Package becomes the canonical input for Response Generation.

\-\--

# 26.6 Internal Architecture

\`\`\`

Ranked Knowledge Set

↓

Context Selector

↓

Chunk Organizer

↓

Neighbor Expander

↓

Token Optimizer

↓

Citation Builder

↓

Retrieval Context Package

\`\`\`

Each stage owns a single responsibility.

\-\--

# 26.7 Context Selection

Select the subset of Knowledge Objects that fit within the available
context budget.

Selection considers:

Ranking

Coverage

Diversity

Repository Balance

Topic Balance

Policy Constraints

Selection never changes Knowledge Object content.

\-\--

# 26.8 Chunk Organization

Arrange chunks into a coherent reading order.

Ordering strategies include:

Document Order

Section Order

Chronological Order

Semantic Flow

Planner-defined Order

The objective is to maximize reasoning quality.

\-\--

# 26.9 Neighbor Expansion

When beneficial, include adjacent chunks to preserve context.

Policies include:

No Expansion

Previous Chunk

Next Chunk

Bidirectional Expansion

Section Expansion

Document Expansion

Expansion respects token budgets.

\-\--

# 26.10 Token Optimization

Optimize context to fit model constraints.

Techniques include:

Duplicate removal

Whitespace normalization

Boilerplate removal

Redundant metadata pruning

Optional summarization (future)

Token optimization must preserve factual accuracy.

\-\--

# 26.11 Citation Builder

Prepare citation metadata for downstream response generation.

Each citation includes:

Knowledge ID

Document ID

Chunk ID

Repository

Page Number (if available)

Section

Source URI

Version

Citation metadata is immutable.

\-\--

# 26.12 Context Policies

Supported policies:

Maximum Coverage

Highest Precision

Balanced Coverage

Repository Diversity

Freshness-first

Compliance-first

Policies are configurable by tenant.

\-\--

# 26.13 Budget Enforcement

Context assembly respects:

Token budget

Latency budget

Memory budget

Maximum Knowledge Objects

Execution timeout

Graceful degradation is preferred over failure.

\-\--

# 26.14 Failure Handling

Examples:

Token budget exceeded

Chunk unavailable

Missing citation metadata

Compression failure

Execution timeout

Recovery:

Reduce context

Skip optional expansion

Record warnings

Maintain audit trace

\-\--

# 26.15 Configuration

Administrators configure:

Maximum tokens

Expansion policy

Compression policy

Citation format

Ordering strategy

Telemetry

Feature flags

\-\--

# 26.16 Performance Targets

Illustrative goals:

Selection

\<5 ms

Chunk Organization

\<5 ms

Neighbor Expansion

\<10 ms

Token Optimization

\<10 ms

Retrieval Context Package Generation

\<25 ms

\-\--

# 26.17 Observability

Metrics include:

Context Size

Token Usage

Compression Ratio

Knowledge Objects Selected

Chunk Count

Citation Count

Assembly Latency

Budget Utilization

\-\--

# 26.18 Extension Points

Future enhancements:

Hierarchical context

Dynamic summarization

Multimodal context

Graph-aware context

Long-context optimization

Agent-specific context assembly

\-\--

# 26.19 Architecture Rules

The Context Assembly Engine SHALL NOT:

Retrieve knowledge

Rank Knowledge Objects

Generate responses

Call LLMs

Modify evidence

Its responsibility ends after producing an immutable Retrieval Context Package.

\-\--

# End of Chapter 26

------------------------------------------------------------------------

**🏛 Principal Architect Review (Major Architectural Improvement)**

I think we can improve this even further.

Instead of viewing the output as just a prompt, define it as a
**Model-Agnostic Retrieval Context Package (MACP)**.

Model-Agnostic Retrieval Context Package

├── Context Header

├── Knowledge Objects

├── Ordered Chunks

├── Citation Map

├── Token Statistics

├── Confidence Summary

├── Conversation Context

├── Response Constraints

├── Safety Constraints

├── Execution Metadata

└── Planner Metadata

Why?

Because the Retrieval Context Package should work with:

- GPT

- Claude

- Gemini

- Llama

- Mistral

- Future enterprise models

without changing EKRE.

The Response Generation Domain becomes responsible for converting this
**model-agnostic package** into provider-specific prompts or API
requests.

This creates a clean contract between retrieval and generation.

------------------------------------------------------------------------

**📚 Updated Handbook Progress**

**Volume III --- Retrieval Execution Domain**

**Runtime**

- ✅ Chapter 14 --- Retrieval Execution Domain Overview

- ✅ Chapter 15 --- Retrieval Orchestrator

- ✅ Chapter 16 --- Execution Runtime

- ✅ Chapter 17 --- Execution Scheduler

**Workers**

- ✅ Chapter 18 --- Retrieval Worker Framework

- ✅ Chapter 19 --- Vector Retrieval Worker

- ✅ Chapter 20 --- Keyword Retrieval Worker

- ✅ Chapter 21 --- Metadata Retrieval Worker

**Repository Layer**

- ✅ Chapter 22 --- Repository Connector Framework

**Candidate Processing**

- ✅ Chapter 23 --- Unified Candidate Collection Framework

- ✅ Chapter 24 --- Candidate Fusion Framework

**Intelligence**

- ✅ Chapter 25 --- Ranking Engine

**Context**

- ✅ **Chapter 26 --- Context Assembly Engine**

**Remaining Chapters (Platform-Level Completion)**

- ⏳ Chapter 27 --- Response Packaging & Handoff

- ⏳ Chapter 28 --- End-to-End Observability & Traceability

- ⏳ Chapter 29 --- Security, Governance & Compliance

- ⏳ Chapter 30 --- Deployment Architecture & Scalability

------------------------------------------------------------------------

**🏆 Principal Architect Review (One Important Correction)**

I want to make one recommendation that slightly changes the overall
architecture and will make the platform stronger.

**Introduce a new platform object: Knowledge Package**

Currently, the flow is:

Knowledge Objects

↓

Retrieval Context Package

↓

LLM

I recommend introducing one intermediate artifact:

Knowledge Objects

↓

Knowledge Package

↓

Retrieval Context Package

↓

Response Generation

**Why?**

A **Knowledge Package** is a model-independent representation of all
selected knowledge and supporting evidence.

It contains:

- Selected Knowledge Objects

- Evidence summaries

- Confidence assessment

- Citation graph

- Governance metadata

- Security decisions

- Retrieval explanations

- Trace identifiers

The **Retrieval Context Package** is then a model-specific projection of that
Knowledge Package, optimized for a particular LLM\'s context window,
prompt format, and API requirements.

This distinction gives the Enterprise Knowledge Platform two significant
advantages:

1.  **Portability**: The same Knowledge Package can be rendered
    differently for GPT, Claude, Gemini, Llama, or any future model
    without repeating retrieval or ranking.

2.  **Future extensibility**: Non-LLM consumers (analytics, dashboards,
    workflow engines, human review tools) can consume the Knowledge
    Package directly, making EKRE a reusable enterprise knowledge
    service rather than a retrieval layer tied exclusively to language
    models.

I recommend adopting this refinement before beginning the Response
Generation domain, as it establishes a clean and durable contract
between retrieval and generation across the entire Enterprise Knowledge
Platform.

Excellent.

We have now completed what I would call the **functional architecture**
of EKRE. Before we close the Retrieval Execution Domain, there are four
platform chapters remaining. These chapters are not \"features\"---they
define how EKRE operates as an enterprise-grade system.

The next chapter is the contract between EKRE and the Response
Generation Domain.

------------------------------------------------------------------------

**🏛 Principal Architect Review**

One architectural improvement before proceeding.

At the moment we have:

Retrieval Domain

↓

Retrieval Context Package

↓

LLM

I don\'t think this is the correct boundary.

The Retrieval Engine should never know that an LLM exists.

Instead the architecture should become:

Retrieval Domain

↓

Knowledge Package

↓

Generation Gateway

↓

Prompt Builder

↓

LLM Provider

Notice something important.

The Retrieval Engine hands off a **Knowledge Package**.

The Response Generation Domain decides:

- Which LLM

- Which prompt template

- Which tools

- Which function calls

- Which system instructions

- Which safety policies

This keeps Retrieval completely model-independent.

------------------------------------------------------------------------

**Volume III**


### 26.X Citation Lineage Guarantee

**Integration Contract:** The Context Assembly Engine guarantees that all final chunks handed off to EKCP will contain perfectly preserved citation lineage (`source_path`, `document_id`, `repository_id`) originally provided by EKIE. Candidate Fusion and Ranking engines are strictly prohibited from stripping this metadata.


# Chapter 27 - Response Packaging & Handoff

\-\--

# 27.1 Purpose

The Response Packaging & Handoff Layer (RPHL) represents the boundary
between the Retrieval Execution Domain and the Response Generation
Domain.

Its purpose is to package retrieved knowledge into a portable,
immutable, model-agnostic representation suitable for downstream
consumers.

It does not generate prompts or invoke language models.

\-\--

# 27.2 Design Goals

The Response Packaging Layer shall provide:

✓ Model independence

✓ Immutable packaging

✓ Complete provenance

✓ Security preservation

✓ Auditability

✓ Version compatibility

✓ Deterministic serialization

\-\--

# 27.3 Responsibilities

The layer owns:

Knowledge Package creation

Knowledge Package validation

Evidence serialization

Citation packaging

Security metadata packaging

Execution metadata packaging

Confidence packaging

Version management

\-\--

# 27.4 Responsibilities NOT Owned

The layer SHALL NOT:

Generate prompts

Choose LLMs

Call model APIs

Modify Knowledge Objects

Perform ranking

Retrieve documents

\-\--

# 27.5 Inputs

Knowledge Package Builder

↓

Knowledge Objects

↓

Evidence

↓

Citation Map

↓

Confidence Model

↓

Execution Metadata

\-\--

# 27.6 Outputs

Knowledge Package

Containing:

Package ID

Knowledge Objects

Evidence Objects

Citation Graph

Confidence Assessment

Security Context

Governance Metadata

Execution Trace

Planner Metadata

Repository References

Version

\-\--

# 27.7 Internal Architecture

Knowledge Objects

↓

Package Builder

↓

Validation Engine

↓

Serializer

↓

Knowledge Package

\-\--

# 27.8 Package Validation

Validation verifies:

Required fields

Evidence integrity

Citation integrity

Execution IDs

Repository references

Schema version

Package checksum

Packages are immutable once validated.

\-\--

# 27.9 Serialization

Supported formats:

JSON

Protocol Buffers

Avro

MessagePack

Future binary formats

Serialization is deterministic.

\-\--

# 27.10 Citation Packaging

Each citation contains:

Knowledge ID

Document ID

Chunk ID

Repository

Version

URI

Section

Page

Confidence

Citation identifiers remain stable across versions.

\-\--

# 27.11 Confidence Packaging

Package-level confidence includes:

Retrieval confidence

Evidence confidence

Repository confidence

Governance confidence

Overall confidence

Confidence is descriptive rather than predictive.

\-\--

# 27.12 Security Packaging

Security metadata includes:

Access decisions

Security labels

Classification

Compliance tags

Retention policies

Tenant information

No security information is discarded.

\-\--

# 27.13 Execution Metadata

Metadata includes:

Execution ID

Planner Version

Runtime Version

Ranking Version

Fusion Version

Timestamp

Latency

Budgets

Trace ID

\-\--

# 27.14 Versioning

Every package includes:

Schema Version

Platform Version

Package Version

Evidence Version

Ranking Version

This guarantees backward compatibility.

\-\--

# 27.15 Performance Targets

Illustrative goals:

Package Creation

\<5 ms

Validation

\<2 ms

Serialization

\<5 ms

Total

\<15 ms

\-\--

# 27.16 Observability

Metrics include:

Package Count

Serialization Time

Validation Failures

Package Size

Citation Count

Knowledge Objects

Latency

\-\--

# 27.17 Extension Points

Future support:

Streaming Packages

Incremental Updates

Binary Serialization

Compression

Signed Packages

Encrypted Packages

\-\--

# 27.18 Architecture Rules

The Response Packaging Layer SHALL NOT:

Generate prompts

Invoke LLMs

Interpret user intent

Modify retrieved knowledge

Its responsibility ends after producing a validated Knowledge Package.

\-\--

# End of Chapter 27

------------------------------------------------------------------------

**🏛 Principal Architect Review (A Major Platform Improvement)**

At this point, I think we should formalize something that has been
implicit throughout EKRE.

**Enterprise Knowledge Schema (EKS)**

Currently we have discussed:

- Knowledge Object

- Evidence Object

- Candidate

- Retrieval Context Package

- Knowledge Package

Rather than treating them as unrelated models, define a single platform
schema.

Enterprise Knowledge Schema (EKS)

├── Candidate

├── Knowledge Object

├── Evidence

├── Citation

├── Knowledge Package

├── Retrieval Context Package

├── Confidence Model

├── Security Context

├── Governance Metadata

├── Execution Metadata

├── Audit Metadata

└── Trace Metadata

Every subsystem in the Enterprise Knowledge Platform should exchange
objects defined by the Enterprise Knowledge Schema.

Benefits:

- A single canonical contract across EKIE, EKRE, EKCP, and future
  domains.

- Independent versioning of schemas without breaking components.

- Easier interoperability and testing.

- Consistent observability and auditing.

- Simplified SDK generation for multiple programming languages.

------------------------------------------------------------------------

**📚 Updated Handbook Progress**

**Volume III --- Retrieval Execution Domain**

**Architecture**

- ✅ Chapter 14 --- Retrieval Execution Domain Overview

**Runtime**

- ✅ Chapter 15 --- Retrieval Orchestrator

- ✅ Chapter 16 --- Execution Runtime

- ✅ Chapter 17 --- Execution Scheduler

**Workers**

- ✅ Chapter 18 --- Retrieval Worker Framework

- ✅ Chapter 19 --- Vector Retrieval Worker

- ✅ Chapter 20 --- Keyword Retrieval Worker

- ✅ Chapter 21 --- Metadata Retrieval Worker

**Repository Layer**

- ✅ Chapter 22 --- Repository Connector Framework

**Candidate Processing**

- ✅ Chapter 23 --- Unified Candidate Collection Framework

- ✅ Chapter 24 --- Candidate Fusion Framework

**Intelligence**

- ✅ Chapter 25 --- Ranking Engine

**Context**

- ✅ Chapter 26 --- Context Assembly Engine

**Platform Boundary**

- ✅ **Chapter 27 --- Response Packaging & Handoff**

**Remaining Platform Chapters**

- ⏳ **Chapter 28 --- End-to-End Observability & Traceability**
  *(critical for enterprise operations)*

- ⏳ **Chapter 29 --- Security, Governance & Compliance**

- ⏳ **Chapter 30 --- Deployment Architecture & Scalability**

------------------------------------------------------------------------

**🚀 Product Manager Recommendation (Strategic Refinement)**

Before considering EKRE complete, I recommend adding a short appendix
that defines the **Enterprise Knowledge SDK (EKSDK)**.

Rather than exposing internal objects directly, the SDK would provide
typed models, validation utilities, serialization, tracing hooks, and
extension interfaces built on the Enterprise Knowledge Schema. Both EKIE
(ingestion) and EKRE (retrieval), along with future platform components,
would depend on this SDK. This creates a stable developer experience,
reduces duplicated model definitions across services, and ensures every
team building on the Enterprise Knowledge Platform adheres to the same
contracts and architectural standards. This SDK becomes the foundation
for long-term maintainability and ecosystem growth.

Excellent.

Now we arrive at one of the chapters that differentiates a
**production-grade enterprise platform** from an engineering prototype.

Most RAG systems stop after retrieval.

Very few answer these questions:

- Which repository was queried?

- Which worker failed?

- Why was a document ranked #3 instead of #1?

- Which connector exceeded its latency budget?

- Which embedding model was used?

- Which planner version created this execution plan?

- Can I replay the execution six months later?

Without these capabilities, operating the platform at enterprise scale
becomes extremely difficult.

------------------------------------------------------------------------

**🏛 Principal Architect Review**

Before writing this chapter, I want to introduce a new architectural
concept.

Today we have observability scattered across components.

Planner Logs

Runtime Logs

Worker Logs

Connector Logs

Ranking Logs

Instead, EKRE should produce a single **Execution Graph** for every
request.

Think of it as a distributed execution plan with complete traceability.

User Query

↓

Execution Session

↓

Execution Graph

├── Planner

├── Runtime

├── Scheduler

├── Worker A

├── Worker B

├── Worker C

├── Connector

├── Fusion

├── Ranking

├── Context Assembly

└── Packaging

This graph becomes the source of truth for:

- Debugging

- Monitoring

- Performance tuning

- Auditing

- Replay

- Cost analysis

------------------------------------------------------------------------

**Volume III**

# Chapter 28 - End-to-End Observability & Traceability

\-\--

# 28.1 Purpose

The End-to-End Observability & Traceability Framework (EOTF) provides
complete visibility into every retrieval execution performed by EKRE.

It enables operators, developers, auditors, and platform services to
understand exactly how a retrieval request was planned, executed,
ranked, and packaged.

Every execution produces a complete, immutable execution trace.

\-\--

# 28.2 Design Goals

The framework shall provide:

✓ End-to-end tracing

✓ Distributed observability

✓ Performance monitoring

✓ Replay capability

✓ Audit support

✓ Cost tracking

✓ Version traceability

✓ Root cause analysis

\-\--

# 28.3 Responsibilities

The framework owns:

Execution tracing

Distributed correlation

Metrics collection

Logging

Execution graph generation

Performance analytics

Replay metadata

Audit trail generation

\-\--

# 28.4 Responsibilities NOT Owned

The framework SHALL NOT:

Modify execution

Perform retrieval

Perform ranking

Generate responses

Change execution policies

It observes but never influences execution.

\-\--

# 28.5 Execution Session

Every retrieval request creates an Execution Session.

Example:

Execution ID

Planner Version

Runtime Version

Scheduler Version

Timestamp

Tenant

User Context

Correlation ID

Trace ID

Every downstream component inherits this session.

\-\--

# 28.6 Execution Graph

The Execution Graph records every stage.

Planner

↓

Execution Plan

↓

Runtime

↓

Scheduler

↓

Workers

↓

Repository Connectors

↓

Fusion

↓

Ranking

↓

Context Assembly

↓

Knowledge Package

Every node is timestamped.

\-\--

# 28.7 Distributed Tracing

Every component propagates:

Trace ID

Span ID

Parent Span

Execution ID

Worker ID

Repository ID

This enables distributed tracing across services.

\-\--

# 28.8 Metrics Collection

Metrics include:

Execution latency

Planning latency

Worker latency

Repository latency

Ranking latency

Context assembly latency

Package generation latency

Total execution time

\-\--

# 28.9 Logging

Logs are structured.

Every log includes:

Timestamp

Execution ID

Component

Severity

Correlation ID

Message

Structured Payload

No unstructured logs are emitted.

\-\--

# 28.10 Cost Tracking

Track resource usage:

Embedding requests

Vector searches

Repository calls

LLM reranking

Token usage

CPU time

Memory usage

Network usage

Cost attribution is available per execution.

\-\--

# 28.11 Replay Support

The framework stores enough metadata to replay executions.

Replay includes:

Execution Plan

Worker configuration

Ranking policy

Connector versions

Knowledge Package

Replay never modifies production data.

\-\--

# 28.12 Failure Analysis

Failures include:

Worker timeout

Repository unavailable

Authentication failure

Budget exceeded

Policy violation

Connector failure

Root causes are linked to execution nodes.

\-\--

# 28.13 Dashboards

Operational dashboards include:

Latency trends

Worker health

Repository health

Ranking distribution

Failure rates

Cost trends

Execution throughput

\-\--

# 28.14 Alerts

Supported alerts:

Latency threshold exceeded

Worker unavailable

Repository degraded

Retry storm

Budget exhaustion

Authentication failures

High error rates

\-\--

# 28.15 Configuration

Configurable options:

Sampling rate

Retention policy

Metrics aggregation

Log verbosity

Replay retention

Alert thresholds

Trace storage

\-\--

# 28.16 Performance Targets

Illustrative goals:

Trace Creation

\<2 ms

Metrics Collection

\<1 ms

Logging Overhead

\<1 ms

Total Observability Overhead

\<5 ms

\-\--

# 28.17 Extension Points

Future enhancements:

AI-assisted diagnostics

Predictive failure detection

Automatic bottleneck analysis

Execution optimization recommendations

Anomaly detection

\-\--

# 28.18 Architecture Rules

The Observability Framework SHALL NOT:

Influence execution

Modify retrieval

Change ranking

Alter Knowledge Packages

It provides complete visibility while remaining passive.

\-\--

# End of Chapter 28

------------------------------------------------------------------------

**🏛 Principal Architect Review (Major Architectural Improvement)**

I think EKRE can go even further by introducing a **Knowledge Execution
Graph (KEG)**.

Rather than treating observability as logs and traces, model the
execution as a graph.

Execution Graph

├── Planner Node

├── Runtime Node

├── Scheduler Node

├── Worker Nodes

├── Repository Nodes

├── Fusion Node

├── Ranking Node

├── Context Node

├── Packaging Node

└── Generation Gateway Node

Each node contains:

- Inputs

- Outputs

- Duration

- Resource usage

- Parent/child relationships

- Configuration version

- Evidence references

- Failure information

Advantages:

- Graph-based debugging.

- Execution replay.

- Dependency analysis.

- Visual execution inspection.

- AI-assisted diagnostics.

- Historical comparisons between executions.

------------------------------------------------------------------------

**📚 Updated Handbook Progress**

**Volume III --- Retrieval Execution Domain**

**Architecture**

- ✅ Chapter 14 --- Retrieval Execution Domain Overview

**Runtime**

- ✅ Chapter 15 --- Retrieval Orchestrator

- ✅ Chapter 16 --- Execution Runtime

- ✅ Chapter 17 --- Execution Scheduler

**Workers**

- ✅ Chapter 18 --- Retrieval Worker Framework

- ✅ Chapter 19 --- Vector Retrieval Worker

- ✅ Chapter 20 --- Keyword Retrieval Worker

- ✅ Chapter 21 --- Metadata Retrieval Worker

**Repository Layer**

- ✅ Chapter 22 --- Repository Connector Framework

**Candidate Processing**

- ✅ Chapter 23 --- Unified Candidate Collection Framework

- ✅ Chapter 24 --- Candidate Fusion Framework

**Intelligence**

- ✅ Chapter 25 --- Ranking Engine

**Context**

- ✅ Chapter 26 --- Context Assembly Engine

**Platform Boundary**

- ✅ Chapter 27 --- Response Packaging & Handoff

**Platform Operations**

- ✅ **Chapter 28 --- End-to-End Observability & Traceability**

**Remaining Chapters**

- ⏳ **Chapter 29 --- Security, Governance & Compliance**

- ⏳ **Chapter 30 --- Deployment Architecture & Scalability**

------------------------------------------------------------------------

**🏆 Principal Architect Recommendation (Critical Architectural
Enhancement)**

Before finalizing EKRE, I recommend introducing a **Platform Telemetry
SDK** shared across EKIE, EKRE, EKCP, and future platform domains.

Instead of each service implementing its own logging, metrics, and
tracing, provide a unified SDK with standardized APIs for:

- Trace creation and propagation.

- Metrics emission.

- Structured logging.

- Audit event generation.

- Cost attribution.

- OpenTelemetry integration.

- Correlation ID management.

- Health reporting.

This ensures every platform component emits telemetry in a consistent
format, enabling unified dashboards, cross-domain tracing, and
enterprise-grade operational visibility without duplicating
instrumentation logic. It also positions the Enterprise Knowledge
Platform for seamless integration with observability stacks such as
Grafana, Prometheus, Jaeger, OpenTelemetry Collectors, Azure Monitor, or
Datadog while preserving a stable internal telemetry contract.

Excellent.

We have now reached the final architectural pillar of EKRE.

Everything we have designed so far assumes the system is allowed to
retrieve knowledge.

In an enterprise, that assumption is false.

Before any retrieval result reaches a user, the platform must answer:

- Is this user authorized to access this document?

- Should this repository even be queried?

- Can this document leave its country of origin?

- Does this document violate retention policies?

- Is this version still valid?

- Should confidential information be masked?

- Can an LLM receive this content?

These are **not retrieval concerns**.

They are **platform governance concerns**.

This is why Security & Governance deserves its own dedicated domain.

------------------------------------------------------------------------

**🏛 Principal Architect Review**

One architectural improvement before writing this chapter.

Currently the pipeline looks like:

Planner

↓

Runtime

↓

Workers

↓

Ranking

↓

Context Assembly

Security is implicit.

Instead, Security should exist as a **cross-cutting platform layer**,
affecting every stage.

Security & Governance

│

┌──────────────────┼────────────────────┐

▼ ▼ ▼

Planner Runtime Workers

▼ ▼ ▼

Ranking Context Assembly Packaging

This means **every component consults governance**, rather than
governance being a final filter.

This is how mature enterprise platforms are designed.

------------------------------------------------------------------------

**Volume III**

# Chapter 29 - Security, Governance & Compliance

\-\--

# 29.1 Purpose

The Security, Governance & Compliance Framework (SGCF) provides
enterprise-wide policy enforcement across the Retrieval Execution
Domain.

Its purpose is to ensure that every retrieval operation complies with
organizational security policies, governance rules, regulatory
requirements, and tenant-specific constraints.

The framework is policy-driven and operates as a cross-cutting concern
across all EKRE components.

\-\--

# 29.2 Design Goals

The framework shall provide:

✓ Zero Trust security

✓ Policy-driven governance

✓ Fine-grained authorization

✓ Data classification enforcement

✓ Regulatory compliance

✓ Multi-tenant isolation

✓ Immutable audit trails

✓ Security observability

\-\--

# 29.3 Responsibilities

The framework owns:

Authentication validation

Authorization enforcement

Access control

Data classification

Policy evaluation

Compliance validation

Security auditing

Governance metadata

Retention policy enforcement

Privacy controls

\-\--

# 29.4 Responsibilities NOT Owned

The framework SHALL NOT:

Perform retrieval

Rank knowledge

Generate responses

Modify Knowledge Objects

Plan retrieval

Interpret user intent

Security governs execution but does not execute business logic.

\-\--

# 29.5 Identity & Authentication

Supported identity providers include:

Enterprise SSO

OAuth2

OpenID Connect

SAML

LDAP

Azure AD

Custom enterprise identity providers

Authentication is completed before retrieval begins.

\-\--

# 29.6 Authorization

Authorization is evaluated continuously.

Examples:

Repository permissions

Document ACLs

Role-Based Access Control (RBAC)

Attribute-Based Access Control (ABAC)

Policy-Based Access Control (PBAC)

Tenant isolation

Authorization decisions are immutable for an execution session.

\-\--

# 29.7 Data Classification

Knowledge Objects inherit classifications.

Examples:

Public

Internal

Confidential

Restricted

Highly Restricted

Classification affects retrieval, ranking, context assembly, and
packaging.

\-\--

# 29.8 Governance Policies

Examples:

Document approval required

Latest version only

Retention period enforcement

Repository trust levels

Geographic restrictions

Export controls

Custom enterprise policies

Policies are declarative and versioned.

\-\--

# 29.9 Compliance

Supported compliance domains include:

GDPR

HIPAA

ISO 27001

SOC 2

PCI DSS

Regional data residency

Tenant-specific regulations

Compliance evaluation is recorded in the execution trace.

\-\--

# 29.10 Data Masking

When required, the framework supports:

Field masking

PII redaction

Content redaction

Metadata suppression

Selective citation masking

No unauthorized content reaches downstream components.

\-\--

# 29.11 Security Context

Every execution carries:

Tenant ID

User Identity

Roles

Permissions

Session ID

Authentication Method

Policy Version

Security decisions are propagated through the entire execution.

\-\--

# 29.12 Audit Trail

Every security decision records:

Decision ID

Policy ID

Timestamp

Evaluator

Outcome

Affected Knowledge Objects

Execution ID

Audit records are immutable.

\-\--

# 29.13 Configuration

Administrators configure:

Identity providers

Authorization policies

Classification taxonomy

Compliance rules

Masking rules

Retention periods

Feature flags

\-\--

# 29.14 Performance Targets

Illustrative goals:

Authentication Validation

\<5 ms

Authorization Check

\<2 ms

Policy Evaluation

\<5 ms

Classification Lookup

\<2 ms

Security Overhead

\<10 ms

\-\--

# 29.15 Observability

Metrics include:

Authorization failures

Policy violations

Classification distribution

Compliance failures

Masking operations

Audit events

Security latency

\-\--

# 29.16 Extension Points

Future enhancements:

Dynamic policy evaluation

Risk-based authorization

Continuous trust scoring

AI-assisted policy recommendations

Automated compliance validation

Data lineage governance

\-\--

# 29.17 Architecture Rules

The Security, Governance & Compliance Framework SHALL NOT:

Retrieve documents

Modify rankings

Generate prompts

Invoke LLMs

It provides policy enforcement while remaining independent of retrieval
logic.

\-\--

# End of Chapter 29

------------------------------------------------------------------------

**🏛 Principal Architect Review (Major Architectural Improvement)**

I recommend introducing one more platform service:

**Enterprise Policy Engine (EPE)**

Instead of embedding policies across components, centralize them.

Enterprise Policy Engine

│

┌────────────────┼─────────────────┐

▼ ▼ ▼

Retrieval Policy Security Policy Compliance Policy

▼ ▼ ▼

Ranking Policy Context Policy Packaging Policy

Every EK platform component asks one question:

\"Given this execution context, what policies apply?\"

The Policy Engine responds with immutable policy decisions.

This architecture offers several advantages:

- Centralized governance.

- Consistent policy evaluation.

- Versioned policies.

- Simplified auditing.

- Runtime policy updates.

- Easier regulatory compliance.

------------------------------------------------------------------------

**📚 Handbook Progress**

**Volume III --- Retrieval Execution Domain**

**Runtime**

- ✅ Chapter 14 --- Retrieval Execution Domain Overview

- ✅ Chapter 15 --- Retrieval Orchestrator

- ✅ Chapter 16 --- Execution Runtime

- ✅ Chapter 17 --- Execution Scheduler

**Workers**

- ✅ Chapter 18 --- Retrieval Worker Framework

- ✅ Chapter 19 --- Vector Retrieval Worker

- ✅ Chapter 20 --- Keyword Retrieval Worker

- ✅ Chapter 21 --- Metadata Retrieval Worker

**Repository Layer**

- ✅ Chapter 22 --- Repository Connector Framework

**Candidate Processing**

- ✅ Chapter 23 --- Unified Candidate Collection Framework

- ✅ Chapter 24 --- Candidate Fusion Framework

**Intelligence**

- ✅ Chapter 25 --- Ranking Engine

**Context**

- ✅ Chapter 26 --- Context Assembly Engine

**Platform Boundary**

- ✅ Chapter 27 --- Response Packaging & Handoff

**Platform Operations**

- ✅ Chapter 28 --- End-to-End Observability & Traceability

- ✅ **Chapter 29 --- Security, Governance & Compliance**

------------------------------------------------------------------------

**🚨 Before the Final Chapter (Architect Review)**

Before writing **Chapter 30**, I want to make one important
architectural correction to everything we\'ve designed so far.

**Introduce the Enterprise Knowledge Control Plane (EKCP)**

Originally, EKCP was discussed as a separate project. After completing
EKRE, it\'s clear that **EKCP should not own retrieval logic**, but it
**must own operational control** over EKRE.

That means EKCP becomes the platform control plane responsible for:

- Worker registration and lifecycle.

- Repository registration.

- Connector deployment.

- Policy distribution.

- Configuration management.

- Feature flags.

- Health monitoring.

- Runtime scaling.

- Tenant management.

- Secret and credential references.

- Platform-wide observability aggregation.

In contrast, **EKRE remains a pure execution plane** responsible only
for planning, retrieving, ranking, and packaging knowledge.

This separation mirrors the architecture used in systems like Kubernetes
(Control Plane vs. Data Plane) and modern service meshes. It keeps
retrieval deterministic while allowing operations, governance, and
platform administration to evolve independently.

I recommend incorporating this distinction before finalizing **Chapter
30 -- Deployment Architecture & Scalability**, because it establishes
the long-term operating model for the entire Enterprise Knowledge
Platform.

Excellent.

We have reached the final chapter of EKRE.

This chapter is different from all previous chapters.

Everything before this described **how EKRE works**.

This chapter describes **how EKRE lives inside the Enterprise Knowledge
Platform**.

This is where we transition from software architecture to platform
architecture.

------------------------------------------------------------------------

**🏛 Principal Architect Final Review**

After reviewing all 29 chapters, I think there is one architectural
improvement that will make the entire platform significantly stronger.

Throughout the handbook we\'ve designed:

EKIE

↓

EKRE

↓

Generation Domain

However, these are not standalone applications.

They are **Platform Services** managed by the Enterprise Knowledge
Control Plane (EKCP).

The final architecture should explicitly separate:

Enterprise Knowledge Platform

────────────────────────────────────────────────────────────

Enterprise Knowledge Control Plane

────────────────────────────────────────────────────────────

Configuration

Policy

Observability

Secrets

Scaling

Deployment

Worker Registry

Repository Registry

Health

Feature Flags

Scheduling Policies

────────────────────────────────────────────────────────────

Execution Plane

────────────────────────────────────────────────────────────

EKIE

↓

EKRE

↓

Generation

↓

Future AI Services

This is much closer to Kubernetes,

Istio,

Temporal,

Airflow,

and other modern distributed platforms.

------------------------------------------------------------------------

**Volume III**

# Chapter 30 - Deployment Architecture & Scalability

\-\--

# 30.1 Purpose

This chapter defines how EKRE is deployed, operated, scaled, monitored,
and managed within the Enterprise Knowledge Platform.

Deployment architecture is intentionally separated from business logic.

The Retrieval Execution Domain remains deterministic regardless of
deployment topology.

\-\--

# 30.2 Design Goals

Deployment architecture shall provide:

✓ Horizontal scalability

✓ High availability

✓ Fault isolation

✓ Multi-tenancy

✓ Zero-downtime upgrades

✓ Elastic scaling

✓ Cloud portability

✓ Operational simplicity

\-\--

# 30.3 Platform Architecture

\`\`\`

Enterprise Knowledge Platform

│

▼

Enterprise Knowledge Control Plane (EKCP)

│

────────────────────────────────────────────────────

Retrieval Execution Plane

────────────────────────────────────────────────────

Planner

↓

Runtime

↓

Scheduler

↓

Workers

↓

Repository Connectors

↓

Fusion

↓

Ranking

↓

Context Assembly

↓

Knowledge Packaging

\`\`\`

EKCP manages the platform.

EKRE executes retrieval.

\-\--

# 30.4 Deployment Units

Each major subsystem is independently deployable.

Examples:

Planner Service

Runtime Service

Scheduler Service

Worker Pool

Connector Pool

Ranking Service

Fusion Service

Context Assembly Service

Packaging Service

Services communicate through platform APIs.

\-\--

# 30.5 Scaling Strategy

Horizontal scaling is preferred.

Examples:

Planner

1 → N

Workers

10 → 1000

Repository Connectors

Dynamic Pool

Ranking

Auto Scale

Context Assembly

Auto Scale

Scaling policies are managed by EKCP.

\-\--

# 30.6 Worker Pools

Workers are grouped by capability.

Examples:

Vector Pool

Keyword Pool

Metadata Pool

Future Graph Pool

Future SQL Pool

Future Image Pool

Each pool scales independently.

\-\--

# 30.7 High Availability

Platform supports:

Redundant workers

Multi-zone deployment

Automatic failover

Health-based routing

Circuit breakers

Retry policies

Graceful degradation

No single retrieval worker becomes a platform bottleneck.

\-\--

# 30.8 Multi-Tenancy

Supported models:

Shared infrastructure

Dedicated tenant clusters

Hybrid deployment

Regional isolation

Tenant-aware scheduling

Tenant-aware policies

Tenant-aware observability

All execution metadata carries Tenant Context.

\-\--

# 30.9 Repository Scaling

Repository Connectors support:

Connection pooling

Adaptive throttling

Request batching

Caching

Read replicas

Regional routing

Repository-specific optimization

\-\--

# 30.10 Platform Configuration

Configuration is externalized.

Examples:

Worker configuration

Connector configuration

Ranking policies

Context policies

Timeouts

Feature flags

Telemetry

Configurations are version-controlled.

\-\--

# 30.11 Deployment Models

Supported deployments:

Single Node

Development

Docker Compose

Kubernetes

OpenShift

Azure Kubernetes Service

Amazon EKS

Google GKE

On-Premises

Hybrid Cloud

No deployment model changes business logic.

\-\--

# 30.12 Disaster Recovery

Recovery strategies include:

Checkpoint recovery

Configuration backup

Execution replay

Repository failover

Cross-region deployment

Automated restoration

Recovery procedures are tested regularly.

\-\--

# 30.13 Performance Targets

Illustrative goals:

Planner Availability

99.99%

Worker Availability

99.95%

Repository Availability

99.90%

Overall Retrieval Availability

99.95%

Deployment Downtime

Zero

\-\--

# 30.14 Capacity Planning

Capacity dimensions include:

Concurrent executions

Worker concurrency

Repository throughput

Embedding throughput

Memory

Storage

Network bandwidth

Token usage

Capacity planning is telemetry-driven.

\-\--

# 30.15 Extension Points

Future enhancements:

Serverless workers

GPU-aware scheduling

Cross-region execution

Edge retrieval

Federated retrieval

Distributed ranking

Global execution routing

\-\--

# 30.16 Architecture Rules

Deployment architecture SHALL NOT:

Change retrieval behavior

Modify ranking logic

Alter evidence

Influence Knowledge Objects

Deployment concerns remain separate from business logic.

\-\--

# End of Chapter 30

------------------------------------------------------------------------

**🏛 Final Principal Architect Review of EKRE**

Now that all chapters are complete, I\'d like to step back and evaluate
the architecture as a whole.

**Overall Assessment**

The architecture has evolved from a traditional RAG pipeline into a
**distributed enterprise retrieval platform**. However, there are three
refinements I would make before declaring Version 1.0 complete.

**1. Define a Canonical Enterprise Schema**

Over the course of the design, we\'ve introduced several core entities:

Candidate

↓

Knowledge Object

↓

Evidence

↓

Knowledge Package

↓

Retrieval Context Package

These should be formalized into a dedicated **Enterprise Knowledge
Schema (EKS)** with versioned specifications (for example, JSON Schema
or Protocol Buffers). Every platform service---EKIE, EKRE, EKCP, and
future domains---should exchange only these canonical objects.

**2. Standardize Platform SDKs**

To ensure consistency across implementations, define shared SDKs:

- **EKSDK Core** -- domain models, serialization, validation.

- **Connector SDK** -- repository driver interfaces.

- **Worker SDK** -- retrieval worker lifecycle and contracts.

- **Telemetry SDK** -- tracing, metrics, logging.

- **Policy SDK** -- interaction with the Enterprise Policy Engine.

- **Configuration SDK** -- dynamic configuration and feature flags.

This minimizes duplicated infrastructure code and guarantees
architectural consistency.

**3. Adopt a Control Plane / Execution Plane Model**

Finalize the platform around two distinct layers:

Enterprise Knowledge Platform

├── Enterprise Knowledge Control Plane (EKCP)

│ ├── Worker Registry

│ ├── Repository Registry

│ ├── Policy Engine

│ ├── Configuration Service

│ ├── Secrets Management

│ ├── Feature Flags

│ ├── Observability

│ ├── Deployment Manager

│ └── Health Management

│

└── Enterprise Knowledge Execution Plane

├── EKIE (Ingestion)

├── EKRE (Retrieval)

├── Response Generation

└── Future AI Services

This separation provides a clean operational model where EKCP manages
platform behavior while EKRE remains a deterministic execution engine.

------------------------------------------------------------------------

**📚 EKRE Handbook Status**

With Chapter 30 complete, **Volume III -- Retrieval Execution Domain**
is now structurally complete.

**Completed Chapters**

**Runtime**

- ✅ Chapter 14 --- Retrieval Execution Domain Overview

- ✅ Chapter 15 --- Retrieval Orchestrator

- ✅ Chapter 16 --- Execution Runtime

- ✅ Chapter 17 --- Execution Scheduler

**Workers**

- ✅ Chapter 18 --- Retrieval Worker Framework

- ✅ Chapter 19 --- Vector Retrieval Worker

- ✅ Chapter 20 --- Keyword Retrieval Worker

- ✅ Chapter 21 --- Metadata Retrieval Worker

**Repository Layer**

- ✅ Chapter 22 --- Repository Connector Framework

**Candidate Processing**

- ✅ Chapter 23 --- Unified Candidate Collection Framework

- ✅ Chapter 24 --- Candidate Fusion Framework

**Intelligence**

- ✅ Chapter 25 --- Ranking Engine

**Context**

- ✅ Chapter 26 --- Context Assembly Engine

**Platform Boundary**

- ✅ Chapter 27 --- Response Packaging & Handoff

**Operations**

- ✅ Chapter 28 --- End-to-End Observability & Traceability

- ✅ Chapter 29 --- Security, Governance & Compliance

- ✅ Chapter 30 --- Deployment Architecture & Scalability

------------------------------------------------------------------------

