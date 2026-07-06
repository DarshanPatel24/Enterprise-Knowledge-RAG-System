# EKIE — Enterprise Knowledge Ingestion Engine
## Enterprise Architecture Handbook

> **Version:** 1.0
> **Status:** Approved
> **Owner:** Product Management
> **Architecture Owner:** Principal Architect

---

## Table of Contents

- [Chapter 1 - Introduction to EKIE](#chapter-1-introduction-to-ekie)
- [Chapter 2 - Enterprise Architecture Principles](#chapter-2-enterprise-architecture-principles)
- [Chapter 3 - Product Vision, Scope & Non-Functional Requirements](#chapter-3-product-vision-scope-non-functional-requirements)
- [Chapter 5 - Enterprise Knowledge Lifecycle & Digital Twin Model](#chapter-5-enterprise-knowledge-lifecycle-digital-twin-model)
- [Chapter 6 - Repository Synchronization Framework](#chapter-6-repository-synchronization-framework)
- [Chapter 7 - Document Transformation & Canonical Markdown Framework](#chapter-7-document-transformation-canonical-markdown-framework)
- [Chapter 8 - Document Intelligence Framework](#chapter-8-document-intelligence-framework)
- [Chapter 9 - Intelligent Chunking Framework](#chapter-9-intelligent-chunking-framework)
- [Chapter 10 - Embedding Framework](#chapter-10-embedding-framework)
- [Chapter 11 - Vector Publishing Framework](#chapter-11-vector-publishing-framework)
- [Chapter 12 - Workflow Orchestration Framework](#chapter-12-workflow-orchestration-framework)
- [Chapter 13 - Control Plane & Metadata Platform](#chapter-13-control-plane-metadata-platform)
- [Chapter 14 - Enterprise Storage Architecture](#chapter-14-enterprise-storage-architecture)
- [Chapter 15 - Configuration & Policy Engine](#chapter-15-configuration-policy-engine)
- [Chapter 16 - Observability Framework](#chapter-16-observability-framework)
- [Chapter 17 - Security & Governance Framework](#chapter-17-security-governance-framework)
- [Chapter 18 - Plugin & Extension SDK](#chapter-18-plugin-extension-sdk)
- [Chapter 19 - Deployment Architecture](#chapter-19-deployment-architecture)
- [Chapter 20 - Testing & Validation Strategy](#chapter-20-testing-validation-strategy)
- [Chapter 21 - Disaster Recovery & Business Continuity](#chapter-21-disaster-recovery-business-continuity)
- [Chapter 22 - Operations Runbook & Production Management](#chapter-22-operations-runbook-production-management)

---

# Chapter 1 - Introduction to EKIE

**Version:** 1.0\
**Status:** Approved\
**Volume:** I --- Vision & Product Strategy

## 1.1 Introduction

Enterprise AI initiatives are rapidly moving from experimentation to
production. Organizations are building intelligent assistants,
enterprise search platforms, copilots, and autonomous AI agents that
rely on one critical capability---the ability to retrieve trustworthy
organizational knowledge.

Most implementations focus heavily on Retrieval-Augmented Generation
(RAG), embeddings, vector databases, and Large Language Models (LLMs).
However, one of the most overlooked aspects is the quality of the
ingestion pipeline responsible for preparing enterprise knowledge.

Poor ingestion results in poor retrieval.

Poor retrieval results in inaccurate AI responses.

EKIE (Enterprise Knowledge Ingestion Engine) addresses this problem by
providing a dedicated enterprise platform responsible for transforming
heterogeneous enterprise documents into governed, versioned, traceable,
and AI-ready knowledge assets.

Unlike traditional ingestion scripts or ETL pipelines, EKIE is designed
as a long-lived enterprise platform with governance, observability,
extensibility, and operational resilience built into its foundation.

## 1.2 Background

Enterprise information exists across a wide variety of systems,
including:

- File Servers

- Microsoft SharePoint

- Microsoft OneDrive

- Git repositories

- Wikis

- Knowledge Bases

- PDF document repositories

- Engineering documentation

- Standard Operating Procedures (SOPs)

- Internal portals

- Content Management Systems

These repositories continuously evolve.

Documents are:

- Created

- Modified

- Renamed

- Moved

- Archived

- Deleted

Most ingestion pipelines assume documents are static, leading to stale
indexes, duplicate embeddings, inconsistent metadata, and poor
synchronization.

EKIE treats enterprise repositories as living systems and continuously
maintains a synchronized digital representation of their state.

## 1.3 The Enterprise Problem

Traditional ingestion pipelines often exhibit the following limitations:

  -----------------------------------------------------------------------
  **Challenge**                  **Business Impact**
  ------------------------------ ----------------------------------------
  One-time ingestion             Knowledge quickly becomes outdated

  No version control             Loss of traceability

  Duplicate embeddings           Increased storage and cost

  Weak metadata                  Poor retrieval quality

  No workflow orchestration      Difficult recovery from failures

  Limited observability          Operational blind spots

  Hardcoded processing logic     Difficult maintenance and extension

  No governance                  Compliance and audit challenges
  -----------------------------------------------------------------------

These limitations become increasingly problematic as organizations scale
their AI initiatives.

## 1.4 Vision

The vision of EKIE is to establish a standardized enterprise platform
that prepares organizational knowledge for AI consumption while ensuring
governance, consistency, and operational excellence.

The platform transforms raw enterprise content into structured knowledge
assets without coupling itself to any specific retrieval or chat
implementation.

## 1.5 Mission

EKIE exists to solve one problem exceptionally well:

**Convert enterprise documents into trusted, governed, versioned,
observable, and AI-ready knowledge assets.**

Every architectural decision within EKIE supports this mission.

## 1.6 Product Boundaries

One of the most important architectural decisions is defining what EKIE
is **not**.

EKIE intentionally focuses only on ingestion.

**Included**

- Repository synchronization

- Document discovery

- File transformation

- Canonical Markdown generation

- Metadata extraction

- Chunk generation

- Embedding generation

- Vector publishing

- Workflow orchestration

- Asset lineage

- Governance

- Observability

- Security

- Operational management

**Excluded**

- Retrieval

- Semantic search

- Hybrid search

- Query planning

- Prompt construction

- Chat interfaces

- AI agents

- LLM orchestration

- User conversations

These capabilities belong to downstream systems that consume EKIE
outputs.

## 1.7 Product Positioning

EKIE should be viewed as foundational infrastructure within the
enterprise AI ecosystem.

Enterprise AI Ecosystem

Repositories

│

▼

+\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\--+

\| EKIE Platform \|

\|\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\--\|

\| Repository Sync \|

\| Transformation \|

\| Markdown Generation \|

\| Chunking \|

\| Embedding \|

\| Publishing \|

\| Governance \|

\| Control Plane \|

+\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\--+

│

▼

AI-Ready Knowledge Assets

│

▼

Retrieval Platform (Future Project)

│

▼

Chat Platform (Future Project)

│

▼

Enterprise AI Applications

EKIE becomes the trusted producer of knowledge assets, while retrieval
and conversational AI remain independent consumers.

## 1.8 Core Objectives

The platform is designed to achieve the following objectives:

**Functional Objectives**

- Synchronize enterprise repositories continuously.

- Produce deterministic Markdown representations.

- Generate reusable knowledge chunks.

- Create version-controlled embeddings.

- Publish vectors reliably.

**Operational Objectives**

- Ensure high availability.

- Support horizontal scaling.

- Enable automated recovery.

- Maintain complete observability.

- Support enterprise governance.

**Engineering Objectives**

- Modular architecture.

- Plugin extensibility.

- Configuration-driven behavior.

- Deterministic workflows.

- Immutable asset management.

## 1.9 Design Principles

EKIE is guided by the following principles:

**1. Canonical Representation**

Markdown is the canonical intermediate representation for all supported
document formats.

**2. Immutable Assets**

Derived artifacts are never modified in place.

Every significant change creates a new version.

**3. Deterministic Processing**

The same document and configuration should always produce identical
outputs.

**4. Separation of Concerns**

Transformation, chunking, embedding, publishing, and orchestration are
independent frameworks.

**5. Configuration Over Code**

Behavior is controlled through versioned configuration rather than
hardcoded logic.

**6. Extensibility**

Every major processing stage supports plugin-based extension.

**7. Observability First**

Every workflow is traceable from repository discovery through vector
publication.

**8. Recoverability**

Failures are expected.

Data loss is not.

## 1.10 Key Architectural Concepts

Throughout this handbook, several concepts are referenced repeatedly.

**Repository**

A source system containing enterprise documents.

**Digital Twin**

EKIE's internal representation of the repository state.

**Document**

An original source file.

**Asset**

A derived artifact created during processing.

Examples:

- Markdown Asset

- Chunk Asset

- Embedding Asset

- Vector Asset

**Workflow**

The orchestrated execution of processing tasks.

**Control Plane**

The centralized SQL Server database that manages metadata,
orchestration, lineage, and operational state.

**Worker**

A runtime component responsible for executing tasks.

## 1.11 Success Criteria

EKIE will be considered successful when it consistently provides:

- Accurate repository synchronization.

- Deterministic transformations.

- Complete asset lineage.

- Reliable vector publishing.

- Comprehensive observability.

- Enterprise-grade governance.

- Scalable processing.

- Operational resilience.

## 1.12 Non-Functional Requirements

The architecture is designed to satisfy the following qualities:

  -----------------------------------------------------------------------
  **Category**         **Goal**
  -------------------- --------------------------------------------------
  Reliability          High availability and deterministic recovery

  Scalability          Horizontal worker scaling

  Performance          Efficient processing of large repositories

  Maintainability      Modular, plugin-driven architecture

  Security             Zero Trust and policy-driven access

  Observability        End-to-end tracing and metrics

  Extensibility        Versioned plugin ecosystem

  Compliance           Auditability and governance
  -----------------------------------------------------------------------

## 1.13 Summary

EKIE is not another RAG framework, document parser, or vector indexing
script.

It is an enterprise platform dedicated to one responsibility:

**Transforming enterprise knowledge into trusted, governed, versioned,
and AI-ready assets.**

By separating ingestion from retrieval and conversational AI, EKIE
establishes a robust architectural foundation that enables downstream
systems to evolve independently while consuming high-quality,
well-governed knowledge.

**Chapter 2 -- Enterprise
Architecture Principles**.

# Chapter 2 - Enterprise Architecture Principles

**Version:** 1.0\
**Status:** Approved\
**Volume:** I --- Vision & Product Strategy

## 2.1 Objective

This chapter establishes the architectural principles that govern every
design decision within EKIE.

These principles are **non-negotiable engineering rules**, not
implementation guidelines.

Every module, framework, plugin, workflow, and future enhancement must
comply with these principles.

If a future implementation conflicts with these principles, the
implementation---not the architecture---should be reconsidered.

## 2.2 Why Architecture Principles Matter

Enterprise platforms typically have long lifecycles, multiple
engineering teams, and evolving requirements.

Without clearly defined architectural principles:

- Components evolve independently.

- Technologies become tightly coupled.

- Codebases become inconsistent.

- Operational complexity increases.

- Future maintenance becomes expensive.

Architecture principles create a shared engineering language that
remains stable even as technologies evolve.

## 2.3 Principle 1 --- Single Responsibility Platform

**Statement**

**EKIE exists solely to transform enterprise knowledge into AI-ready
assets.**

EKIE does not retrieve information.

EKIE does not answer user questions.

EKIE does not execute AI agents.

EKIE prepares trusted knowledge for systems that perform those
responsibilities.

**Why?**

Keeping ingestion independent allows:

- Independent scaling

- Independent deployment

- Independent versioning

- Independent evolution

This separation reduces architectural coupling across the enterprise AI
ecosystem.

## 2.4 Principle 2 --- Canonical Knowledge Representation

**Statement**

**Every supported document must be converted into a single canonical
representation before further processing.**

The canonical representation chosen for EKIE is:

**Markdown**

Regardless of the source:

- PDF

- DOCX

- XLSX

- PPTX

- HTML

- TXT

- CSV

- Images (via OCR)

- Emails

every document eventually becomes Markdown. This conversion is performed
upstream by the EKDC agent (`services/ekdc`); EKIE ingests the resulting
Markdown.

**Benefits**

- Uniform processing

- Consistent chunking

- Simplified plugin architecture

- Reproducible transformations

- Easier debugging

- Future parser independence

Markdown becomes the universal language inside EKIE.

## 2.5 Principle 3 --- Deterministic Processing

**Statement**

**The same input and the same configuration must always produce the same
output.**

Deterministic processing applies to:

- Markdown generation

- Metadata extraction

- Chunking

- Embedding requests

- Publishing decisions

Deterministic behavior simplifies:

- Testing

- Recovery

- Auditing

- Version comparisons

- Compliance

## 2.6 Principle 4 --- Immutable Assets

Derived assets must never be modified after publication.

Instead:

Document v1

│

▼

Markdown v1

│

▼

Chunk Set v1

│

▼

Embedding Set v1

If a document changes:

Document v2

│

▼

Markdown v2

│

▼

Chunk Set v2

│

▼

Embedding Set v2

Previous versions remain available for lineage, auditing, and rollback.

## 2.7 Principle 5 --- Control Plane as the Source of Truth

The Control Plane is the authoritative system for:

- Workflow state

- Repository metadata

- Asset lineage

- Configuration

- Policies

- Operational history

- Processing status

External systems should never become the authoritative source of
operational state.

## 2.8 Principle 6 --- Digital Twin Architecture

EKIE never works directly against repositories alone.

Instead, it maintains a continuously synchronized Digital Twin.

Repository

↓

Synchronization

↓

Digital Twin

↓

Processing

Benefits:

- Fast reconciliation

- Reliable change detection

- Offline analysis

- Workflow replay

- Operational consistency

## 2.9 Principle 7 --- Event-Driven Processing

Every important action produces an event.

Examples:

- Document discovered

- Markdown generated

- Chunking completed

- Embedding created

- Publishing verified

The Event Store becomes the historical record of platform activity.

This enables:

- Replay

- Auditing

- Monitoring

- Recovery

## 2.10 Principle 8 --- Workflow-Centric Execution

Workers do not make business decisions.

Workflows define:

- Task order

- Dependencies

- Retry behavior

- Recovery logic

- Completion criteria

Workers simply execute assigned tasks.

This separation simplifies orchestration and operational control.

## 2.11 Principle 9 --- Configuration Over Code

Platform behavior must be configurable.

Examples:

- Chunk size

- Overlap

- Embedding model

- Retry limits

- Repository schedules

- Parser selection

- Publishing strategy

Business logic should not require source code changes for operational
adjustments.

## 2.12 Principle 10 --- Plugin-First Extensibility

Core components interact through contracts rather than concrete
implementations.

Supported plugin categories include:

- Repository Connectors

- Parsers

- Metadata Extractors

- Chunk Strategies

- Embedding Providers

- Vector Publishers

This allows organizations to extend EKIE without modifying the core
platform.

## 2.13 Principle 11 --- Security by Design

Security is not a post-processing activity.

It is integrated into every framework.

Examples:

- Authentication

- Authorization

- Encryption

- Secrets management

- Audit trails

- Policy enforcement

Every component must assume a Zero Trust environment.

## 2.14 Principle 12 --- Observability by Default

Every workflow, task, and worker must produce telemetry.

This includes:

- Structured logs

- Metrics

- Distributed traces

- Operational events

A production issue should be diagnosable without attaching a debugger.

## 2.15 Principle 13 --- Failure is Expected

Failures are normal.

Recovery should be automatic whenever possible.

The platform should support:

- Checkpointing

- Retry policies

- Replay

- Dead-letter queues

- Lease recovery

- Self-healing

Operational resilience is a first-class architectural concern.

## 2.16 Principle 14 --- Version Everything

The following must be versioned:

- Documents

- Assets

- Configurations

- Plugins

- Policies

- Workflows

- Schemas

- APIs

Versioning enables reproducibility, compatibility, and controlled
evolution.

## 2.17 Principle 15 --- Enterprise Scalability

The architecture must scale horizontally.

Scaling targets include:

- Worker pools

- Repository connectors

- Embedding providers

- Publishing services

- Workflow execution

Scaling should not require architectural redesign.

## 2.18 Principle 16 --- Technology Independence

Technologies may change over time.

Therefore:

- SQL Server can be replaced.

- Qdrant can be replaced.

- Embedding providers can be replaced.

- OCR engines (in the EKDC converter) can be replaced.

The architecture should depend on abstractions, not specific vendors.

## 2.19 Principle 17 --- Compliance Through Governance

Compliance requirements should be implemented through configurable
policies rather than hardcoded logic.

Examples include:

- Data retention

- Document classification

- Access control

- Regional restrictions

- Audit requirements

This allows EKIE to adapt to different regulatory environments.

## 2.20 Principle 18 --- AI Agnostic

EKIE prepares knowledge for AI but is not tied to any single AI model or
provider.

Supported providers should be interchangeable through the plugin
framework.

This ensures long-term flexibility as the AI ecosystem evolves.

## 2.21 Architectural Decision Hierarchy

When architectural decisions conflict, the following order of precedence
applies:

1.  Product Vision

2.  Architecture Principles

3.  Non-Functional Requirements

4.  Security Policies

5.  Operational Policies

6.  Framework Specifications

7.  Implementation Details

This hierarchy ensures consistency across future development.

## 2.22 Summary

These principles define the engineering DNA of EKIE.

Every framework described in subsequent chapters---from repository
synchronization through deployment---must reinforce these principles.

By establishing these rules early, the platform remains consistent,
maintainable, extensible, and resilient throughout its lifecycle.

**Chapter 3 -- Product
Vision, Scope, and Non-Functional Requirements**.

# Chapter 3 - Product Vision, Scope & Non-Functional Requirements

**Version:** 1.0\
**Status:** Approved\
**Volume:** I --- Vision & Product Strategy

## 3.1 Objective

This chapter defines **why EKIE exists**, **what business problems it
solves**, **where its responsibilities begin and end**, and the
**quality attributes** that drive every architectural decision.

Unlike functional requirements, which describe *what* the system does,
non-functional requirements define *how well* it must perform those
functions.

For an enterprise ingestion platform, these requirements are as
important as the functional capabilities.

## 3.2 Product Vision

**Vision Statement**

**To become the enterprise standard for transforming heterogeneous
organizational knowledge into trusted, governed, versioned, observable,
and AI-ready knowledge assets.**

This vision establishes EKIE as foundational infrastructure within the
enterprise AI ecosystem rather than as an application or feature.

**Long-Term Vision**

In the long term, organizations should be able to connect any supported
repository to EKIE and trust that the platform will:

- Discover knowledge automatically.

- Detect changes continuously.

- Preserve complete lineage.

- Govern every processing step.

- Produce deterministic AI-ready assets.

- Maintain synchronization throughout the document lifecycle.

- Provide enterprise-grade operational visibility.

EKIE becomes the trusted producer of knowledge rather than simply
another ingestion tool.

## 3.3 Product Mission

The mission of EKIE is simple:

**Continuously transform enterprise knowledge into high-quality AI-ready
assets while maintaining governance, traceability, operational
excellence, and long-term maintainability.**

Every framework introduced in this handbook supports this mission.

## 3.4 Business Problems

Organizations face several recurring challenges when preparing knowledge
for AI systems.

**Fragmented Information**

Knowledge is distributed across multiple repositories.

Examples include:

- File Shares

- SharePoint

- Git Repositories

- Wiki Platforms

- Internal Portals

- Network Drives

- Cloud Storage

There is rarely a single source of truth.

**Poor Data Quality**

Documents often contain:

- Duplicate information

- Inconsistent formatting

- Missing metadata

- Embedded images

- Broken hyperlinks

- Outdated versions

Without normalization, these issues propagate into downstream AI
systems.

**Manual Synchronization**

Many ingestion pipelines require manual execution or scheduled full
rescans.

This results in:

- Delayed updates

- High infrastructure costs

- Duplicate processing

- Stale vector indexes

**Lack of Governance**

Organizations frequently struggle to answer questions such as:

- Which document produced this embedding?

- Which parser generated this Markdown?

- Which configuration version was used?

- Who published this vector?

- When was the last successful synchronization?

Without governance, trust in AI outputs decreases significantly.

**Vendor Lock-In**

Many ingestion solutions are tightly coupled to:

- One embedding provider.

- One vector database.

- One repository.

- One cloud platform.

EKIE avoids this by introducing abstraction layers and plugin contracts.

## 3.5 Product Goals

The platform is designed to achieve the following goals.

**Business Goals**

- Improve AI knowledge quality.

- Reduce operational costs.

- Increase governance.

- Improve compliance.

- Enable enterprise-scale deployments.

**Engineering Goals**

- Modular architecture.

- Deterministic processing.

- Horizontal scalability.

- High availability.

- Extensible plugin ecosystem.

**Operational Goals**

- Continuous synchronization.

- Automatic recovery.

- Complete observability.

- Policy-driven operation.

- Simplified maintenance.

## 3.6 Product Scope

Clearly defining scope prevents feature creep.

**In Scope**

**Repository Layer**

- Repository registration

- Repository synchronization

- Change detection

- Digital Twin maintenance

**Transformation Layer**

- File parsing

- Markdown generation

- Metadata extraction

- Canonical document creation

**Processing Layer**

- Chunk generation

- Embedding generation

- Asset versioning

- Publishing preparation

**Publishing Layer**

- Vector publication

- Verification

- Retry

- Replay

**Platform Layer**

- Workflow orchestration

- Control Plane

- Plugin Framework

- Configuration

- Policy Engine

- Security

- Observability

- Recovery

## 3.7 Out of Scope

The following capabilities are intentionally excluded.

**Retrieval**

Not included:

- Semantic search

- Hybrid retrieval

- BM25

- Vector search APIs

**AI Orchestration**

Not included:

- Prompt engineering

- Context construction

- Conversation memory

- Agent execution

- Tool calling

**LLM Layer**

Not included:

- Model selection

- Response generation

- Chat interfaces

- AI assistants

**Business Applications**

Not included:

- Enterprise portals

- Web applications

- Mobile applications

- End-user interfaces

EKIE prepares knowledge but does not consume it.

## 3.8 Product Position within Enterprise AI

Enterprise AI Stack

Business Applications

│

▼

Conversational AI Platform

│

▼

Retrieval Engine

│

▼

=============================

Enterprise Knowledge Ingestion Engine (EKIE)

=============================

│

▼

Enterprise Repositories

This separation allows each platform to evolve independently.

## 3.9 Stakeholders

The platform serves multiple stakeholder groups.

  -----------------------------------------------------------------------
  **Stakeholder**              **Primary Interest**
  ---------------------------- ------------------------------------------
  Business Leadership          Reliable enterprise AI foundation

  Product Managers             Platform capabilities and roadmap

  Enterprise Architects        Long-term architecture

  AI Engineers                 Knowledge quality

  Backend Engineers            Framework implementation

  DevOps                       Deployment and operations

  Security Teams               Governance and compliance

  Operations                   Monitoring and recovery
  -----------------------------------------------------------------------

## 3.10 Functional Requirements

At a high level, EKIE shall:

- Synchronize repositories.

- Detect document changes.

- Transform documents.

- Generate Markdown.

- Produce chunks.

- Generate embeddings.

- Publish vectors.

- Maintain lineage.

- Expose operational metadata.

- Recover automatically from failures.

Detailed functional specifications are provided in later chapters.

## 3.11 Non-Functional Requirements (NFRs)

The following quality attributes govern the platform.

**Reliability**

The platform shall:

- Detect failures automatically.

- Retry transient operations.

- Resume interrupted workflows.

- Maintain data integrity.

Target:

- Workflow Success Rate ≥ 99.5%

**Availability**

The platform shall support high availability deployments.

Target:

- Platform Availability ≥ 99.95%

**Scalability**

The platform shall support horizontal scaling of:

- Workers

- Repositories

- Processing pipelines

- Publishing services

Scaling should not require architectural redesign.

**Performance**

Representative targets:

  -----------------------------------------------------------------------
  **Operation**                  **Target**
  ------------------------------ ----------------------------------------
  Repository Scan                Configurable by repository size

  Markdown Generation            \<5 seconds per average document

  Chunk Generation               \<2 seconds per document

  Embedding Throughput           Configurable by provider limits

  Publish Verification           \<1 second per asset
  -----------------------------------------------------------------------

Performance budgets may be refined for specific deployments.

**Maintainability**

The architecture shall support:

- Plugin extensibility.

- Independent framework evolution.

- Versioned APIs.

- Configuration-driven behavior.

No major subsystem should require modifications to unrelated components.

**Security**

The platform shall implement:

- Authentication

- Authorization

- Encryption

- Audit logging

- Secret management

- Policy enforcement

Security must be integrated into every processing stage.

**Observability**

Every workflow shall expose:

- Logs

- Metrics

- Distributed traces

- Events

- Health status

No processing stage should operate as a "black box."

**Recoverability**

The platform shall support:

- Checkpoints

- Replay

- Dead-letter handling

- Lease recovery

- Repository reconciliation

Recovery should minimize reprocessing through lineage-aware replay.

**Extensibility**

Organizations shall be able to introduce new:

- Parsers

- Repository connectors

- Chunking strategies

- Embedding providers

- Vector publishers

without modifying the core platform.

## 3.12 Assumptions

The architecture assumes:

- Enterprise repositories remain the authoritative content source.

- SQL Server acts as the Control Plane.

- Markdown is the canonical representation.

- Asset storage is persistent and versioned.

- Vector databases can be rebuilt from canonical assets if necessary.

## 3.13 Constraints

Current architectural constraints include:

- Only ingestion is implemented.

- Downstream retrieval systems are external.

- Asset immutability is mandatory.

- Workflow execution is centrally orchestrated.

- Processing must remain deterministic.

These constraints protect the integrity and long-term maintainability of
the platform.

## 3.14 Success Metrics

Success is measured through both technical and business outcomes.

**Technical Metrics**

- Synchronization accuracy

- Processing throughput

- Recovery success rate

- Workflow completion rate

- Operational availability

**Business Metrics**

- Reduction in stale knowledge

- Increased trust in AI outputs

- Reduced operational effort

- Faster onboarding of repositories

- Improved governance and auditability

## 3.15 Summary

This chapter establishes the strategic direction of EKIE.

It defines:

- The business problem.

- The product mission.

- The architectural scope.

- Stakeholders.

- Functional boundaries.

- Non-functional expectations.

- Success criteria.

These definitions serve as the foundation for every technical framework
introduced in the remainder of this handbook.

**Chapter 4 -- High-Level Enterprise Architecture & End-to-End
Ingestion Lifecycle**, where we introduce the complete EKIE
architecture, major subsystems, data flow, and the end-to-end processing
lifecycle that the remaining chapters will elaborate in detail.

**Chapter 4 --- High-Level Enterprise Architecture & End-to-End
Ingestion Lifecycle**

**Version:** 1.0\
**Status:** Approved\
**Volume:** I --- Vision & Product Strategy

## 4.1 Objective

This chapter introduces the complete Enterprise Knowledge Ingestion
Engine (EKIE) architecture from a system perspective.

Previous chapters answered:

- Why does EKIE exist?

- What problems does it solve?

- What principles govern the platform?

This chapter answers the next question:

**How does the complete platform work as a single system?**

The remaining chapters of this handbook will progressively decompose
each subsystem introduced here.

## 4.2 Architectural Philosophy

EKIE is designed as a **distributed, event-driven, workflow-oriented
ingestion platform**.

It is **not** a linear ETL pipeline.

Instead, it is composed of loosely coupled frameworks coordinated
through a central Control Plane.

Each framework has a single responsibility and communicates through
well-defined contracts.

This architecture enables:

- Independent evolution

- Horizontal scalability

- Fault isolation

- Operational observability

- Plugin extensibility

- Technology independence

## 4.3 Enterprise Context

EKIE sits between enterprise knowledge repositories and downstream AI
platforms.

┌────────────────────────────────────────────┐

│ Enterprise Repositories │

│\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\--│

│ SharePoint │ File Server │ Git │ OneDrive │

│ Wiki │ PDFs │ Office Docs │ Emails │ APIs │

└────────────────────────────────────────────┘

│

▼

═══════════════════════════════════════════════

Enterprise Knowledge Ingestion Engine

═══════════════════════════════════════════════

│

▼

AI-Ready Knowledge Assets (Markdown, Chunks,

Embeddings, Metadata, Vectors, Lineage)

│

▼

═══════════════════════════════════════════════

Retrieval Platform (Future Product)

═══════════════════════════════════════════════

│

▼

═══════════════════════════════════════════════

Enterprise AI Applications (Future Products)

═══════════════════════════════════════════════

The architectural boundary is explicit:

**EKIE ends after publishing verified knowledge assets.**

## 4.4 Architectural Layers

The platform is organized into logical layers.

Presentation Layer (Administration)

↓

Management Layer

↓

Control Plane

↓

Workflow Orchestration

↓

Processing Frameworks

↓

Infrastructure Layer

↓

Enterprise Repositories

Each layer depends only on the layer directly beneath it.

No layer bypasses another.

## 4.5 Major Platform Components

The architecture consists of eleven primary subsystems.

  -----------------------------------------------------------------------
  **Component**                 **Responsibility**
  ----------------------------- -----------------------------------------
  Repository Synchronization    Discover and track enterprise documents

  Digital Twin                  Maintain repository state

  Workflow Engine               Orchestrate processing

  Markdown Framework            Generate canonical documents

  Chunking Framework            Produce semantic chunks

  Embedding Framework           Generate vector embeddings

  Publishing Framework          Publish to Vector DB

  Control Plane                 Metadata, lineage, orchestration

  Worker Runtime                Execute processing tasks

  Plugin Framework              Extensibility

  Observability Framework       Logging, metrics, tracing
  -----------------------------------------------------------------------

Each subsystem is explored in dedicated chapters.

## 4.6 Complete System Architecture

┌────────────────────────────┐

│ Enterprise Repositories │

└─────────────┬──────────────┘

│

▼

Repository Synchronization

│

▼

Digital Twin Manager

│

▼

Workflow Engine

│

┌───────────────────────┼────────────────────────┐

▼ ▼ ▼

Markdown Framework Metadata Framework Policy Engine

│

▼

Canonical Markdown

│

▼

Chunking Framework

│

▼

Embedding Framework

│

▼

Publishing Framework

│

▼

Vector Database

──────────────────────────────────────────────────────────

▲

│

Enterprise Control Plane

│

──────────────────────────────────────────────────────────

Stores:

• Metadata

• Lineage

• Workflow State

• Version History

• Configuration

• Policies

• Operational Events

This architecture separates processing from orchestration and
governance.

## 4.7 Processing Lifecycle

Every document follows the same deterministic lifecycle.

Repository

↓

Discovery

↓

Registration

↓

Transformation

↓

Markdown Generation

↓

Metadata Extraction

↓

Chunk Generation

↓

Embedding Generation

↓

Publishing

↓

Verification

↓

Completed

Every transition is recorded by the Control Plane.

## 4.8 Document State Machine

Every document progresses through a defined state machine.

DISCOVERED

↓

REGISTERED

↓

TRANSFORMING

↓

MARKDOWN_READY

↓

CHUNKED

↓

EMBEDDED

↓

PUBLISHED

↓

VERIFIED

Additional states:

FAILED

WAITING

RETRYING

ARCHIVED

DELETED

Future chapters will formally define every transition and recovery path.

## 4.9 Asset Lifecycle

A document produces multiple derived assets.

Original Document

↓

Markdown Asset

↓

Chunk Assets

↓

Embedding Assets

↓

Published Vectors

Each asset:

- Receives a unique identifier.

- Is independently versioned.

- Maintains lineage to its parent.

- Can be replayed if required.

Assets are immutable after publication.

## 4.10 Control Plane Responsibilities

The Control Plane is the operational heart of EKIE.

It manages:

- Repository registration

- Document inventory

- Workflow orchestration

- Version tracking

- Lineage

- Processing status

- Policies

- Configuration

- Audit history

- Recovery checkpoints

It does **not** store document content or vectors.

Those remain in dedicated storage systems.

## 4.11 Workflow Execution Model

Workflows are orchestrated centrally.

Workers execute tasks.

Control Plane

↓

Workflow Engine

↓

Task Queue

↓

Worker Pool

↓

Processing Framework

↓

Status Update

↓

Control Plane

Workers are stateless and disposable.

The Control Plane owns workflow state.

## 4.12 Event Flow

Every significant operation emits an event.

Examples:

- RepositoryDiscovered

- RepositorySynchronized

- DocumentRegistered

- MarkdownGenerated

- MetadataExtracted

- ChunkCreated

- EmbeddingGenerated

- PublishingStarted

- PublishingCompleted

- WorkflowCompleted

- WorkflowFailed

Events support observability, replay, auditing, and operational
analytics.

## 4.13 Versioning Strategy

Versioning exists at multiple levels.

  -----------------------------------------------------------------------
  **Entity**                                 **Versioned**
  ------------------------------------------ ----------------------------
  Repository                                 ✓

  Document                                   ✓

  Markdown                                   ✓

  Chunks                                     ✓

  Embeddings                                 ✓

  Published Vectors                          ✓

  Configuration                              ✓

  Plugins                                    ✓

  Policies                                   ✓

  Workflows                                  ✓
  -----------------------------------------------------------------------

This ensures complete reproducibility of every processing decision.

## 4.14 Failure Philosophy

EKIE assumes failures will occur.

Common failure scenarios include:

- Repository unavailable

- Markdown parser failure

- Embedding timeout

- Vector publishing error

- Worker crash

- Database interruption

The architecture is designed so that:

- No data is lost.

- Work can resume from checkpoints.

- Failed tasks are isolated.

- Successful assets are not regenerated unnecessarily.

## 4.15 Scalability Model

Horizontal scaling is achieved by increasing worker capacity rather than
modifying platform architecture.

Scalable components include:

- Repository scanners

- Transformation workers

- Chunking workers

- Embedding workers

- Publishing workers

The Control Plane coordinates distributed execution while maintaining a
consistent system state.

## 4.16 Deployment Perspective

A production deployment consists of the following logical services:

Administration API

↓

Control Plane

↓

Workflow Service

↓

Worker Pool

↓

Plugin Runtime

↓

SQL Server

↓

Artifact Storage

↓

Vector Database

These services may be deployed independently to support scaling and high
availability.

## 4.17 Architectural Characteristics

The architecture exhibits the following qualities:

  -----------------------------------------------------------------------
  **Characteristic**       **Implementation**
  ------------------------ ----------------------------------------------
  Modular                  Framework-based decomposition

  Extensible               Plugin contracts

  Deterministic            Canonical processing pipeline

  Observable               Centralized telemetry

  Recoverable              Checkpoints and replay

  Scalable                 Stateless worker pools

  Governed                 Control Plane and policy engine

  Vendor Neutral           Interface-driven integrations
  -----------------------------------------------------------------------

## 4.18 Architectural Boundaries

To maintain a clean separation of responsibilities:

EKIE **owns**:

- Knowledge ingestion

- Knowledge transformation

- Knowledge publication

EKIE **does not own**:

- Knowledge retrieval

- Search optimization

- Prompt generation

- LLM interaction

- Conversational AI

This boundary ensures that ingestion remains stable even as AI
technologies evolve.

## 4.19 Summary

This chapter establishes the complete architectural blueprint for EKIE.

It introduces:

- Platform layers

- Major subsystems

- Processing lifecycle

- Document state model

- Asset lineage

- Workflow execution

- Event flow

- Deployment model

- Architectural boundaries

Every remaining chapter in this handbook expands one or more components
introduced here.

**Chapter 5 -- Enterprise Knowledge Lifecycle & Digital Twin
Model**, where we define the complete lifecycle of repositories,
documents, assets, lineage, and the Digital Twin that becomes the
authoritative operational representation of enterprise knowledge.

# Chapter 5 - Enterprise Knowledge Lifecycle & Digital Twin Model

**Version:** 1.0\
**Status:** Approved\
**Volume:** II --- Functional Architecture

## 5.1 Objective

This chapter introduces one of the most important architectural concepts
within EKIE:

**The Digital Twin.**

Rather than interacting directly with enterprise repositories during
processing, EKIE maintains an internal, continuously synchronized
representation of every repository, document, version, and derived
asset.

This Digital Twin becomes the operational model that drives
synchronization, orchestration, lineage, governance, recovery, and
auditing.

Without a Digital Twin, enterprise-scale synchronization becomes
unreliable and expensive.

## 5.2 Why a Digital Twin?

Most ingestion systems repeatedly scan repositories and compare files to
determine what has changed.

As repositories grow to millions of files, this approach becomes:

- Slow

- Expensive

- Difficult to recover

- Hard to audit

- Error-prone

Instead, EKIE builds and maintains its own internal model of the
repository.

The repository remains the **source of content**, while the Digital Twin
becomes the **source of operational truth**.

## 5.3 Design Philosophy

The repository tells EKIE **what exists**.

The Digital Twin tells EKIE:

- What has already been processed.

- What version exists.

- What changed.

- What assets were generated.

- What workflows completed.

- What requires reprocessing.

- What has been deleted.

- What failed.

- What can be replayed.

The platform never needs to guess its current state.

## 5.4 High-Level Architecture

Enterprise Repository

│

▼

Repository Synchronization

│

▼

═════════════════════════════════════════════

Enterprise Digital Twin

═════════════════════════════════════════════

Repositories

│

Documents

│

Versions

│

Assets

│

Chunks

│

Embeddings

│

Vectors

│

Workflow State

│

Policies

│

Events

═════════════════════════════════════════════

│

▼

Processing Frameworks

Every processing framework interacts with the Digital Twin rather than
directly with repository metadata.

## 5.5 Core Principles

The Digital Twin follows several architectural rules.

**Principle 1**

Every repository has exactly one Digital Twin.

**Principle 2**

Every document has one logical identity throughout its lifetime.

Renaming a document does **not** create a new document.

Moving a document does **not** create a new document.

Deleting and recreating a document creates a new identity only if the
underlying document identity changes.

**Principle 3**

Every significant change creates a new version.

Nothing is overwritten.

**Principle 4**

Every asset maintains complete lineage.

Every chunk can always identify:

- Markdown

- Source document

- Repository

- Workflow

- Configuration

- Embedding model

**Principle 5**

The Digital Twin never stores business content.

Instead it stores:

- Metadata

- Relationships

- State

- Version history

- Processing history

Content resides in dedicated storage.

## 5.6 Digital Twin Hierarchy

The Digital Twin is hierarchical.

Enterprise

↓

Repository

↓

Folder

↓

Document

↓

Document Version

↓

Markdown Asset

↓

Chunk Assets

↓

Embedding Assets

↓

Published Vector Assets

Every node has its own identity.

## 5.7 Repository Lifecycle

A repository progresses through defined states.

REGISTERED

↓

DISCOVERING

↓

SYNCHRONIZING

↓

ACTIVE

↓

RECONCILING

↓

ARCHIVED

Failure states:

ERROR

DISCONNECTED

DISABLED

## 5.8 Document Lifecycle

Each document follows a deterministic lifecycle.

DISCOVERED

↓

REGISTERED

↓

HASH VERIFIED

↓

PROCESSING

↓

MARKDOWN READY

↓

CHUNKED

↓

EMBEDDED

↓

PUBLISHED

↓

VERIFIED

Additional operational states:

WAITING

RETRYING

FAILED

DELETED

ARCHIVED

The lifecycle is controlled by the Workflow Engine and persisted within
the Control Plane.

## 5.9 Asset Lifecycle

Every derived asset progresses independently.

CREATED

↓

VALIDATED

↓

READY

↓

PUBLISHED

↓

VERIFIED

↓

SUPERSEDED

↓

ARCHIVED

Assets are immutable.

A superseded asset is retained for lineage and audit purposes.

## 5.10 Document Identity

One of the most critical architectural decisions concerns document
identity.

A document should **not** be identified solely by its file path.

Why?

Paths change.

Folders change.

Names change.

Instead, EKIE assigns an immutable internal identifier when the document
is first discovered.

Repository

↓

Internal Document ID

↓

Current Location

↓

Current Version

↓

Current State

This allows rename and move operations to preserve document history.

## 5.11 Version Model

Versioning occurs at multiple levels.

Document

Version 1

↓

Markdown v1

↓

Chunks v1

↓

Embeddings v1

↓

Vectors v1

\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\--

Document Modified

↓

Version 2

↓

Markdown v2

↓

Chunks v2

↓

Embeddings v2

↓

Vectors v2

Previous versions remain available for replay, auditing, and comparison.

## 5.12 Lineage Model

Every object in EKIE participates in a lineage graph.

Repository

↓

Document

↓

Document Version

↓

Markdown

↓

Chunk

↓

Embedding

↓

Published Vector

This enables questions such as:

- Which document produced this vector?

- Which embedding model was used?

- Which Markdown version generated this chunk?

- Which workflow published this asset?

Every answer should be obtainable through the Control Plane.

## 5.13 Change Detection

Repository synchronization identifies the following events:

  -----------------------------------------------------------------------
  **Change**          **Action**
  ------------------- ---------------------------------------------------
  New Document        Create Digital Twin entry and start workflow

  Content Modified    Create new document version

  Rename              Update location metadata only

  Move                Update hierarchy only

  Metadata Changed    Update metadata and evaluate reprocessing policy

  Deleted             Mark document as deleted and initiate cleanup
                      workflow
  -----------------------------------------------------------------------

Each event is evaluated independently.

## 5.14 Relationship with the Workflow Engine

The Workflow Engine operates exclusively on Digital Twin entities.

Digital Twin

↓

Workflow Request

↓

Workflow Instance

↓

Tasks

↓

Workers

↓

State Update

↓

Digital Twin

The Workflow Engine never directly scans repositories.

## 5.15 Relationship with Asset Storage

The Digital Twin references assets but does not contain them.

Digital Twin

↓

Asset Metadata

↓

Storage URI

↓

Artifact Storage

This separation improves scalability and simplifies backup strategies.

## 5.16 Relationship with the Vector Database

Similarly, the Digital Twin tracks published vectors without storing
vector payloads.

Stored information includes:

- Vector identifier

- Collection

- Embedding version

- Publish timestamp

- Verification status

- Provider

- Dimension

The vector itself resides within the Vector Database.

## 5.17 Digital Twin Responsibilities

The Digital Twin is responsible for:

- Repository inventory

- Document identity

- Version tracking

- Asset lineage

- Workflow state

- Processing status

- Configuration association

- Policy association

- Operational history

- Replay eligibility

It is **not** responsible for content storage or vector storage.

## 5.18 Architectural Benefits

The Digital Twin provides significant enterprise advantages.

  ----------------------------------------------------------------------
  **Capability**              **Benefit**
  --------------------------- ------------------------------------------
  Version History             Complete audit trail

  Stable Identity             Rename and move resilience

  Lineage                     End-to-end traceability

  Replay                      Efficient recovery

  Operational State           Reliable orchestration

  Governance                  Policy enforcement

  Analytics                   Platform insights

  Synchronization             Accurate change detection
  ----------------------------------------------------------------------

## 5.19 Design Decisions (ADRs)

**ADR-005: Digital Twin as Operational Truth**

**Decision**

The Digital Twin is the authoritative operational model for all
processing workflows.

**Rationale**

Separating repository content from operational state enables
deterministic workflows, efficient synchronization, replay, and
governance.

**ADR-006: Immutable Asset Lineage**

**Decision**

Derived assets are immutable and permanently linked to their parent
entities.

**Rationale**

Immutability guarantees reproducibility, simplifies auditing, and
enables reliable rollback and comparison.

**ADR-007: Stable Document Identity**

**Decision**

Documents receive immutable internal identifiers independent of file
paths.

**Rationale**

Paths and names change over time, but document identity must remain
stable to preserve history and lineage.

## 5.20 Summary

The Digital Twin is one of the foundational architectural pillars of
EKIE.

It provides a stable, versioned, lineage-aware representation of
enterprise knowledge that separates repository content from operational
state.

Every subsequent framework---repository synchronization, transformation,
workflow orchestration, chunking, embedding, publishing, recovery, and
governance---depends on the Digital Twin to provide deterministic
behavior and complete traceability.

**Chapter 6 -- Repository Synchronization Framework**, where
we will design the complete ingestion entry point, including repository
registration, file discovery, hashing strategy, rename/move detection,
deletion handling, incremental synchronization, reconciliation, and
event generation. This chapter will define the heart of the ingestion
engine.

# Chapter 6 - Repository Synchronization Framework

**Version:** 1.0\
**Status:** Approved\
**Volume:** II --- Functional Architecture

## 6.1 Objective

The Repository Synchronization Framework is the **entry point of the
EKIE ingestion platform**.

Its responsibility is **not** to process documents.

Its responsibility is to continuously maintain an accurate
representation of enterprise repositories and notify the platform
whenever meaningful changes occur.

No downstream framework (Markdown, Chunking, Embedding, Publishing)
should directly access enterprise repositories.

All repository interaction is centralized within this framework.

## 6.2 Why a Dedicated Synchronization Framework?

Many ingestion pipelines simply execute:

Scan Folder

↓

Process Every File

This approach has several problems:

- Expensive rescans

- Duplicate processing

- Slow synchronization

- Difficult recovery

- No operational visibility

- Poor scalability

EKIE instead performs:

Repository

↓

Synchronization Engine

↓

Digital Twin

↓

Workflow Engine

↓

Processing

Only documents requiring action are processed.

## 6.3 Responsibilities

The Repository Synchronization Framework is responsible for:

- Repository registration

- Repository connectivity

- Repository health monitoring

- Repository discovery

- Folder hierarchy synchronization

- File discovery

- Metadata synchronization

- Change detection

- Rename detection

- Move detection

- Deletion detection

- Incremental synchronization

- Repository reconciliation

- Event generation

It **does not** transform documents.

## 6.4 Supported Repository Types

The framework is intentionally repository-agnostic.

Initial connectors include:

  -----------------------------------------------------------------------
  **Repository**                                **Supported**
  --------------------------------------------- -------------------------
  Local File System                             ✓

  Network Share (SMB)                           ✓

  SharePoint                                    ✓

  OneDrive                                      ✓

  Git Repository                                ✓

  Azure Blob Storage                            Future

  Amazon S3                                     Future

  Google Drive                                  Future

  FTP/SFTP                                      Future

  REST Repository                               Future
  -----------------------------------------------------------------------

Each connector implements a common interface.

## 6.5 Architecture

Repository Connectors

File System

SharePoint

Git

OneDrive

───────────────

↓

Repository Synchronization Framework

↓

Repository Scanner

↓

Change Detector

↓

Digital Twin

↓

Workflow Engine

The rest of EKIE remains unaware of repository implementation details.

## 6.6 Repository Registration

Before synchronization begins, repositories are registered with the
Control Plane.

Example metadata:

  -----------------------------------------------------------------------
  **Property**                    **Description**
  ------------------------------- ---------------------------------------
  Repository ID                   Internal UUID

  Name                            Logical repository name

  Type                            File System, SharePoint, Git

  Root Path                       Repository root

  Authentication Profile          Credential reference

  Scan Schedule                   Policy-driven

  Status                          Active, Disabled, Archived

  Connector Version               Plugin version
  -----------------------------------------------------------------------

Repositories become manageable enterprise assets.

## 6.7 Repository Discovery

Discovery identifies:

- Folder hierarchy

- Files

- Metadata

- Permissions (optional)

- Repository capabilities

Discovery **does not** trigger processing.

It only builds the repository inventory.

## 6.8 Repository Metadata

For every discovered object, metadata is collected.

Examples:

Repository ID

Document Path

Document Name

Extension

Size

Created Time

Modified Time

Checksum

Owner

Last Scan

Current Status

Additional metadata can be extracted by connector plugins.

## 6.9 Repository Scan Strategy

The framework supports multiple scan strategies.

**Full Scan**

Used for:

- Initial onboarding

- Complete reconciliation

- Disaster recovery

Advantages:

- Complete verification

Disadvantages:

- Slow

**Incremental Scan**

Default strategy.

Only changed objects are evaluated.

Advantages:

- Fast

- Low resource usage

- Enterprise scalable

**Event-Based Scan**

Repositories capable of generating change notifications may push events.

Examples:

- SharePoint Webhooks

- File System Watchers

- Git Webhooks

This minimizes unnecessary polling.

## 6.10 Change Detection

The Change Detector evaluates repository changes.

Supported events:

New File

Modified File

Renamed File

Moved File

Deleted File

Metadata Updated

Each event is normalized before entering the Workflow Engine.

## 6.11 Hashing Strategy

Content hashing determines whether a document has materially changed.

Recommended algorithm:

SHA-256

Hashes are computed after normalization when appropriate.

Hash comparison avoids unnecessary downstream processing.

Example:

Previous Hash

↓

Current Hash

↓

Equal

↓

Skip Processing

## 6.12 Rename Detection

Renaming should **not** create duplicate documents.

Instead:

Old Path

↓

New Path

↓

Same Internal Document ID

History remains intact.

Only location metadata changes.

## 6.13 Move Detection

Moving documents behaves similarly.

Folder A

↓

Folder B

↓

Document Identity Preserved

The Workflow Engine evaluates whether downstream processing is required
based on policy.

## 6.14 Deletion Detection

Deletion is one of the most critical operations.

When a document is removed:

Repository

↓

Deletion Event

↓

Digital Twin Updated

↓

Cleanup Workflow

↓

Vector Removal

↓

Asset Archived

↓

Workflow Complete

The source repository always remains authoritative.

## 6.15 Reconciliation

Periodic reconciliation validates repository consistency.

Example:

Repository

↓

Current Inventory

↓

Digital Twin

↓

Compare

↓

Differences

↓

Repair

Reconciliation detects:

- Missed events

- Failed updates

- Repository drift

- Metadata inconsistencies

## 6.16 Synchronization Policies

Synchronization behavior is policy-driven.

Example policies:

  -----------------------------------------------------------------------
  **Policy**                            **Example**
  ------------------------------------- ---------------------------------
  Scan Interval                         Every 15 minutes

  Ignore Hidden Files                   Yes

  Ignore Temporary Files                Yes

  Maximum File Size                     500 MB

  Allowed Extensions                    MD (Markdown from EKDC)

  Hash Algorithm                        SHA-256

  Rename Detection                      Enabled

  Delete Propagation                    Enabled
  -----------------------------------------------------------------------

Policies are versioned within the Control Plane.

## 6.17 Repository State Machine

Each repository follows a defined lifecycle.

REGISTERED

↓

CONNECTING

↓

DISCOVERING

↓

SYNCHRONIZING

↓

ACTIVE

Operational states:

PAUSED

ERROR

RECONCILING

DISABLED

ARCHIVED

Transitions are managed by the Repository Synchronization Framework.

## 6.18 Document Synchronization State Machine

Each discovered document transitions through synchronization states
before processing.

NEW

↓

DISCOVERED

↓

HASH VERIFIED

↓

UNCHANGED

↓

CHANGED

↓

WORKFLOW CREATED

Alternative states:

RENAMED

MOVED

DELETED

FAILED

WAITING

## 6.19 Events Generated

Repository synchronization emits standardized events.

Examples:

RepositoryRegistered

RepositoryConnected

RepositoryDisconnected

RepositorySynchronized

DocumentDiscovered

DocumentModified

DocumentRenamed

DocumentMoved

DocumentDeleted

RepositoryReconciled

SynchronizationFailed

These events become inputs for the Workflow Engine.

## 6.20 Failure Handling

Expected failures include:

  -----------------------------------------------------------------------
  **Failure**                        **Recovery**
  ---------------------------------- ------------------------------------
  Repository unavailable             Retry using backoff policy

  Authentication expired             Refresh credentials

  Network timeout                    Retry

  Partial scan                       Resume from checkpoint

  Connector failure                  Restart connector

  Hash computation failure           Retry or quarantine
  -----------------------------------------------------------------------

The framework is designed so that synchronization failures do **not**
corrupt the Digital Twin.

## 6.21 Performance Considerations

The synchronization framework must be optimized for enterprise-scale
repositories.

Key design principles:

- Incremental scanning by default.

- Parallel repository scanning.

- Configurable worker pools.

- Batched metadata persistence.

- Hash caching where safe.

- Streaming enumeration for large repositories.

- Event-driven synchronization when supported.

The objective is to minimize repository load while maintaining
synchronization accuracy.

## 6.22 Security Considerations

Repository access follows the principle of least privilege.

Requirements include:

- Read-only access whenever possible.

- Secure credential storage.

- Credential rotation support.

- Encrypted communication.

- Connector authentication abstraction.

- Complete audit logging for repository access.

Repository credentials must never be embedded in connector
implementations.

## 6.23 Design Decisions (ADRs)

**ADR-008: Centralized Repository Access**

**Decision**

All repository communication is performed exclusively through the
Repository Synchronization Framework.

**Rationale**

Centralizing repository interaction simplifies governance, improves
observability, and prevents duplicated repository logic across
downstream frameworks.

**ADR-009: Repository as Content Authority**

**Decision**

The repository remains the authoritative source of document content.

**Rationale**

EKIE derives knowledge assets but never becomes the master copy of
enterprise documents.

**ADR-010: Synchronization Before Processing**

**Decision**

Every document must first be synchronized into the Digital Twin before
any transformation workflow is created.

**Rationale**

This guarantees consistent identity, versioning, lineage, and
operational state throughout the ingestion lifecycle.

## 6.24 Summary

The Repository Synchronization Framework establishes the foundation of
the EKIE ingestion pipeline. By separating repository interaction from
document processing, it enables scalable, deterministic, and
policy-driven synchronization while maintaining a continuously accurate
Digital Twin.

Every downstream framework relies on the synchronization layer to
provide stable document identities, reliable change detection, and
consistent operational events.

# Chapter 7 - Document Transformation & Canonical Markdown Framework

**Version:** 1.0\
**Status:** Approved\
**Volume:** II --- Functional Architecture

## 7.1 Objective

Once the Repository Synchronization Framework has identified that a
document requires processing, the next responsibility is to establish
EKIE's **canonical representation**.

For EKIE, the canonical representation is:

**Markdown (.md)**

Conversion of heterogeneous source formats (PDF, DOCX, PPTX, HTML, CSV,
images, audio, video) into Markdown is performed **upstream** by the
**Enterprise Knowledge Document Converter (EKDC)** agent
(`services/ekdc`), which writes `.md` files while preserving the source
folder structure. EKIE ingests that Markdown directly.

This chapter defines the **Document Transformation Framework**, which
canonicalizes incoming Markdown into deterministic, structured,
metadata-rich Markdown assets suitable for downstream chunking and
embedding. It normalizes text, applies YAML front matter, validates
structure, and creates immutable versions --- it does not convert binary
document formats.

## 7.2 Why Markdown?

A common question is:

**Why convert everything to Markdown instead of chunking documents
directly?**

Because enterprise documents come in many different formats, each with
its own parsing logic.

Examples include:

- PDF

- DOCX

- PPTX

- XLSX

- TXT

- HTML

- XML

- CSV

- Images

- Emails

If chunking is performed directly on every format, every downstream
framework must understand every document type.

Instead, the platform standardizes processing through Markdown. The EKDC
agent performs the format-specific conversion once, upstream of EKIE, so
EKIE and all downstream frameworks operate on a single format.

PDF

DOCX

PPTX

HTML

CSV

EMAIL

↓

EKDC Converter (format-specific conversion)

↓

Markdown

↓

EKIE Transformation Framework (canonicalize + validate)

↓

Chunking

↓

Embedding

↓

Publishing

Every EKIE framework processes exactly one format.

## 7.3 Responsibilities

The Transformation Framework is responsible for:

- Markdown intake (reading `.md` / plain-text bytes)

- Text normalization

- Front-matter metadata assembly

- Canonical Markdown generation

- Validation

- Deduplication by content hash

- Version creation

It is **not** responsible for:

- Format conversion of binary documents (owned by EKDC)

- OCR and rich-media extraction (owned by EKDC)

- Content extraction from PDF/DOCX/PPTX/images/audio/video (owned by EKDC)

- Chunking

- Embedding

- Publishing

## 7.4 Supported File Types (Phase 1)

  -----------------------------------------------------------------------
  **Category**         **Formats**
  -------------------- --------------------------------------------------
  Markdown             MD, MARKDOWN

  Plain text           TXT, TEXT, LOG, RTF
  -----------------------------------------------------------------------

EKIE ingests Markdown only. All other source formats (PDF, DOCX, PPTX,
XLSX, HTML, XML, CSV, images, email, audio, video) are converted to
Markdown upstream by the EKDC agent before they reach EKIE. The
plain-text parser is retained as a defensive fallback. The framework
remains extensible through parser plugins.

## 7.5 High-Level Architecture

Source File (any format)

↓

EKDC Converter (→ Markdown)

↓

Markdown File

↓

Parser Registry (Markdown / plain text)

↓

Markdown Intake

↓

Normalization Engine

↓

Markdown Generator

↓

Validation

↓

Markdown Asset

↓

Digital Twin

Every stage is independently testable and replaceable.

## 7.6 Parser Registry

The Parser Registry selects the appropriate parser based on document
type. Because EKIE ingests Markdown, the registry resolves to the
Markdown parser (or the plain-text fallback).

Extension

↓

MIME Type

↓

Parser Registry

↓

Registered Parser

↓

Execution

Example:

  -----------------------------------------------------------------------
  **File**                **Parser**
  ----------------------- -----------------------------------------------
  MD                      Markdown Parser

  MARKDOWN                Markdown Parser

  TXT                     Plain-Text Parser
  -----------------------------------------------------------------------

Parsers implement a common interface, allowing new formats to be added
through plugins without modifying the framework.

## 7.7 Transformation Pipeline

Every document follows the same transformation lifecycle.

Markdown Document (from EKDC)

↓

Parser Selection (Markdown / plain text)

↓

Content Decode

↓

Metadata / Front-Matter Assembly

↓

Normalization

↓

Canonical Markdown Generation

↓

Validation

↓

Asset Storage

↓

Workflow Complete

The output is always a single canonical Markdown document.

## 7.8 Normalization Rules

Before Markdown generation, extracted content is normalized to ensure
deterministic output.

Normalization includes:

- Unicode normalization (UTF-8)

- Consistent newline characters

- Removal of hidden control characters

- Standardized whitespace

- Preservation of paragraph structure

- Normalized bullet lists

- Standardized heading hierarchy

- Consistent code block formatting

Normalization ensures that identical source content produces identical
Markdown.

## 7.9 Metadata Extraction

The framework extracts both system and document metadata.

**System Metadata**

- File name

- File extension

- File size

- Repository ID

- Document ID

- Version

- Hash

- Created timestamp

- Modified timestamp

**Document Metadata**

- Title

- Author

- Subject

- Keywords

- Language

- Creation date

- Last editor

- Page count (if applicable)

Metadata is stored separately from the Markdown content and linked
through the Digital Twin.

## 7.10 Markdown Structure Standard

Every generated Markdown document follows a consistent structure.

\-\--

document_id: DOC-001

repository_id: REP-001

version: 3

source_type: PDF

created_at: 2026-06-30T10:15:00Z

hash: SHA256:\...

language: en

\-\--

\# Document Title

\## Section 1

Content\...

\## Section 2

Content\...

\### Subsection

Content\...

\| Table \| Example \|

\|\-\-\-\-\-\-\--\|\-\-\-\-\-\-\-\--\|

\| A \| B \|

This YAML front matter enables downstream frameworks to consume metadata
without querying the Control Plane for every operation.

## 7.11 Handling Tables

Tables often contain critical enterprise knowledge.

Tables are converted to Markdown by EKDC during conversion; EKIE
preserves them unchanged through normalization and chunking.

Example:

\| Equipment \| Status \| Last Inspection \|

\|\-\-\-\-\-\-\-\-\-\--\|\-\-\-\-\-\-\--\|\-\-\-\-\-\-\-\-\-\-\-\-\-\-\-\--\|

\| Pump A \| Operational \| 2026-05-01 \|

\| Pump B \| Maintenance \| 2026-05-15 \|

Because tables are already expressed as Markdown on ingestion, EKIE does
not re-parse tabular source formats. Table extraction quality (layout
fidelity, merged cells, parsing confidence) is a concern of the EKDC
converter, upstream of EKIE.

## 7.12 Handling Images

Image handling and OCR are performed by the EKDC converter before
ingestion. EKDC decides whether informational images (diagrams,
flowcharts, screenshots, engineering drawings) are transcribed via OCR
or image-understanding models, and whether decorative images (logos,
icons, background graphics) are ignored.

EKIE receives the resulting Markdown and preserves any image references
and associated metadata unchanged. EKIE performs no OCR or image
processing.

## 7.13 OCR Strategy

OCR is **not** performed by EKIE. Scanned documents and image-based PDFs
are transcribed by the EKDC converter, which owns OCR engine selection
(e.g., Tesseract, Azure Document Intelligence, or future providers).

Source Image (in EKDC)

↓

OCR Engine (EKDC)

↓

Extracted Text

↓

Markdown (.md)

↓

EKIE Transformation (normalize + validate)

By the time content reaches EKIE it is already text-based Markdown, so
EKIE requires no OCR dependencies.

## 7.14 Handling Embedded Objects

Enterprise documents may contain embedded objects (Excel sheets,
PowerPoint slides, PDFs, images, Visio diagrams, CAD drawings). Handling
of embedded objects --- extraction, referencing, or ignoring --- is
performed by the EKDC converter, which flattens them into the generated
Markdown according to its policy.

EKIE ingests the resulting Markdown. Any object that EKDC exports as a
separate Markdown file is ingested by EKIE as its own document, with
lineage maintained through the Digital Twin.

## 7.15 Validation Framework

Before a Markdown asset is published, it undergoes validation.

Validation checks include:

  -----------------------------------------------------------------------
  **Check**                       **Purpose**
  ------------------------------- ---------------------------------------
  UTF-8 Encoding                  Ensure compatibility

  Required Metadata               Verify completeness

  Empty Content                   Prevent invalid assets

  Broken Structure                Validate Markdown syntax

  Duplicate Generation            Prevent redundant versions
  -----------------------------------------------------------------------

Documents failing validation are routed to a configurable error handling
workflow.

## 7.16 Versioning Strategy

Transformation is deterministic and version-aware.

If:

- Source content changes.

- Transformation policy changes.

- Normalization or parser version changes.

A new Markdown version is generated.

Document v1

↓

Markdown v1

Parser Updated

↓

Markdown v2

This preserves historical reproducibility.

## 7.17 Asset Storage

Markdown assets are stored independently of the Control Plane.

The Control Plane maintains references such as:

- Asset ID

- Storage URI

- Version

- Hash

- Parser Version

- Generation Timestamp

- Validation Status

This separation keeps the operational database lightweight.

## 7.18 Error Handling

Transformation failures are categorized for targeted recovery.

  -----------------------------------------------------------------------
  **Error Type**      **Example**             **Recovery**
  ------------------- ----------------------- ---------------------------
  Unsupported Format  Non-Markdown input      Reject; convert via EKDC

  Parser Failure      Malformed Markdown      Retry / quarantine

  Validation Failure  Missing metadata        Quarantine

  Storage Failure     Artifact store          Retry with exponential
                      unavailable             backoff
  -----------------------------------------------------------------------

No failed transformation should block unrelated workflows.

## 7.19 Performance Considerations

The Transformation Framework should support enterprise-scale throughput.

Design goals include:

- Streaming large Markdown files instead of loading entirely into memory.

- Lightweight, text-only processing (no binary parsing or OCR overhead).

- Deduplication by content hash to skip unchanged Markdown.

- Incremental reprocessing when only metadata changes.

- Parallel intake across documents.

## 7.20 Security Considerations

Document transformation must preserve enterprise security requirements.

Key measures include:

- Sandboxed parser execution.

- Malware scanning before parsing (optional policy).

- Secure handling of temporary files.

- Encryption of stored Markdown assets.

- Audit logging for every transformation.

- Validation of file type against content (not just extension).

## 7.21 Design Decisions (ADRs)

**ADR-011: Markdown as the Canonical Representation**

**Decision**

All supported document formats shall be transformed into Markdown before
downstream processing.

**Rationale**

A single canonical format simplifies chunking, embedding, validation,
testing, and future extensibility.

**ADR-012: Parser Abstraction**

**Decision**

All document parsers shall implement a common interface managed by the
Parser Registry.

**Rationale**

This enables new formats and parser technologies to be introduced
without modifying the core framework.

**ADR-013: Deterministic Markdown Generation**

**Decision**

Transformation must produce deterministic Markdown for identical inputs
and configurations.

**Rationale**

Determinism is essential for reproducibility, versioning, and efficient
change detection.

**ADR-014: Document Conversion Offloaded to EKDC**

**Decision**

Conversion of non-Markdown source formats (PDF, DOCX, PPTX, HTML, CSV,
images, audio, video) is performed by the Enterprise Knowledge Document
Converter (EKDC) agent. EKIE ingests Markdown only.

**Rationale**

Offloading conversion keeps EKIE lightweight and free of OCR and
rich-media dependencies, shortens and stabilizes the ingestion pipeline,
and lets conversion concerns (new formats, OCR engines, media
transcription) evolve independently in EKDC without changing EKIE.

## 7.22 Summary

The Document Transformation Framework establishes the canonical
knowledge representation for the entire EKIE platform. By canonicalizing
Markdown --- produced upstream by the EKDC converter --- into
standardized, metadata-rich assets, it decouples downstream frameworks
from document-specific complexity and ensures deterministic, extensible,
and governable processing.

This framework is the bridge between converted enterprise content and
AI-ready knowledge assets.

**Chapter 8**, with Chunking moving to **Chapter 9**.
This refinement would make the architecture stronger while remaining
fully aligned with the ingestion-only scope.

# Chapter 8 - Document Intelligence Framework

**Version:** 1.0\
**Status:** Approved\
**Volume:** II --- Functional Architecture

## 8.1 Objective

After a document has been transformed into canonical Markdown, but
**before chunking begins**, EKIE performs an additional enrichment phase
called the **Document Intelligence Framework (DIF)**.

This framework analyzes the document's semantic structure rather than
simply treating it as plain text.

Its objective is to transform Markdown into **structured knowledge**
that enables significantly higher-quality chunking, embedding,
governance, and downstream retrieval.

**Transformation converts formats.**

**Document Intelligence understands documents.**

This distinction is fundamental to enterprise-scale knowledge
engineering.

## 8.2 Why Document Intelligence?

Consider two approaches.

**Traditional Pipeline**

PDF

↓

Markdown

↓

Chunk

↓

Embedding

Everything is treated as text.

The system loses important information such as:

- Section hierarchy

- Document outline

- Tables

- Captions

- Figures

- Lists

- Warnings

- Notes

- Code blocks

- Headers

- Footers

**EKIE Pipeline**

PDF

↓

Markdown

↓

Document Intelligence

↓

Enriched Markdown

↓

Chunking

↓

Embedding

The document is now understood before it is divided.

## 8.3 Responsibilities

The Document Intelligence Framework is responsible for:

- Document structure analysis

- Heading hierarchy extraction

- Section boundary detection

- Table understanding

- Figure detection

- Caption extraction

- Code block detection

- Warning and note identification

- Language detection

- Content classification

- PII detection (optional)

- Duplicate section detection

- Semantic metadata generation

- Document quality scoring

It **does not** generate embeddings.

It **does not** chunk documents.

## 8.4 High-Level Architecture

Markdown Asset

↓

Document Intelligence Engine

├── Structure Analyzer

├── Table Analyzer

├── Figure Analyzer

├── Language Detector

├── Metadata Enricher

├── Classification Engine

├── PII Detector

└── Quality Analyzer

↓

Enriched Markdown

↓

Chunking Framework

## 8.5 Why This Layer Matters

Most enterprise RAG failures are **not** caused by embeddings.

They are caused because chunking occurs without understanding document
structure.

Example:

Safety Procedure

Section 1

\...

Table

\...

Section 2

\...

A naïve chunker may split the table across multiple chunks or mix
unrelated sections.

The Document Intelligence Framework prevents this.

## 8.6 Structure Analyzer

The Structure Analyzer identifies logical sections.

Example:

\# Plant Operations

\## Startup

\### Safety Checks

\### Inspection

\## Shutdown

\### Cooling

\### Lockout

The analyzer produces a structural tree.

Plant Operations

├── Startup

│ ├── Safety Checks

│ └── Inspection

│

└── Shutdown

├── Cooling

└── Lockout

This hierarchy is preserved for downstream chunking.

## 8.7 Table Intelligence

Enterprise documents frequently contain:

- Equipment lists

- Inspection records

- Maintenance schedules

- Bills of Materials

- Configuration matrices

Rather than treating tables as plain text, EKIE classifies them.

Example metadata:

Table Type

Rows

Columns

Header Confidence

Contains Numerical Data

Contains Dates

Contains IDs

Contains Measurements

This information allows future chunking policies to keep tables intact.

## 8.8 Figure Intelligence

Figures are identified and classified.

Examples:

- Flowchart

- Architecture Diagram

- Network Diagram

- Engineering Drawing

- Screenshot

- Organization Chart

Associated metadata includes:

- Caption

- Figure Number

- Page Number

- Image Reference

- OCR Confidence

Future multimodal models can consume these assets without redesigning
the platform.

## 8.9 Code Block Detection

Technical repositories frequently contain source code.

Example:

\`\`\`python

def calculate():

pass

\`\`\`

Code blocks are detected and tagged.

Metadata includes:

- Language

- Number of Lines

- Block Identifier

- Parent Section

Chunking policies can ensure code is never split mid-function.

## 8.10 Language Detection

Repositories often contain multilingual content.

Supported examples:

- English

- German

- French

- Spanish

- Japanese

- Chinese

Detected language becomes metadata for:

- Embedding model selection

- Chunking policy

- Retrieval optimization

- Compliance

## 8.11 Content Classification

Documents are automatically classified.

Examples:

Policy

Procedure

Manual

Technical Specification

API Documentation

Meeting Notes

Maintenance Guide

Training Material

Source Code

Architecture

Classification enables future governance policies.

## 8.12 Sensitive Content Detection

Optional policy-driven scanning identifies:

- Personal Information

- Email Addresses

- Phone Numbers

- Credit Card Numbers

- National IDs

- API Keys

- Passwords

- Secrets

Detected content is never modified automatically.

Instead, metadata is generated for governance workflows.

## 8.13 Section Intelligence

Each section receives semantic metadata.

Example:

Section ID

Parent Section

Heading Level

Token Count

Estimated Reading Time

Contains Table

Contains Image

Contains Code

Contains Warning

Contains Procedure

Chunking uses this metadata extensively.

## 8.14 Document Quality Score

Every document receives a quality score.

Example factors:

- OCR confidence

- Parser confidence

- Missing headings

- Broken tables

- Corrupted sections

- Empty pages

- Unsupported objects

Example:

Overall Score

94 / 100

OCR

98%

Structure

96%

Tables

92%

Images

88%

Low-quality documents can be routed for review.

## 8.15 Semantic Metadata

The framework generates metadata unavailable from the original file.

Examples:

Primary Topic

Secondary Topic

Department

Business Domain

Document Category

Document Complexity

Estimated Audience

Language

Knowledge Density

This metadata significantly improves downstream retrieval.

## 8.16 Output Contract

The framework outputs:

Markdown Asset

\+

Structure Tree

\+

Semantic Metadata

\+

Classification

\+

Quality Metrics

\+

Section Graph

\+

Document Intelligence Report

Nothing is lost.

Everything is enriched.

## 8.17 Integration with Chunking

Instead of chunking plain Markdown:

Markdown

↓

Chunk

EKIE performs:

Markdown

↓

Document Intelligence

↓

Semantic Markdown

↓

Chunk

Chunking now understands:

- Sections

- Tables

- Lists

- Code

- Figures

- Notes

- Warnings

Resulting chunks are significantly more meaningful.

## 8.18 Performance Considerations

Document Intelligence should:

- Reuse parser output where possible.

- Execute analyzers in parallel.

- Cache language detection results.

- Cache document classification.

- Support configurable analysis depth.

Organizations may disable expensive analyzers for lightweight
deployments.

## 8.19 Design Decisions (ADRs)

**ADR-014: Intelligence Before Chunking**

**Decision**

Every document shall undergo semantic analysis before chunk generation.

**Rationale**

Semantic understanding produces higher-quality chunks, improves
metadata, and increases downstream retrieval accuracy without coupling
intelligence to the chunking implementation.

**ADR-015: Analyzer Plugin Architecture**

**Decision**

Every analyzer shall be implemented as a plugin.

Examples include:

- Language Analyzer

- PII Analyzer

- Table Analyzer

- Figure Analyzer

- Custom Enterprise Analyzer

**Rationale**

Organizations can extend document intelligence without modifying the
EKIE core.

**ADR-016: Metadata Enrichment as a First-Class Asset**

**Decision**

Semantic metadata generated by the Document Intelligence Framework shall
be versioned and tracked as a managed asset.

**Rationale**

Metadata influences downstream chunking and embedding decisions and
therefore requires lineage, reproducibility, and governance.

## 8.20 Summary

The Document Intelligence Framework elevates EKIE from a document
conversion pipeline to a true **knowledge engineering platform**. By
understanding document structure, semantics, and quality before
chunking, it enables smarter processing, richer metadata, stronger
governance, and significantly better AI-ready assets.

This framework forms the critical bridge between canonical Markdown and
intelligent chunk generation.

**Chapter 9 -- Intelligent Chunking Framework**, where we will
design one of the most critical components of EKIE. Rather than
implementing simple fixed-size chunking, we will define an
enterprise-grade chunking engine that uses document structure, semantic
boundaries, configurable strategies, lineage, and versioning to produce
optimal AI-ready chunks. This chapter will establish the foundation for
high-quality embeddings and efficient downstream retrieval.

# Chapter 9 - Intelligent Chunking Framework

**Version:** 1.0\
**Status:** Approved\
**Volume:** II --- Functional Architecture

## 9.1 Objective

The Intelligent Chunking Framework is responsible for transforming
enriched Markdown documents into **high-quality, semantically
meaningful, versioned, and traceable knowledge chunks**.

Chunking is **not** a string-splitting operation.

It is a **knowledge engineering process** that determines how
information will be represented inside the vector database.

The quality of chunking directly impacts:

- Embedding quality

- Retrieval accuracy

- Context relevance

- Token efficiency

- Hallucination reduction

- Long-term maintainability

For this reason, chunking is treated as an independent framework rather
than a utility function.

## 9.2 Why Traditional Chunking Fails

Most RAG implementations use simple approaches such as:

chunk_size = 1000

overlap = 200

or

RecursiveCharacterTextSplitter(\...)

Although effective for prototypes, these methods have significant
limitations in enterprise environments.

Common issues include:

- Breaking sections mid-sentence

- Splitting procedures across chunks

- Separating tables from their headings

- Losing document hierarchy

- Mixing unrelated topics

- Breaking code blocks

- Duplicating excessive context

- Producing inconsistent chunks across versions

These limitations reduce retrieval quality and increase embedding costs.

For this reason the **Semantic** strategy is EKIE's default. A recursive
character splitter is still offered as an opt-in strategy (§9.7) for teams that
prefer it; EKIE applies it within section boundaries so section metadata is
retained, mitigating the worst of the issues above.

## 9.3 EKIE Chunking Philosophy

EKIE follows a fundamentally different philosophy.

**Chunks represent knowledge boundaries, not character boundaries.**

Chunking decisions should be driven by:

- Document structure

- Semantic meaning

- Content type

- Section hierarchy

- Context preservation

- Token budget

- Retrieval objectives

## 9.4 Responsibilities

The Chunking Framework is responsible for:

- Chunk strategy selection

- Boundary detection

- Section-aware chunking

- Table-aware chunking

- Code-aware chunking

- Figure-aware chunking

- Token estimation

- Context overlap generation

- Chunk metadata creation

- Chunk validation

- Chunk versioning

- Chunk lineage

It does **not** generate embeddings.

## 9.5 High-Level Architecture

Enriched Markdown

↓

Chunk Strategy Manager

↓

Boundary Detector

↓

Chunk Generator

↓

Metadata Generator

↓

Validation

↓

Chunk Assets

↓

Embedding Framework

Each component is independently replaceable through plugins.

## 9.6 Chunking Workflow

Every document follows the same workflow.

Markdown Asset

↓

Read Structure Tree

↓

Identify Semantic Boundaries

↓

Select Chunk Strategy

↓

Generate Chunks

↓

Generate Metadata

↓

Validate

↓

Persist Chunk Assets

## 9.7 Chunking Strategies

EKIE supports multiple chunking strategies.

  -----------------------------------------------------------------------
  **Strategy**               **Purpose**
  -------------------------- --------------------------------------------
  Semantic                   Default enterprise strategy

  Section-Based              Large structured documents

  Heading-Based              Technical documentation

  Paragraph-Based            Policies and manuals

  Token-Based                LLM optimization

  Table-Based                Spreadsheet-heavy documents

  Code-Based                 Source repositories

  Recursive                  Opt-in LangChain character splitter

  Custom Plugin              Organization-specific
  -----------------------------------------------------------------------

Policies determine which strategy is applied. The default is Semantic. The
opt-in **Recursive** strategy uses LangChain's
``RecursiveCharacterTextSplitter`` (configurable character window and overlap)
and splits within each section so section identity, title, and breadcrumb
metadata are preserved. It is selected with
``EKIE_CHUNKING__DEFAULT_STRATEGY=recursive`` and requires the
``langchain-text-splitters`` package.

## 9.8 Semantic Boundary Detection

The framework determines natural knowledge boundaries.

Boundaries include:

- Heading changes

- Topic changes

- Procedure boundaries

- Warning blocks

- Tables

- Lists

- Code blocks

- Notes

- Appendices

Chunks should never cross major semantic boundaries unless explicitly
configured.

## 9.9 Section-Aware Chunking

Example document:

\# Equipment Maintenance

\## Safety

\...

\## Inspection

\...

\## Shutdown

\...

Generated chunks:

Chunk 1

Equipment Maintenance → Safety

Chunk 2

Equipment Maintenance → Inspection

Chunk 3

Equipment Maintenance → Shutdown

Each chunk retains its full hierarchical context.

## 9.10 Table-Aware Chunking

Tables should remain intact whenever possible.

Example:

\| Equipment \| Status \| Next Inspection \|

\|\-\-\-\-\-\-\-\-\-\-\--\|\-\-\-\-\-\-\--\|\-\-\-\-\-\-\-\-\-\-\-\-\-\-\--\|

Rules:

- Do not split rows across chunks.

- Preserve header rows.

- Associate tables with the nearest heading.

- Maintain row ordering.

Large tables may be partitioned while repeating the header row.

## 9.11 Code-Aware Chunking

Source code requires specialized handling.

Rules:

- Never split a function.

- Never split a class definition.

- Preserve imports with related code.

- Keep comments with associated code.

- Preserve language metadata.

Example metadata:

Language

Python

Function Name

calculate_pressure()

Class

PumpController

## 9.12 Figure & Diagram Handling

Figures generate contextual chunks.

Example:

Figure

↓

Caption

↓

Referenced Section

↓

Associated Explanation

↓

Chunk

Image references remain linked to the parent section for future
multimodal retrieval.

## 9.13 Context Preservation

Chunk overlap is semantic rather than fixed.

Example:

Section A

↓

Chunk 1

↓

Shared Context

↓

Chunk 2

↓

Section B

Overlap includes only information necessary to preserve meaning.

This reduces duplicate embeddings while maintaining context.

## 9.14 Token Budget Management

Every embedding model has token limits.

The Chunking Framework estimates token counts before embedding.

Example:

  -----------------------------------------------------------------------
  **Model**                      **Max Tokens**
  ------------------------------ ----------------------------------------
  Model A                        8K

  Model B                        16K

  Model C                        32K
  -----------------------------------------------------------------------

Chunk generation respects configurable target token budgets rather than
character counts.

## 9.15 Chunk Metadata

Every chunk becomes a managed asset with rich metadata.

Example:

chunk_id: CHK-000145

document_id: DOC-001

markdown_version: 3

section: \"Inspection\"

heading_level: 2

chunk_sequence: 8

token_count: 742

language: en

chunk_strategy: Semantic

contains_table: false

contains_code: true

contains_image: false

quality_score: 98

This metadata supports governance, analytics, and retrieval
optimization.

## 9.16 Chunk Identity

Every chunk receives a stable internal identifier.

Document

↓

Markdown Version

↓

Chunk Version

↓

Chunk ID

Chunk identity is independent of the embedding provider.

This enables embeddings to be regenerated without changing chunk
identity.

## 9.17 Chunk Versioning

Chunks are regenerated when:

- Markdown changes.

- Chunking policy changes.

- Chunking algorithm changes.

- Semantic structure changes.

If no meaningful changes occur, chunk regeneration is skipped.

This minimizes unnecessary embedding costs.

## 9.18 Chunk Validation

Every generated chunk passes validation.

Validation rules include:

  -----------------------------------------------------------------------
  **Validation**                              **Purpose**
  ------------------------------------------- ---------------------------
  Empty Content                               Reject

  Invalid UTF-8                               Reject

  Missing Metadata                            Reject

  Broken Hierarchy                            Reject

  Exceeds Token Budget                        Split or reject

  Duplicate Chunk                             Skip
  -----------------------------------------------------------------------

Validation failures are routed to workflow recovery.

## 9.19 Performance Considerations

The Chunking Framework is optimized for enterprise-scale processing.

Design goals:

- Streaming document processing.

- Parallel chunk generation.

- Cached token estimation.

- Efficient overlap calculation.

- Incremental regeneration of affected chunks only.

This avoids recomputing the entire document when only one section
changes.

## 9.20 Security Considerations

Chunking must preserve governance metadata.

Examples:

- Document classification.

- Confidentiality labels.

- PII detection results.

- Security policies.

- Access restrictions.

No chunk should lose the security context inherited from its parent
document.

## 9.21 Design Decisions (ADRs)

**ADR-017: Semantic Chunking by Default**

**Decision**

Semantic chunking is the default strategy for all enterprise documents.

**Rationale**

Knowledge boundaries produce higher-quality embeddings and improve
retrieval accuracy compared to fixed-size chunking.

**ADR-018: Chunk as a First-Class Asset**

**Decision**

Chunks are managed assets with their own lifecycle, metadata,
versioning, and lineage.

**Rationale**

Treating chunks as first-class assets enables governance, replay,
analytics, and efficient re-embedding.

**ADR-019: Embedding Independence**

**Decision**

Chunk identity is independent of embedding providers.

**Rationale**

Organizations should be able to regenerate embeddings using new models
without affecting document or chunk lineage.

**ADR-020: Incremental Chunk Regeneration**

**Decision**

Only chunks affected by document changes should be regenerated.

**Rationale**

This significantly reduces compute costs and shortens ingestion time for
large repositories.

## 9.22 Future Extensions

The framework has been designed to support future capabilities without
architectural redesign.

Potential enhancements include:

- Graph-aware chunking

- Knowledge graph generation

- Multimodal chunking (text + image + table)

- LLM-assisted semantic segmentation

- Domain-specific chunking strategies

- Adaptive chunk sizing based on retrieval analytics

- Cross-document chunk linking

- Citation-aware chunk generation

These capabilities can be introduced through plugins while preserving
the framework's contracts.

## 9.23 Summary

The Intelligent Chunking Framework is one of the most influential
components in the EKIE ingestion pipeline. By transforming enriched
Markdown into semantically coherent, metadata-rich, and versioned
knowledge chunks, it lays the foundation for high-quality embeddings and
efficient downstream retrieval.

Unlike traditional text splitters, EKIE treats chunking as a knowledge
engineering discipline, ensuring that chunks preserve meaning, context,
lineage, and governance throughout their lifecycle.

# Chapter 10 - Embedding Framework

**Version:** 1.0\
**Status:** Approved\
**Volume:** II --- Functional Architecture

## 10.1 Objective

The Embedding Framework is responsible for converting validated
knowledge chunks into numerical vector representations that preserve
semantic meaning while maintaining complete governance, versioning,
reproducibility, and provider independence.

An embedding is **not** simply a vector.

Within EKIE, an embedding is a **managed enterprise asset** with its own
lifecycle, lineage, metadata, version history, operational state, and
quality controls.

The framework ensures that organizations can change embedding providers
or models without redesigning the ingestion platform.

## 10.2 Why an Independent Embedding Framework?

Many RAG implementations tightly couple embedding generation with vector
database insertion.

Example:

embedding = model.embed(chunk)

vector_db.upsert(embedding)

This coupling introduces several limitations:

- Embeddings cannot be regenerated independently.

- Provider migration becomes expensive.

- Failed vector publishing requires recomputing embeddings.

- Model comparisons are difficult.

- Governance and lineage are limited.

EKIE separates these responsibilities.

Chunk

↓

Embedding Framework

↓

Embedding Asset

↓

Publishing Framework

↓

Vector Database

This separation provides flexibility, resiliency, and operational
efficiency.

## 10.3 Responsibilities

The Embedding Framework is responsible for:

- Embedding model selection

- Provider abstraction

- Token validation

- Batch management

- Rate limiting

- Retry handling

- Embedding generation

- Embedding validation

- Embedding versioning

- Cost tracking

- Embedding asset creation

- Metadata generation

It is **not** responsible for publishing vectors.

## 10.4 High-Level Architecture

Chunk Assets

↓

Embedding Strategy Manager

↓

Provider Registry

↓

Embedding Provider Plugin

↓

Embedding Validator

↓

Embedding Asset

↓

Publishing Framework

Each provider implements the same interface, enabling seamless
replacement.

## 10.5 Embedding Asset Model

An embedding is treated as a first-class asset.

Each embedding includes:

- Embedding ID

- Chunk ID

- Embedding Version

- Model Name

- Provider

- Vector Dimension

- Generation Timestamp

- Token Count

- Processing Duration

- Cost Metadata

- Validation Status

- Quality Metrics

The vector payload itself is stored separately from the Control Plane.

## 10.6 Provider Abstraction

EKIE never communicates directly with a specific embedding API.

Instead:

Embedding Framework

↓

Provider Interface

↓

Provider Plugin

↓

Embedding Service

Supported providers may include:

- Azure OpenAI

- OpenAI

- Voyage AI

- Jina AI

- Cohere

- NVIDIA NIM

- Ollama

- Hugging Face

- Sentence Transformers

- Future enterprise models

Adding a new provider requires implementing the provider contract, not
modifying the framework.

A single **LangChain resource template** (``domain/integrations``) is the
configuration-driven init point for the LangChain-backed embedding models
(HuggingFace, Ollama) and the vector store, so providers and tooling do not each
construct LangChain clients. The deterministic local hash provider stays
dependency-free and offline.

## 10.7 Embedding Model Registry

The Control Plane maintains a registry of approved embedding models.

Example:

  -------------------------------------------------------------------------
  **Model**                 **Provider**   **Dimensions**   **Status**
  ------------------------- -------------- ---------------- ---------------
  text-embedding-3-large    OpenAI         3072             Active

  text-embedding-3-small    OpenAI         1536             Active

  Voyage Large              Voyage AI      Configurable     Approved

  BGE-M3                    Local          1024             Experimental
  -------------------------------------------------------------------------

The registry supports governance, auditing, and controlled upgrades.

## 10.8 Embedding Workflow

Each chunk follows the same lifecycle.

Chunk

↓

Policy Evaluation

↓

Model Selection

↓

Token Validation

↓

Batch Assignment

↓

Embedding Generation

↓

Validation

↓

Embedding Asset Created

↓

Publishing Queue

The workflow is deterministic and fully auditable.

## 10.9 Model Selection Policy

Embedding model selection is policy-driven.

Selection criteria may include:

- Document language

- Document classification

- Repository type

- Security classification

- Token budget

- Cost policy

- Accuracy requirements

- Deployment environment

This enables organizations to optimize embedding generation without
changing application code.

## 10.10 Token Management

Before embedding generation, the framework estimates and validates token
usage.

Checks include:

- Maximum supported tokens

- Estimated cost

- Chunk size compliance

- Provider-specific constraints

Chunks exceeding limits are returned to the Chunking Framework for
regeneration rather than being truncated.

## 10.11 Batch Processing

Embedding requests are grouped into batches where supported.

Chunk 1

Chunk 2

Chunk 3

Chunk 4

↓

Batch Manager

↓

Embedding Request

↓

Provider

Batching improves throughput and reduces API overhead while respecting
provider limits. The batch size is configuration-driven
(``EKIE_EMBEDDING__BATCH_SIZE``, default 16); raising it increases throughput on
large document sets without changing the resulting vectors.

## 10.12 Rate Limiting

Different providers enforce different quotas.

The framework includes configurable rate limit policies.

Examples:

- Requests per minute

- Tokens per minute

- Concurrent requests

- Daily quotas

The Rate Limit Manager ensures compliance without affecting upstream
workflows. EKIE implements this as an optional token-bucket limiter
(``EKIE_EMBEDDING__MAX_REQUESTS_PER_MINUTE``, default 0 = unlimited) that paces
embedding requests per minute; the deterministic offline path is unaffected.

## 10.13 Retry Strategy

Transient failures are expected.

Examples include:

- Network interruption

- API timeout

- Rate limit exceeded

- Temporary provider outage

Recovery strategy:

Failure

↓

Exponential Backoff

↓

Retry

↓

Circuit Breaker Evaluation

↓

Provider Failover (Optional)

↓

Quarantine

Retries are governed by configurable policies.

## 10.14 Embedding Validation

Generated embeddings undergo validation before becoming managed assets.

Validation checks include:

  -----------------------------------------------------------------------
  **Validation**                       **Purpose**
  ------------------------------------ ----------------------------------
  Vector Dimension                     Ensure model compliance

  Empty Vector                         Reject invalid output

  NaN/Infinity Values                  Reject corrupted vectors

  Metadata Completeness                Ensure governance

  Provider Response Integrity          Verify consistency
  -----------------------------------------------------------------------

Invalid embeddings never proceed to publishing.

## 10.15 Embedding Versioning

Embeddings are regenerated only when necessary.

Triggers include:

- Chunk changes

- Embedding model changes

- Provider changes

- Embedding policy updates

- Quality improvement initiatives

Versioning enables historical comparison and controlled migration.

## 10.16 Cost Management

Embedding generation often represents the largest operational cost in an
ingestion pipeline.

EKIE tracks cost metadata for every embedding operation.

Examples:

- Provider

- Model

- Tokens processed

- Estimated cost

- Processing duration

- Batch efficiency

This data supports budgeting, optimization, and chargeback reporting.

## 10.17 Quality Metrics

Operational metrics are recorded for every embedding.

Examples:

- Latency

- Throughput

- Retry count

- Batch size

- Provider response time

- Success rate

- Average token count

These metrics feed the Observability Framework.

## 10.18 Security Considerations

Embedding generation must adhere to enterprise security requirements.

Key controls include:

- Secure API key management

- Encrypted communication

- Model allowlists

- Provider approval policies

- Audit logging

- Regional routing policies

- Sensitive document restrictions

The framework must prevent unauthorized use of embedding providers.

## 10.19 Failure Handling

Representative failures include:

  -----------------------------------------------------------------------
  **Failure**                           **Recovery**
  ------------------------------------- ---------------------------------
  Provider Timeout                      Retry

  Rate Limit Exceeded                   Backoff

  Authentication Failure                Refresh credentials

  Invalid Response                      Quarantine

  Unsupported Model                     Policy failure

  Network Failure                       Retry
  -----------------------------------------------------------------------

Failures are isolated to the affected chunks and do not interrupt
unrelated workflows.

## 10.20 Embedding State Machine

Each embedding progresses through a managed lifecycle.

PENDING

↓

VALIDATING

↓

GENERATING

↓

VALIDATED

↓

READY

↓

PUBLISHED

↓

VERIFIED

Alternative states:

FAILED

RETRYING

SUPERSEDED

ARCHIVED

The state machine supports replay, rollback, and operational visibility.

## 10.21 Design Decisions (ADRs)

**ADR-021: Provider Independence**

**Decision**

Embedding providers shall be accessed exclusively through a standardized
provider interface.

**Rationale**

This prevents vendor lock-in and enables controlled migration between
cloud, on-premises, and future embedding technologies.

**ADR-022: Embeddings as Managed Assets**

**Decision**

Embeddings shall be treated as first-class versioned assets with
complete lineage.

**Rationale**

Embeddings influence downstream retrieval quality and therefore require
governance, reproducibility, and auditability.

**ADR-023: Deferred Publishing**

**Decision**

Embedding generation and vector publication are separate workflows.

**Rationale**

Separating these responsibilities enables retries, replay, provider
migration, and independent scaling.

**ADR-024: Policy-Driven Model Selection**

**Decision**

Embedding models are selected through configurable policies rather than
hardcoded logic.

**Rationale**

Organizations can optimize for accuracy, latency, cost, compliance, or
deployment environment without modifying the framework.

## 10.22 Future Extensions

The Embedding Framework is designed to support future innovations,
including:

- Multi-vector embeddings

- Sparse and dense hybrid embeddings

- Domain-specific embedding models

- Multimodal embeddings (text, image, table)

- Ensemble embedding strategies

- Automatic model evaluation

- Embedding quality benchmarking

- Dynamic provider routing based on latency or cost

These capabilities can be introduced without changing the framework's
core contracts.

## 10.23 Summary

The Embedding Framework transforms semantically meaningful chunks into
governed, versioned embedding assets while maintaining complete provider
independence and operational control.

By treating embeddings as managed enterprise assets rather than
transient API responses, EKIE enables reproducibility, cost
optimization, provider flexibility, and long-term maintainability.

This framework completes the **knowledge representation phase** of the
ingestion pipeline and prepares assets for reliable publication into
vector databases.

# Chapter 11 - Vector Publishing Framework

**Version:** 1.0\
**Status:** Approved\
**Volume:** II --- Functional Architecture

## 11.1 Objective

The Vector Publishing Framework is the final stage of the EKIE ingestion
pipeline.

Its responsibility is to publish validated embedding assets into the
enterprise Vector Database while maintaining complete consistency
between:

- Repository

- Digital Twin

- Asset Storage

- Embedding Assets

- Vector Database

Publishing is **not** simply an "upsert" operation.

It is an enterprise synchronization framework responsible for ensuring
that the Vector Database always represents the latest approved knowledge
state.

## 11.2 Why a Dedicated Publishing Framework?

Many RAG systems directly perform:

vector_db.upsert(vector)

This approach creates several problems:

- No publishing history

- No rollback

- No verification

- No replay

- No deletion tracking

- No idempotency

- Tight coupling with a specific Vector DB

EKIE separates publishing from embedding generation.

Embedding Asset

↓

Publishing Framework

↓

Publishing Queue

↓

Vector Provider

↓

Verification

↓

Digital Twin Updated

This enables reliability, governance, and provider independence.

## 11.3 Responsibilities

The Publishing Framework is responsible for:

- Publishing embeddings

- Provider abstraction

- Batch publishing

- Idempotent operations

- Update propagation

- Delete propagation

- Version publishing

- Publish verification

- Replay support

- Rollback support

- Synchronization with Digital Twin

- Publishing metrics

It does **not** generate embeddings.

## 11.4 High-Level Architecture

Embedding Assets

↓

Publishing Manager

↓

Provider Registry

↓

Vector Provider Plugin

↓

Vector Database

↓

Verification Engine

↓

Digital Twin Update

## 11.5 Supported Vector Providers

The framework remains vendor-neutral.

Examples:

  -----------------------------------------------------------------------
  **Provider**                                     **Status**
  ------------------------------------------------ ----------------------
  Qdrant                                           Phase 1

  Azure AI Search                                  Phase 2

  Pinecone                                         Future

  Milvus                                           Future

  Weaviate                                         Future

  Elasticsearch Vector                             Future

  pgvector                                         Future

  OpenSearch                                       Future
  -----------------------------------------------------------------------

Every provider implements the same publishing contract.

## 11.6 Publishing Workflow

Every embedding follows a deterministic workflow.

Embedding Ready

↓

Policy Validation

↓

Publishing Queue

↓

Provider Selection

↓

Batch Publishing

↓

Verification

↓

Publish Metadata

↓

Digital Twin Update

Publishing is considered complete only after verification succeeds.

## 11.7 Publishing Queue

Publishing requests are queued independently from embedding generation.

Benefits include:

- Retry capability

- Rate limiting

- Batch optimization

- Provider failover

- Operational monitoring

Example:

Embedding

↓

Queue

↓

Worker

↓

Vector DB

This decouples ingestion throughput from vector database performance.

## 11.8 Batch Publishing

Publishing is performed in configurable batches.

Example:

Embedding 1

Embedding 2

Embedding 3

↓

Publishing Batch

↓

Qdrant

Batch size depends on:

- Provider limits

- Payload size

- Network latency

- Infrastructure capacity

The batch size is configuration-driven (``EKIE_PUBLISHING__BATCH_SIZE``, default
64); raising it speeds up ingest. An optional token-bucket rate limiter
(``EKIE_PUBLISHING__MAX_VECTORS_PER_MINUTE``, default 0 = unlimited) paces vector
upserts per minute to protect the vector database, without weakening
post-publish verification.

## 11.9 Idempotent Publishing

Publishing must be repeatable.

If the same embedding is published twice:

Embedding ID

↓

Already Published?

↓

YES

↓

Skip

No duplicate vectors are created.

This property is essential for replay and recovery.

## 11.10 Vector Identity

Every published vector receives a stable identifier.

Relationship:

Document

↓

Chunk

↓

Embedding

↓

Vector

Vector identity references:

- Chunk ID

- Embedding Version

- Provider

- Collection

- Publish Version

The Vector ID should be deterministic wherever possible.

## 11.11 Collection Management

Collections are managed centrally.

Examples:

Enterprise_Documents

Engineering

Policies

Operations

Training

Policies determine:

- Collection assignment

- Distance metric

- Replication

- Sharding

- Index configuration

Application code never hardcodes collection names.

## 11.12 Metadata Publishing

Every vector includes metadata.

Example:

document_id: DOC-1001

chunk_id: CHK-3002

repository_id: REP-02

section: Safety

language: en

classification: Internal

version: 5

embedding_model: text-embedding-3-large

Rich metadata enables powerful downstream filtering without additional
joins.

## 11.13 Verification Framework

Publishing is not complete until verification succeeds.

Verification confirms:

- Vector exists

- Metadata matches

- Embedding dimension is correct

- Collection is correct

- Version is correct

Workflow:

Published

↓

Read Back

↓

Compare

↓

Verified

Verification failures trigger retry workflows.

## 11.14 Update Propagation

When content changes:

Document Updated

↓

Chunk Updated

↓

Embedding Updated

↓

Vector Updated

↓

Verification

Only affected vectors are republished.

## 11.15 Delete Propagation

Deletion must propagate throughout the platform.

Workflow:

Repository Delete

↓

Digital Twin

↓

Publishing Framework

↓

Vector Removal

↓

Verification

↓

Archive Metadata

No orphan vectors remain.

## 11.16 Replay Support

A major enterprise requirement is replay.

Example:

Embedding Exists

↓

Vector Lost

↓

Replay

↓

Publish Again

Replay never regenerates embeddings unnecessarily.

## 11.17 Rollback

Example:

Embedding Version 5

↓

Problem Detected

↓

Rollback

↓

Embedding Version 4

↓

Publish

Rollback uses existing embedding assets rather than recomputing vectors.

## 11.18 Synchronization States

Publishing lifecycle:

READY

↓

QUEUED

↓

PUBLISHING

↓

VERIFYING

↓

PUBLISHED

↓

VERIFIED

Alternative states:

FAILED

RETRYING

ROLLBACK

ARCHIVED

## 11.19 Failure Handling

Typical failures:

  -----------------------------------------------------------------------
  **Failure**                           **Recovery**
  ------------------------------------- ---------------------------------
  Network Timeout                       Retry

  Provider Error                        Retry

  Duplicate Publish                     Ignore

  Metadata Mismatch                     Republish

  Verification Failure                  Retry

  Collection Missing                    Create or fail policy

  Authentication Failure                Refresh credentials
  -----------------------------------------------------------------------

Failures are isolated and recoverable.

## 11.20 Performance Optimization

The Publishing Framework is designed for high throughput.

Optimization techniques include:

- Parallel publishing workers

- Adaptive batch sizing

- Queue prioritization

- Incremental publishing

- Compression (provider permitting)

- Asynchronous verification

This enables ingestion of millions of vectors efficiently.

## 11.21 Security Considerations

Publishing must comply with enterprise security policies.

Requirements:

- Encrypted communication

- Provider authentication

- Collection authorization

- Metadata validation

- Audit logging

- Least-privilege access

Security classifications inherited from the Digital Twin accompany every
published vector.

## 11.22 Design Decisions (ADRs)

**ADR-025: Publishing as an Independent Framework**

**Decision**

Vector publishing shall remain independent of embedding generation.

**Rationale**

This separation enables replay, rollback, provider migration, and
independent scaling.

**ADR-026: Verified Publishing**

**Decision**

Publishing is considered complete only after successful verification.

**Rationale**

Acknowledgement from a provider alone does not guarantee durable storage
or metadata integrity.

**ADR-027: Idempotent Operations**

**Decision**

All publishing operations must be idempotent.

**Rationale**

Idempotency ensures safe retries, replay, disaster recovery, and
distributed execution.

**ADR-028: Provider-Neutral Vector Interface**

**Decision**

All vector databases shall implement a common publishing interface.

**Rationale**

Organizations should be able to migrate between vector databases without
redesigning ingestion workflows.

## 11.23 Future Extensions

The framework is prepared for future capabilities, including:

- Multi-region publishing

- Cross-provider replication

- Hybrid dense + sparse indexing

- Multi-vector publishing

- Automatic index optimization

- Zero-downtime collection migration

- Blue/green vector deployments

- Canary publishing strategies

These enhancements can be introduced without changing the publishing
contract.

## 11.24 Summary

The Vector Publishing Framework completes the core EKIE ingestion
pipeline by reliably synchronizing governed embedding assets with
enterprise vector databases.

By separating publishing from embedding generation and enforcing
verification, idempotency, and provider abstraction, EKIE delivers a
resilient, scalable, and future-proof publication layer capable of
supporting enterprise AI workloads.


### 11.X Vector Math & Distance Metric Contract

**Integration Contract:** EKIE must explicitly publish the exact `distance_metric` (e.g., Cosine, DotProduct, Euclidean) alongside the Vector Database Collection Schema. EKRE strictly depends on this metadata to perform compatible vector similarity searches. Without it, downstream retrieval math will fail silently.


# Chapter 12 - Workflow Orchestration Framework

**Version:** 1.0\
**Status:** Approved\
**Volume:** III --- Platform Runtime Architecture

## 12.1 Objective

The Workflow Orchestration Framework is the execution engine of EKIE.

While previous chapters define **what** should happen during ingestion,
this chapter defines **how** every task is executed, monitored, retried,
resumed, and completed.

Without orchestration, EKIE would simply be a collection of services.

With orchestration, EKIE becomes an enterprise platform capable of
processing millions of documents reliably.

## 12.2 Why Orchestration?

Many ingestion systems execute tasks like this:

Scan

↓

Transform

↓

Chunk

↓

Embed

↓

Publish

If any stage fails:

- everything restarts

- duplicate work occurs

- recovery becomes manual

- partial processing is lost

This is unacceptable for enterprise systems.

EKIE executes workflows instead.

Document

↓

Workflow Instance

↓

Tasks

↓

Workers

↓

State Persistence

↓

Recovery

↓

Completion

Every operation is resumable.

Every task is independently recoverable.

## 12.3 Design Philosophy

The Workflow Engine follows five principles.

**Principle 1**

Every document has its own workflow.

**Principle 2**

Every task is resumable.

**Principle 3**

Every task is idempotent.

**Principle 4**

Workflow state is persisted after every transition.

**Principle 5**

Workers are stateless.

This allows unlimited horizontal scaling.

## 12.4 Responsibilities

The Workflow Engine is responsible for:

- Workflow creation

- Task scheduling

- Queue management

- State persistence

- Dependency management

- Retry policies

- Failure recovery

- Checkpoint creation

- Parallel execution

- Event generation

- Workflow completion

- Cancellation

- Replay

It is **not** responsible for business logic.

Business logic remains inside the individual frameworks.

## 12.5 High-Level Architecture

Repository Sync

↓

Workflow Manager

↓

Workflow Instance

↓

Task Scheduler

↓

Execution Queue

↓

Workers

↓

Task Result

↓

Workflow State Store

↓

Digital Twin Update

The Workflow Engine coordinates execution but does not perform document
processing itself.

## 12.6 Workflow Definition

Every ingestion follows the same logical workflow.

Repository Sync

↓

Transformation

↓

Document Intelligence

↓

Chunking

↓

Embedding

↓

Publishing

↓

Verification

↓

Completed

Each stage is a separate task.

## 12.7 Workflow Instance

Every document creates its own workflow instance.

Example:

Workflow ID

WF-00001523

Document

DOC-00952

Repository

Engineering

Status

Running

Started

2026-07-01 10:15 UTC

Workflow instances remain permanently auditable.

## 12.8 Task Model

Every workflow consists of independent tasks.

Workflow

↓

Task 1

↓

Task 2

↓

Task 3

↓

Task 4

Each task contains:

- Task ID

- Workflow ID

- Parent Task

- Task Type

- State

- Retry Count

- Assigned Worker

- Start Time

- Completion Time

- Result

## 12.9 Task Types

Examples include:

  -----------------------------------------------------------------------
  **Task**                             **Description**
  ------------------------------------ ----------------------------------
  Repository Scan                      Detect changes

  Markdown Generation                  Canonicalize Markdown

  Document Intelligence                Semantic analysis

  Chunk Generation                     Build chunk assets

  Embedding Generation                 Generate embeddings

  Vector Publishing                    Publish vectors

  Verification                         Validate publication
  -----------------------------------------------------------------------

New task types are introduced through plugins.

## 12.10 State Machine

Every workflow follows a deterministic lifecycle.

CREATED

↓

READY

↓

RUNNING

↓

WAITING

↓

COMPLETED

Alternative states:

FAILED

CANCELLED

PAUSED

RETRYING

ARCHIVED

State transitions are persisted immediately.

## 12.11 Task State Machine

Each task has its own lifecycle.

PENDING

↓

QUEUED

↓

RUNNING

↓

SUCCESS

Alternative states:

FAILED

SKIPPED

WAITING

RETRYING

CANCELLED

Task state is independent of workflow state.

## 12.12 Queue Architecture

The Workflow Engine uses specialized queues.

Repository Queue

Markdown Queue

Chunk Queue

Embedding Queue

Publishing Queue

Verification Queue

Each queue scales independently.

This prevents one processing stage from becoming a bottleneck for the
entire platform.

## 12.13 Worker Architecture

Workers execute tasks from queues.

Queue

↓

Worker Pool

↓

Worker

↓

Task

↓

Result

Workers are completely stateless.

If a worker crashes, another worker resumes processing.

## 12.14 Dependency Graph

Tasks are not always linear.

Example:

Markdown

↓

Document Intelligence

↓

Chunking

↓

Embedding

↓

Publishing

However:

OCR

↓

Markdown

↓

Metadata

↓

Validation

may execute in parallel.

Dependencies are explicitly defined.

## 12.15 Retry Policies

Retries are configurable.

Example:

  -----------------------------------------------------------------------
  **Failure**                              **Retry**
  ---------------------------------------- ------------------------------
  Network Error                            Yes

  Timeout                                  Yes

  Provider Busy                            Yes

  Validation Failure                       No

  Corrupt File                             No

  Permission Error                         Policy Based
  -----------------------------------------------------------------------

Exponential backoff is recommended.

## 12.16 Checkpointing

After every successful task:

Task Completed

↓

Persist State

↓

Create Checkpoint

↓

Continue

If failure occurs:

Restart

↓

Read Checkpoint

↓

Resume

No completed work is repeated unnecessarily.

## 12.17 Replay

Replay is a first-class capability.

Example:

Workflow

↓

Completed

↓

Policy Updated

↓

Replay

↓

Only Required Tasks Execute

Replay uses the Digital Twin to determine what needs regeneration.

## 12.18 Parallel Execution

Independent tasks execute simultaneously.

Example:

Markdown

↓

Language Detection

Table Analysis

PII Detection

Classification

↓

Merge Results

Parallelism significantly reduces overall processing time.

## 12.19 Workflow Events

The engine publishes events.

Examples:

- Workflow Created

- Workflow Started

- Task Queued

- Task Completed

- Task Failed

- Retry Started

- Workflow Paused

- Workflow Completed

- Workflow Cancelled

These events feed monitoring dashboards and audit logs.

## 12.20 Failure Recovery

Representative failures include:

  -----------------------------------------------------------------------
  **Failure**                   **Recovery**
  ----------------------------- -----------------------------------------
  Worker Crash                  Reassign Task

  Queue Failure                 Restore Queue

  Database Timeout              Retry

  API Failure                   Retry

  Process Restart               Resume from Checkpoint

  Server Failure                Continue on Another Node
  -----------------------------------------------------------------------

Recovery is automatic wherever possible.

## 12.21 Scalability

The Workflow Engine is horizontally scalable.

Scaling dimensions include:

- Repository workers

- Markdown workers

- OCR workers

- Chunk workers

- Embedding workers

- Publishing workers

Each worker pool can scale independently according to workload.

## 12.22 Monitoring Metrics

Operational metrics include:

- Active workflows

- Queue depth

- Average task duration

- Worker utilization

- Retry rate

- Failure rate

- Throughput

- Average ingestion time

These metrics are exposed through the Observability Framework.

## 12.23 Design Decisions (ADRs)

**ADR-029: Workflow per Document**

**Decision**

Every document shall have an independent workflow instance.

**Rationale**

This enables fine-grained retries, parallel processing, and precise
operational tracking.

**ADR-030: Stateless Workers**

**Decision**

Workers shall not maintain execution state.

**Rationale**

Stateless workers simplify scaling, failover, and infrastructure
management.

**ADR-031: Persistent Workflow State**

**Decision**

Workflow state shall be persisted after every transition.

**Rationale**

Persistent state enables resumability, disaster recovery, and
deterministic execution.

**ADR-032: Queue-Based Execution**

**Decision**

Tasks shall execute through dedicated queues rather than direct
invocation.

**Rationale**

Queues decouple producers from consumers, improve scalability, and
isolate workload spikes.

## 12.24 Future Extensions

The orchestration framework has been designed to support future
enterprise capabilities such as:

- Priority-based scheduling

- SLA-aware workflows

- Multi-tenant execution

- Distributed orchestration across regions

- Human approval tasks

- Conditional workflow branching

- Event-driven orchestration

- AI-assisted scheduling

- Kubernetes-native execution

- Workflow simulation and dry-run mode

## 12.25 Summary

The Workflow Orchestration Framework provides the runtime backbone of
EKIE. It transforms a sequence of processing steps into a resilient,
scalable, observable, and recoverable execution platform.

By combining persistent workflow state, queue-based scheduling,
stateless workers, checkpointing, and deterministic replay, EKIE ensures
that enterprise document ingestion remains reliable even under failures,
infrastructure changes, and large-scale workloads.

# Chapter 13 - Control Plane & Metadata Platform

**Version:** 1.0\
**Status:** Approved\
**Volume:** III --- Platform Runtime Architecture

## 13.1 Objective

The **Control Plane** is the operational brain of EKIE.

Every framework designed in previous chapters depends upon the Control
Plane.

It stores **only operational metadata**, never enterprise business
content.

The Control Plane answers questions such as:

- Which repositories exist?

- Which documents have changed?

- Which Markdown version is current?

- Which chunks belong to this document?

- Which embeddings are active?

- Which vectors were published?

- Which workflow failed?

- Which parser generated this Markdown?

- Which embedding model created this vector?

- Can this document be replayed?

Without the Control Plane, EKIE becomes a collection of disconnected
services.

## 13.2 Design Philosophy

The Control Plane is **not** a document repository.

It is **not** an asset repository.

It is **not** a vector database.

Instead, it stores:

- Metadata

- Relationships

- State

- Lineage

- Configuration

- Policies

- Operational history

It becomes the **single operational source of truth** for the platform.

## 13.3 Why SQL Server?

For EKIE v1.0, Microsoft SQL Server is selected as the metadata platform
because it provides:

- ACID transactions

- Mature indexing

- Excellent concurrency

- Enterprise security

- Backup and recovery

- Temporal tables

- Partitioning

- High Availability

- Always On support

- Integration with enterprise ecosystems

Future versions may support PostgreSQL or other relational databases
through an abstraction layer.

## 13.4 High-Level Architecture

Repository

│

▼

Repository Synchronization

│

▼

══════════════════════════════════════

CONTROL PLANE

(Microsoft SQL Server Metadata Platform)

══════════════════════════════════════

Repositories

Documents

Versions

Assets

Chunks

Embeddings

Publishing

Policies

Workflows

Audit

Events

══════════════════════════════════════

│

▼

Every EKIE Framework

## 13.5 Design Principles

The Control Plane follows several principles.

**Principle 1**

No business content.

Only metadata.

**Principle 2**

Every entity has a stable identity.

**Principle 3**

Everything is versioned.

**Principle 4**

Everything is auditable.

**Principle 5**

Everything is replayable.

**Principle 6**

Everything is traceable.

## 13.6 Metadata Domains

The database is divided into logical domains.

Repositories

↓

Documents

↓

Versions

↓

Assets

↓

Chunk Assets

↓

Embedding Assets

↓

Publishing

↓

Workflows

↓

Policies

↓

Audit

↓

Events

Each domain owns its own tables and APIs.

## 13.7 Core Database Schema

The first version of EKIE contains the following logical schemas.

Repository

Document

Asset

Chunk

Embedding

Publishing

Workflow

Configuration

Security

Audit

Observability

Separating schemas simplifies maintenance and permissions.

## 13.8 Repository Schema

Main tables:

Repositories

RepositoryConnections

RepositorySchedules

RepositoryCapabilities

RepositoryHealth

Repository metadata includes:

- Repository ID

- Name

- Type

- Root Path

- Authentication Profile

- Status

- Created Date

- Last Sync

- Connector Version

## 13.9 Document Schema

Main tables:

Documents

DocumentVersions

DocumentMetadata

DocumentRelationships

DocumentLifecycle

Each document has:

- Internal Document ID

- Repository ID

- Current Version

- Hash

- Current Path

- State

- Classification

- Language

## 13.10 Asset Schema

Assets include:

Markdown Assets

OCR Assets

Extracted Tables

Extracted Images

Derived Metadata

Each asset references:

- Parent Document

- Version

- Storage URI

- Generation Time

- Generator Version

## 13.11 Chunk Schema

Tables:

Chunks

ChunkMetadata

ChunkRelationships

ChunkVersions

Metadata includes:

- Chunk ID

- Parent Markdown

- Section

- Strategy

- Token Count

- Sequence Number

- Quality Score

Chunks become first-class managed assets.

## 13.12 Embedding Schema

Tables:

Embeddings

EmbeddingVersions

EmbeddingModels

EmbeddingProviders

Stored metadata includes:

- Embedding ID

- Chunk ID

- Provider

- Model

- Dimensions

- Token Count

- Cost

- Latency

- Status

Vectors themselves are **not** stored here.

## 13.13 Publishing Schema

Tables:

PublishedVectors

PublishingHistory

Collections

ProviderMappings

Metadata includes:

- Collection

- Vector ID

- Publish Timestamp

- Verification Status

- Publish Version

- Provider

## 13.14 Workflow Schema

Tables:

Workflows

WorkflowTasks

WorkflowCheckpoints

TaskHistory

Each workflow stores:

- Workflow ID

- Current State

- Retry Count

- Duration

- Assigned Worker

- Completion Status

## 13.15 Policy Schema

Configuration is fully versioned.

Examples:

Chunk Policies

Embedding Policies

Publishing Policies

Retry Policies

Repository Policies

Security Policies

Policies are referenced rather than duplicated.

## 13.16 Security Schema

Security metadata includes:

- Users

- Roles

- Permissions

- API Keys

- Credential References

- Tenant Information (future)

- Access Policies

Secrets themselves are stored in an external secrets manager, not in SQL
Server.

## 13.17 Audit Schema

Everything important generates an audit record.

Examples:

- Repository Registered

- Document Modified

- Workflow Started

- Chunk Generated

- Embedding Published

- Policy Changed

- Replay Executed

Audit entries are immutable.

## 13.18 Event Schema

Platform events are stored for diagnostics and analytics.

Examples:

Repository Events

Workflow Events

Publishing Events

System Events

Recovery Events

These events support observability and replay.

## 13.19 Relationships

One of the strongest features of the Control Plane is complete lineage.

Repository

↓

Document

↓

Document Version

↓

Markdown

↓

Chunk

↓

Embedding

↓

Published Vector

Every relationship is represented by foreign keys and immutable
identifiers.

## 13.20 Database Performance Strategy

To support enterprise-scale repositories, the metadata platform
incorporates:

- Clustered indexes on primary identifiers.

- Non-clustered indexes for frequent queries.

- Partitioning of large audit/event tables.

- Read-optimized indexes for dashboards.

- Optimistic concurrency control.

- Batched writes for workflow updates.

- Archival policies for historical data.

The database is optimized for **metadata operations**, not document
storage.

## 13.21 Backup & Recovery

Operational metadata is critical.

Recommended strategy:

  -----------------------------------------------------------------------
  **Component**         **Backup Strategy**
  --------------------- -------------------------------------------------
  SQL Server            Full + Differential + Transaction Log

  Configuration         Versioned Export

  Policies              Version Controlled

  Audit                 Long-term Retention

  Events                Configurable Retention
  -----------------------------------------------------------------------

Recovery objectives should align with enterprise RPO/RTO requirements.

## 13.22 Design Decisions (ADRs)

**ADR-033: SQL Server as Metadata Authority**

**Decision**

Microsoft SQL Server shall serve as the authoritative metadata store for
EKIE.

**Rationale**

SQL Server provides enterprise-grade transactional consistency,
security, scalability, and operational tooling suitable for metadata
management.

**ADR-034: Metadata Without Business Content**

**Decision**

The Control Plane shall store metadata only.

**Rationale**

Separating operational metadata from business content simplifies
governance, improves scalability, and reduces security exposure.

**ADR-035: Version Everything**

**Decision**

Every operational entity shall support versioning.

**Rationale**

Versioning enables replay, rollback, auditing, reproducibility, and
controlled evolution of the ingestion platform.

**ADR-036: Complete Lineage**

**Decision**

Every managed asset shall maintain lineage back to its originating
repository and document.

**Rationale**

Complete lineage enables enterprise governance, troubleshooting,
compliance, and explainability.

## 13.23 Implementation Readiness

This chapter defines the conceptual metadata platform.

During implementation, it will be expanded into:

- Complete SQL Server ER diagrams.

- Normalized table definitions.

- Primary and foreign key specifications.

- Index strategies.

- Stored procedures (where appropriate).

- Views for reporting.

- Migration scripts.

- Data retention policies.

- API contracts for each metadata domain.

This detailed design will be delivered in **Volume V -- Database Design
& Implementation**.

## 13.24 Summary

The Control Plane is the operational foundation of EKIE. It coordinates
every framework by maintaining authoritative metadata, workflow state,
configuration, lineage, and audit history while intentionally excluding
business content and vector payloads.

By centralizing operational intelligence in SQL Server, EKIE gains
deterministic execution, enterprise governance, efficient recovery, and
complete traceability across the ingestion lifecycle.

**Chapter 14 -- Storage Architecture** (Markdown repository, asset
    storage, logs, temporary files, cache)

2.  **Chapter 15 -- Configuration & Policy Engine**

3.  **Chapter 16 -- Observability Framework**

4.  **Chapter 17 -- Security & Governance**

5.  **Chapter 18 -- Plugin & Extension SDK**

6.  **Chapter 19 -- Deployment Architecture**

7.  **Chapter 20 -- Testing & Validation Strategy**

8.  **Chapter 21 -- Disaster Recovery & Business Continuity**

9.  **Chapter 22 -- Operations Runbook**

These chapters will elevate EKIE from a well-designed ingestion engine
to a **production-ready enterprise platform** suitable for large-scale
deployment.

# Chapter 14 - Enterprise Storage Architecture

**Version:** 1.0\
**Status:** Approved\
**Volume:** III --- Platform Runtime Architecture

## 14.1 Objective

The Enterprise Storage Architecture defines how EKIE manages **all
physical artifacts** generated throughout the ingestion lifecycle.

A common mistake in many RAG systems is storing everything inside the
Vector Database or relational database.

EKIE deliberately separates:

- Operational Metadata

- Knowledge Assets

- Temporary Files

- Logs

- Cache

- Recovery Data

Each storage type has different performance, lifecycle, security, and
retention requirements.

This separation improves scalability, governance, recovery, and
maintainability.

## 14.2 Storage Philosophy

EKIE follows the principle:

**"Store every artifact in the storage system designed for its
purpose."**

For example:

  -----------------------------------------------------------------------
  **Artifact**          **Storage**
  --------------------- -------------------------------------------------
  Metadata              SQL Server

  Markdown              File/Object Storage

  Images                File/Object Storage

  OCR Output            File/Object Storage

  Chunks                File/Object Storage + SQL Metadata

  Embeddings            File/Object Storage (Optional) + SQL Metadata

  Published Vectors     Vector Database

  Logs                  Log Platform

  Cache                 Memory Cache

  Temporary Files       Temporary Workspace
  -----------------------------------------------------------------------

No single storage technology should be responsible for every artifact.

## 14.3 High-Level Storage Architecture

Enterprise Repository

│

▼

Repository Synchronization

▼

────────────────────────────────────────────────────

CONTROL PLANE (SQL Server)

────────────────────────────────────────────────────

Repository Metadata

Workflow Metadata

Policies

Lineage

Audit

Events

────────────────────────────────────────────────────

KNOWLEDGE ASSET STORAGE

────────────────────────────────────────────────────

Markdown

Extracted Images

OCR Output

Extracted Tables

Chunk Assets

Embedding Assets (Optional)

Validation Reports

────────────────────────────────────────────────────

VECTOR DATABASE

────────────────────────────────────────────────────

Dense Vectors

Sparse Vectors (Future)

Metadata Index

────────────────────────────────────────────────────

CACHE

TEMP STORAGE

LOG STORAGE

BACKUP STORAGE

## 14.4 Storage Domains

The platform defines six independent storage domains.

**1. Operational Storage**

Purpose:

Store metadata only.

Technology:

- Microsoft SQL Server

Contains:

- Workflows

- Documents

- Policies

- State

- Lineage

**2. Knowledge Storage**

Purpose:

Persist generated assets.

Examples:

- Markdown

- OCR output

- Extracted images

- Tables

- Validation reports

Technology:

- Local Storage (Development)

- NAS

- Azure Blob

- S3

- MinIO

- Enterprise Object Storage

**3. Vector Storage**

Purpose:

Store searchable embeddings.

Technology:

- Qdrant

Future:

- Azure AI Search

- Milvus

- Pinecone

- Weaviate

**4. Temporary Storage**

Purpose:

Workspace during processing.

Contains:

- Temporary OCR files

- Extracted ZIPs

- Intermediate Markdown

- Processing artifacts

Characteristics:

- Short-lived

- Automatically cleaned

- Never referenced by Digital Twin

**5. Cache**

Purpose:

Improve performance.

Examples:

- Parser cache

- Token cache

- Policy cache

- Language detection cache

- Embedding capability cache

Recommended technologies:

- Redis

- In-Memory Cache

**6. Log Storage**

Purpose:

Operational diagnostics.

Contains:

- Application logs

- Worker logs

- Errors

- Metrics

- Traces

Recommended technologies:

- ELK

- OpenSearch

- Azure Monitor

- Splunk

## 14.5 Knowledge Asset Storage

Every generated artifact is stored using immutable storage.

Example hierarchy:

KnowledgeStore/

Repositories/

Engineering/

Operations/

Documents/

DOC-001/

Version-1/

markdown.md

tables/

images/

ocr/

metadata.json

Version-2/

markdown.md

Assets are never overwritten.

New versions create new folders.

## 14.6 Storage Identity

Each asset receives a permanent identity.

Example:

Asset ID

↓

Storage URI

↓

Version

↓

Hash

↓

Created Time

The SQL Control Plane references assets by URI.

The asset storage never contains workflow logic.

## 14.7 Storage Versioning

Every generated asset is immutable.

Example:

Document

↓

Markdown v1

↓

Markdown v2

↓

Markdown v3

No asset is modified in place.

This guarantees:

- Replay

- Rollback

- Audit

- Reproducibility

## 14.8 Storage Lifecycle

Each asset progresses through a lifecycle.

Created

↓

Validated

↓

Approved

↓

Published

↓

Archived

↓

Deleted (Policy Driven)

Deletion policies are configurable.

Some industries require permanent retention.

## 14.9 Temporary Workspace

Processing requires a secure workspace.

Example:

Incoming File

↓

Temporary Folder

↓

Transformation

↓

Validation

↓

Knowledge Store

↓

Workspace Cleanup

Temporary files should never persist after successful processing.

## 14.10 Asset Cleanup

Automatic cleanup removes:

- Expired temporary files

- Failed partial outputs

- Obsolete cache

- Old checkpoints (policy driven)

Cleanup jobs are scheduled through the Workflow Engine.

## 14.11 Retention Policies

Different artifacts require different retention periods.

  -----------------------------------------------------------------------
  **Artifact**                     **Retention**
  -------------------------------- --------------------------------------
  Markdown                         Permanent (default)

  OCR Output                       Configurable

  Temporary Files                  Hours/Days

  Cache                            Minutes/Hours

  Logs                             30--365 days

  Audit                            Years

  Checkpoints                      Policy Based
  -----------------------------------------------------------------------

Policies are centrally managed.

## 14.12 Storage Security

Every storage domain follows enterprise security principles.

Requirements:

- Encryption at rest

- Encryption in transit

- Role-based access

- Immutable audit logs

- Version protection

- Malware scanning (optional)

- Integrity verification through hashes

Sensitive documents inherit classification from the Control Plane.

## 14.13 Backup Strategy

Each storage domain has independent backup requirements.

  -----------------------------------------------------------------------
  **Storage**                   **Backup**
  ----------------------------- -----------------------------------------
  SQL Server                    Full + Incremental

  Knowledge Assets              Object Storage Replication

  Vector DB                     Snapshot

  Logs                          Archive

  Configuration                 Git + Backup

  Policies                      Version Control
  -----------------------------------------------------------------------

Recovery strategies differ by storage type.

## 14.14 Storage Scalability

Storage architecture supports enterprise growth.

Strategies include:

- Object storage for large assets.

- Hierarchical folder organization.

- Compression where appropriate.

- Lifecycle management.

- Automatic archival.

- Multi-region replication (future).

The architecture targets repositories containing **tens of millions of
documents**.

## 14.15 Design Decisions (ADRs)

**ADR-037: Storage Separation**

**Decision**

Operational metadata, knowledge assets, vectors, logs, cache, and
temporary files shall use independent storage systems.

**Rationale**

Different workloads have different performance, retention, and
governance requirements. Separation simplifies scaling and maintenance.

**ADR-038: Immutable Asset Storage**

**Decision**

Knowledge assets shall never be modified in place.

**Rationale**

Immutability enables reproducibility, replay, rollback, and auditability
while preventing accidental corruption.

**ADR-039: URI-Based Asset Referencing**

**Decision**

The Control Plane shall reference assets using stable storage URIs
rather than storing file contents.

**Rationale**

This keeps the metadata platform lightweight and allows storage
technologies to evolve independently.

**ADR-040: Policy-Driven Lifecycle Management**

**Decision**

Retention, archival, cleanup, and deletion shall be governed by
centrally managed policies.

**Rationale**

Different organizations and industries have varying compliance
requirements, making configurable lifecycle management essential.

## 14.16 Future Enhancements

The storage architecture is designed to support:

- Multi-cloud object storage.

- Content-addressable storage.

- Deduplication of identical assets.

- Cold archive integration.

- WORM (Write Once Read Many) storage.

- Tiered storage optimization.

- Intelligent lifecycle automation.

- Global asset replication.

These enhancements can be added without affecting upstream frameworks.

## 14.17 Summary

The Enterprise Storage Architecture provides a clear separation of
concerns for every physical artifact generated by EKIE. By assigning
each artifact type to the most appropriate storage technology and
enforcing immutability, versioning, and policy-driven lifecycle
management, the platform achieves enterprise-grade scalability,
resilience, and governance.

Storage is no longer viewed as a passive persistence layer---it becomes
an integral part of the ingestion platform's architecture.

# Chapter 15 - Configuration & Policy Engine

**Version:** 1.0\
**Status:** Approved\
**Volume:** III --- Platform Runtime Architecture

## 15.1 Objective

The Configuration & Policy Engine is the **decision brain of EKIE
execution behavior**.

While the Control Plane stores metadata (what exists), the Policy Engine
defines:

**How EKIE behaves at runtime across all frameworks**

It eliminates hardcoded logic from the system.

Everything becomes configurable:

- Chunking behavior

- Embedding models

- Retry strategies

- Publishing rules

- Storage locations

- Workflow execution rules

- Security constraints

- Performance tuning

This is what transforms EKIE from a pipeline into a **configurable
enterprise platform**.

## 15.2 Why a Policy Engine?

Without a policy system, systems become:

Hardcoded → Fragile → Non-Scalable → Unmaintainable

Example of a bad design:

chunk_size = 1000

model = \"text-embedding-3-large\"

retry = 3

Problems:

- Requires code changes for updates

- No environment-specific behavior

- No governance

- No version control

- No audit trail

EKIE replaces this with:

Policy Driven Execution

## 15.3 Design Philosophy

The Policy Engine follows five principles:

**Principle 1 --- Everything is a Policy**

No configuration exists outside policy definitions.

**Principle 2 --- Policies are Versioned**

Every change creates a new policy version.

**Principle 3 --- Policies are Context-Aware**

Policies vary by:

- Repository

- Document type

- Security classification

- Region

- Environment

- Tenant (future)

**Principle 4 --- Policies are Evaluated at Runtime**

No static configuration caching without validation.

**Principle 5 --- Policies are Centralized**

All frameworks query the same policy engine.

## 15.4 High-Level Architecture

Control Plane (SQL Server)

│

▼

Policy & Configuration Engine

│

┌──────────────┬──────────────┐

▼ ▼ ▼

Chunking Embedding Publishing

Policy Policy Policy

▼ ▼ ▼

Workflow Engine ← Policy Evaluation Layer → Storage Engine

## 15.5 Policy Types

EKIE defines multiple policy domains.

**1. Chunking Policy**

Controls:

- Chunk size

- Chunk overlap

- Strategy selection

- Semantic rules

- Table handling

- Code handling

Example:

chunking:

strategy: semantic

max_tokens: 1200

overlap: adaptive

preserve_tables: true

**2. Embedding Policy**

Controls:

- Model selection

- Provider selection

- Batch size

- Cost limits

- Token constraints

Example:

embedding:

model: text-embedding-3-large

provider: openai

max_tokens: 8000

fallback_model: bge-m3

**3. Publishing Policy**

Controls:

- Vector DB selection

- Collection mapping

- Retry behavior

- Verification rules

Example:

publishing:

provider: qdrant

batch_size: 256

verify_after_write: true

**4. Workflow Policy**

Controls:

- Task execution order

- Parallelization rules

- Retry logic

- Failure handling

Example:

workflow:

max_retries: 3

backoff: exponential

parallel_tasks: true

**5. Storage Policy**

Controls:

- Storage provider

- Retention rules

- Compression rules

**6. Security Policy**

Controls:

- Access restrictions

- Document classification handling

- Data masking rules

## 15.6 Policy Evaluation Engine

The Policy Engine evaluates policies at runtime.

Document Context

│

▼

Policy Resolver

│

▼

Rule Matching Engine

│

▼

Active Policy

│

▼

Execution Framework

## 15.7 Policy Resolution Flow

Policies are resolved using hierarchy:

Global Policy

↓

Repository Policy

↓

Document Policy

↓

Section Policy (advanced)

↓

Runtime Overrides

The most specific rule wins.

## 15.8 Policy Storage Model

Policies are stored in Control Plane.

Tables:

Policies

PolicyVersions

PolicyRules

PolicyBindings

PolicyOverrides

Each policy is:

- Versioned

- Auditable

- Reversible

- Testable

## 15.9 Policy Binding System

Policies are bound to:

- Repositories

- Document types

- File formats

- Security levels

Example:

Engineering Repo → Chunking Policy A

HR Repo → Security Policy B

Legal Docs → Embedding Policy C

## 15.10 Dynamic Overrides

Runtime overrides allow temporary behavior changes:

Example:

High Priority Document → Increase chunk size

Emergency Mode → Reduce retries

Cost Optimization Mode → Switch embedding model

Overrides expire automatically.

## 15.11 Policy Conflict Resolution

If multiple policies match:

Priority order:

1\. Runtime Override

2\. Document Policy

3\. Repository Policy

4\. Global Policy

## 15.12 Policy Validation

Before activation:

- Schema validation

- Conflict detection

- Safety checks

- Cost estimation

- Impact analysis

Invalid policies are rejected.

## 15.13 Policy Versioning

Each change creates a new immutable version.

Example:

ChunkingPolicy v1

ChunkingPolicy v2

ChunkingPolicy v3

Benefits:

- Replay consistency

- Audit history

- Safe rollback

## 15.14 Policy Simulation Mode

Policies can be tested before deployment:

Input Document → Policy Simulation → Expected Behavior

Used for:

- Cost estimation

- Chunk preview

- Embedding prediction

- Risk analysis

## 15.15 Policy Impact Analysis

Before activating:

- Number of documents affected

- Expected cost change

- Processing time impact

- Storage impact

## 15.16 Performance Optimization

Policy Engine is optimized using:

- Cached policy resolution

- Precompiled rules

- Indexed lookups

- Lazy evaluation

- Hierarchical caching

## 15.17 Security Considerations

Policies define system behavior, so security is critical:

- Only authorized roles can modify policies

- Full audit logging

- Approval workflows (optional)

- Immutable version history

- Environment isolation

## 15.18 Failure Handling

If policy engine fails:

Fallback behavior:

Last Known Good Policy

No execution should halt due to policy unavailability.

## 15.19 Observability

Tracked metrics:

- Policy evaluation time

- Policy cache hit ratio

- Conflict rate

- Override usage

- Version adoption rate

## 15.20 Design Decisions (ADRs)

**ADR-041: Policy-Driven Architecture**

**Decision**

All runtime behaviors shall be controlled through policies.

**Rationale**

Eliminates hardcoding and enables dynamic enterprise configuration.

**ADR-042: Hierarchical Policy Resolution**

**Decision**

Policies follow a strict hierarchy from global to runtime overrides.

**Rationale**

Ensures predictable and deterministic execution behavior.

**ADR-043: Versioned Policies**

**Decision**

All policies must be immutable and version-controlled.

**Rationale**

Enables replay, rollback, and auditability.

**ADR-044: Runtime Policy Evaluation**

**Decision**

Policies are evaluated at runtime rather than compile-time.

**Rationale**

Enables dynamic adaptation without redeployment.

## 15.21 Future Extensions

- AI-generated policy suggestions

- Auto-tuning policies based on performance

- Cost-aware dynamic policy switching

- Multi-tenant policy isolation

- Graph-based policy dependency system

- Policy simulation UI dashboard

## 15.22 Summary

The Configuration & Policy Engine is the **control brain of EKIE runtime
behavior**.

It removes all hardcoded logic and replaces it with:

- Versioned rules

- Context-aware evaluation

- Hierarchical resolution

- Runtime flexibility

- Enterprise governance

This is what makes EKIE truly **adaptive and production-grade**.

# Chapter 16 - Observability Framework

This will define:

- Logging architecture

- Metrics system

- Distributed tracing

- Pipeline monitoring

- Workflow visibility

- Failure analytics

- Real-time dashboards

This is essential to make EKIE a **fully production-grade,
self-monitoring enterprise system**.

**Version:** 1.0\
**Status:** Approved\
**Volume:** III --- Platform Runtime Architecture

## 16.1 Objective

The Observability Framework is the **sensory system of EKIE**.

It ensures the platform is:

- Visible

- Debuggable

- Measurable

- Auditable

- Diagnosable in real time

Without observability, EKIE becomes a "black box ingestion engine".

With observability, EKIE becomes a **fully explainable distributed
system**.

## 16.2 Why Observability is Critical

In enterprise ingestion systems:

- Failures are inevitable

- Latency varies

- External APIs fail

- Workers crash

- Data quality shifts

Without observability:

Failure → Unknown Cause → Manual Debugging → Downtime

With observability:

Failure → Traceable Root Cause → Automated Recovery → Continuous
Operation

## 16.3 Observability Pillars

EKIE follows the three classical pillars:

**1. Logs (What happened?)**

- Event-level details

- Debug information

- Error traces

**2. Metrics (How is the system performing?)**

- Aggregated numbers

- Time-series data

- Performance KPIs

**3. Traces (Where did it happen?)**

- End-to-end workflow tracking

- Distributed execution visibility

- Task-level lineage

## 16.4 High-Level Architecture

EKIE Runtime Systems

(Workflow, Chunking, Embedding, Publishing)

│

▼

────────────────────────────────────────────

OBSERVABILITY COLLECTION LAYER

────────────────────────────────────────────

Logs Metrics Traces

│ │ │

▼ ▼ ▼

Log Pipeline Metrics Engine Trace Engine

│ │ │

└──────┬─────┴──────┬───────┘

▼ ▼

Observability Storage Layer

│

▼

Dashboards / Alerts / Analytics

## 16.5 Observability Domains

EKIE defines observability across five domains:

**1. Workflow Observability**

Tracks:

- Workflow states

- Task execution

- Failures

- Retries

**2. Document Observability**

Tracks:

- Document lifecycle

- Transformation stages

- Version changes

**3. Chunk Observability**

Tracks:

- Chunk generation quality

- Token distribution

- Chunk failures

**4. Embedding Observability**

Tracks:

- Model performance

- Latency

- Cost per embedding

- Batch efficiency

**5. Publishing Observability**

Tracks:

- Vector DB success rate

- Latency

- Verification failures

## 16.6 Logging Framework

Logs are structured and machine-readable.

**Log Format**

{

\"timestamp\": \"2026-07-01T10:15:00Z\",

\"service\": \"chunking-engine\",

\"level\": \"INFO\",

\"workflow_id\": \"WF-123\",

\"document_id\": \"DOC-456\",

\"message\": \"Chunk generated successfully\",

\"metadata\": {

\"chunk_id\": \"CHK-789\",

\"tokens\": 1120

}

}

**Log Levels**

  -----------------------------------------------------------------------
  **Level**               **Purpose**
  ----------------------- -----------------------------------------------
  DEBUG                   Internal diagnostics

  INFO                    Normal operation

  WARN                    Unexpected but recoverable

  ERROR                   Task failure

  CRITICAL                System failure
  -----------------------------------------------------------------------

**Log Categories**

- Workflow logs

- System logs

- Security logs

- Performance logs

- API logs

## 16.7 Metrics Framework

Metrics are time-series based.

**Core Metrics**

**Workflow Metrics**

- workflows_started

- workflows_completed

- workflows_failed

- workflow_duration

**Chunk Metrics**

- chunks_created

- chunk_size_avg

- chunk_split_count

**Embedding Metrics**

- embeddings_generated

- embedding_latency

- embedding_cost

**Publishing Metrics**

- vectors_published

- publish_latency

- publish_failures

**System Metrics**

- CPU usage

- Memory usage

- Queue depth

- Worker utilization

## 16.8 Trace Framework

Tracing provides **end-to-end visibility**.

**Example Trace**

TRACE: WF-123

Repository Sync

└── Success (120ms)

Markdown Generation

└── Success (1.2s)

Chunking

└── Success (3.4s)

Embedding

└── Success (5.1s)

Publishing

└── Success (2.2s)

Total: 12.0s

**Span Model**

Each operation is a span:

- span_id

- parent_span_id

- workflow_id

- duration

- status

## 16.9 Observability Storage Layer

All observability data is stored separately:

  -----------------------------------------------------------------------
  **Type**                             **Storage**
  ------------------------------------ ----------------------------------
  Logs                                 ELK / OpenSearch

  Metrics                              Prometheus

  Traces                               Jaeger / Tempo

  Long-term analytics                  Data Lake
  -----------------------------------------------------------------------

## 16.10 Dashboards

Observability dashboards provide:

**System Dashboard**

- Overall throughput

- Active workflows

- Failure rates

**Pipeline Dashboard**

- Stage-wise latency

- Bottleneck detection

**Cost Dashboard**

- Embedding cost

- Storage cost

- API cost

**Quality Dashboard**

- Chunk quality score

- Embedding consistency

- Retrieval readiness metrics

## 16.11 Alerting System

Alerts are triggered when thresholds are exceeded.

**Alert Types**

- Workflow failure spike

- Embedding latency spike

- Vector DB downtime

- Queue backlog growth

- Policy engine failure

**Alert Flow**

Metric Threshold Breach

↓

Alert Engine

↓

Notification Layer

↓

Slack / Email / PagerDuty

## 16.12 Distributed Correlation ID

Every request in EKIE carries:

correlation_id

workflow_id

document_id

task_id

This ensures full traceability across:

- Services

- Workers

- APIs

- Databases

## 16.13 Performance Monitoring

Key performance indicators:

- End-to-end ingestion latency

- Stage-wise bottlenecks

- Queue wait times

- Worker utilization efficiency

## 16.14 Failure Analytics

The system automatically categorizes failures:

  -----------------------------------------------------------------------
  **Type**                     **Example**
  ---------------------------- ------------------------------------------
  Infrastructure               CPU overload

  API Failure                  OpenAI timeout

  Data Issue                   malformed document

  Policy Issue                 invalid configuration
  -----------------------------------------------------------------------

## 16.15 Observability Integration Points

Each framework emits observability events:

- Repository Sync → logs + metrics

- Chunking → metrics + traces

- Embedding → cost + latency metrics

- Publishing → success/failure logs

## 16.16 Security Observability

Tracks:

- Unauthorized access attempts

- Policy violations

- Token misuse

- API abuse patterns

## 16.17 Design Decisions (ADRs)

**ADR-045: Full Observability Requirement**

**Decision**

Every EKIE operation must emit logs, metrics, and traces.

**Rationale**

Ensures full system visibility and production-grade reliability.

**ADR-046: Structured Logging Only**

**Decision**

Logs must be structured (JSON), not plain text.

**Rationale**

Enables machine parsing, indexing, and automated analysis.

**ADR-047: Correlation-Based Traceability**

**Decision**

Every operation must include correlation and workflow identifiers.

**Rationale**

Allows full end-to-end debugging across distributed systems.

**ADR-048: Separate Observability Storage**

**Decision**

Observability data must not be stored in Control Plane.

**Rationale**

Prevents metadata system overload and ensures scalability.

## 16.18 Future Extensions

- AI-driven anomaly detection

- Predictive failure forecasting

- Self-healing workflows

- Cost optimization recommendations

- Intelligent alert suppression

- Observability graph visualization

## 16.19 Summary

The Observability Framework transforms EKIE into a **fully transparent,
measurable, and diagnosable platform**.

It ensures that every ingestion event is:

- Logged

- Measured

- Traced

- Analyzed

- Alerted if needed

This completes the **visibility layer** of the ingestion architecture.

This will define:

- Authentication & authorization model

- Role-based access control (RBAC/ABAC)

- Data classification enforcement

- Audit enforcement

- Multi-tenant isolation (future-ready)

- Secrets management integration

- Compliance controls (GDPR, SOC2-ready design)

This is the final step toward making EKIE **enterprise deployment
ready**.

# Chapter 17 - Security & Governance Framework

**Version:** 1.0\
**Status:** Approved\
**Volume:** III --- Platform Runtime Architecture

## 17.1 Objective

The Security & Governance Framework ensures that EKIE operates in a
**secure, compliant, and policy-controlled enterprise environment**.

It governs:

- Who can access the system

- What they can access

- How data is classified

- How operations are audited

- How secrets are managed

- How compliance is enforced

Security in EKIE is not an external layer.

It is **embedded into every framework**.

## 17.2 Design Philosophy

EKIE security is built on five principles:

**Principle 1 --- Security by Design**

Every component enforces security internally.

**Principle 2 --- Least Privilege Access**

Every action must be explicitly authorized.

**Principle 3 --- Full Auditability**

Every operation is traceable.

**Principle 4 --- Policy-Driven Security**

Security rules are defined in the Policy Engine.

**Principle 5 --- Zero Trust Architecture**

No service is trusted by default.

## 17.3 High-Level Security Architecture

Users / Systems

│

▼

Authentication Layer

│

▼

Authorization Layer

│

▼

Policy Engine (Security Rules)

│

▼

┌──────────────────────────────────┐

│ EKIE Core Systems │

│ Workflow \| Chunk \| Embed \| DB │

└──────────────────────────────────┘

│

▼

Audit & Observability

## 17.4 Authentication Model

EKIE supports multiple authentication methods:

**1. API Key Authentication**

Used for:

- Internal services

- External integrations

**2. OAuth 2.0 / OpenID Connect**

Used for:

- Enterprise SSO

- User login systems

**3. Service Identity Authentication**

Used for:

- Workers

- Internal services

- Orchestration engine

## 17.5 Authorization Model

EKIE uses a hybrid model:

**RBAC (Role-Based Access Control)**

Defines roles such as:

- Admin

- Engineer

- Data Scientist

- Viewer

- Service Worker

**ABAC (Attribute-Based Access Control)**

Access depends on attributes such as:

- Document classification

- Repository type

- Environment

- Region

- User department

## 17.6 Access Decision Flow

User Request

│

▼

Authentication Verified

│

▼

Role Evaluation (RBAC)

│

▼

Attribute Evaluation (ABAC)

│

▼

Policy Engine Decision

│

▼

Allow / Deny

## 17.7 Data Classification System

All documents and assets are classified.

**Classification Levels**

  -----------------------------------------------------------------------
  **Level**                      **Description**
  ------------------------------ ----------------------------------------
  Public                         Open data

  Internal                       Internal use only

  Confidential                   Restricted

  Highly Confidential            Strict access control

  Restricted                     Legal/compliance controlled
  -----------------------------------------------------------------------

**Classification Propagation**

Classification flows through:

Document

↓

Markdown

↓

Chunks

↓

Embeddings

↓

Vectors

No downgrade is allowed unless explicitly permitted.

## 17.8 Secrets Management

EKIE never stores secrets in:

- SQL Server

- File storage

- Logs

Instead, it uses:

- Azure Key Vault

- AWS Secrets Manager

- HashiCorp Vault

**Secret Types**

- API keys

- Database credentials

- Embedding provider keys

- Vector DB credentials

- Encryption keys

**Access Flow**

Service Request

│

▼

Secrets Manager

│

▼

Ephemeral Secret Injection

│

▼

Runtime Usage (No Persistence)

## 17.9 Encryption Model

EKIE enforces encryption at all layers:

**1. In Transit**

- TLS 1.2+

- Mutual TLS for internal services

**2. At Rest**

- AES-256 encryption

- Applied to:

  - Object storage

  - Logs

  - Temporary files

**3. Field-Level Encryption (Optional)**

Used for:

- Sensitive metadata

- PII fields

## 17.10 Audit System

Every action is recorded.

**Audited Events**

- Document ingestion

- Policy changes

- Workflow execution

- Chunk creation

- Embedding generation

- Vector publishing

- Access attempts

**Audit Record Structure**

{

\"event_id\": \"AUD-001\",

\"timestamp\": \"2026-07-01T10:15:00Z\",

\"actor\": \"service-account-1\",

\"action\": \"embedding_generated\",

\"resource\": \"chunk-123\",

\"result\": \"success\"

}

**Audit Properties**

- Immutable

- Append-only

- Tamper-resistant

- Long-term retention

## 17.11 Governance Controls

Governance ensures system compliance.

**Key Controls**

- Data retention policies

- Access restrictions

- Approval workflows

- Policy enforcement

- Data lineage tracking

## 17.12 Compliance Support

EKIE is designed to support:

- GDPR

- SOC 2

- ISO 27001

- HIPAA (optional extension)

- Internal enterprise compliance rules

## 17.13 Multi-Tenant Isolation (Future-Ready)

EKIE is designed for future multi-tenancy:

**Isolation Layers**

- Metadata isolation (SQL schema)

- Storage isolation (bucket-level)

- Vector isolation (collection-level)

- Policy isolation (tenant-specific policies)

## 17.14 Security in Each Framework

Security is embedded everywhere:

**Workflow Engine**

- Task-level authorization

- Worker identity validation

**Chunking Engine**

- Content classification enforcement

- Sensitive data filtering

**Embedding Engine**

- Model access control

- Provider restriction policies

**Publishing Engine**

- Collection-level access control

- Write permission validation

## 17.15 Threat Model

EKIE protects against:

  -----------------------------------------------------------------------
  **Threat**                      **Mitigation**
  ------------------------------- ---------------------------------------
  Unauthorized access             RBAC + ABAC

  Data leakage                    Encryption + classification

  Secret exposure                 Vault integration

  Injection attacks               Input validation

  Cross-tenant leakage            Isolation layers

  Replay attacks                  Workflow validation
  -----------------------------------------------------------------------

## 17.16 Security Monitoring

Security events are monitored via Observability Framework:

- Failed login attempts

- Unauthorized access attempts

- Policy violations

- Suspicious API usage

- Token abuse patterns

## 17.17 Incident Response Flow

Detection

↓

Alert Trigger

↓

Audit Analysis

↓

Containment

↓

Remediation

↓

Postmortem Logging

## 17.18 Design Decisions (ADRs)

**ADR-049: Zero Trust Architecture**

**Decision**

No internal or external service is trusted by default.

**Rationale**

Reduces attack surface and ensures strict verification at every layer.

**ADR-050: External Secrets Management**

**Decision**

All secrets must be stored in dedicated external vault systems.

**Rationale**

Prevents accidental leakage through logs, metadata, or storage systems.

**ADR-051: Policy-Driven Security**

**Decision**

All access control decisions are evaluated via the Policy Engine.

**Rationale**

Ensures centralized governance and consistency across the platform.

**ADR-052: Immutable Audit Logs**

**Decision**

Audit logs must be append-only and immutable.

**Rationale**

Ensures compliance, traceability, and forensic capability.

## 17.19 Future Enhancements

- AI-based anomaly detection for security events

- Automated compliance reporting

- Real-time threat detection

- Fine-grained field-level ACL system

- Blockchain-based audit verification (optional)

- Adaptive security policies based on behavior

## 17.20 Summary

The Security & Governance Framework ensures EKIE operates as a **trusted
enterprise-grade ingestion system**.

It enforces:

- Authentication

- Authorization

- Classification

- Encryption

- Auditing

- Compliance

across every stage of the ingestion pipeline.

This guarantees that EKIE is not only functional, but also **secure,
auditable, and enterprise-compliant by design**.

This will define:

- How new chunking strategies are added

- How embedding providers are integrated

- How custom parsers are plugged in

- How workflows are extended

- How enterprises build custom EKIE modules without modifying core code

This will finalize EKIE's transformation into a **fully extensible
platform ecosystem**.


### 17.X Cross-System GDPR & DSAR Purge Integration

**Integration Contract:** To comply with Data Subject Access Requests (DSAR), EKIE must subscribe to the global `EnterpriseDataPurgeEvent` topic on the Event Bus. When a user requests deletion, EKIE must trace and hard-delete any personal documents, derived chunks, and vector embeddings owned by that user across the entire pipeline.


# Chapter 18 - Plugin & Extension SDK

**Version:** 1.0\
**Status:** Approved\
**Volume:** IV --- Extensibility & Ecosystem Architecture

## 18.1 Objective

The Plugin & Extension SDK transforms EKIE from a **closed ingestion
system** into an **extensible enterprise platform**.

It allows organizations to extend EKIE without modifying core code.

Everything in EKIE becomes pluggable:

- Chunking strategies

- Embedding providers

- Parsers

- Workflow tasks

- Storage adapters

- Policy evaluators

- Validation rules

This is the foundation of EKIE's ecosystem strategy.

## 18.2 Design Philosophy

The SDK follows five principles:

**Principle 1 --- Core is Stable, Extensions are Flexible**

Core frameworks never change for custom logic.

**Principle 2 --- Everything is a Plugin**

If behavior changes, it is a plugin.

**Principle 3 --- Plugins are Isolated**

Plugins cannot break core system stability.

**Principle 4 --- Versioned Compatibility**

Every plugin declares compatibility with EKIE versions.

**Principle 5 --- Secure Execution**

Plugins execute under strict sandboxed conditions.

## 18.3 High-Level Architecture

EKIE Core Engine

│

▼

Plugin Runtime Manager

│

┌──────────────┬──────────────┬──────────────┐

▼ ▼ ▼ ▼

Chunk Plugin Embed Plugin Parser Plugin Workflow Plugin

│ │ │ │

└──────────────┴──────────────┴──────────────┘

│

▼

Plugin Execution Layer

## 18.4 Plugin Categories

EKIE supports multiple plugin types.

**1. Chunking Plugins**

Used to define custom chunking logic.

Examples:

- Legal document chunking

- Code-aware chunking

- Financial statement chunking

- Domain-specific segmentation

**2. Embedding Plugins**

Used to integrate new embedding providers.

Examples:

- OpenAI embeddings

- Local BGE models

- Enterprise LLM embeddings

- Hybrid embedding systems

**3. Parser Plugins**

Used for file transformation.

Examples:

- PDF parser

- DOCX parser

- HTML parser

- OCR parser

- Email parser

**4. Workflow Plugins**

Used to extend ingestion pipeline.

Examples:

- Custom validation steps

- Human approval steps

- Data enrichment steps

- Compliance checks

**5. Storage Plugins**

Used to support new storage systems.

Examples:

- S3 adapter

- Azure Blob adapter

- MinIO adapter

- On-prem file system

**6. Policy Plugins**

Used to extend policy evaluation logic.

Examples:

- Cost-aware policies

- Region-based policies

- AI-assisted policies

## 18.5 Plugin Lifecycle

Each plugin follows a lifecycle:

Installed

↓

Validated

↓

Registered

↓

Active

↓

Executed

↓

Updated

↓

Retired

## 18.6 Plugin Interface Contract

All plugins implement a standard interface:

class EKIEPlugin:

def initialize(self, context):

pass

def execute(self, input_data):

pass

def validate(self):

pass

def metadata(self):

pass

## 18.7 Plugin Manifest

Every plugin includes a manifest file:

name: custom_chunking_plugin

version: 1.0.0

type: chunking

compatible_ekie_versions:

\- 1.x

author: enterprise-team

description: Domain-specific chunking strategy for legal docs

## 18.8 Plugin Execution Model

Plugins execute inside a controlled runtime:

Core Engine

│

▼

Sandbox Executor

│

▼

Plugin Runtime

│

▼

Output Validation Layer

## 18.9 Sandboxing Strategy

Plugins are isolated using:

- Process isolation (recommended)

- Container isolation (Kubernetes)

- Restricted file system access

- No direct DB access

- Controlled API access only

## 18.10 Plugin Registry

The Plugin Registry stores:

- Plugin metadata

- Versions

- Compatibility matrix

- Security approval status

- Usage statistics

Stored in Control Plane.

## 18.11 Dependency Management

Plugins can depend on:

- Core EKIE APIs

- Other plugins (limited)

- External libraries (restricted whitelist)

Circular dependencies are forbidden.

## 18.12 Plugin Communication

Plugins communicate via:

- Input/output contracts

- Event bus (recommended)

- Shared context object

Direct coupling is avoided.

## 18.13 Security Controls

Plugins must pass:

- Static validation

- Signature verification

- Security sandbox checks

- Execution permission checks

Untrusted plugins are rejected.

## 18.14 Versioning Strategy

Plugins follow semantic versioning:

MAJOR.MINOR.PATCH

Compatibility is enforced:

- Major mismatch → blocked

- Minor mismatch → warning

- Patch mismatch → allowed

## 18.15 Hot Reload Capability

EKIE supports runtime plugin updates:

- New versions can be deployed without system restart

- Old versions remain active for running workflows

- Gradual migration supported

## 18.16 Plugin Marketplace (Future)

EKIE is designed for an ecosystem:

- Internal enterprise marketplace

- Private plugin registries

- Third-party extensions (future)

## 18.17 Observability for Plugins

All plugin activity is tracked:

- Execution time

- Failure rate

- Input/output size

- Resource usage

- Error logs

Plugins are fully observable via Chapter 16 framework.

## 18.18 Failure Handling

If a plugin fails:

Failure Detected

↓

Retry (Policy Driven)

↓

Fallback Plugin (Optional)

↓

Workflow Failure Handling

## 18.19 Performance Optimization

- Lazy loading of plugins

- Cached plugin execution

- Pre-warmed runtimes

- Parallel plugin execution

## 18.20 Design Decisions (ADRs)

**ADR-053: Plugin-Based Extensibility**

**Decision**

All extensibility must be implemented via plugins.

**Rationale**

Ensures core system stability and long-term maintainability.

**ADR-054: Sandboxed Plugin Execution**

**Decision**

Plugins must execute in isolated environments.

**Rationale**

Prevents system compromise and ensures safe execution.

**ADR-055: Versioned Plugin Compatibility**

**Decision**

Plugins must declare compatibility with EKIE versions.

**Rationale**

Prevents runtime failures due to version mismatch.

**ADR-056: Controlled Plugin Registry**

**Decision**

All plugins must be registered and validated before execution.

**Rationale**

Ensures governance and security compliance.

## 18.21 Future Extensions

- AI-generated plugins

- Auto-plugin optimization

- Plugin recommendation engine

- Marketplace monetization

- Cross-tenant plugin sharing

- Self-healing plugin system

## 18.22 Summary

The Plugin & Extension SDK transforms EKIE into a **fully extensible
enterprise platform**.

It ensures:

- No core modification for customization

- Secure plugin execution

- Versioned compatibility

- Ecosystem scalability

- Enterprise governance

This layer enables EKIE to evolve without architectural rewrites.

This will define:

- Kubernetes-based deployment model

- Microservices architecture mapping

- Scaling strategy for ingestion workloads

- High availability design

- Multi-region deployment

- CI/CD pipeline architecture

- Environment separation (dev/stage/prod)

This chapter will move EKIE from **logical architecture → production
infrastructure design**.

# Chapter 19 - Deployment Architecture

**Version:** 1.0\
**Status:** Approved\
**Volume:** V --- Production Infrastructure & Operations

## 19.1 Objective

The Deployment Architecture defines how EKIE is:

- Packaged

- Deployed

- Scaled

- Updated

- Isolated

- Operated in production environments

It bridges the gap between:

**Logical system design → Real-world infrastructure execution**

This chapter ensures EKIE runs reliably at enterprise scale across cloud
and hybrid environments.

## 19.2 Design Philosophy

EKIE deployment is based on five principles:

**Principle 1 --- Cloud-Native First**

EKIE is designed for Kubernetes-based environments.

**Principle 2 --- Stateless Compute**

All runtime services are stateless.

State is externalized to:

- SQL Server (Control Plane)

- Object Storage

- Vector DB

- Observability Stack

**Principle 3 --- Horizontal Scaling**

Every component must scale horizontally without redesign.

**Principle 4 --- Environment Isolation**

Dev, staging, and production are strictly isolated.

**Principle 5 --- Declarative Deployment**

All infrastructure is defined via declarative manifests.

## 19.3 High-Level Deployment Architecture

Internet / Enterprise Network

│

▼

API Gateway Layer

│

┌───────────────────────────┼───────────────────────────┐

▼ ▼ ▼

Auth Service Workflow API Admin Console

│ │ │

└──────────────┬────────────┴────────────┬─────────────┘

▼ ▼

Kubernetes Cluster (EKIE Core)

│

┌───────────────────┼────────────────────┐

▼ ▼ ▼

Workflow Engine Chunking Engine Embedding Engine

│ │ │

└──────────────┬────┴────┬─────────────┘

▼ ▼

Storage Layer Vector DB Layer

(SQL, Object Storage) (Qdrant, etc.)

▼

Observability Stack

## 19.4 Core Deployment Units

EKIE is deployed as microservices.

**1. API Layer Services**

- Ingestion API

- Admin API

- Policy API

- Plugin API

**2. Core Processing Services**

- Workflow Engine Service

- Chunking Service

- Embedding Service

- Publishing Service

- Parser Service

**3. Control Plane Services**

- SQL Server Cluster

- Migration Service

- Metadata API

**4. Storage Services**

- Object Storage (S3 / Azure Blob / MinIO)

- Vector Database (Qdrant)

- Cache Layer (Redis)

**5. Observability Services**

- Prometheus

- Grafana

- ELK / OpenSearch

- Jaeger / Tempo

## 19.5 Kubernetes Architecture

EKIE runs entirely on Kubernetes.

**Namespace Strategy**

ekie-dev

ekie-staging

ekie-prod

ekie-system

ekie-observability

**Deployment Types**

  -----------------------------------------------------------------------
  **Component**                   **Type**
  ------------------------------- ---------------------------------------
  Workflow Engine                 Deployment

  Chunk Workers                   Horizontal Pod Autoscaler

  Embedding Workers               Deployment

  API Gateway                     Deployment

  SQL Server                      StatefulSet

  Qdrant                          StatefulSet
  -----------------------------------------------------------------------

**Scaling Strategy**

- CPU-based scaling for parsing

- Queue-depth-based scaling for workflows

- Custom metrics for embeddings

- Event-driven autoscaling (KEDA)

## 19.6 CI/CD Pipeline

EKIE uses a multi-stage CI/CD pipeline.

Code Commit

↓

Build Pipeline

↓

Unit Tests

↓

Integration Tests

↓

Security Scan

↓

Container Build

↓

Artifact Registry

↓

Staging Deployment

↓

Smoke Tests

↓

Production Deployment

**Deployment Strategies**

- Blue-Green Deployment

- Canary Deployment

- Rolling Updates

## 19.7 Environment Strategy

EKIE uses three primary environments:

**Development**

- Local clusters

- Mocked dependencies

- Fast iteration

**Staging**

- Production-like data

- Full pipeline testing

- Performance validation

**Production**

- Fully secured

- Multi-node clusters

- High availability enabled

## 19.8 High Availability Design

EKIE ensures zero single point of failure.

**Redundancy Model**

  -----------------------------------------------------------------------
  **Layer**                          **Strategy**
  ---------------------------------- ------------------------------------
  API Layer                          Multi-replica

  Workflow Engine                    Active-active

  SQL Server                         Always On Cluster

  Vector DB                          Sharded cluster

  Storage                            Replicated buckets
  -----------------------------------------------------------------------

**Failover Strategy**

Node Failure

↓

Kubernetes Reschedule

↓

Worker Reassignment

↓

Workflow Resume from Checkpoint

## 19.9 Multi-Region Deployment (Future-Ready)

EKIE supports global scaling.

**Architecture**

- Region A (Primary)

- Region B (Failover)

- Region C (Read-only / Analytics)

**Data Replication**

- SQL Server replication

- Object storage replication

- Vector DB partial sync

## 19.10 Resource Management

EKIE enforces strict resource controls:

- CPU limits

- Memory limits

- GPU allocation (embedding workloads)

- Queue-based throttling

## 19.11 Configuration Management

Deployment configuration is managed via:

- Helm charts

- Kubernetes manifests

- Policy Engine integration

- Environment variables

- Secrets manager

## 19.12 Security in Deployment

Security is enforced at infrastructure level:

- Network policies

- Pod security policies

- TLS everywhere

- Secret injection only

- RBAC in Kubernetes

- Image signing (optional)

## 19.13 Observability in Deployment

Every deployment includes:

- Central logging agents

- Metrics exporters

- Distributed tracing agents

- Node-level monitoring

## 19.14 Disaster Recovery

EKIE supports full disaster recovery:

**Recovery Model**

  -----------------------------------------------------------------------
  **Failure Type**               **Recovery Strategy**
  ------------------------------ ----------------------------------------
  Pod Failure                    Auto-restart

  Node Failure                   Reschedule

  Cluster Failure                Failover Region

  DB Failure                     Restore from backup

  Storage Failure                Replication recovery
  -----------------------------------------------------------------------

**Recovery Time Objectives**

- API layer: \< 1 min

- Workflow engine: \< 5 min

- Full cluster: \< 15 min

## 19.15 Deployment Security Model

- Image scanning before deployment

- Signed containers

- Runtime security monitoring

- Secrets never exposed in logs

- Policy-driven deployment approvals

## 19.16 Cost Optimization Strategy

EKIE optimizes cost using:

- Autoscaling workers

- Spot instances for batch processing

- Idle pod termination

- Tiered storage

- Embedding batching

## 19.17 Design Decisions (ADRs)

**ADR-057: Kubernetes-Native Architecture**

**Decision**

All EKIE components must run on Kubernetes.

**Rationale**

Ensures scalability, portability, and cloud independence.

**ADR-058: Stateless Microservices**

**Decision**

All services must remain stateless.

**Rationale**

Enables horizontal scaling and fault tolerance.

**ADR-059: Event-Driven Scaling**

**Decision**

Scaling must be driven by queue depth and metrics.

**Rationale**

Ensures efficient resource utilization.

**ADR-060: Multi-Environment Isolation**

**Decision**

Each environment must be fully isolated.

**Rationale**

Prevents cross-environment contamination and ensures safety.

## 19.18 Future Enhancements

- Serverless execution mode

- Edge deployment support

- Hybrid cloud orchestration

- GPU scheduling optimization

- Self-healing clusters

- AI-driven scaling decisions

## 19.19 Summary

The Deployment Architecture transforms EKIE into a **production-grade
distributed system** capable of:

- Scaling horizontally

- Running in multiple environments

- Recovering from failures automatically

- Operating across regions

- Maintaining security and governance at infrastructure level

This completes the transition from **system design → real-world
deployable platform**.

This will define:

- Unit testing strategy for ingestion pipeline

- Integration testing across frameworks

- Data validation rules

- Chunk quality validation

- Embedding correctness validation

- Workflow simulation testing

- Load testing & stress testing

- Regression testing for plugins

This chapter ensures EKIE is **correct, reliable, and production-safe
before scaling further**.

# Chapter 20 - Testing & Validation Strategy

**Version:** 1.0\
**Status:** Approved\
**Volume:** VI --- Reliability, Quality & Assurance Layer

## 20.1 Objective

The Testing & Validation Strategy ensures that EKIE is:

- Functionally correct

- Deterministic

- Stable under load

- Safe for production deployment

- Consistent across versions

- Reliable across plugin extensions

This chapter defines how we ensure:

Every ingestion result is **correct, reproducible, and verifiable**

## 20.2 Design Philosophy

EKIE testing is built on five principles:

**Principle 1 --- Every Layer is Testable**

From repository sync → vector publishing.

**Principle 2 --- Deterministic Outputs**

Same input + same policy → same output.

**Principle 3 --- Pipeline-Level Validation**

Not just unit tests---full ingestion validation.

**Principle 4 --- Data-Centric Testing**

We test outputs, not just code.

**Principle 5 --- Continuous Validation**

Testing is part of runtime, not only CI/CD.

## 20.3 Testing Layers

Unit Tests

↓

Component Tests

↓

Integration Tests

↓

Pipeline Tests

↓

System Tests

↓

Production Validation

## 20.4 Unit Testing Layer

Focus:

- Individual functions

- Parsing logic

- Chunk generation rules

- Policy evaluation logic

**Example Tests**

- Markdown parser correctness

- Chunk splitter behavior

- Embedding request builder

- Policy resolver logic

**Goal**

Ensure each module behaves correctly in isolation.

## 20.5 Component Testing Layer

Focus:

- Single service validation

- Workflow engine correctness

- Chunking service behavior

- Embedding service correctness

**Example**

Input Document → Chunking Service → Expected Chunk Structure

## 20.6 Integration Testing Layer

Focus:

- Interaction between services

- Control Plane consistency

- Storage + workflow coordination

- Policy engine integration

**Example Flow**

Repository Sync

↓

Markdown Generation

↓

Chunking

↓

Embedding

↓

Vector Publishing

Validation ensures:

- No data loss

- Correct transitions

- Proper metadata updates

## 20.7 Pipeline Testing (Core EKIE Testing Layer)

This is the MOST important testing layer.

It validates full ingestion flow.

**Pipeline Test Flow**

Input File

↓

Ingestion Engine

↓

Markdown

↓

Chunks

↓

Embeddings

↓

Vector DB

**Validations**

- Chunk completeness

- No missing sections

- Token consistency

- Embedding shape correctness

- Vector alignment accuracy

## 20.8 System Testing Layer

Focus:

- Full EKIE system behavior

- Multi-repository ingestion

- Multi-worker execution

- Failure recovery scenarios

**Example**

- 10,000 documents ingestion simulation

- Worker crash recovery validation

- Queue overflow handling

## 20.9 Data Validation Strategy

EKIE validates data at every stage.

**Validation Points**

  -----------------------------------------------------------------------
  **Stage**                   **Validation**
  --------------------------- -------------------------------------------
  Markdown                    structure correctness

  Chunking                    completeness

  Embedding                   dimensionality

  Vector DB                   persistence

  Metadata                    consistency
  -----------------------------------------------------------------------

**Validation Rules**

- No empty chunks

- No orphan embeddings

- No missing metadata links

- No broken lineage chains

## 20.10 Chunk Quality Validation

Chunks are evaluated using:

- Token distribution balance

- Semantic coherence scoring

- Boundary correctness

- Overlap correctness

**Example Rule**

Chunk must not exceed max token limit defined by policy

## 20.11 Embedding Validation

Ensures:

- Vector dimensional correctness

- Model consistency

- Batch correctness

- Cost consistency

- Latency thresholds

**Example Checks**

- cosine similarity sanity

- zero-vector detection

- drift detection across models

## 20.12 Workflow Validation

Ensures:

- All tasks executed in order

- Retry logic correctness

- Checkpoint recovery works

- No duplicate executions

**Example Scenario**

Simulate worker crash at embedding stage → ensure resume from checkpoint

## 20.13 Plugin Validation System

All plugins must pass validation before activation.

**Checks**

- Interface compliance

- Sandbox execution test

- Output validation

- Security scan

- Performance test

**Plugin Test Flow**

Install Plugin

↓

Run Sandbox Tests

↓

Validate Output Schema

↓

Security Approval

↓

Activate

## 20.14 Load Testing Strategy

EKIE must support enterprise-scale ingestion.

**Load Scenarios**

- 1K documents/min

- 10K documents/min (stress)

- Multi-repository ingestion

- Parallel workflow execution

**Metrics**

- Queue saturation

- Worker utilization

- Latency distribution

- Failure rates

## 20.15 Stress Testing Strategy

Purpose:

- Identify system breaking points

- Validate recovery behavior

**Stress Scenarios**

- Sudden ingestion spike

- Worker failure cascade

- Vector DB overload

- Storage latency spikes

## 20.16 Regression Testing

Ensures:

- New updates do not break ingestion flow

- Policy changes do not alter outputs unexpectedly

- Plugin updates remain compatible

**Regression Scope**

- Chunk structure stability

- Embedding consistency

- Workflow integrity

## 20.17 Test Data Strategy

EKIE uses:

- Synthetic documents

- Real enterprise documents (sanitized)

- Edge-case documents (corrupt, large, nested)

## 20.18 Continuous Testing (Runtime Validation)

Unlike traditional systems, EKIE performs:

- Live validation of workflows

- Real-time chunk validation

- Embedding sanity checks during execution

## 20.19 Failure Simulation Framework

EKIE simulates:

- Node failure

- Network latency

- API failures

- Storage downtime

Used to validate resilience.

## 20.20 Observability Integration

Testing system integrates with Chapter 16:

- Test logs

- Test metrics

- Test traces

- Failure reports

## 20.21 Design Decisions (ADRs)

**ADR-061: Pipeline-Level Testing Requirement**

**Decision**

Full ingestion pipeline must be testable end-to-end.

**Rationale**

Ensures system correctness beyond isolated components.

**ADR-062: Data-Centric Validation**

**Decision**

Validation must focus on output data correctness, not just code
execution.

**Rationale**

Ensures real-world reliability of ingestion results.

**ADR-063: Continuous Runtime Testing**

**Decision**

Validation must occur during runtime execution, not only CI/CD.

**Rationale**

Detects issues in production-like conditions early.

**ADR-064: Plugin Pre-Activation Testing**

**Decision**

No plugin can be activated without full sandbox validation.

**Rationale**

Ensures system safety and stability.

## 20.22 Future Enhancements

- AI-based test generation

- Self-healing test failures

- Predictive failure detection

- Automated quality scoring of ingestion outputs

- Continuous fuzz testing of ingestion pipeline

## 20.23 Summary

The Testing & Validation Strategy ensures EKIE is not just
functional---but **provably correct, reproducible, and
enterprise-safe**.

It validates:

- Data correctness

- Pipeline integrity

- Workflow reliability

- Plugin safety

- System scalability

This ensures EKIE can safely operate in production environments at
scale.

This will define:

- Full system recovery strategy

- Backup and restore architecture

- Workflow recovery guarantees

- Control Plane restoration

- Storage reconstruction

- Multi-region failover design

- RPO/RTO guarantees

- Failure blast radius containment

This chapter ensures EKIE is **resilient even under catastrophic system
failures**.

# Chapter 21 - Disaster Recovery & Business Continuity

**Version:** 1.0\
**Status:** Approved\
**Volume:** VI --- Reliability, Resilience & Enterprise Continuity

## 21.1 Objective

The Disaster Recovery (DR) & Business Continuity framework ensures that
EKIE can:

- Recover from catastrophic failures

- Restore full ingestion capability

- Preserve metadata integrity

- Rebuild workflows without data loss

- Maintain enterprise SLAs under extreme conditions

This chapter defines:

**How EKIE survives system-wide failures and continues operating**

## 21.2 Design Philosophy

EKIE disaster recovery is based on five principles:

**Principle 1 --- Nothing is Irrecoverable**

Every state is either:

- Persisted

- Reconstructible

- Recomputable

**Principle 2 --- Metadata is the Source of Truth**

Control Plane (SQL Server) is always authoritative.

**Principle 3 --- Storage is Replaceable**

Object storage and vector DBs can be rebuilt.

**Principle 4 --- Workflows are Replayable**

Every ingestion workflow can be re-executed safely.

**Principle 5 --- Failures are Expected**

System design assumes failure as normal, not exceptional.

## 21.3 Failure Classification Model

EKIE classifies failures into layers:

**1. Component Failure**

- Worker crash

- API failure

- Plugin failure

**2. Service Failure**

- Workflow engine outage

- Chunking engine failure

- Embedding service failure

**3. Infrastructure Failure**

- Node failure

- Cluster failure

- Storage failure

**4. Data Layer Failure**

- Corrupt metadata

- Partial ingestion failure

- Broken lineage

**5. Regional Failure (Worst Case)**

- Entire region outage

- Network isolation

- Cloud provider failure

## 21.4 Recovery Architecture Overview

Failure Detected

│

▼

Observability System Alerts

│

▼

Disaster Recovery Controller

│

┌───────────────┼────────────────┐

▼ ▼ ▼

Control Plane Storage Layer Workflow Engine

(SQL Restore) (Rebuild) (Replay)

│ │ │

└───────────────┴────────────────┘

▼

EKIE System Restored

## 21.5 Recovery Pillars

**Pillar 1 --- Control Plane Recovery**

SQL Server restoration ensures:

- Workflow state recovery

- Document lineage recovery

- Policy restoration

- Metadata reconstruction

**Pillar 2 --- Storage Recovery**

Object storage recovery includes:

- Markdown files

- OCR outputs

- Chunk assets

- Validation artifacts

**Pillar 3 --- Vector Recovery**

Vector DB recovery:

- Rebuild embeddings from chunks

- Restore collections

- Re-index metadata

**Pillar 4 --- Workflow Recovery**

Workflow engine recovery:

- Resume from checkpoints

- Re-execute incomplete tasks

- Skip completed tasks

**Pillar 5 --- Observability Recovery**

- Logs restored from archive

- Metrics rebuilt from time-series DB

- Traces re-linked via correlation IDs

## 21.6 Recovery Time Objectives (RTO)

  ----------------------------------------------------------------------
  **Component**                           **RTO**
  --------------------------------------- ------------------------------
  API Layer                               \< 1 minute

  Workflow Engine                         \< 5 minutes

  Control Plane                           \< 10 minutes

  Full System                             \< 30 minutes
  ----------------------------------------------------------------------

## 21.7 Recovery Point Objectives (RPO)

  -----------------------------------------------------------------------
  **Layer**                     **RPO**
  ----------------------------- -----------------------------------------
  Metadata                      \< 5 minutes

  Storage                       \< 15 minutes

  Vectors                       \< 1 hour

  Logs                          Near real-time
  -----------------------------------------------------------------------

## 21.8 Checkpoint-Based Recovery Model

Every workflow uses checkpoints:

Workflow Start

↓

Task 1 (Checkpoint)

↓

Task 2 (Checkpoint)

↓

Task 3 (Checkpoint)

↓

Completion

If failure occurs:

System Restored

↓

Load Last Checkpoint

↓

Resume Execution

## 21.9 Data Reconstruction Strategy

If data is lost:

**Step 1 --- Metadata Recovery**

- Restore SQL backup

- Validate workflow states

**Step 2 --- Asset Reconstruction**

- Rebuild markdown from source if needed

- Re-run parser plugins

**Step 3 --- Chunk Re-generation**

- Regenerate chunks from markdown

**Step 4 --- Embedding Re-computation**

- Re-run embedding pipeline

**Step 5 --- Vector Re-publishing**

- Push to vector DB again

## 21.10 Multi-Region Disaster Recovery

EKIE supports cross-region failover:

**Architecture**

Primary Region (Active)

│

▼

Replication Layer

│

▼

Secondary Region (Standby)

**Failover Types**

- Automatic failover

- Manual failover

- Partial service failover

## 21.11 Storage Resilience Model

  -----------------------------------------------------------------------
  **Storage Type**            **Recovery Strategy**
  --------------------------- -------------------------------------------
  SQL Server                  Full replication + backups

  Object Storage              Multi-region replication

  Vector DB                   Rebuild from embeddings

  Cache                       Reconstructable

  Logs                        Append-only archive
  -----------------------------------------------------------------------

## 21.12 Workflow Replay Engine

One of EKIE's most powerful capabilities:

**Replay Logic**

Identify Failed Workflow

↓

Check Completed Tasks

↓

Skip Completed Steps

↓

Re-run Remaining Steps

↓

Restore Completion State

## 21.13 Failure Blast Radius Control

EKIE isolates failures:

- Per workflow isolation

- Per repository isolation

- Per worker pool isolation

- Per queue isolation

This ensures:

No single failure can collapse the entire system

## 21.14 Backup Strategy

**Types of Backups**

**1. Full Backup**

- Weekly system snapshot

**2. Incremental Backup**

- Every few minutes for metadata

**3. Continuous Log Backup**

- Transaction logs for SQL Server

**4. Object Storage Replication**

- Near real-time duplication

## 21.15 Disaster Recovery Controller

A dedicated system component:

- Detects failure

- Initiates recovery workflows

- Coordinates restoration steps

- Validates system health

## 21.16 Health Validation After Recovery

After recovery:

- Workflow integrity check

- Metadata consistency check

- Vector consistency validation

- Storage verification

- Observability reconciliation

## 21.17 Incident Response Flow

Alert Triggered

↓

Severity Classification

↓

Auto-Mitigation Attempt

↓

DR Activation

↓

System Restoration

↓

Post-Incident Audit

## 21.18 Design Decisions (ADRs)

**ADR-065: Workflow Replay as Primary Recovery Mechanism**

**Decision**

All ingestion recovery must rely on workflow replay.

**Rationale**

Ensures deterministic reconstruction of system state.

**ADR-066: Metadata-First Recovery Strategy**

**Decision**

Control Plane is the first system restored during disaster recovery.

**Rationale**

All other systems depend on metadata integrity.

**ADR-067: Multi-Layer Backup Strategy**

**Decision**

Each storage layer must have independent backup and replication.

**Rationale**

Prevents correlated failure across systems.

**ADR-068: Checkpoint-Based Execution Guarantee**

**Decision**

Every workflow must support checkpoint-based resumption.

**Rationale**

Minimizes recomputation and reduces recovery time.

## 21.19 Future Enhancements

- AI-driven failure prediction

- Automatic failover orchestration

- Self-healing distributed workflows

- Cross-cloud DR activation

- Real-time recovery simulation

- Chaos engineering integration

## 21.20 Summary

The Disaster Recovery & Business Continuity framework ensures EKIE is:

- Resilient under catastrophic failure

- Capable of full system reconstruction

- Safe under partial or total outages

- Deterministic in recovery behavior

- Enterprise-grade in continuity guarantees

It transforms EKIE from a distributed system into a **self-recovering
enterprise ingestion platform**.

This will define:

- Day-to-day system operations

- Monitoring playbooks

- Incident response procedures

- Scaling operations

- Performance tuning guides

- Cost optimization workflows

- Maintenance routines

- Upgrade strategies

This chapter completes EKIE as a **fully production-operable enterprise
platform**.

# Chapter 22 - Operations Runbook & Production Management

**Version:** 1.0\
**Status:** Approved\
**Volume:** VII --- Operational Excellence Layer

## 22.1 Objective

The Operations Runbook defines how EKIE is **operated in real production
environments on a daily basis**.

While previous chapters define architecture and resilience, this chapter
defines:

**How engineers actually run, monitor, maintain, and evolve EKIE in
production**

It is the final layer that converts EKIE from a system design into an
**operational enterprise platform**.

## 22.2 Design Philosophy

EKIE operations follow five principles:

**Principle 1 --- Everything is Observable**

No hidden system behavior.

**Principle 2 --- Everything is Repeatable**

Operations must be reproducible across environments.

**Principle 3 --- Everything is Automated First**

Manual intervention is fallback, not default.

**Principle 4 --- Safe Failure Handling**

Every operation assumes failure will occur.

**Principle 5 --- Low-Disruption Maintenance**

No downtime for upgrades or fixes.

## 22.3 Daily Operations Overview

A production EKIE system runs continuously:

Repositories → Ingestion → Chunking → Embedding → Publishing →
Monitoring

Operators manage:

- System health

- Workflow queues

- Worker scaling

- Failures

- Performance

- Costs

## 22.4 System Health Dashboard

The primary operational view includes:

**Key Indicators**

- Active workflows

- Queue depth

- Worker utilization

- Failure rate

- Latency per stage

- Embedding cost

- Vector DB health

**Health States**

  -----------------------------------------------------------------------
  **State**            **Meaning**
  -------------------- --------------------------------------------------
  Green                Normal operation

  Yellow               Degraded performance

  Red                  System failure
  -----------------------------------------------------------------------

## 22.5 Workflow Operations

**Monitoring Workflows**

Operators track:

- Running workflows

- Stuck workflows

- Failed workflows

- Long-running tasks

**Workflow Intervention**

Actions allowed:

- Pause workflow

- Resume workflow

- Retry failed tasks

- Cancel workflow

- Replay workflow

**Example Scenario**

Embedding Failure Detected

↓

Retry Policy Triggered

↓

If failure persists → Switch Model

↓

Resume Workflow

## 22.6 Queue Management Operations

Queues are central to EKIE execution.

**Monitoring Metrics**

- Queue depth

- Processing rate

- Worker lag

**Operational Actions**

- Scale workers

- Pause queue

- Prioritize queue

- Drain queue

**Bottleneck Handling**

Queue Backlog Detected

↓

Auto Scaling Triggered

↓

Worker Pool Increased

↓

Backlog Cleared

## 22.7 Worker Management

Workers execute all ingestion tasks.

**Worker States**

- Active

- Idle

- Overloaded

- Failed

**Scaling Operations**

- Horizontal scaling via Kubernetes

- Auto-scaling based on queue metrics

- Manual override scaling

**Worker Failure Handling**

Worker Crash

↓

Kubernetes Reschedules

↓

Workflow Reassigns Task

## 22.8 Embedding Cost Control Operations

Embedding is a major cost driver.

**Monitoring**

- Cost per 1K tokens

- Daily embedding cost

- Model usage distribution

**Cost Optimization Actions**

- Switch embedding models

- Reduce chunk size

- Batch requests

- Enable caching

## 22.9 Storage Operations

**Object Storage Operations**

- Bucket monitoring

- Storage growth tracking

- Lifecycle policy enforcement

**Vector DB Operations**

- Index health checks

- Latency monitoring

- Collection scaling

- Reindex operations

**SQL Control Plane Operations**

- Query performance tuning

- Index optimization

- Backup validation

- Failover checks

## 22.10 Incident Management

**Incident Lifecycle**

Detection

↓

Classification

↓

Mitigation

↓

Resolution

↓

Postmortem

**Severity Levels**

  -----------------------------------------------------------------------
  **Level**              **Description**
  ---------------------- ------------------------------------------------
  SEV-1                  System down

  SEV-2                  Major degradation

  SEV-3                  Partial impact

  SEV-4                  Minor issue
  -----------------------------------------------------------------------

**Response Actions**

- Restart services

- Replay workflows

- Scale workers

- Failover region

## 22.11 Deployment Operations

**Release Process**

Code → Build → Test → Staging → Canary → Production

**Deployment Types**

- Rolling updates

- Blue-green deployment

- Canary rollout

**Rollback Strategy**

- Instant rollback to previous version

- Policy rollback supported

- Plugin rollback supported

## 22.12 Performance Tuning Operations

Operators tune:

- Chunk size policies

- Embedding batch size

- Worker concurrency

- Queue priorities

**Optimization Loop**

Monitor → Identify Bottleneck → Adjust Policy → Validate → Deploy

## 22.13 Cost Optimization Operations

Key strategies:

- Autoscaling workers

- Spot instance usage

- Cold storage for old data

- Embedding caching

- Batch processing

## 22.14 Maintenance Operations

**Routine Tasks**

- Index rebuilding

- Log cleanup

- Storage compaction

- Policy updates

- Plugin updates

**Scheduled Maintenance Window**

- Rolling maintenance preferred

- No full downtime required

## 22.15 Backup Operations

**Validation**

- Backup integrity checks

- Restore simulations

- Cross-region backup verification

**Backup Types**

- Metadata backups

- Storage snapshots

- Vector DB snapshots

## 22.16 Security Operations

Operators monitor:

- Unauthorized access attempts

- API abuse

- Policy violations

- Secret leaks

**Security Response**

Threat Detected

↓

Block Request

↓

Audit Logging

↓

Alert Security Team

## 22.17 Scaling Operations

**Vertical Scaling**

- Increase compute resources per node

**Horizontal Scaling**

- Add worker pods

- Expand queues

- Increase embedding capacity

**Auto-Scaling Triggers**

- Queue depth

- CPU utilization

- Latency thresholds

## 22.18 Upgrade Operations

**Safe Upgrade Model**

Deploy New Version

↓

Run Parallel Execution

↓

Compare Outputs

↓

Switch Traffic

**Zero Downtime Upgrades**

- Supported for all services

- Workflow continuity guaranteed

## 22.19 Operational Metrics

Key KPIs:

- Ingestion throughput

- Average workflow time

- Failure rate

- Cost per document

- Queue latency

- Recovery time

## 22.20 Operational Automation

EKIE supports automation for:

- Auto-scaling

- Auto-retry

- Auto-healing

- Auto-recovery

- Auto-failover

## 22.21 Design Decisions (ADRs)

**ADR-069: Operations Must Be Fully Observable**

**Decision**

Every operational action must be tracked via observability framework.

**Rationale**

Ensures full transparency and debugging capability.

**ADR-070: Zero Downtime Operations**

**Decision**

All maintenance and upgrades must avoid system downtime.

**Rationale**

Required for enterprise SLA compliance.

**ADR-071: Automation First Operations Model**

**Decision**

All operational tasks must default to automation.

**Rationale**

Reduces human error and operational cost.

**ADR-072: Replay-Based Recovery Operations**

**Decision**

All failed workflows must be recovered via replay.

**Rationale**

Ensures deterministic recovery and consistency.

## 22.22 Future Enhancements

- AI-driven operations assistant

- Predictive scaling engine

- Self-healing infrastructure loops

- Autonomous cost optimization

- Fully autonomous incident resolution

## 22.23 Final Summary

The Operations Runbook completes EKIE as a **fully production-operable
enterprise system**.

It ensures:

- Continuous operation

- Predictable maintenance

- Safe failure handling

- Automated scaling

- Controlled deployments

- Enterprise-grade reliability

EKIE is now not just an architecture---it is a **fully operational
platform blueprint**.

**🏁 Final System Summary --- EKIE Ingestion Platform (Complete)**

Across all chapters, EKIE now includes:

**Core Systems**

- Workflow Orchestration

- Control Plane (SQL Metadata Brain)

- Storage Architecture

- Policy Engine

**Runtime Systems**

- Observability

- Security & Governance

- Plugin SDK

**Infrastructure**

- Kubernetes Deployment

- CI/CD Pipeline

- Multi-region DR

**Reliability**

- Testing Framework

- Disaster Recovery

- Business Continuity

**Operations**

- Full production runbooks

- Scaling and maintenance strategy

- Incident management

**🎯 Final Principal Architect Statement**

EKIE is now a:

**Fully enterprise-grade, policy-driven, observable, extensible,
self-healing ingestion platform with deterministic workflow execution
and complete operational governance.**

If you want next step, we can now:

1.   Convert this into **real implementation roadmap (week-by-week build
    plan)**

2.  Or  generate **actual codebase structure (repo, services, folders,
    APIs)**

3.  Or  build **Step 1: Ingestion Engine MVP (production-ready code)**

Below is your **real implementation roadmap (week-by-week build plan)**
to turn the EKIE ingestion architecture into a working production
system.

This is intentionally structured like a **buildable engineering
execution plan**, not theory.

**🚀 EKIE Ingestion Engine --- Implementation Roadmap (Week-by-Week)**

**🧭 Scope Reminder (What we are building first)**

We are ONLY building:

- Ingestion Engine (core focus)

- File detection + sync system

- Markdown preprocessing layer

- Chunking engine

- Embedding pipeline

- Vector DB publishing (Qdrant / similar)

- Observability + control plane basics

❌ NOT included yet:

- Retrieval system

- Chat system

**🟢 PHASE 0 --- Foundation Setup (Week 1)**

**Week 1 --- Project Bootstrap + System Skeleton**

**🎯 Goal:**

Create a working repo + service skeleton + basic ingestion flow shell.

**Deliverables:**

- Monorepo setup

- Base folder architecture

- Docker environment

- SQL Server schema (basic metadata tables)

- Initial API service skeleton

**Tasks:**

- Setup repo structure:

  - ekie-core/

  - services/

  - workflow-engine/

  - chunking-service/

  - embedding-service/

  - control-plane/

- Setup:

  - FastAPI (or similar)

  - Docker compose

  - Qdrant local instance

  - PostgreSQL / SQL Server schema

- Define:

  - Document table

  - Workflow table

  - File registry table

**🟡 PHASE 1 --- File Ingestion Engine (Weeks 2--3)**

**Week 2 --- File Detection + Sync Engine**

**🎯 Goal:**

Build intelligent file system watcher + state tracking.

**Core Features:**

- Folder scanning

- File change detection

- File version tracking

- Deleted file detection

**Logic:**

- Compare:

  - Input folder state

  - DB registry state

**Output:**

- New file → ingest

- Modified file → reprocess

- Deleted file → mark inactive + remove vectors

**Deliverables:**

- File watcher service

- File registry DB sync

- Change detection engine

**Week 3 --- Markdown Conversion Layer**

**🎯 Goal:**

Convert ANY file → normalized Markdown format.

**Supported inputs:**

- PDF

- DOCX

- TXT

- HTML (basic)

- Markdown (pass-through)

**Features:**

- Parser plugin system (basic version)

- Standard markdown normalization

- Metadata attachment

**Output:**

Raw File → Clean Markdown + Metadata JSON

**Deliverables:**

- Parser engine

- Markdown generator

- Plugin interface v1 (parser only)

**🟠 PHASE 2 --- Chunking Engine (Weeks 4--5)**

**Week 4 --- Basic Chunking System**

**🎯 Goal:**

Convert markdown → structured chunks.

**Features:**

- Heading-based splitting

- Token-based limits

- Overlap control

- Chunk metadata tagging

**Output:**

{

chunk_id,

document_id,

text,

tokens,

section_path

}

**Deliverables:**

- Chunking service

- Token estimator

- Chunk metadata schema

**Week 5 --- Smart Chunking + Validation**

**Enhancements:**

- Semantic chunk boundaries

- Table/code-aware splitting

- Chunk validation engine

- Chunk quality scoring

**Deliverables:**

- Advanced chunker

- Chunk validator

- Chunk quality metrics

**🔵 PHASE 3 --- Embedding Pipeline (Weeks 6--7)**

**Week 6 --- Embedding Service**

**🎯 Goal:**

Generate embeddings from chunks.

**Features:**

- Batch embedding calls

- Model abstraction layer

- Retry handling

- Cost tracking

**Deliverables:**

- Embedding service

- Model adapter interface

- Batch processing pipeline

**Week 7 --- Optimization + Caching Layer**

**Features:**

- Embedding cache (avoid recomputation)

- Deduplication system

- Parallel batch processing

- Queue-based execution

**Deliverables:**

- Embedding cache system

- Queue worker optimization

- Performance tuning

**🟣 PHASE 4 --- Vector DB Publishing (Week 8)**

**Week 8 --- Qdrant Integration Layer**

**🎯 Goal:**

Store embeddings + metadata in vector DB.

**Features:**

- Upsert vectors

- Delete vectors (for removed files)

- Metadata filtering support

- Collection management

**Logic:**

- chunk → embedding → vector insert

**Deliverables:**

- Vector publisher service

- Delete sync mechanism

- Collection schema design

**🟤 PHASE 5 --- Control Plane + State Management (Week 9)**

**Week 9 --- Metadata Brain (SQL Control Plane)**

**🎯 Goal:**

Central system of truth.

**Features:**

- Workflow state tracking

- File registry state machine

- Chunk lineage tracking

- Embedding job tracking

**Deliverables:**

- Complete SQL schema

- State transition engine

- Workflow status API

**⚫ PHASE 6 --- Observability Layer (Week 10)**

**Week 10 --- Logs, Metrics, Traces**

**🎯 Goal:**

Make system fully observable.

**Features:**

- Structured logs

- Workflow tracing

- Metrics collection

- Failure tracking

**Stack:**

- Prometheus

- Grafana

- OpenTelemetry

**Deliverables:**

- Observability pipeline

- Dashboard setup

- Trace correlation IDs

**🔴 PHASE 7 --- Sync + Deletion Intelligence (Week 11)**

**Week 11 --- Full File Lifecycle Intelligence**

**🎯 Goal:**

Make ingestion fully self-healing.

**Features:**

- Detect file deletion → remove vectors

- Detect modification → reprocess pipeline

- Idempotent ingestion

- Conflict resolution

**Deliverables:**

- Sync engine v2

- Vector cleanup engine

- Idempotent workflow system

**⚙️ PHASE 8 --- Performance + Scaling (Week 12)**

**Week 12 --- Production Hardening**

**🎯 Goal:**

Make system production-ready.

**Features:**

- Horizontal scaling

- Queue-based ingestion

- Backpressure handling

- Worker autoscaling

- Performance tuning

**Deliverables:**

- K8s deployment configs

- Autoscaler setup

- Load-tested pipeline

**🧠 FINAL PHASE --- System Stabilization (Week 13)**

**Week 13 --- Enterprise Readiness**

**🎯 Goal:**

Make system stable for enterprise rollout.

**Features:**

- Failure recovery testing

- Replay workflows

- Full regression testing

- Security validation

**Deliverables:**

- Production-ready ingestion engine

- Recovery system verified

- SLA benchmarks met

**📊 Final Outcome After 13 Weeks**

You will have:

**✔ Fully working ingestion engine**

- File → Markdown → Chunk → Embedding → Vector DB

**✔ Intelligent sync system**

- Add / update / delete detection

**✔ Production-grade architecture**

- Scalable, observable, recoverable

**✔ Plugin-ready ingestion pipeline**

- Extensible from day one

**🧭 Suggested Build Order (IMPORTANT)**

If you want fastest usable system:

**MVP path (compressed):**

- Week 1--3 → File ingestion + markdown

- Week 4--5 → Chunking

- Week 6--7 → Embeddings

- Week 8 → Vector DB

👉 You already have a working RAG ingestion system here.

**If you want next step**

I can now generate:

**1. 🧱 Real folder structure (production repo layout)**

**2. 💻 Actual FastAPI + worker code skeleton**

**3. 🗄 SQL Server schema (ready-to-run)**

**4. 🧪 First working ingestion MVP code (end-to-end)**

Just tell me:

"Start coding the ingestion engine"

Below is your **real production-grade EKIE Ingestion Engine codebase
structure**.

This is designed so you can literally:

- clone repo → run docker → start ingestion pipeline

- scale later into distributed microservices

- plug LLMs, embeddings, vector DBs, workflows

**🧱 EKIE Ingestion Engine --- Production Codebase Structure**

ekie-ingestion-engine/

│

├── README.md

├── docker-compose.yml

├── pyproject.toml

├── .env.example

├── Makefile

│

├── docs/

│ ├── architecture.md

│ ├── ingestion_flow.md

│ ├── plugin_sdk.md

│ └── api_contracts.md

│

├── configs/

│ ├── app_config.yaml

│ ├── logging.yaml

│ ├── embedding_models.yaml

│ └── chunking_policies.yaml

│

├── scripts/

│ ├── bootstrap_db.py

│ ├── seed_data.py

│ ├── run_local.py

│ └── load_test.py

│

├── deployments/

│ ├── docker/

│ │ ├── Dockerfile.api

│ │ ├── Dockerfile.worker

│ │ ├── Dockerfile.chunker

│ │ └── Dockerfile.embedder

│ │

│ ├── k8s/

│ │ ├── api-deployment.yaml

│ │ ├── worker-deployment.yaml

│ │ ├── chunker-deployment.yaml

│ │ ├── embedder-deployment.yaml

│ │ ├── hpa.yaml

│ │ └── namespace.yaml

│ │

│ └── helm/

│ └── ekie-ingestion/

│

├── shared/

│ ├── models/

│ │ ├── document.py

│ │ ├── chunk.py

│ │ ├── workflow.py

│ │ ├── embedding.py

│ │ └── file_registry.py

│ │

│ ├── enums/

│ │ ├── status.py

│ │ ├── file_type.py

│ │ └── workflow_state.py

│ │

│ ├── utils/

│ │ ├── logger.py

│ │ ├── time.py

│ │ ├── hashing.py

│ │ ├── retry.py

│ │ └── id_generator.py

│ │

│ ├── exceptions/

│ │ ├── base.py

│ │ ├── ingestion.py

│ │ ├── workflow.py

│ │ └── embedding.py

│ │

│ └── constants/

│ ├── limits.py

│ └── defaults.py

│

├── services/

│ │

│ ├── api-gateway/

│ │ ├── main.py

│ │ ├── routes/

│ │ │ ├── ingest.py

│ │ │ ├── status.py

│ │ │ ├── file_sync.py

│ │ │ └── admin.py

│ │ ├── schemas/

│ │ └── controllers/

│ │

│ ├── control-plane/

│ │ ├── main.py

│ │ ├── db/

│ │ │ ├── session.py

│ │ │ ├── models.py

│ │ │ └── migrations/

│ │ ├── repositories/

│ │ ├── services/

│ │ └── api/

│ │

│ ├── ingestion-worker/

│ │ ├── main.py

│ │ ├── orchestrator.py

│ │ ├── file_watcher.py

│ │ ├── sync_engine.py

│ │ ├── change_detector.py

│ │ └── scheduler.py

│ │

│ ├── parser-service/

│ │ ├── main.py

│ │ ├── parsers/

│ │ │ ├── pdf_parser.py

│ │ │ ├── docx_parser.py

│ │ │ ├── html_parser.py

│ │ │ └── base_parser.py

│ │ ├── markdown_builder.py

│ │ └── metadata_extractor.py

│ │

│ ├── chunking-service/

│ │ ├── main.py

│ │ ├── chunkers/

│ │ │ ├── base_chunker.py

│ │ │ ├── heading_chunker.py

│ │ │ ├── token_chunker.py

│ │ │ └── semantic_chunker.py

│ │ ├── validators/

│ │ └── policies/

│ │

│ ├── embedding-service/

│ │ ├── main.py

│ │ ├── clients/

│ │ │ ├── openai_client.py

│ │ │ ├── local_model_client.py

│ │ │ └── base_client.py

│ │ ├── embedder.py

│ │ ├── batcher.py

│ │ ├── cache.py

│ │ └── cost_tracker.py

│ │

│ ├── vector-service/

│ │ ├── main.py

│ │ ├── qdrant_client.py

│ │ ├── index_manager.py

│ │ ├── upsert_engine.py

│ │ └── delete_engine.py

│ │

│ ├── workflow-engine/

│ │ ├── main.py

│ │ ├── orchestrator.py

│ │ ├── state_machine.py

│ │ ├── task_executor.py

│ │ ├── checkpoint_manager.py

│ │ └── retry_handler.py

│ │

│ ├── observability/

│ │ ├── logger.py

│ │ ├── metrics.py

│ │ ├── tracing.py

│ │ └── dashboards.py

│ │

│ ├── plugin-runtime/

│ │ ├── registry.py

│ │ ├── loader.py

│ │ ├── sandbox.py

│ │ ├── executor.py

│ │ └── interfaces/

│ │ ├── chunk_plugin.py

│ │ ├── parser_plugin.py

│ │ └── embedding_plugin.py

│

└── tests/

├── unit/

├── integration/

├── pipeline/

├── load/

└── regression/

**🧠 API Layer (Core Endpoints Design)**

**📍 API Gateway (**

**services/api-gateway**

**)**

**1. Ingestion APIs**

POST /ingest/file

Upload or register file for ingestion.

{

\"file_path\": \"/data/docs/file.pdf\",

\"source\": \"local_fs\"

}

**2. Sync APIs**

POST /sync/run

Triggers file sync engine manually.

**3. Status APIs**

GET /status/workflow/{workflow_id}

Returns full ingestion pipeline state.

**4. Admin APIs**

POST /admin/reprocess

POST /admin/rebuild-vectors

POST /admin/retry-failed

**🔁 Internal Service Communication Flow**

API Gateway

↓

Workflow Engine

↓

Parser Service

↓

Chunking Service

↓

Embedding Service

↓

Vector Service

↓

Control Plane Update

**🧩 Control Plane (SQL Brain)**

Tracks:

- document lifecycle

- workflow state

- chunk lineage

- embedding status

- file versioning

**⚙️ Key Design Decision (Important)**

**Everything is event-driven internally:**

Each stage emits event:

FILE_DETECTED

→ MARKDOWN_READY

→ CHUNKS_CREATED

→ EMBEDDINGS_GENERATED

→ VECTORS_PUBLISHED

**🚀 Minimal Running System (MVP Path)**

If you want to run this FAST:

**Only start these services first:**

1.  api-gateway

2.  ingestion-worker

3.  parser-service

4.  chunking-service

5.  embedding-service

6.  vector-service

7.  control-plane

**📦 First Execution Flow (Real Ingestion)**

File Drop

↓

API / Sync Trigger

↓

Workflow Engine

↓

Markdown Conversion

↓

Chunking

↓

Embedding

↓

Qdrant Insert

↓

SQL State Update

