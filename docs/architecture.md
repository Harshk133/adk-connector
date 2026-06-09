# ADK Connectors — Architecture Document

> **"Connect Google ADK Agents to Telegram, Discord, Slack, WhatsApp, Teams, and other communication platforms with minimal code."**

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Problem Statement](#2-problem-statement)
3. [Solution Overview](#3-solution-overview)
4. [Target Users](#4-target-users)
5. [Market Opportunity](#5-market-opportunity)
6. [Unique Selling Propositions](#6-unique-selling-propositions)
7. [Why Developers Will Use This Package](#7-why-developers-will-use-this-package)
8. [Core Product Vision](#8-core-product-vision)
9. [High-Level Architecture](#9-high-level-architecture)
1REMOVED_VALUE. [Internal Component Architecture](#1REMOVED_VALUE-internal-component-architecture)
11. [Folder Structure](#11-folder-structure)
12. [Detailed Package Structure](#12-detailed-package-structure)
13. [Telegram Connector Architecture](#13-telegram-connector-architecture)
14. [Session Management Design](#14-session-management-design)
15. [Plugin Architecture](#15-plugin-architecture)
16. [Public SDK Design](#16-public-sdk-design)
17. [Advanced Features](#17-advanced-features)
18. [Security Architecture](#18-security-architecture)
19. [Scalability Architecture](#19-scalability-architecture)
2REMOVED_VALUE. [Performance Considerations](#2REMOVED_VALUE-performance-considerations)
21. [Testing Strategy](#21-testing-strategy)
22. [Documentation Strategy](#22-documentation-strategy)
23. [Open Source Growth Strategy](#23-open-source-growth-strategy)
24. [Download Growth Strategy](#24-download-growth-strategy)
25. [Monetization Possibilities](#25-monetization-possibilities)
26. [Competitive Analysis](#26-competitive-analysis)
27. [Development Roadmap](#27-development-roadmap)
28. [Risks and Challenges](#28-risks-and-challenges)
29. [Success Metrics](#29-success-metrics)
3REMOVED_VALUE. [Final Vision](#3REMOVED_VALUE-final-vision)

---

## 1. Executive Summary

### What Problem This Project Solves

Developers who build AI agents with Google's Agent Development Kit (ADK) face a consistent, frustrating bottleneck: getting their agents into the hands of real users. Google ADK is an exceptional framework for constructing reasoning, multi-step, tool-using agents — but it ships with no native integration to the messaging platforms where users actually live: Telegram, Discord, Slack, WhatsApp, Microsoft Teams.

**ADK Connectors** is an open-source transport layer that bridges the gap between a Google ADK agent and any major messaging platform. With a single Python import and a handful of lines of configuration code, a developer can deploy a production-grade conversational AI agent to Telegram — without writing webhook handlers, session management logic, message-formatting utilities, or platform authentication code from scratch.

### Why This Project Exists

The AI agent ecosystem in 2REMOVED_VALUE24–2REMOVED_VALUE25 exploded. Google ADK became one of the most capable frameworks for building agents that reason, plan, and use tools. Yet the "last mile" problem — deploying those agents to users — remained unsolved. Every developer deploying an ADK agent to Telegram reinvents the same wheel: webhooks, polling loops, user session isolation, message chunking, error recovery, and Markdown-to-Telegram-HTML translation.

ADK Connectors exists to eliminate that reinvention permanently.

### Current Pain Points in the Google ADK Ecosystem

- **No official messaging platform connectors.** Google ADK provides no first-party integrations with Telegram, Slack, Discord, or WhatsApp.
- **No shared session management standard.** Each developer rolls their own session binding between a platform user ID and an ADK session ID.
- **No streaming support out of the box.** Streaming agent responses to a chat message requires non-trivial async plumbing that most developers get wrong on first attempt.
- **No community-standard boilerplate.** Every team that ships an ADK Telegram bot has a different, incompatible implementation — making it impossible to share knowledge or tooling.
- **No observable, production-hardened transport layer.** Developers ship weekend-project-quality webhook handlers into production with no rate limiting, no retry logic, and no audit logs.

### Why Telegram Is the First Connector

Telegram is the primary distribution platform for AI bots in 2REMOVED_VALUE24–2REMOVED_VALUE25 by a significant margin:

- Over 9REMOVED_VALUEREMOVED_VALUE million active users as of 2REMOVED_VALUE24.
- The dominant platform for developer-built AI bots globally.
- A well-documented, stable Bot API with native webhook support.
- Strong adoption in developer communities, crypto ecosystems, and international markets.
- Free, no-approval-required bot creation with `@BotFather`.
- Native support for inline keyboards, Markdown, file uploads, and voice messages.

Starting with Telegram delivers maximum developer impact with minimum architectural risk. It also provides a clean reference implementation that future connectors (Discord, Slack, WhatsApp) can follow.

### Long-Term Vision

ADK Connectors aspires to become the universal communication standard for AI agents — the equivalent of what Express.js is for Node.js web servers, or what SQLAlchemy is for Python databases. Every team building a Google ADK agent should naturally reach for ADK Connectors when they want to deploy to any messaging platform.

Beyond open source, the project will evolve into a hosted cloud platform (managed connectors, dashboards, analytics), an enterprise SDK (SSO, audit logs, SLA support), and ultimately a Connector Marketplace where third-party developers publish and monetize custom connectors.

---

## 2. Problem Statement

### The Current Developer Workflow

A developer who wants to put their Google ADK agent on Telegram today must navigate the following journey:

```
[Google ADK Agent]
        ↓
  Write REST API wrapper (FastAPI / Flask)
        ↓
  Handle Telegram Webhook (POST endpoint)
        ↓
  Parse Telegram Update JSON
        ↓
  Extract user_id, chat_id, message text
        ↓
  Create / retrieve ADK session for user
        ↓
  Forward message to ADK runner
        ↓
  Handle streaming vs. non-streaming response
        ↓
  Convert ADK response format → Telegram-compatible format
        ↓
  Handle Telegram message length limits (4REMOVED_VALUE96 chars)
        ↓
  Send response to Telegram Bot API
        ↓
  Handle Telegram API errors, rate limits, retries
        ↓
[User receives response]
```

This is not a two-hour task. This is a two-day task, done poorly. Done well, it takes a week.

### Boilerplate Code

A minimal, production-grade Telegram bot wrapper for a Google ADK agent requires, at minimum:

- A webhook registration and verification handler.
- An `Update` model parser (text, photo, document, voice, callback queries, inline queries).
- A session registry mapping `telegram_user_id → adk_session_id`.
- An ADK runner invocation wrapper with async support.
- A message chunker that splits responses over 4REMOVED_VALUE96 characters.
- A Markdown-to-Telegram HTML converter (ADK often returns standard Markdown; Telegram uses a restricted HTML subset).
- An error handler that catches `TelegramAPIError`, `ADKSessionError`, network timeouts.
- A startup/shutdown lifecycle manager for the bot poller or webhook server.

That is thousands of lines of plumbing that has nothing to do with the developer's actual agent logic.

### Session Management Challenges

ADK sessions are not inherently tied to any platform identity. A developer must:

- Maintain a mapping between platform user IDs and ADK session objects.
- Handle session expiry and recreation transparently.
- Decide on a storage backend (in-memory for development, Redis/PostgreSQL for production).
- Implement session locking to prevent race conditions when a user sends multiple messages rapidly.
- Handle session cleanup to prevent memory leaks.

None of this is documented in Google ADK's current quickstart guides for platform deployment.

### Platform Integration Complexity

Each messaging platform has a different:

- Authentication model (bot tokens, OAuth flows, app credentials).
- Webhook payload format.
- Message type taxonomy (text, photo, audio, document, sticker, reaction).
- Rate limiting behavior (Telegram: 3REMOVED_VALUE messages/second globally; 1 per user per second).
- Message length limits.
- Markdown/formatting dialect.
- File upload and download mechanism.

A developer supporting two platforms must learn and implement two completely separate systems. Supporting four platforms means four systems.

### Why This Workflow Is Painful

The core indignity is that none of this complexity is related to what the developer is trying to build. They chose Google ADK because they want to create a smart, capable agent. Instead, they spend 8REMOVED_VALUE% of their time on infrastructure scaffolding that every other developer in the world is also writing, independently, at the same time, with slightly different bugs.

This is solved — definitively — by ADK Connectors.

---

## 3. Solution Overview

### ADK Connectors Architecture

```
┌──────────────────────────────────────────────────────────┐
│                        END USERS                         │
│          (Telegram / Discord / Slack / WhatsApp)         │
└───────────────────────┬──────────────────────────────────┘
                        │  Native Platform Protocol
                        ▼
┌──────────────────────────────────────────────────────────┐
│                   CONNECTOR LAYER                        │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────────┐ │
│  │  Platform   │  │   Session   │  │    Message       │ │
│  │  Adapter    │  │   Manager   │  │    Processor     │ │
│  └─────────────┘  └─────────────┘  └──────────────────┘ │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────────────┐ │
│  │   Event     │  │  Response   │  │  Plugin          │ │
│  │   Router    │  │  Formatter  │  │  System          │ │
│  └─────────────┘  └─────────────┘  └──────────────────┘ │
└───────────────────────┬──────────────────────────────────┘
                        │  ADK Runner API
                        ▼
┌──────────────────────────────────────────────────────────┐
│                  GOOGLE ADK AGENT                        │
│         (Tools / Memory / Reasoning / Planning)          │
└───────────────────────┬──────────────────────────────────┘
                        │  Model API
                        ▼
┌──────────────────────────────────────────────────────────┐
│                        LLM                               │
│         (Gemini / Claude / GPT / Local Models)           │
└──────────────────────────────────────────────────────────┘
```

### The Abstraction Layer

ADK Connectors introduces a clean separation between three concerns:

**1. Platform Protocol** — how messages arrive from and are delivered to Telegram, Discord, etc. The `PlatformAdapter` handles this.

**2. Session & State** — maintaining conversation continuity between requests. The `SessionManager` handles this.

**3. Agent Execution** — running the ADK agent and processing its output. The `ConnectorCore` handles this.

By separating these concerns, a developer only ever touches the configuration surface. They bring their agent, provide a token, and call `connector.start()`.

### Platform Adapters

Each messaging platform is encapsulated in a `PlatformAdapter` that implements a standardized `BaseAdapter` interface:

```python
class BaseAdapter(ABC):
    async def start(self) -> None: ...
    async def stop(self) -> None: ...
    async def send_message(self, session_id: str, message: AdkConnectorMessage) -> None: ...
    async def on_update(self, update: RawPlatformUpdate) -> None: ...
```

Adding support for a new platform means implementing this interface — approximately 2REMOVED_VALUEREMOVED_VALUE–4REMOVED_VALUEREMOVED_VALUE lines of code, with no changes required to the core connector framework.

### Session Handling

The `SessionManager` maintains a registry:

```
platform_user_id  →  AdkSession
```

Sessions are created on first contact, persisted across messages, expired after configurable inactivity periods, and stored in a pluggable backend (in-memory, Redis, or SQLite/PostgreSQL).

### Event Routing

The `EventRouter` classifies incoming platform events (text message, file upload, voice note, callback button press) and dispatches them to the appropriate handler chain. Middleware can be registered on specific event types.

### Message Transformation

The `MessageProcessor` and `ResponseFormatter` handle bidirectional transformation:

- **Inbound:** Raw platform message → normalized `IncomingMessage` object.
- **Outbound:** ADK agent response → platform-native message (handling formatting, chunking, media attachments).

---

## 4. Target Users

### Individual Developers

**Profile:** Hobbyist, side-project builder, student, weekend hacker. Building personal productivity bots, creative AI tools, or experimenting with ADK.

**Needs:**
- Get something working quickly (under 3REMOVED_VALUE minutes).
- No DevOps complexity — runs on a laptop or free-tier cloud VM.
- Clear, copy-pasteable examples.
- Free and open source.

**Pain Points:**
- Hits webhook boilerplate walls immediately.
- Gets stuck on ADK session wiring.
- Overwhelmed by Telegram's update types.
- No time to read through 3 different API docs.

**Benefits from ADK Connectors:**
- Single-file quickstart. Agent deployed to Telegram in under 1REMOVED_VALUE minutes.
- Zero infrastructure required for development mode (long-polling).
- Extensive examples covering all common scenarios.

---

### AI Engineers

**Profile:** ML engineer or LLM application developer, professionally building AI products. Deeply familiar with ADK, less familiar with platform API quirks.

**Needs:**
- Production-grade reliability (retry logic, error handling, rate limiting).
- Streaming response support for responsive UX.
- Ability to handle multi-modal inputs (images, documents, voice).
- Observability and logging hooks.

**Pain Points:**
- Existing bot frameworks (python-telegram-bot, aiogram) are not ADK-aware.
- Streaming ADK responses to Telegram requires non-trivial async architecture.
- No standard pattern for multi-modal input handling in ADK context.
- Must instrument their own observability stack.

**Benefits from ADK Connectors:**
- Native streaming response support with Telegram message editing.
- Built-in multi-modal input pipeline (image → ADK content, PDF → ADK content).
- OpenTelemetry-compatible observability hooks.
- Production-hardened retry and rate limit handling.

---

### Startup Founders

**Profile:** Non-technical or semi-technical founder, or CTO of early-stage startup. Needs to ship fast, prove product-market fit, and minimize technical debt.

**Needs:**
- Ship a working Telegram bot MVP in days, not weeks.
- Low ongoing maintenance burden.
- A codebase that won't become a liability as they scale.
- Easy to hand off to a future engineering hire.

**Pain Points:**
- Every hour spent on infrastructure is an hour not spent on product.
- Patched-together bot code becomes unmaintainable at scale.
- Hard to find contract developers who know both ADK and Telegram bot development.

**Benefits from ADK Connectors:**
- Standard, well-documented codebase that any Python developer can understand.
- Clean separation of concerns — business logic stays in the agent, transport in the connector.
- Path to scale: the same codebase works in production with Redis session storage and horizontal scaling.

---

### SaaS Builders

**Profile:** Engineering team building a SaaS product that includes an AI assistant component. Needs a reliable, multi-tenant connector.

**Needs:**
- Multi-tenant session isolation (each customer's users get isolated sessions).
- Webhook security verification.
- Configurable per-tenant agent customization.
- Scalable architecture (handles thousands of concurrent users).

**Pain Points:**
- Multi-tenancy session management is complex to build correctly.
- Security requirements (webhook signature verification, secret rotation) are easy to misconfigure.
- Platform-specific quirks become blockers for non-platform experts on the team.

**Benefits from ADK Connectors:**
- Built-in multi-tenant session architecture.
- Webhook signature verification enabled by default.
- Pluggable session storage (Redis) for horizontal scaling.
- Secrets management integration (environment variables, Vault, AWS Secrets Manager).

---

### Internal Enterprise Teams

**Profile:** Platform engineering or AI enablement team at a mid-to-large enterprise. Building internal AI tools deployed to Microsoft Teams or Slack for employees.

**Needs:**
- Enterprise-grade security and auditability.
- SSO/identity integration.
- On-premises or VPC deployment.
- SLA and support options.
- Compliance with internal security review requirements.

**Pain Points:**
- Bot frameworks don't have enterprise connectors (Teams, Slack Enterprise Grid).
- No audit logging in open-source bot frameworks.
- Security teams require code review before deployment — open-source, well-structured code accelerates this.

**Benefits from ADK Connectors:**
- Audit log middleware for all agent interactions.
- Enterprise connector support (Teams, Slack Enterprise Grid) on the roadmap.
- Clean, reviewable codebase that passes security audits.
- Enterprise support tier (paid) for SLA guarantees.

---

### Open Source Contributors

**Profile:** Open-source developer wanting to contribute to the AI tooling ecosystem, build a reputation, or scratch their own itch with a custom connector.

**Needs:**
- Clear contribution guidelines.
- Stable, well-documented internal APIs.
- Friendly maintainer community.
- Their contributions having real-world impact.

**Pain Points:**
- Many open-source AI projects have messy internals that are hard to contribute to.
- Lack of clear specs for what a "correct" connector implementation looks like.
- Maintainers who are slow to review PRs.

**Benefits from ADK Connectors:**
- `BaseAdapter` interface makes writing a new connector well-defined.
- Architecture document (this document) provides a complete contributor onboarding guide.
- Active, responsive maintainer team.
- High GitHub activity = résumé value.

---

## 5. Market Opportunity

### Macro Trends

**AI Agents:** Gartner predicts that by 2REMOVED_VALUE28, 33% of enterprise software applications will include agentic AI. The AI agent framework market is growing at approximately 45% CAGR through 2REMOVED_VALUE3REMOVED_VALUE.

**Google ADK:** Launched in 2REMOVED_VALUE24, Google ADK is rapidly becoming a first-class agent development framework for teams already in the Google Cloud ecosystem. With Google's distribution power and developer advocacy, ADK adoption is projected to accelerate significantly through 2REMOVED_VALUE25–2REMOVED_VALUE26.

**Conversational AI on Messaging Platforms:** The global conversational AI market was valued at approximately $1REMOVED_VALUE.7 billion in 2REMOVED_VALUE23 and is expected to reach $29.8 billion by 2REMOVED_VALUE28 (CAGR ~22%). Messaging platforms are the primary deployment surface.

**Telegram Bots:** Telegram has over 9REMOVED_VALUEREMOVED_VALUE million monthly active users. There are over 1REMOVED_VALUE million active bots on the platform. The Telegram bot market serves use cases from customer support to education to finance to entertainment.

### TAM / SAM / SOM Analysis

**Total Addressable Market (TAM):** All developers building conversational AI applications across all platforms — estimated at 5–8 million developers globally by 2REMOVED_VALUE26. At an average infrastructure tooling spend of $2REMOVED_VALUEREMOVED_VALUE–$5REMOVED_VALUEREMOVED_VALUE/year per developer, TAM exceeds $2 billion.

**Serviceable Addressable Market (SAM):** Developers specifically using Google ADK or planning to, deploying to messaging platforms — estimated at 2REMOVED_VALUEREMOVED_VALUE,REMOVED_VALUEREMOVED_VALUEREMOVED_VALUE–5REMOVED_VALUEREMOVED_VALUE,REMOVED_VALUEREMOVED_VALUEREMOVED_VALUE developers by 2REMOVED_VALUE26. This number grows proportionally with ADK's adoption.

**Serviceable Obtainable Market (SOM):** In Year 1, realistically capturing 2–5% of the SAM (5,REMOVED_VALUEREMOVED_VALUEREMOVED_VALUE–25,REMOVED_VALUEREMOVED_VALUEREMOVED_VALUE developers) as active users of the open-source package. By Year 3, with strong community growth, 15–2REMOVED_VALUE% SAM capture is achievable.

**Monetization Surface:** Even at 1% conversion from free to a $49/month hosted tier, 25,REMOVED_VALUEREMOVED_VALUEREMOVED_VALUE active developers yields $147,REMOVED_VALUEREMOVED_VALUEREMOVED_VALUE ARR. At scale (1REMOVED_VALUEREMOVED_VALUE,REMOVED_VALUEREMOVED_VALUEREMOVED_VALUE+ developers), this becomes a multi-million dollar ARR business.

### Competitive Positioning

No existing package provides a production-grade, idiomatic Python connector layer specifically designed for Google ADK agents. This is a white-space opportunity. The first credible, well-maintained package in this niche becomes the default — the same way `python-telegram-bot` became the default Telegram library for Python despite competitors.

---

## 6. Unique Selling Propositions

| Feature | ADK Connectors Value | Status Quo (DIY) | Generic Bot Frameworks |
|---|---|---|---|
| **Plug-and-play setup** | 3 lines of code, agent deployed | Hours to days of boilerplate | Not ADK-aware |
| **ADK-native session management** | Automatic `user_id → ADK session` mapping | Manual, per-project implementation | Not applicable |
| **Streaming responses** | Built-in streaming with live message editing | Complex async engineering required | Not supported |
| **Multi-platform support** | Single API, swap platform adapter | Rewrite for each platform | Mixed support |
| **File & media handling** | Image/PDF/voice → ADK content pipeline | Manual per-type implementation | Basic file support |
| **Voice message support** | Auto-transcription pipeline (Whisper/Google STT) | None, or complex integration | Rare |
| **Webhook security** | Signature verification by default | Often misconfigured or missing | Sometimes available |
| **Rate limiting** | Built-in, configurable | Often missing | Varies |
| **Observability** | OpenTelemetry hooks, structured logging | None | None |
| **Open source** | MIT licensed, fully auditable | N/A | Varies |
| **Plugin system** | First-class middleware and plugin API | N/A | Limited |
| **Session storage backends** | Memory / Redis / SQL, switchable | One-off per project | None |
| **Multi-tenant support** | Built-in tenant isolation | Complex to implement | Not available |
| **Production-hardened** | Retry logic, backoff, error recovery | DIY | Basic |

---

## 7. Why Developers Will Use This Package

### Time Savings

**Scenario:** A solo developer wants to put their ADK customer support agent on Telegram for a client demo next week.

Without ADK Connectors:
- Day 1: Research Telegram Bot API. Register webhook. Write FastAPI endpoint. Parse `Update` objects.
- Day 2: Wire ADK runner. Figure out session management. Handle async correctly.
- Day 3: Debug formatting issues. Handle long messages. Test edge cases.
- Day 4: Discover they missed rate limiting. Discover they missed webhook verification. Fix bugs.

**Result:** 4 days of infrastructure work. Demo may still be rough.

With ADK Connectors:
- Day 1 (morning): Install package. Copy quickstart. Bot is running. Afternoon: polish agent logic.

**Time savings: 3–3.5 developer-days on the first project alone.** The compounding effect across a team or multiple projects is enormous.

### Reduced Complexity

Every custom integration carries a long-tail of hidden complexity:

- What happens when Telegram sends a duplicate update (it does, under retry conditions)?
- What happens when an ADK session expires mid-conversation?
- What happens when the agent response is 8,REMOVED_VALUEREMOVED_VALUEREMOVED_VALUE characters (Telegram's limit is 4,REMOVED_VALUE96)?
- What happens when a user sends a voice message to a text-only agent?

ADK Connectors handles all of these scenarios. A developer using the package doesn't need to even know these edge cases exist.

### Better Maintainability

A project using ADK Connectors has a clear dependency boundary: **agent logic** and **connector configuration** are separate concerns. A new developer joining the project understands the architecture immediately:

```
my_agent.py        ← all business logic lives here
main.py            ← connector setup and configuration
requirements.txt   ← adk-connectors is a standard dependency
```

Compare to a custom implementation where platform code, session code, and agent code are intertwined in a single 6REMOVED_VALUEREMOVED_VALUE-line file.

### Faster Deployment

ADK Connectors ships with:

- Docker container templates (webhook server + worker pattern).
- Railway / Render one-click deployment templates.
- Environment variable configuration (12-factor app compliant).
- Health check endpoints out of the box.

A developer can go from working local bot to production cloud deployment in under two hours.

### Consistent Architecture

When an entire team adopts ADK Connectors, every bot they build has the same structure. Code review is faster. Oncall handoff is faster. Debugging a production issue at 2 AM is faster because the architecture is familiar.

### Scalability

The same ADK Connectors code that runs on a Raspberry Pi in development runs on a 5REMOVED_VALUE-container Kubernetes deployment in production. The session storage backend, concurrency model, and event queue are all configurable — developers scale infrastructure, not application code.

### Real-World Scenario: AI Startup

An AI startup building a Telegram tutoring bot:

- **Month 1:** Ships MVP using ADK Connectors in one week. Spends remaining three weeks on pedagogy and content.
- **Month 3:** Scales to 1REMOVED_VALUE,REMOVED_VALUEREMOVED_VALUEREMOVED_VALUE users. Switches session storage from in-memory to Redis with a single config change.
- **Month 6:** Launches Discord channel. Adds Discord connector with two lines of code, same agent.
- **Month 12:** Adds voice lesson feature. Activates voice message pipeline in connector config.

At no point did the team write or maintain platform-specific infrastructure code. They focused entirely on their product.

---

## 8. Core Product Vision

### Version 1.REMOVED_VALUE — Telegram Connector (Current)

**Goal:** Production-grade, zero-boilerplate Telegram connector for Google ADK agents.

**Scope:**
- Text message handling (in/out)
- Streaming response support
- Session management (memory + Redis)
- Webhook + long-polling modes
- Basic media handling (images, documents)
- Voice message transcription (optional)
- Inline keyboard support
- Rate limiting + error recovery
- Structured logging

**Target Audience:** Individual developers, early-stage startups, AI engineers.

---

### Version 2.REMOVED_VALUE — Discord Connector

**Goal:** Full Discord bot connector with slash command support.

**Scope:**
- Slash command registration and handling
- Server/channel/DM context management
- Thread-based conversation support
- Role-based access control hooks
- Embed-formatted responses
- Voice channel text-to-speech output (Phase 2)

---

### Version 3.REMOVED_VALUE — Slack Connector

**Goal:** Enterprise-ready Slack connector with Bolt SDK integration.

**Scope:**
- Slack Bolt integration
- App mentions and DM handling
- Block Kit formatted responses
- Slash commands
- Home tab support
- Slack Connect (cross-workspace) support
- Enterprise Grid compatibility

---

### Version 4.REMOVED_VALUE — WhatsApp Connector

**Goal:** WhatsApp Business API connector.

**Scope:**
- WhatsApp Cloud API (Meta) integration
- Template message support
- Media messaging (images, documents, audio)
- Interactive buttons and lists
- WhatsApp Business Profile integration

---

### Version 5.REMOVED_VALUE — Universal Connector SDK

**Goal:** First-class SDK for third-party connector development.

**Scope:**
- Full `BaseAdapter` SDK with documentation and testing utilities
- Connector validation test suite
- Connector registry and discovery
- Community connector marketplace (GitHub-based)
- Connectors for: Microsoft Teams, Line, Viber, WeChat, SMS (Twilio)

---

### Version 6.REMOVED_VALUE — Hosted Cloud Platform

**Goal:** Managed connector infrastructure — no server required.

**Scope:**
- Web dashboard for connector management
- One-click deploy: connect Telegram bot token + ADK agent endpoint
- Built-in analytics: message volume, response latency, error rates
- Multi-tenant connector hosting
- Connector health monitoring and alerting
- Automatic scaling

**Business Model:** Freemium SaaS. Free tier (1 connector, 1,REMOVED_VALUEREMOVED_VALUEREMOVED_VALUE messages/month). Paid tiers for volume, additional connectors, analytics.

---

### Version 7.REMOVED_VALUE — Managed Enterprise SaaS

**Goal:** Enterprise-grade managed platform for large organizations.

**Scope:**
- SSO / SAML integration
- Advanced audit logs (SOC2, HIPAA compliance helpers)
- Dedicated infrastructure options
- SLA-backed uptime guarantees
- Enterprise support with named TAM
- Custom connector development services
- On-premises deployment option

---

## 9. High-Level Architecture

### Single Connector Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  USER                                                           │
│  (Telegram / Discord / Slack / WhatsApp / Teams)               │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                  [Platform Network Layer]
                  (HTTPS / WebSocket / Poll)
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  PLATFORM ADAPTER                                               │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │ Webhook Handler / Poller                                  │  │
│  │ Update Parser       → IncomingMessage                     │  │
│  │ Auth Verifier       (signature verification)              │  │
│  └───────────────────────────────────────────────────────────┘  │
└───────────────────────────┬─────────────────────────────────────┘
                            │ IncomingMessage
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│  CONNECTOR CORE                                                 │
│  ┌─────────────────┐  ┌──────────────────┐  ┌───────────────┐  │
│  │ Event Router    │  │ Session Manager  │  │ Message       │  │
│  │                 │→ │                  │→ │ Processor     │  │
│  └─────────────────┘  └──────────────────┘  └───────────────┘  │
│                                                      │          │
│                                            [Middleware Chain]   │
│                                                      │          │
└──────────────────────────────────────────────────────┼──────────┘
                                                       │ ADK Input
                                                       ▼
┌─────────────────────────────────────────────────────────────────┐
│  GOOGLE ADK AGENT                                               │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Runner  →  Agent  →  Tools  →  Memory  →  LLM          │   │
│  └─────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────┬──────────┘
                                                       │ ADK Output
                                                       ▼
┌─────────────────────────────────────────────────────────────────┐
│  RESPONSE FORMATTER                                             │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  Chunk Splitter → Markdown Converter → Media Assembler  │   │
│  └─────────────────────────────────────────────────────────┘   │
└──────────────────────────────────────────────────────┬──────────┘
                                                       │ OutgoingMessage
                                                       ▼
┌─────────────────────────────────────────────────────────────────┐
│  PLATFORM ADAPTER (Outbound)                                    │
│  Platform API Client → Rate Limiter → Retry Handler → Send      │
└──────────────────────────────────────────────────────┬──────────┘
                                                       │
                                              [Platform Network]
                                                       │
                                                       ▼
                                                    USER
```

### Multi-Platform Architecture

```
                        ┌──────────────────────┐
                        │    GOOGLE ADK AGENT  │
                        │   (Single Instance)  │
                        └──────────┬───────────┘
                                   │
                    ┌──────────────┼──────────────┐
                    │              │              │
                    ▼              ▼              ▼
          ┌─────────────┐ ┌─────────────┐ ┌─────────────┐
          │  Telegram   │ │   Discord   │ │    Slack    │
          │  Connector  │ │  Connector  │ │  Connector  │
          └──────┬──────┘ └──────┬──────┘ └──────┬──────┘
                 │               │               │
                 ▼               ▼               ▼
          ┌─────────────────────────────────────────────┐
          │           SESSION MANAGER                   │
          │  (Shared Redis / Unified Session Registry)  │
          └─────────────────────────────────────────────┘
                 │               │               │
                 ▼               ▼               ▼
          ┌─────────┐     ┌─────────┐     ┌─────────┐
          │Telegram │     │ Discord │     │  Slack  │
          │  Users  │     │  Users  │     │  Users  │
          └─────────┘     └─────────┘     └─────────┘
```

### High-Availability Production Architecture

```
                    ┌──────────────────────┐
                    │    LOAD BALANCER      │
                    │  (nginx / ALB / GCP)  │
                    └──────────┬───────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
     ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
     │ Webhook      │ │ Webhook      │ │ Webhook      │
     │ Worker #1    │ │ Worker #2    │ │ Worker #N    │
     └──────┬───────┘ └──────┬───────┘ └──────┬───────┘
            │                │                │
            └────────────────┼────────────────┘
                             ▼
                   ┌──────────────────┐
                   │   MESSAGE QUEUE  │
                   │  (Redis Streams) │
                   └────────┬─────────┘
                            │
              ┌─────────────┼─────────────┐
              ▼             ▼             ▼
    ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
    │  ADK Worker  │ │  ADK Worker  │ │  ADK Worker  │
    │      #1      │ │      #2      │ │      #N      │
    └──────┬───────┘ └──────┬───────┘ └──────┬───────┘
           │                │                │
           └────────────────┼────────────────┘
                            ▼
                  ┌──────────────────────┐
                  │   SESSION STORE      │
                  │   (Redis Cluster)    │
                  └──────────────────────┘
```

---

## 1REMOVED_VALUE. Internal Component Architecture

### Connector Manager

**File:** `core/connector_manager.py`

The central orchestration component. Responsible for:

- Registering and initializing one or more `PlatformAdapter` instances.
- Starting and stopping the connector lifecycle (startup hooks, shutdown hooks).
- Wiring adapters to the `EventRouter`.
- Managing the shared `SessionManager` instance.
- Exposing a health check endpoint.
- Coordinating graceful shutdown on SIGTERM/SIGINT.

```python
class ConnectorManager:
    def __init__(self, agent: BaseAgent, config: ConnectorConfig): ...
    def register_adapter(self, adapter: BaseAdapter) -> None: ...
    async def start(self) -> None: ...
    async def stop(self) -> None: ...
    def get_health(self) -> HealthStatus: ...
```

---

### Event Router

**File:** `core/event_router.py`

Routes normalized `IncomingEvent` objects to registered handlers. Supports:

- Event type routing (`text_message`, `photo_message`, `voice_message`, `document_message`, `callback_query`, `inline_query`).
- Priority-ordered middleware chain execution.
- Async handler dispatch.
- Dead letter queue for unhandled events.

```python
class EventRouter:
    def register_handler(self, event_type: EventType, handler: AsyncHandler) -> None: ...
    def use_middleware(self, middleware: Middleware) -> None: ...
    async def dispatch(self, event: IncomingEvent) -> None: ...
```

---

### Session Manager

**File:** `core/session_manager.py`

Manages the mapping between platform user identities and ADK sessions. Responsibilities:

- Create new ADK sessions for first-time users.
- Retrieve existing sessions for returning users.
- Handle session expiry and transparent recreation.
- Provide session locking to prevent concurrent message race conditions.
- Support pluggable storage backends (`MemoryBackend`, `RedisBackend`, `SQLBackend`).
- Emit session lifecycle events (created, resumed, expired, destroyed).

```python
class SessionManager:
    def __init__(self, storage: SessionStorage, config: SessionConfig): ...
    async def get_or_create(self, platform_id: str, platform: str) -> AdkSession: ...
    async def destroy(self, platform_id: str, platform: str) -> None: ...
    async def lock(self, platform_id: str) -> AsyncContextManager: ...
```

---

### Message Processor

**File:** `core/message_processor.py`

Transforms raw platform-specific `IncomingMessage` objects into normalized `ProcessedInput` objects suitable for ADK runner invocation. Handles:

- Text extraction and normalization.
- Image download and base64 encoding for ADK vision inputs.
- PDF text extraction.
- Voice message download and transcription dispatch.
- Document analysis pipeline.
- Command parsing (`/command args`).

```python
class MessageProcessor:
    async def process(self, message: IncomingMessage, session: AdkSession) -> ProcessedInput: ...
    def register_media_handler(self, media_type: MediaType, handler: MediaHandler) -> None: ...
```

---

### Platform Adapter

**File:** `core/base_adapter.py`, `telegram/adapter.py`, `discord/adapter.py`, etc.

The platform-specific integration component. Implements `BaseAdapter`:

```python
class BaseAdapter(ABC):
    @abstractmethod
    async def start(self) -> None: ...

    @abstractmethod
    async def stop(self) -> None: ...

    @abstractmethod
    async def send_message(self, chat_id: str, message: OutgoingMessage) -> None: ...

    @abstractmethod
    async def edit_message(self, chat_id: str, message_id: str, new_content: str) -> None: ...

    @abstractmethod
    async def set_typing_indicator(self, chat_id: str) -> None: ...
```

Each adapter handles:
- Authentication with the platform API.
- Update reception (webhook or long-polling).
- Update parsing into `IncomingMessage` objects.
- Outbound message delivery.
- Platform-specific capabilities (inline keyboards, embeds, blocks).

---

### Response Formatter

**File:** `core/response_formatter.py`

Transforms ADK agent output into platform-deliverable `OutgoingMessage` objects. Handles:

- Markdown-to-platform-HTML conversion (Telegram uses a restricted HTML subset; Discord uses its own Markdown dialect).
- Message length chunking (respects each platform's character limits).
- Code block formatting.
- Table rendering (converts to images or formatted text depending on platform).
- Inline keyboard/button attachment.
- Media attachment assembly.

```python
class ResponseFormatter:
    def __init__(self, platform: str, config: FormatterConfig): ...
    def format(self, adk_response: AdkResponse) -> List[OutgoingMessage]: ...
    def format_streaming_chunk(self, chunk: str, context: StreamingContext) -> StreamingUpdate: ...
```

---

### Configuration Manager

**File:** `core/config.py`

Centralized configuration loading and validation. Features:

- Pydantic-based config models with type validation.
- Environment variable loading (`TELEGRAM_BOT_TOKEN`, `REDIS_URL`, etc.).
- `.env` file support.
- Config schema documentation generation.
- Runtime config validation with meaningful error messages.
- Secrets masking in log output.

---

### Plugin System

**File:** `core/plugins.py`

Enables third-party extension of connector behavior without modifying core code. Provides:

- Middleware hooks (pre-processing, post-processing).
- Event handler hooks.
- Session lifecycle hooks.
- Custom media type handlers.
- Custom response formatters.
- A `BasePlugin` abstract class with lifecycle methods (`on_load`, `on_start`, `on_stop`).

---

### Error Handler

**File:** `core/error_handler.py`

Centralized error management:

- Catches and classifies errors (platform errors, ADK errors, network errors, configuration errors).
- Implements retry logic with exponential backoff for transient failures.
- Sends user-facing error messages in platform-appropriate format.
- Emits error events to observability layer.
- Dead-letter-queue support for messages that permanently fail.

---

### Observability Layer

**File:** `core/observability.py`

Production-grade instrumentation:

- **Structured logging:** JSON log output with correlation IDs, session IDs, platform context.
- **Metrics:** Message throughput, response latency, error rate, session count, queue depth.
- **Tracing:** OpenTelemetry-compatible span creation for each message processing pipeline step.
- **Health endpoints:** `/health`, `/metrics` (Prometheus format), `/ready`.

---

## 11. Folder Structure

```
adk-connectors/
│
├── packages/                        ← Monorepo packages (one per connector + core)
│   │
│   ├── core/                        ← Framework core — shared by all connectors
│   │   ├── adk_connectors/
│   │   │   ├── __init__.py
│   │   │   ├── base_adapter.py      ← Abstract base class for all platform adapters
│   │   │   ├── connector_manager.py ← Lifecycle orchestration
│   │   │   ├── event_router.py      ← Event type routing and dispatch
│   │   │   ├── session_manager.py   ← ADK session lifecycle
│   │   │   ├── message_processor.py ← Inbound message normalization
│   │   │   ├── response_formatter.py← Outbound response formatting
│   │   │   ├── config.py            ← Pydantic config models
│   │   │   ├── plugins.py           ← Plugin system
│   │   │   ├── error_handler.py     ← Centralized error management
│   │   │   ├── observability.py     ← Logging, metrics, tracing
│   │   │   ├── models/
│   │   │   │   ├── incoming.py      ← IncomingMessage, IncomingEvent models
│   │   │   │   ├── outgoing.py      ← OutgoingMessage models
│   │   │   │   └── session.py       ← Session models
│   │   │   └── storage/
│   │   │       ├── base.py          ← SessionStorage abstract class
│   │   │       ├── memory.py        ← In-memory storage (development)
│   │   │       ├── redis_storage.py ← Redis-backed storage (production)
│   │   │       └── sql_storage.py   ← SQLAlchemy-backed storage
│   │   ├── tests/
│   │   ├── pyproject.toml
│   │   └── README.md
│   │
│   ├── telegram/                    ← Telegram connector package
│   │   ├── adk_connectors_telegram/
│   │   │   ├── __init__.py
│   │   │   ├── adapter.py           ← TelegramAdapter (implements BaseAdapter)
│   │   │   ├── webhook.py           ← FastAPI webhook handler
│   │   │   ├── poller.py            ← Long-polling fallback
│   │   │   ├── parser.py            ← Telegram Update → IncomingMessage
│   │   │   ├── formatter.py         ← OutgoingMessage → Telegram API params
│   │   │   ├── keyboard.py          ← InlineKeyboard builder utilities
│   │   │   ├── media.py             ← Media download/upload handling
│   │   │   ├── voice.py             ← Voice message transcription pipeline
│   │   │   └── config.py            ← TelegramConfig (extends BaseConfig)
│   │   ├── tests/
│   │   ├── pyproject.toml
│   │   └── README.md
│   │
│   ├── discord/                     ← Discord connector (v2.REMOVED_VALUE)
│   │   └── [same structure as telegram/]
│   │
│   ├── slack/                       ← Slack connector (v3.REMOVED_VALUE)
│   │   └── [same structure as telegram/]
│   │
│   └── whatsapp/                    ← WhatsApp connector (v4.REMOVED_VALUE)
│       └── [same structure as telegram/]
│
├── examples/                        ← Runnable example projects
│   ├── telegram-basic/              ← Simplest possible Telegram bot
│   ├── telegram-streaming/          ← Streaming response demo
│   ├── telegram-multimodal/         ← Image + PDF + voice demo
│   ├── telegram-redis-sessions/     ← Production session storage demo
│   ├── telegram-multi-agent/        ← Multiple agent handoff demo
│   ├── discord-basic/               ← Discord slash command bot
│   └── multi-platform/              ← Same agent on Telegram + Discord
│
├── docs/                            ← Documentation source
│   ├── getting-started/
│   ├── guides/
│   ├── api-reference/
│   ├── deployment/
│   ├── contributing/
│   └── ARCHITECTURE.md              ← This file
│
├── tests/                           ← Integration and E2E tests
│   ├── integration/
│   ├── e2e/
│   └── load/
│
├── scripts/                         ← Developer tooling scripts
│   ├── setup-dev.sh
│   ├── run-tests.sh
│   ├── release.sh
│   └── benchmark.sh
│
├── website/                         ← Documentation website (Docusaurus)
│   ├── src/
│   ├── docs/
│   └── blog/
│
├── benchmarks/                      ← Performance benchmarks
│   ├── throughput/
│   ├── latency/
│   └── memory/
│
├── .github/
│   ├── workflows/                   ← CI/CD pipelines
│   ├── ISSUE_TEMPLATE/
│   └── PULL_REQUEST_TEMPLATE.md
│
├── CONTRIBUTING.md
├── CODE_OF_CONDUCT.md
├── SECURITY.md
├── CHANGELOG.md
├── pyproject.toml                   ← Root workspace configuration
└── README.md
```

---

## 12. Detailed Package Structure

### `packages/core/` — The Framework Foundation

This package is the heart of ADK Connectors. It defines all abstract interfaces, shared data models, and platform-agnostic business logic. Every connector package depends on `adk-connectors-core`.

**Key responsibilities:** Session management, event routing, middleware system, observability, error handling.

**Published as:** `adk-connectors-core` on PyPI.

---

### `packages/telegram/` — Telegram Transport Adapter

Complete Telegram Bot API integration. Supports webhook mode (production) and long-polling mode (development). Handles all Telegram update types, rate limits, and API quirks.

**Published as:** `adk-connectors-telegram` on PyPI.

---

### `packages/discord/` — Discord Transport Adapter (v2.REMOVED_VALUE)

Discord bot integration using discord.py with slash command support, guild management, and thread-based conversations.

**Published as:** `adk-connectors-discord` on PyPI.

---

### `packages/slack/` — Slack Transport Adapter (v3.REMOVED_VALUE)

Slack Bolt-based integration supporting app mentions, DMs, slash commands, and Block Kit responses.

**Published as:** `adk-connectors-slack` on PyPI.

---

### `packages/whatsapp/` — WhatsApp Transport Adapter (v4.REMOVED_VALUE)

WhatsApp Cloud API integration with template message support and interactive components.

**Published as:** `adk-connectors-whatsapp` on PyPI.

---

### `examples/` — Runnable Reference Implementations

Every example is a complete, runnable project with its own `README.md`, `requirements.txt`, and `.env.example`. Examples are tested in CI to ensure they never silently break.

---

### `docs/` — Documentation Source

Markdown documentation source files for the documentation website. Organized by audience: getting-started (15-minute quickstart), guides (how-to articles), api-reference (generated from code), deployment (production patterns).

---

### `tests/` — Cross-Package Test Suite

Integration tests that test connector packages together with mock ADK agents. End-to-end tests using real (test-mode) platform APIs. Load tests using Locust.

---

### `scripts/` — Developer Tooling

Shell scripts for common development tasks: setting up a development environment, running the full test suite, cutting a release, and running performance benchmarks.

---

### `website/` — Documentation Site

Docusaurus-based documentation website. Deployed to GitHub Pages. Includes full API reference, guides, tutorials, and a blog for announcements and deep-dive articles.

---

### `benchmarks/` — Performance Benchmarks

Automated benchmarks that run in CI on each release to detect performance regressions. Measures: message throughput (messages/second), end-to-end latency (p5REMOVED_VALUE, p95, p99), and memory consumption per concurrent session.

---

## 13. Telegram Connector Architecture

### Incoming Message Flow

```
Telegram Server
      │
      │  POST /webhook/{secret_token}
      ▼
┌─────────────────────────────────────────────────────────┐
│  WEBHOOK HANDLER (FastAPI)                              │
│  1. Verify X-Telegram-Bot-Api-Secret-Token header       │
│  2. Parse Update JSON body                              │
│  3. Acknowledge (return 2REMOVED_VALUEREMOVED_VALUE immediately)                │
│  4. Enqueue update for async processing                 │
└───────────────────────────┬─────────────────────────────┘
                            │ (async queue)
                            ▼
┌─────────────────────────────────────────────────────────┐
│  UPDATE PARSER                                          │
│  Telegram Update → IncomingMessage                      │
│                                                         │
│  update.message.text      → TextMessage                 │
│  update.message.photo     → PhotoMessage                │
│  update.message.voice     → VoiceMessage                │
│  update.message.document  → DocumentMessage             │
│  update.callback_query    → CallbackQuery               │
│  update.inline_query      → InlineQuery                 │
└───────────────────────────┬─────────────────────────────┘
                            │ IncomingMessage
                            ▼
┌─────────────────────────────────────────────────────────┐
│  EVENT ROUTER                                           │
│  Routes to registered handler by event type             │
│  Executes middleware chain                              │
└───────────────────────────┬─────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│  SESSION MANAGER                                        │
│  telegram_user_id → AdkSession                          │
│  (create if new, retrieve if existing)                  │
└───────────────────────────┬─────────────────────────────┘
                            │ (session + message)
                            ▼
┌─────────────────────────────────────────────────────────┐
│  MESSAGE PROCESSOR                                      │
│  Normalize input for ADK runner                         │
│  - Download media files                                 │
│  - Transcribe voice (if enabled)                        │
│  - Extract PDF text (if enabled)                        │
│  - Build ADK-compatible content object                  │
└───────────────────────────┬─────────────────────────────┘
                            │ ProcessedInput
                            ▼
                     ADK Runner.run()
```

### Outgoing Response Flow

```
                     ADK Runner Response
                            │
                            ▼
┌─────────────────────────────────────────────────────────┐
│  RESPONSE FORMATTER                                     │
│  ADK Response → List[OutgoingMessage]                   │
│                                                         │
│  - Convert Markdown → Telegram HTML                     │
│  - Split messages exceeding 4REMOVED_VALUE96 characters             │
│  - Attach inline keyboards (if configured)              │
│  - Format code blocks                                   │
└───────────────────────────┬─────────────────────────────┘
                            │ List[OutgoingMessage]
                            ▼
┌─────────────────────────────────────────────────────────┐
│  TELEGRAM API CLIENT                                    │
│  - Rate limiter (1 msg/sec per chat, 3REMOVED_VALUE/sec global)     │
│  - Retry with exponential backoff on 429/5xx            │
│  - sendMessage / sendPhoto / sendDocument               │
└───────────────────────────┬─────────────────────────────┘
                            │ HTTPS
                            ▼
                     Telegram Server
                            │
                            ▼
                          USER
```

### Streaming Response Flow (Telegram Edit Pattern)

```
ADK Agent starts streaming
        │
        ▼
Send initial message to Telegram
("⏳ Thinking...")
        │
        ▼ [ADK stream yields chunk]
Edit message with accumulated content
("Here is your answer: The capital...")
        │
        ▼ [ADK stream yields more]
Edit message again
("Here is your answer: The capital of France is Paris, which...")
        │
        ▼ [ADK stream complete]
Final edit with full response + inline keyboard
```

### Sequence Diagram

```
User          Telegram         ADK Connectors         ADK Agent
 │               │                    │                    │
 │──[message]───►│                    │                    │
 │               │──[POST /webhook]──►│                    │
 │               │◄──[2REMOVED_VALUEREMOVED_VALUE OK]─────────│                    │
 │               │                    │──[get/create session]
 │               │                    │──[process message]─►│
 │               │                    │                    │──[LLM call]
 │               │                    │◄──[stream chunk 1]──│
 │               │◄──[send message]───│                    │
 │               │◄──[edit message]───│◄──[stream chunk 2]──│
 │               │◄──[edit message]───│◄──[stream chunk 3]──│
 │◄──[response]──│                    │◄──[stream complete]─│
 │               │                    │                    │
```

---

## 14. Session Management Design

### Why Session Management Matters

A messaging platform user sends messages over time, across a conversation that may span days or weeks. Google ADK maintains conversation context through its session mechanism — but sessions are not inherently linked to platform identities. Without proper session management:

- Each message from a user is treated as the start of a brand-new conversation.
- The agent has no memory of previous turns.
- Multi-step workflows (e.g., filling out a form) become impossible.
- Personalization is impossible.

ADK Connectors provides a session management layer that is correct, production-grade, and transparent to the developer.

### Session Registry Design

```
┌──────────────────────────────────────────────────────────┐
│  PLATFORM MESSAGE                                        │
│  platform: "telegram"                                    │
│  user_id: 123456789                                      │
│  chat_id: 123456789                                      │
└─────────────────────────┬────────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────┐
│  SESSION REGISTRY                                        │
│                                                          │
│  Key: "telegram:123456789"                               │
│  Value: {                                                │
│    adk_session_id: "sess_abc123",                        │
│    adk_user_id: "tg_123456789",                          │
│    created_at: 172REMOVED_VALUEREMOVED_VALUEREMOVED_VALUEREMOVED_VALUEREMOVED_VALUEREMOVED_VALUEREMOVED_VALUE,                               │
│    last_active: 172REMOVED_VALUEREMOVED_VALUEREMOVED_VALUE36REMOVED_VALUEREMOVED_VALUE,                              │
│    platform_metadata: { username: "johndoe", ... }       │
│  }                                                       │
└─────────────────────────┬────────────────────────────────┘
                          │
                          ▼
┌──────────────────────────────────────────────────────────┐
│  ADK SESSION                                             │
│  session_id: "sess_abc123"                               │
│  user_id: "tg_123456789"                                 │
│  conversation_history: [...]                             │
│  agent_state: {...}                                      │
└──────────────────────────────────────────────────────────┘
```

### Session Lifecycle

```
User sends first message
        │
        ▼
SessionManager.get_or_create("telegram:123456789")
        │
        ├──[No existing session]──► Create new ADK session
        │                           Store in registry
        │                           Return new session
        │
        └──[Session exists]────────► Check expiry
                                     ├──[Not expired]──► Return existing
                                     └──[Expired]──────► Create new session
                                                         Optionally preserve history
```

### Memory Handling

ADK Connectors supports three session memory strategies:

**1. Stateless Memory:** Each session contains only the current conversation. No persistence across bot restarts.

**2. Persistent Memory:** Session state is written to Redis or SQL on every update. Survives bot restarts.

**3. Long-term Memory:** Optional integration with ADK's memory service for cross-session recall ("Remember when you told me last week...").

### Storage Backends

```python
# Development: in-memory (default)
from adk_connectors.storage import MemorySessionStorage
storage = MemorySessionStorage()

# Production: Redis
from adk_connectors.storage import RedisSessionStorage
storage = RedisSessionStorage(
    url="redis://localhost:6379",
    key_prefix="adk:sessions:",
    ttl_seconds=864REMOVED_VALUEREMOVED_VALUE,  # 24 hours
)

# Enterprise: PostgreSQL
from adk_connectors.storage import SQLSessionStorage
storage = SQLSessionStorage(
    database_url="postgresql://user:pass@host/db",
    table_name="adk_sessions",
)
```

### Session Locking

To prevent race conditions when a user sends multiple messages rapidly before the first completes:

```python
async with session_manager.lock("telegram:123456789"):
    session = await session_manager.get_or_create("telegram:123456789")
    response = await adk_runner.run(session, message)
    await session_manager.update(session)
```

Locks are implemented as Redis `SET NX PX` operations in production, with a configurable wait timeout and a user-facing "I'm still processing your previous message" fallback.

---

## 15. Plugin Architecture

### Plugin Design Principles

ADK Connectors uses a layered plugin system that allows third-party developers to extend any part of the framework without modifying core code. Plugins are Python packages that register hooks at well-defined extension points.

### BasePlugin Interface

```python
from adk_connectors.plugins import BasePlugin

class MyPlugin(BasePlugin):
    name = "my_plugin"
    version = "1.REMOVED_VALUE.REMOVED_VALUE"

    async def on_load(self, connector: ConnectorManager) -> None:
        """Called when the plugin is registered."""
        ...

    async def on_start(self) -> None:
        """Called when the connector starts."""
        ...

    async def on_stop(self) -> None:
        """Called when the connector stops."""
        ...
```

### Middleware System

Middleware intercepts the message processing pipeline:

```python
from adk_connectors.plugins import Middleware, IncomingMessage, ProcessedInput

class LoggingMiddleware(Middleware):
    async def process_incoming(
        self, message: IncomingMessage, next: AsyncCallable
    ) -> ProcessedInput:
        print(f"Incoming: {message.user_id}: {message.text}")
        result = await next(message)
        print(f"Processed: {result}")
        return result

    async def process_outgoing(
        self, response: OutgoingMessage, next: AsyncCallable
    ) -> OutgoingMessage:
        return await next(response)
```

### Custom Message Processors

```python
from adk_connectors.plugins import MediaHandler, MediaType

class SpreadsheetProcessor(MediaHandler):
    media_type = MediaType.DOCUMENT
    supported_mime_types = ["application/vnd.ms-excel",
                            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"]

    async def process(self, file_bytes: bytes, filename: str) -> AdkContent:
        # Parse spreadsheet, convert to structured text for ADK
        df = pd.read_excel(io.BytesIO(file_bytes))
        return AdkContent(text=df.to_markdown())
```

### Custom Event Handlers

```python
from adk_connectors.plugins import EventHandler, EventType

class JoinWelcomeHandler(EventHandler):
    event_type = EventType.NEW_CHAT_MEMBER

    async def handle(self, event: IncomingEvent, session: AdkSession) -> None:
        await connector.send_message(
            event.chat_id,
            "Welcome! I'm an AI assistant. How can I help?"
        )
```

### Custom Connectors (New Platforms)

Third-party developers can publish entirely new platform connectors by implementing `BaseAdapter`:

```python
# Published as: adk-connectors-line (LINE messaging platform)
from adk_connectors import BaseAdapter, IncomingMessage, OutgoingMessage

class LineAdapter(BaseAdapter):
    platform = "line"

    def __init__(self, channel_access_token: str, channel_secret: str): ...

    async def start(self) -> None:
        # Register LINE webhook
        ...

    async def stop(self) -> None: ...

    async def send_message(self, chat_id: str, message: OutgoingMessage) -> None:
        # Send message via LINE Messaging API
        ...
```

### Plugin Registration

```python
from adk_connectors import TelegramConnector
from my_plugins import LoggingPlugin, SpreadsheetProcessor, JoinWelcomeHandler

connector = TelegramConnector(token="...", agent=my_agent)
connector.use_plugin(LoggingPlugin())
connector.use_media_handler(SpreadsheetProcessor())
connector.on(EventType.NEW_CHAT_MEMBER, JoinWelcomeHandler())
connector.start()
```

---

## 16. Public SDK Design

### Design Principles

The public SDK follows three principles: **minimal API surface** (the common case is simple), **progressive disclosure** (advanced features are available when needed), and **Pythonic idioms** (it should feel like idiomatic Python, not a port from another language).

### Quickstart — Minimum Viable Bot

```python
from google.adk.agents import LlmAgent
from adk_connectors.telegram import TelegramConnector

# Your existing ADK agent
agent = LlmAgent(
    name="my_assistant",
    model="gemini-2.REMOVED_VALUE-flash",
    instruction="You are a helpful assistant.",
)

# One connector, three lines
connector = TelegramConnector(
    token="YOUR_TELEGRAM_BOT_TOKEN",
    agent=agent,
)

connector.start()
```

### Production Configuration

```python
from adk_connectors.telegram import TelegramConnector, TelegramConfig
from adk_connectors.storage import RedisSessionStorage
from adk_connectors.observability import configure_logging

configure_logging(level="INFO", format="json")

storage = RedisSessionStorage(url="redis://redis:6379")

config = TelegramConfig(
    token="YOUR_BOT_TOKEN",
    webhook_url="https://yourdomain.com/webhook",
    webhook_secret="YOUR_WEBHOOK_SECRET",
    session_ttl_hours=24,
    streaming=True,
    max_message_length=4REMOVED_VALUE96,
    rate_limit_per_user_per_second=1,
)

connector = TelegramConnector(
    config=config,
    agent=agent,
    session_storage=storage,
)

connector.start()
```

### Environment Variable Configuration (12-Factor)

```python
# All config can come from environment variables
# TELEGRAM_BOT_TOKEN, TELEGRAM_WEBHOOK_URL, REDIS_URL, etc.

connector = TelegramConnector.from_env(agent=agent)
connector.start()
```

### Custom Message Handler

```python
@connector.on_message
async def handle_message(message: IncomingMessage, session: AdkSession) -> None:
    # Custom pre-processing
    if "/reset" in message.text:
        await session.clear()
        await connector.send_text(message.chat_id, "Conversation reset!")
        return

    # Default processing (forward to ADK agent)
    await connector.process_with_agent(message, session)
```

### Multi-Platform Setup

```python
from adk_connectors import ConnectorManager
from adk_connectors.telegram import TelegramConnector
from adk_connectors.discord import DiscordConnector
from adk_connectors.storage import RedisSessionStorage

shared_storage = RedisSessionStorage(url="redis://redis:6379")

manager = ConnectorManager(
    agent=agent,
    session_storage=shared_storage,
)

manager.add_connector(TelegramConnector(token="TG_TOKEN"))
manager.add_connector(DiscordConnector(token="DISCORD_TOKEN"))

manager.start()
```

### Streaming Response

```python
# Streaming is enabled by default when supported by the platform
# For Telegram: edits the message as content arrives

connector = TelegramConnector(
    token="TOKEN",
    agent=agent,
    streaming=True,              # Default: True
    stream_edit_interval=REMOVED_VALUE.5,    # Edit message every REMOVED_VALUE.5 seconds of streaming
)
```

### Voice Message Handling

```python
from adk_connectors.telegram.voice import WhisperTranscriber

connector = TelegramConnector(
    token="TOKEN",
    agent=agent,
    voice_transcriber=WhisperTranscriber(model="base"),
)
# Voice messages are automatically transcribed and forwarded as text to ADK
```

### Multi-Agent Orchestration

```python
from adk_connectors.telegram import TelegramConnector
from adk_connectors.routing import AgentRouter

router = AgentRouter(
    default_agent=general_agent,
    routes={
        r"^/code\s": coding_agent,
        r"^/translate\s": translation_agent,
        r"^/image\s": image_agent,
    }
)

connector = TelegramConnector(token="TOKEN", agent=router)
connector.start()
```

---

## 17. Advanced Features

### Streaming Responses

ADK agents can return responses incrementally. ADK Connectors uses the Telegram "edit message" pattern to show live streaming responses:

- Sends an initial placeholder message ("Thinking...").
- Edits the message as each chunk arrives from the ADK stream.
- Finalizes with the complete response and optional interactive buttons.
- Respects Telegram's edit rate limits (configurable minimum interval between edits).

This dramatically improves perceived latency for slow-LLM responses.

### Voice Messages

The voice pipeline:

```
User sends voice message
        │
        ▼
Download OGG/OPUS file from Telegram
        │
        ▼
Convert to WAV (ffmpeg)
        │
        ▼
Transcribe (Whisper / Google Speech-to-Text / Deepgram)
        │
        ▼
Forward transcript as text message to ADK agent
        │
        ▼
(Optional) Convert agent response to audio (TTS)
        │
        ▼
Send voice response back to user
```

### Image Processing

```
User sends image
        │
        ▼
Download image from Telegram CDN
        │
        ▼
Build ADK multimodal content:
  { type: "image", data: base64_encoded, mime_type: "image/jpeg" }
        │
        ▼
ADK agent processes image (Gemini vision)
        │
        ▼
Text response sent back to user
```

### PDF Processing

```
User sends PDF document
        │
        ▼
Download PDF from Telegram
        │
        ▼
Extract text (PyMuPDF / pdfplumber)
[OR]
Pass raw bytes as ADK document content (Gemini native PDF support)
        │
        ▼
ADK agent analyzes document
        │
        ▼
Response (summary / analysis / Q&A) sent back
```

### Document Analysis Pipeline

The document analysis pipeline is configurable per MIME type. Developers register custom processors for any file type:

```python
connector.register_document_processor(
    mime_types=["text/csv"],
    processor=CSVAnalysisProcessor(),
)
```

### Multi-Agent Orchestration

The `AgentRouter` class enables routing different message types or commands to specialized agents:

- Pattern-based routing (regex matching on message text).
- Intent-based routing (a "router agent" classifies intent and delegates to specialist).
- Stateful handoff (session context transferred between agents).
- Agent chains (output of one agent becomes input of next).

### Agent Handoff

```python
from adk_connectors.routing import AgentHandoff

# Agent A can request handoff to Agent B mid-conversation
class SupportAgent(LlmAgent):
    tools = [
        AgentHandoff(
            target_agent=billing_agent,
            trigger_condition="user asks about billing or refunds"
        )
    ]
```

### Agent Memory

Integration with ADK's memory service for long-term cross-session recall:

```python
from adk_connectors.memory import LongTermMemoryMiddleware

connector.use_middleware(
    LongTermMemoryMiddleware(
        memory_service=adk_memory_service,
        recall_on_session_start=True,
    )
)
```

### Conversation History Export

```python
# Export conversation history for a user
history = await connector.session_manager.get_history("telegram:123456789")
# Returns list of IncomingMessage + OutgoingMessage objects
```

---

## 18. Security Architecture

### Webhook Verification

All incoming webhook requests are verified before processing:

**Telegram:** Verifies the `X-Telegram-Bot-Api-Secret-Token` header against a server-side secret set during webhook registration. Requests without a valid token are rejected with 4REMOVED_VALUE1.

**Discord:** Verifies the `X-Signature-Ed25519` and `X-Signature-Timestamp` headers using Ed25519 signature verification against the application's public key.

**Slack:** Verifies the `X-Slack-Signature` header using HMAC-SHA256 with the signing secret.

Verification is implemented in constant-time comparison to prevent timing attacks.

### Rate Limiting

ADK Connectors implements three layers of rate limiting:

1. **Platform-level compliance:** Respects each platform's API rate limits automatically (Telegram: 3REMOVED_VALUE msgs/sec global, 1/sec per chat).

2. **User-level limits:** Configurable per-user message rate limits to prevent runaway API costs.

3. **Global limits:** Circuit breaker pattern — if ADK agent error rate exceeds a threshold, incoming requests are queued or rejected with a user-friendly message.

### Token Security

- Bot tokens and API keys are never logged, even at DEBUG level.
- Tokens are loaded from environment variables or a secrets manager — never hardcoded.
- Token values are masked in all observability output.
- Secrets rotation is supported: tokens can be hot-reloaded without a connector restart (v2.REMOVED_VALUE).

### Secrets Management

ADK Connectors integrates with:

- Environment variables (default, 12-factor app compliant).
- AWS Secrets Manager.
- Google Cloud Secret Manager.
- HashiCorp Vault.
- Kubernetes Secrets (via environment injection).

### Encryption

- All communication with platform APIs uses HTTPS/TLS.
- Session data in Redis can be encrypted at the application layer using Fernet symmetric encryption.
- Optional field-level encryption for sensitive session fields (PII).

### Audit Logs

The `AuditLogMiddleware` produces structured audit events for every agent interaction:

```json
{
  "event": "agent_interaction",
  "timestamp": "2REMOVED_VALUE25-REMOVED_VALUE1-REMOVED_VALUE1T12:REMOVED_VALUEREMOVED_VALUE:REMOVED_VALUEREMOVED_VALUEZ",
  "platform": "telegram",
  "user_id_hash": "sha256:abc123...",
  "session_id": "sess_xyz",
  "message_length": 142,
  "response_length": 876,
  "latency_ms": 234REMOVED_VALUE,
  "tools_invoked": ["search", "calculator"],
  "error": null
}
```

User IDs are hashed by default (configurable to store plaintext for compliance systems that require it).

---

## 19. Scalability Architecture

### Horizontal Scaling

ADK Connectors is designed stateless-first: all mutable state lives in Redis, not in-process. This means any number of connector instances can run behind a load balancer, handling different webhook requests from the same bot.

```
                    ┌─────────────────┐
                    │  Load Balancer  │
                    │ (nginx / ALB)   │
                    └────────┬────────┘
              ┌──────────────┼──────────────┐
              ▼              ▼              ▼
    ┌──────────────┐ ┌──────────────┐ ┌──────────────┐
    │  Connector   │ │  Connector   │ │  Connector   │
    │  Instance 1  │ │  Instance 2  │ │  Instance N  │
    └──────┬───────┘ └──────┬───────┘ └──────┬───────┘
           └───────────────────────────────────┘
                             │
                    ┌────────▼────────┐
                    │  Redis Cluster  │
                    │ (Sessions + Lock│
                    │  + Rate Limits) │
                    └─────────────────┘
```

### Queue-Based Architecture (High Volume)

For high-volume deployments, decouple webhook reception from ADK processing:

```
Telegram
    │
    ▼
Webhook Workers (lightweight, just enqueue)
    │
    ▼
Redis Streams / Kafka / RabbitMQ
    │
    ▼
ADK Workers (heavy processing, LLM calls)
    │
    ▼
Response Queue
    │
    ▼
Delivery Workers (send responses to Telegram)
```

This architecture allows independent scaling of webhook handling capacity vs. LLM processing capacity.

### Redis Architecture

```python
# Redis keyspace design
"adk:sessions:{platform}:{user_id}"        # Session data (TTL: configurable)
"adk:locks:{platform}:{user_id}"           # Session locks (TTL: 3REMOVED_VALUEs)
"adk:rate:{platform}:{user_id}:{minute}"   # Rate limit counters (TTL: 6REMOVED_VALUEs)
"adk:queue:incoming"                        # Incoming message queue
"adk:queue:outgoing"                        # Outgoing response queue
"adk:metrics:{date}"                        # Daily metrics aggregates
```

### Worker Architecture

```python
# Scale ADK workers independently
# docker-compose.yml (simplified)
services:
  webhook-server:
    image: adk-connectors:latest
    command: ["webhook-server"]
    replicas: 3

  adk-worker:
    image: adk-connectors:latest
    command: ["worker"]
    replicas: 1REMOVED_VALUE  # Scale based on LLM throughput

  delivery-worker:
    image: adk-connectors:latest
    command: ["delivery-worker"]
    replicas: 3
```

### Auto-Scaling Signals

- Queue depth in Redis → scale up ADK workers.
- CPU usage on connector instances → scale up webhook servers.
- Redis memory usage → alert and consider session TTL reduction.

---

## 2REMOVED_VALUE. Performance Considerations

### Latency Budget

A well-optimized ADK Connectors deployment targets:

| Component | Target Latency |
|---|---|
| Webhook acknowledgement | < 5REMOVED_VALUEms |
| Update parsing | < 5ms |
| Session lookup (Redis) | < 2ms |
| Message processing | < 1REMOVED_VALUEms |
| ADK runner (LLM call) | 5REMOVED_VALUEREMOVED_VALUEms – 5REMOVED_VALUEREMOVED_VALUEREMOVED_VALUEms (model-dependent) |
| Response formatting | < 5ms |
| Telegram API send | < 2REMOVED_VALUEREMOVED_VALUEms |
| **Total (non-LLM)** | **< 3REMOVED_VALUEREMOVED_VALUEms** |
| **Total (with streaming start)** | **< 75REMOVED_VALUEms to first token** |

### Throughput Goals

- **Single connector instance:** 1REMOVED_VALUEREMOVED_VALUE+ messages/second (webhook handling + session lookup).
- **ADK worker:** Limited by LLM throughput (typically 5–5REMOVED_VALUE concurrent requests per Gemini API key).
- **Delivery worker:** 2REMOVED_VALUEREMOVED_VALUE+ response deliveries/second.

### Concurrency

- All I/O operations are `async/await` — no blocking calls in the hot path.
- ADK runner calls use asyncio semaphores to cap concurrency per API key.
- Redis operations use async Redis client (`aioredis` / `redis.asyncio`).
- HTTP calls to platform APIs use `aiohttp` / `httpx` async clients.

### Memory Optimization

- Session objects are not kept in-process memory — always fetched from Redis on demand.
- Media files (images, PDFs, voice) are processed in streaming chunks, not loaded entirely into memory.
- Response chunking uses generators, not string concatenation buffers.

### Benchmark Goals (v1.REMOVED_VALUE)

```
Message processing throughput:   > 5REMOVED_VALUEREMOVED_VALUE messages/second (parse + route + session lookup)
Session creation latency (Redis): p5REMOVED_VALUE < 2ms, p99 < 1REMOVED_VALUEms
End-to-end latency (non-LLM):    p5REMOVED_VALUE < 2REMOVED_VALUEREMOVED_VALUEms, p99 < 5REMOVED_VALUEREMOVED_VALUEms
Memory per concurrent session:   < 5REMOVED_VALUEKB (excluding LLM context)
```

---

## 21. Testing Strategy

### Unit Tests

**Framework:** `pytest` + `pytest-asyncio`

**Coverage targets:** 9REMOVED_VALUE% line coverage on `core/` package.

**What is tested:**

- `EventRouter`: correct dispatch for each event type, middleware chain execution order.
- `SessionManager`: creation, retrieval, expiry, locking logic.
- `MessageProcessor`: normalization for each message type, edge cases (empty text, huge payloads).
- `ResponseFormatter`: chunking at 4REMOVED_VALUE96 characters, Markdown conversion, code block handling.
- `ConfigManager`: validation errors, environment variable loading, secrets masking.

```bash
pytest packages/core/tests/ -v --cov=adk_connectors --cov-report=html
```

### Integration Tests

**Framework:** `pytest` + `testcontainers` (Redis in Docker)

**What is tested:**

- Full session lifecycle with real Redis backend.
- End-to-end message processing with a mock ADK agent.
- Webhook handler with real HTTP requests.
- Rate limiting behavior.
- Error recovery and retry logic.

```bash
pytest tests/integration/ -v --docker
```

### End-to-End Tests

**Framework:** `pytest` + Telegram Bot API (test environment)

Telegram provides a dedicated test environment (`api.telegram.org/bot{token}/test/`) for bot testing. E2E tests:

- Send real messages to a test bot.
- Verify responses are received correctly.
- Test media handling (images, PDFs).
- Test streaming responses.

```bash
TELEGRAM_TEST_MODE=1 pytest tests/e2e/ -v
```

### Load Tests

**Framework:** `Locust`

Simulates high-volume webhook traffic:

```python
class TelegramUserSimulation(HttpUser):
    @task
    def send_text_message(self):
        self.client.post("/webhook/test", json=generate_telegram_update())
```

Load test targets:

- 1,REMOVED_VALUEREMOVED_VALUEREMOVED_VALUE simulated users sending messages simultaneously.
- Confirm no session corruption under concurrent load.
- Confirm rate limiting kicks in correctly.
- Confirm Redis session storage performance at scale.

### Security Tests

- **Webhook signature bypass attempts:** Requests with missing/invalid signatures are rejected.
- **Rate limit evasion:** Confirm per-user limits cannot be bypassed by header manipulation.
- **Session isolation:** Confirm user A cannot access user B's session.
- **Dependency scanning:** `pip-audit` and `safety` run in CI on every PR.
- **SAST:** `bandit` static analysis on every PR.

---

## 22. Documentation Strategy

### README

The project README is optimized for first-time visitors. It follows the pattern:

1. **One-line description** — what it is.
2. **Three-line quickstart** — get a bot running immediately.
3. **Feature list** — why this, not DIY.
4. **Installation** — `pip install adk-connectors-telegram`.
5. **Links to docs** — for more complex use cases.

The README is the most important marketing asset. It is optimized for developer conversion, not technical completeness.

### Architecture Documentation

This document (`ARCHITECTURE.md`) serves as the canonical reference for:

- Understanding the project's design decisions.
- Onboarding new contributors.
- Investor and partner technical due diligence.
- Developer advocacy presentations.

### Tutorials (docs/guides/)

Step-by-step tutorials for common use cases:

- "Deploy your first ADK bot to Telegram in 1REMOVED_VALUE minutes."
- "Adding Redis session storage for production."
- "Handling images and documents."
- "Streaming responses for responsive UX."
- "Building a multi-agent system with handoff."
- "Deploying to Railway / Render / Fly.io."
- "Writing your first custom connector."

### API Reference (docs/api-reference/)

Auto-generated from Python docstrings using `mkdocs` + `mkdocstrings`. Updated on every release.

### Examples

Every example in `examples/` is a complete, runnable project. Examples are the most-used documentation — more than any written guide. Each example has:

- A clear description of what it demonstrates.
- Step-by-step setup instructions.
- Expected output.
- Common variations and extensions.

### Video Tutorials

YouTube channel (`ADK Connectors`) with:

- "Build a Telegram AI bot in 5 minutes" (quickstart).
- "Session management explained."
- "Streaming responses demo."
- "Production deployment walkthrough."
- "Building a custom connector."

---

## 23. Open Source Growth Strategy

### Attracting Contributors

**Low barrier to entry:**

- First-time contributor issues labeled `good first issue` — always available.
- Contributing guide that explains how to run the project locally in under 5 minutes.
- Architectural documentation (this file) that makes the codebase immediately understandable.

**High impact for contributors:**

- Contributors who build new connectors (Discord, Slack) get credited as co-maintainers.
- Community spotlights in blog posts and README.
- Reference in "made with ADK Connectors" showcase.

**Responsive maintainership:**

- PR review SLA: 48 hours for feedback.
- Regular office hours (Discord voice channel, weekly).
- Decision records documented publicly (`docs/decisions/`).

### Attracting GitHub Stars

**Launch strategy:**

- Hacker News "Show HN" post on launch day.
- ProductHunt launch coordinated with HN.
- Reddit posts to r/googlecloud, r/MachineLearning, r/Python, r/selfhosted.
- Twitter/X thread with demo GIF.
- LinkedIn article targeting AI engineers.

**Ongoing:**

- Release notes that highlight community contributions.
- "What's new" blog posts with demos on every minor release.
- GitHub star milestone celebrations (1REMOVED_VALUEREMOVED_VALUE, 5REMOVED_VALUEREMOVED_VALUE, 1K, 5K) with community posts.

### Growing Community

- Discord server with channels: `#general`, `#showcase`, `#help`, `#contributors`, `#feature-requests`.
- Monthly community calls (Zoom / Google Meet).
- Newsletter (substack or beehiiv) for project updates.
- "Showcase" page on docs website for community-built bots.

### Becoming the Default ADK Integration Package

**The path to default:**

1. First mover: be the first credible, well-maintained Telegram connector for ADK.
2. Google ADK documentation: pursue inclusion in official Google ADK docs as a recommended community integration.
3. Template repositories: provide GitHub template repos that include `adk-connectors` pre-configured.
4. Google Cloud Marketplace: list ADK Connectors as a solution on Google Cloud Marketplace.
5. ADK tutorials: appear in tutorial results for "google adk telegram bot" on Google Search.

---

## 24. Download Growth Strategy

### PyPI Growth

**Package naming SEO:** Package names on PyPI are search terms. `adk-connectors-telegram` and `adk-connectors-discord` will appear in PyPI search for "adk telegram" and "adk discord."

**Dependency encouragement:** Once well-established, submit PRs to popular ADK example repositories suggesting ADK Connectors for deployment.

**Quality signals:** High test coverage badges, active CI status, clear documentation — all visible on PyPI and GitHub, increasing developer trust.

### SEO Strategy

Target keywords:

- "google adk telegram bot"
- "google adk discord bot"
- "google adk messaging platform"
- "google agent development kit telegram"
- "adk agent connector"

**Content:** A blog on the documentation website publishing articles targeting these keywords, with code examples that naturally link to the package.

### YouTube Content Strategy

**Channel name:** "ADK Connectors" or "Build AI Bots with ADK"

**Content calendar (Month 1–3):**

- Week 1: "Build a Telegram AI Bot in 5 minutes" (high-volume keyword).
- Week 2: "Google ADK + Telegram: Complete Tutorial."
- Week 3: "Streaming AI Responses in Telegram Bots."
- Week 4: "Deploy Your ADK Bot to Production."

Videos include timestamps, description links to docs, GitHub repo link. YouTube drives sustainable organic traffic to docs and GitHub.

### Developer Advocacy Strategy

**Developer Relations activities:**

- Speak at Google Developer Groups (GDG) meetups about ADK Connectors.
- Submit to Google DevFest and Google I/O sessions.
- Guest posts on Google Cloud blog, Towards Data Science, The New Stack.
- Partner with Google ADK developer advocates.

### Community Building

- **Discord:** Announce on ADK-related Discord servers and subreddits.
- **Twitter/X:** Regular updates with demo videos, feature highlights, and community showcases. Target: 1,REMOVED_VALUEREMOVED_VALUEREMOVED_VALUE followers in Year 1.
- **LinkedIn:** Technical articles targeting AI engineers and startup CTOs. LinkedIn drives enterprise awareness.
- **Reddit:** Active presence in r/googlecloud, r/Python, r/MachineLearning, r/singularity, r/selfhosted.

### Launch Strategy (Day 1 Playbook)

1. **T-7 days:** Prepare demo video, blog post, README, landing page.
2. **T-1 day:** Pre-publish to PyPI. Prepare social posts.
3. **Launch day (Tuesday morning UTC):**
   - Post "Show HN" on Hacker News.
   - Launch on ProductHunt.
   - Publish Reddit posts (staggered by 2 hours per subreddit).
   - Publish Twitter/X thread with demo GIF.
   - Publish LinkedIn article.
4. **T+1 day:** Respond to all comments. Gather feedback. Fix any reported issues.
5. **T+7 days:** "Week 1 wrap-up" post with stats and feedback.

### Conference Strategy

- Target: PyCon US, Google I/O, Google Cloud Next, AI Engineer Summit, local GDG events.
- Talk proposal: "Zero to Production: Deploying Google ADK Agents to Messaging Platforms."
- Workshop: "Build and Deploy a Telegram AI Bot in 6REMOVED_VALUE Minutes."

### Hackathon Strategy

- Provide ADK Connectors as a recommended integration for Google ADK hackathons.
- Create "ADK Connectors Starter Kit" specifically for hackathon participants.
- Offer mentor support in hackathon Discord channels.

---

## 25. Monetization Possibilities

### Open Source Model (Always Free)

The core framework (`adk-connectors-core`) and all platform connectors (`telegram`, `discord`, `slack`, `whatsapp`) remain MIT-licensed and permanently free. This is the foundation of community trust and adoption.

### Cloud Hosting (Freemium SaaS)

**ADK Connectors Cloud** — managed connector hosting:

| Tier | Price | Connectors | Messages/Month | Sessions |
|---|---|---|---|---|
| Free | $REMOVED_VALUE | 1 | 1,REMOVED_VALUEREMOVED_VALUEREMOVED_VALUE | 1REMOVED_VALUEREMOVED_VALUE |
| Starter | $19/month | 3 | 5REMOVED_VALUE,REMOVED_VALUEREMOVED_VALUEREMOVED_VALUE | 1,REMOVED_VALUEREMOVED_VALUEREMOVED_VALUE |
| Growth | $79/month | 1REMOVED_VALUE | 5REMOVED_VALUEREMOVED_VALUE,REMOVED_VALUEREMOVED_VALUEREMOVED_VALUE | 1REMOVED_VALUE,REMOVED_VALUEREMOVED_VALUEREMOVED_VALUE |
| Scale | $299/month | Unlimited | 5,REMOVED_VALUEREMOVED_VALUEREMOVED_VALUE,REMOVED_VALUEREMOVED_VALUEREMOVED_VALUE | Unlimited |

### Managed Platform

**Premium Cloud Features:**

- Analytics dashboard (message volume, response latency, user retention).
- A/B testing for agent prompts.
- Conversation review UI.
- Automated error alerting.
- Custom domain webhook hosting.

### Enterprise Support

**Enterprise License:** $5,REMOVED_VALUEREMOVED_VALUEREMOVED_VALUE–$5REMOVED_VALUE,REMOVED_VALUEREMOVED_VALUEREMOVED_VALUE/year depending on organization size.

- Named technical account manager.
- 4-hour SLA for critical issues.
- Private Slack channel with maintainers.
- Security review assistance.
- Custom feature development.
- On-premises deployment support.

### Premium Features

**Optional paid add-ons (open-core model):**

- Advanced analytics (conversation flow visualization, retention cohorts).
- Compliance add-on (GDPR data export, retention policies, PII masking).
- White-label connector (deploy under custom bot name/brand).
- Multi-region session storage.

### Connector Marketplace

A curated marketplace of community-built connectors and plugins:

- Free connectors listed for discovery.
- Premium connectors (e.g., WhatsApp Enterprise, LINE Official Account, custom CRM integrations) sold by their creators, with ADK Connectors taking a 2REMOVED_VALUE–3REMOVED_VALUE% platform fee.

---

## 26. Competitive Analysis

### Comparison: ADK Connectors vs. Custom Implementation

| Dimension | ADK Connectors | Custom DIY |
|---|---|---|
| Time to first working bot | 1REMOVED_VALUE minutes | 1–3 days |
| Session management | Built-in, production-grade | Built from scratch, often buggy |
| Streaming support | Native | Requires significant async engineering |
| Multi-platform expansion | Add one import | Rewrite from scratch per platform |
| Error handling | Built-in, configurable | Often missing initially |
| Rate limiting | Built-in | Often missing or wrong |
| Production readiness | From day one | After significant refactoring |
| Maintainability | High (clear separation of concerns) | Low (tangled platform + agent code) |
| Community support | GitHub issues + Discord | None |

### Comparison: ADK Connectors vs. Generic Bot Frameworks

| Feature | ADK Connectors | python-telegram-bot | aiogram | Botpress |
|---|---|---|---|---|
| ADK-native | ✅ Purpose-built | ❌ Not ADK-aware | ❌ Not ADK-aware | ❌ Own agent system |
| Session → ADK mapping | ✅ Built-in | ❌ Manual | ❌ Manual | N/A |
| Streaming ADK responses | ✅ Native | ❌ Not supported | ❌ Not supported | ❌ |
| Multi-platform (same agent) | ✅ Core feature | ❌ Telegram-only | ❌ Telegram-only | Limited |
| Plugin system | ✅ First-class | Limited | Limited | ✅ |
| ADK session storage | ✅ Redis/SQL/Memory | N/A | N/A | Own storage |
| Open source | ✅ MIT | ✅ LGPL | ✅ MIT | Freemium |
| Python | ✅ | ✅ | ✅ | ❌ (Node.js) |

### Comparison: ADK Connectors vs. Other AI Agent Frameworks

| Feature | ADK Connectors | LangChain Callbacks | AutoGen Studio | CrewAI Deploy |
|---|---|---|---|---|
| Google ADK support | ✅ Native | ❌ | ❌ | ❌ |
| Telegram connector | ✅ | ❌ | ❌ | ❌ |
| Production-ready | ✅ | ❌ (callbacks only) | Limited | Limited |
| Session management | ✅ | ❌ | ❌ | ❌ |
| Multi-platform | ✅ Roadmap | ❌ | ❌ | ❌ |
| Open source | ✅ | ✅ | ✅ | ✅ |

**Conclusion:** ADK Connectors occupies a unique, uncontested position: production-grade, ADK-native, multi-platform messaging transport. No existing framework or library fills this gap.

---

## 27. Development Roadmap

### Phase 1: Foundation and MVP (Weeks 1–4)

**Goal:** A working Telegram connector that passes quality bar for open-source release.

**Milestones:**

- [ ] Core package scaffolding (`BaseAdapter`, `SessionManager`, `EventRouter`, `MessageProcessor`, `ResponseFormatter`).
- [ ] In-memory session storage backend.
- [ ] Telegram adapter with webhook + long-polling support.
- [ ] Text message handling (inbound + outbound).
- [ ] Basic response formatting (Markdown → Telegram HTML, chunking).
- [ ] Configuration system (Pydantic + env vars).
- [ ] Unit test suite (target: 8REMOVED_VALUE% coverage).
- [ ] README and quickstart documentation.
- [ ] `pip install adk-connectors-telegram` works.

**Deliverable:** Quickstart example deploys a working Telegram bot in < 1REMOVED_VALUE minutes.

---

### Phase 2: Telegram Production Release (Weeks 5–8)

**Goal:** Feature-complete, production-hardened Telegram connector ready for real workloads.

**Milestones:**

- [ ] Redis session storage backend.
- [ ] Streaming response support (edit message pattern).
- [ ] Image processing pipeline (download → ADK vision input).
- [ ] PDF text extraction.
- [ ] Voice message transcription (Whisper integration).
- [ ] Rate limiting (per-user and global).
- [ ] Retry logic with exponential backoff.
- [ ] Webhook signature verification.
- [ ] Inline keyboard support.
- [ ] Structured logging + basic observability.
- [ ] Integration test suite.
- [ ] Docker deployment template.
- [ ] Railway / Render deployment guides.
- [ ] v1.REMOVED_VALUE.REMOVED_VALUE release and launch.

**Deliverable:** v1.REMOVED_VALUE.REMOVED_VALUE PyPI release. Launch campaign. Target: 5REMOVED_VALUEREMOVED_VALUE GitHub stars within 2 weeks of launch.

---

### Phase 3: Discord Connector (Weeks 9–14)

**Goal:** Full Discord connector with slash command support and thread-based conversations.

**Milestones:**

- [ ] Discord adapter implementation.
- [ ] Slash command registration and routing.
- [ ] Guild + DM context management.
- [ ] Embed-formatted responses.
- [ ] Thread-based conversations.
- [ ] Multi-platform session management (shared Redis).
- [ ] Discord-specific response formatter.
- [ ] Examples and documentation.
- [ ] v2.REMOVED_VALUE.REMOVED_VALUE release.

---

### Phase 4: Slack Connector (Weeks 15–22)

**Goal:** Enterprise-ready Slack connector.

**Milestones:**

- [ ] Slack Bolt integration.
- [ ] App mentions and DM handling.
- [ ] Block Kit response formatter.
- [ ] Slash commands.
- [ ] Home tab support.
- [ ] Slack Enterprise Grid compatibility.
- [ ] v3.REMOVED_VALUE.REMOVED_VALUE release.

---

### Phase 5: WhatsApp Connector (Weeks 23–3REMOVED_VALUE)

**Goal:** WhatsApp Business API connector.

**Milestones:**

- [ ] WhatsApp Cloud API integration.
- [ ] Template message support.
- [ ] Interactive buttons and lists.
- [ ] Media messaging.
- [ ] v4.REMOVED_VALUE.REMOVED_VALUE release.

---

### Phase 6: Universal Connector SDK (Month 9–12)

**Goal:** First-class SDK for third-party connector development.

**Milestones:**

- [ ] Connector SDK with full documentation.
- [ ] Connector validation test suite.
- [ ] Connector registry (GitHub-based discovery).
- [ ] Community connectors: Microsoft Teams, LINE, SMS.
- [ ] Connector marketplace (GitHub topic + website showcase).
- [ ] v5.REMOVED_VALUE.REMOVED_VALUE release.

---

### Phase 7: Hosted Cloud Platform (Month 12–18)

**Goal:** Managed connector hosting as SaaS product.

**Milestones:**

- [ ] Web dashboard MVP.
- [ ] One-click connector deployment.
- [ ] Basic analytics (message volume, latency).
- [ ] Freemium billing integration (Stripe).
- [ ] v6.REMOVED_VALUE.REMOVED_VALUE release. Private beta launch.

---

### Phase 8: Enterprise Features (Month 18–24)

**Goal:** Enterprise-grade managed platform.

**Milestones:**

- [ ] SSO / SAML integration.
- [ ] Audit logs with compliance export.
- [ ] Dedicated infrastructure option.
- [ ] Enterprise support tier.
- [ ] SOC2 Type II audit.
- [ ] v7.REMOVED_VALUE.REMOVED_VALUE release.

---

## 28. Risks and Challenges

### Technical Risks

**Risk: Google ADK API breaking changes.**
Google ADK is relatively new (2REMOVED_VALUE24). Its internal APIs may change. ADK Connectors must track ADK releases closely and maintain compatibility.
*Mitigation:* Pin to stable ADK versions. Maintain a compatibility matrix. Set up automated tests against new ADK releases.

**Risk: Platform API deprecation or changes.**
Telegram, Discord, Slack have occasionally made breaking changes to their bot APIs.
*Mitigation:* Abstract platform APIs behind adapter interfaces. When a platform changes, only the adapter changes — core logic is unaffected.

**Risk: Streaming architecture complexity.**
Streaming responses across async boundaries, with correct rate limiting and error recovery, is complex to implement correctly.
*Mitigation:* Extensive async tests. Load testing under concurrent streaming requests. Conservative defaults with clear documentation.

**Risk: Session locking bugs under high concurrency.**
Incorrect session locking leads to race conditions that corrupt conversation history.
*Mitigation:* Comprehensive concurrent-access tests. Redis-based distributed locking with short TTLs and automatic expiry.

### Business Risks

**Risk: Google builds official connectors.**
If Google releases official Telegram/Slack connectors for ADK, it could reduce demand for ADK Connectors.
*Mitigation:* ADK Connectors adds value beyond basic connectivity: session management, multi-platform uniformity, plugin system, streaming, media handling, observability. Community and integrations create switching costs. Position as "the community standard" before any official offering appears.

**Risk: Low adoption if Google ADK itself fails to gain traction.**
ADK Connectors' success is tied to ADK adoption.
*Mitigation:* Design the connector layer to be framework-agnostic. LangChain, LlamaIndex, and other frameworks could be supported by adding framework-specific adapters. Diversification hedge.

**Risk: Monetization path uncertainty.**
Open-source projects struggle to convert free users to paid tiers.
*Mitigation:* Focus on building real value in the cloud tier (analytics, managed infrastructure). Enterprise support is a proven monetization model for open-source infrastructure tools.

### Open Source Risks

**Risk: Maintainer burnout.**
Single-maintainer projects frequently stall and lose community trust.
*Mitigation:* Build a co-maintainer team from day one. Document processes to reduce maintainer cognitive load. Set explicit SLAs that are achievable (48hr PR review, not 24hr).

**Risk: Toxic community.**
Open-source projects can attract entitled or abusive community members.
*Mitigation:* Publish and enforce a Code of Conduct from day one. Set clear expectations in CONTRIBUTING.md. Use GitHub's moderation tools.

**Risk: License conflicts.**
Dependency licenses might conflict with MIT distribution.
*Mitigation:* Regular dependency license audits using `pip-licenses`. Avoid GPL/AGPL dependencies.

### Scaling Risks

**Risk: Redis as single point of failure.**
If Redis is unavailable, the connector cannot process messages (in production Redis mode).
*Mitigation:* Support Redis Sentinel and Redis Cluster for HA. Document fallback to in-memory mode for resilience.

**Risk: ADK API cost explosion.**
At scale, LLM API costs could become unsustainable.
*Mitigation:* Built-in cost estimation tools. Per-user and global rate limiting. Caching layer for repeated identical queries (optional middleware).

---

## 29. Success Metrics

### GitHub Metrics

| Metric | 3 Months | 6 Months | 12 Months | 24 Months |
|---|---|---|---|---|
| GitHub Stars | 5REMOVED_VALUEREMOVED_VALUE | 1,5REMOVED_VALUEREMOVED_VALUE | 5,REMOVED_VALUEREMOVED_VALUEREMOVED_VALUE | 15,REMOVED_VALUEREMOVED_VALUEREMOVED_VALUE |
| Contributors | 1REMOVED_VALUE | 25 | 75 | 2REMOVED_VALUEREMOVED_VALUE |
| Open Issues | < 2REMOVED_VALUE | < 3REMOVED_VALUE | < 5REMOVED_VALUE | < 75 |
| PR Merge Time (p5REMOVED_VALUE) | 48h | 36h | 24h | 24h |

### Download Metrics

| Metric | 3 Months | 6 Months | 12 Months | 24 Months |
|---|---|---|---|---|
| PyPI Monthly Downloads | 1,REMOVED_VALUEREMOVED_VALUEREMOVED_VALUE | 5,REMOVED_VALUEREMOVED_VALUEREMOVED_VALUE | 25,REMOVED_VALUEREMOVED_VALUEREMOVED_VALUE | 1REMOVED_VALUEREMOVED_VALUE,REMOVED_VALUEREMOVED_VALUEREMOVED_VALUE |
| Cumulative Installs | 3,REMOVED_VALUEREMOVED_VALUEREMOVED_VALUE | 15,REMOVED_VALUEREMOVED_VALUEREMOVED_VALUE | 8REMOVED_VALUE,REMOVED_VALUEREMOVED_VALUEREMOVED_VALUE | 4REMOVED_VALUEREMOVED_VALUE,REMOVED_VALUEREMOVED_VALUEREMOVED_VALUE |

### Community Metrics

| Metric | 3 Months | 6 Months | 12 Months | 24 Months |
|---|---|---|---|---|
| Discord Members | 1REMOVED_VALUEREMOVED_VALUE | 4REMOVED_VALUEREMOVED_VALUE | 1,5REMOVED_VALUEREMOVED_VALUE | 5,REMOVED_VALUEREMOVED_VALUEREMOVED_VALUE |
| Twitter/X Followers | 2REMOVED_VALUEREMOVED_VALUE | 8REMOVED_VALUEREMOVED_VALUE | 3,REMOVED_VALUEREMOVED_VALUEREMOVED_VALUE | 1REMOVED_VALUE,REMOVED_VALUEREMOVED_VALUEREMOVED_VALUE |
| Newsletter Subscribers | 1REMOVED_VALUEREMOVED_VALUE | 5REMOVED_VALUEREMOVED_VALUE | 2,REMOVED_VALUEREMOVED_VALUEREMOVED_VALUE | 8,REMOVED_VALUEREMOVED_VALUEREMOVED_VALUE |

### Adoption Metrics

| Metric | 6 Months | 12 Months | 24 Months |
|---|---|---|---|
| Public bots using ADK Connectors | 5REMOVED_VALUE | 5REMOVED_VALUEREMOVED_VALUE | 5,REMOVED_VALUEREMOVED_VALUEREMOVED_VALUE |
| Enterprise users (known) | 2 | 15 | 75 |
| Connector packages published (community) | 2 | 8 | 25 |

### Retention Metrics

- 3REMOVED_VALUE-day active developer retention (developers who install and continue using): target 4REMOVED_VALUE% at 12 months.
- Issue resolution rate: 9REMOVED_VALUE% of reported bugs resolved within 14 days.
- Documentation NPS: target > 6REMOVED_VALUE.

---

## 3REMOVED_VALUE. Final Vision

### The Standard Communication Layer for AI Agents

In 2REMOVED_VALUE15, if you were building a web API in Node.js, you used Express. Not because there were no alternatives — there were many — but because Express had become the community standard. It was well-documented, widely understood, well-tested, and had a rich ecosystem of middleware. Choosing Express meant your codebase would be immediately understood by every other Node.js developer on the planet.

ADK Connectors aspires to occupy the same position in the AI agent ecosystem.

When an AI engineer picks up Google ADK to build an agent in 2REMOVED_VALUE26, they should not need to ask "how do I deploy this to Telegram?" The answer should be so well-known, so standard, so obvious, that it requires no research: you use ADK Connectors. One import, three lines, done.

### The Infrastructure Behind a Million AI Agents

The near future contains a world in which every organization of any significant size deploys AI agents to communicate with their customers, employees, and partners. These agents live where humans live: Telegram, Discord, Slack, WhatsApp, Teams.

ADK Connectors will be the transport layer silently powering these millions of agent deployments. Not because it outmarketed its competition, but because it was the best, most reliable, best-documented, most community-supported solution available — and it got there first.

### Beyond Transport: An Ecosystem

As the connector layer matures, it becomes the foundation for a broader ecosystem:

- **The Connector Marketplace:** A registry of hundreds of community-built connectors — LINE for Japan, KakaoTalk for Korea, Viber for Eastern Europe, WeChat for China, custom enterprise connectors for internal tools. Every developer's agent, reaching every user, on every platform, with a single integration.

- **The Analytics Layer:** ADK Connectors Cloud provides the only cross-platform conversation analytics platform for ADK agents — unified data from Telegram, Discord, and Slack in one dashboard, enabling AI engineers to understand how users interact with their agents across all surfaces.

- **The Enterprise Standard:** Fortune 5REMOVED_VALUEREMOVED_VALUE companies deploying internal AI assistants to Microsoft Teams or Slack will require an enterprise-grade connector with audit logs, SSO, SLA support, and compliance features. ADK Connectors Enterprise will be that product.

- **The Open Standard:** The `BaseAdapter` interface published by ADK Connectors will become the de facto community standard for platform adapter design in the Google ADK ecosystem — referenced in ADK's official documentation, taught in tutorials, and assumed knowledge for any AI engineer working with ADK.

### A Letter to Future Contributors

You are reading this document because you are considering contributing to ADK Connectors. Here is what we promise you:

Your contributions will matter. Every line of code you write could be running inside thousands of production AI deployments within months. The ecosystem you help build will reduce friction for thousands of developers and accelerate the deployment of AI that helps real users solve real problems.

The architecture is designed to be understandable. We have worked hard to ensure that the codebase is clean, the interfaces are clear, and the contribution process is frictionless. You should be able to understand the entire system in an afternoon and make your first meaningful contribution in a weekend.

The community will be kind. Open source is at its best when it is welcoming, generous, and collaborative. We are committed to maintaining a community where every contributor — beginner or veteran — is treated with respect and gratitude.

Join us. Let's build the standard.

---

*ADK Connectors — Connect. Deploy. Scale.*

*Licensed under the MIT License. Contributions welcome. Stars appreciated.*

*GitHub: github.com/your-org/adk-connectors*
*Documentation: docs.adk-connectors.dev*
*Discord: discord.gg/adk-connectors*
*PyPI: pypi.org/project/adk-connectors-telegram*

---

*Document version: 1.REMOVED_VALUE.REMOVED_VALUE | Last updated: 2REMOVED_VALUE25 | Maintained by the ADK Connectors Core Team*