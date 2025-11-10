# Agreement Map Documentation

Welcome to the Agreement Map documentation! This directory contains all project documentation organized by type and purpose.

---

## 📁 Documentation Structure

```
docs/
├── README.md                    ← You are here
├── architecture/                ← Technical setup and integration guides
├── decisions/                   ← Architecture Decision Records (ADRs)
├── guides/                      ← User guides and tutorials
├── roadmap/                     ← Product roadmaps (date-stamped)
└── archive/                     ← Deprecated documentation
```

---

## 📚 Documentation Categories

### 🏗️ Architecture (`architecture/`)

**Purpose**: Technical documentation for system setup, integrations, and infrastructure.

**Contents**:
- **SUPABASE_SETUP.md** - Database setup guide for persistent storage
- **TAVILY_INTEGRATION.md** - Web search API integration guide

**Audience**: Developers, DevOps, System Administrators

**When to use**:
- Setting up the application for the first time
- Configuring external services (Supabase, Tavily)
- Deploying to Streamlit Cloud
- Troubleshooting infrastructure issues

---

### 🧠 Decisions (`decisions/`)

**Purpose**: Architecture Decision Records (ADRs) documenting **why** key technical decisions were made.

**Format**: Each ADR follows a standard template:
- **Context**: What problem were we solving?
- **Decision**: What did we decide to do?
- **Alternatives Considered**: What other options did we evaluate?
- **Consequences**: What are the trade-offs?
- **Status**: Implemented, Proposed, Superseded

**Contents**:
1. **001-supabase-storage-migration.md** - Why we chose Supabase over Google Sheets
2. **002-quote-verification-system.md** - How we verify executive quotes and calculate confidence scores
3. **003-parallel-research-architecture.md** - Why we use asyncio for concurrent research phases

**Audience**: Developers, Technical Leads, Future Team Members

**When to use**:
- Understanding why the system is architected the way it is
- Evaluating whether to change an existing decision
- Onboarding new developers to the project
- Reviewing trade-offs before making new technical choices

**Why ADRs matter**:
> "If you don't document your decisions, you'll spend time re-litigating the same debates in 6 months."

ADRs capture the **context** and **rationale** behind decisions, not just the outcomes. This prevents:
- ❌ Repeating failed experiments
- ❌ Undoing good decisions without understanding trade-offs
- ❌ Making changes that conflict with architectural principles

---

### 📖 Guides (`guides/`)

**Purpose**: Step-by-step tutorials and how-to guides for end users.

**Contents**:
- **user-guide-sales-team.md** - Comprehensive guide for DocuSign sales representatives

**Audience**: End Users (Sales Teams, Business Users)

**When to use**:
- First-time users learning the application
- Training new team members
- Reference during daily use
- Troubleshooting common issues

**Planned Guides** (Future):
- Admin guide for managing Supabase storage
- Developer guide for extending the application
- API integration guide for custom workflows

---

### 🗺️ Roadmap (`roadmap/`)

**Purpose**: Product roadmaps outlining priorities, features, and timelines. **Date-stamped** to track evolution.

**Contents**:
- **roadmap-2024-10-31.md** - Original roadmap (Supabase migration, research enhancement, cost optimization)
- **roadmap-2024-11-10.md** - Current roadmap (post-Supabase migration, next priorities)

**Audience**: Product Managers, Developers, Stakeholders

**When to use**:
- Planning development sprints
- Prioritizing features
- Understanding project history and direction
- Communicating with stakeholders

**Roadmap Philosophy**:
- Roadmaps are **dated** and **versioned** to track how priorities evolve
- Old roadmaps are **kept** (not deleted) to show decision-making history
- Each roadmap reflects **current priorities** at that moment in time

---

### 🗄️ Archive (`archive/`)

**Purpose**: Deprecated documentation that's no longer relevant but kept for historical reference.

**Contents**:
- **GOOGLE_SHEETS_SETUP.md** - Setup guide for Google Sheets storage (replaced by Supabase)

**Audience**: Developers researching project history

**When to use**:
- Understanding what was tried before
- Migrating old data or configurations
- Historical research (e.g., "Why did we stop using Google Sheets?")

**Archive Policy**:
- Documentation is **archived** (not deleted) when superseded
- Archived docs are marked with "DEPRECATED" notice at the top
- Archived docs reference the replacement (e.g., "See SUPABASE_SETUP.md instead")

---

## 🔍 Finding What You Need

### I want to...

**...set up the application for the first time**
→ Start with main `README.md` in project root
→ Then: `architecture/SUPABASE_SETUP.md`, `architecture/TAVILY_INTEGRATION.md`

**...understand why a technical decision was made**
→ Check `decisions/` for relevant ADR (e.g., "Why Supabase?" → `001-supabase-storage-migration.md`)

**...learn how to use the application**
→ Read `guides/user-guide-sales-team.md`

**...know what features are planned**
→ Check latest roadmap in `roadmap/` (sorted by date, newest = latest priorities)

**...troubleshoot an issue**
→ Start with `guides/user-guide-sales-team.md#troubleshooting`
→ Then: Relevant architecture docs

**...contribute to the project**
→ Read latest roadmap, check open issues, review ADRs to understand architecture

---

## ✍️ Contributing to Documentation

### When to Create New Documentation

**Architecture Docs**: When adding new integrations, infrastructure, or setup requirements
**ADRs**: When making significant technical decisions (database choice, API design, major refactors)
**Guides**: When adding features that change user workflows
**Roadmaps**: Quarterly or when priorities shift significantly

### Documentation Standards

#### File Naming Conventions

```
architecture/     → UPPERCASE_WITH_UNDERSCORES.md
decisions/        → ###-lowercase-with-dashes.md (numbered)
guides/           → lowercase-with-dashes.md
roadmap/          → roadmap-YYYY-MM-DD.md (date-stamped)
```

#### ADR Numbering

ADRs are **numbered sequentially**:
- `001-first-decision.md`
- `002-second-decision.md`
- `003-third-decision.md`

**Never reuse numbers**, even if an ADR is superseded. Superseded ADRs are marked with `Status: Superseded by ADR XXX`.

#### Markdown Style

- Use **emoji** for visual hierarchy (📁 folders, 🏗️ categories)
- Include **table of contents** for docs >500 lines
- Use **code blocks** with language identifiers
- Add **examples** wherever possible
- Keep line length **≤120 characters** for readability

#### Roadmap Conventions

- **Date-stamp filenames**: `roadmap-2024-11-10.md`
- **Include "Date" and "Status"** in frontmatter
- **Keep old roadmaps**: Don't delete; archive instead
- **Link to previous roadmap**: Show continuity

---

## 📊 Documentation Metrics

**Current Stats** (as of November 10, 2024):

- **Architecture Docs**: 2 active, 1 archived
- **ADRs**: 3 (Supabase, Quote Verification, Parallel Research)
- **User Guides**: 1 (Sales Team)
- **Roadmaps**: 2 (Oct 31, Nov 10)
- **Total Pages**: ~50 pages of documentation

**Coverage**:
- ✅ Setup/Installation: Complete
- ✅ Architecture Decisions: Well-documented
- ✅ User Workflows: Comprehensive
- ⚠️ API Documentation: Not yet needed (no public API)
- ⚠️ Testing Guide: To be created

---

## 🔗 Related Resources

### External Documentation

- **Streamlit Docs**: https://docs.streamlit.io
- **OpenAI API Docs**: https://platform.openai.com/docs
- **Supabase Docs**: https://supabase.com/docs
- **Tavily API Docs**: https://tavily.com/docs

### Internal Resources

- **Main README**: `../README.md` (project overview, quick start)
- **Source Code**: `../` (Python modules with inline documentation)
- **Requirements**: `../requirements.txt` (dependencies)

---

## 📝 Documentation Roadmap

### Planned Documentation (Future)

**Short Term**:
- [ ] Developer Setup Guide (local development environment)
- [ ] Contribution Guide (how to contribute code)
- [ ] Testing Guide (running tests, writing new tests)

**Medium Term**:
- [ ] API Documentation (if/when public API is added)
- [ ] Deployment Guide (Streamlit Cloud, Docker, etc.)
- [ ] Performance Optimization Guide

**Long Term**:
- [ ] Video Tutorials (screen recordings for common workflows)
- [ ] FAQ Database (searchable knowledge base)
- [ ] Internationalization Guide (when multi-language support added)

---

## 🤝 Getting Help

### Documentation Questions

- **Missing Documentation?** [Open an issue](https://github.com/your-org/agreement-map/issues)
- **Found an Error?** Submit a pull request or open an issue
- **Need Clarification?** Contact the development team

### Contributing Documentation

We welcome documentation contributions! To add or update docs:

1. **Check existing docs** to avoid duplication
2. **Follow naming conventions** above
3. **Use the appropriate directory** (architecture, decisions, guides, roadmap)
4. **Include examples** where helpful
5. **Submit a pull request** with clear description

**Good PR descriptions**:
- ✅ "Add ADR for caching strategy decision"
- ✅ "Update Supabase setup guide with RLS instructions"
- ✅ "Fix broken link in user guide"

**Poor PR descriptions**:
- ❌ "Update docs"
- ❌ "Changes"

---

## 📚 Documentation Philosophy

### Why We Document

> "Code tells you how. Comments tell you why. Documentation tells you what."

**Benefits**:
- 🚀 **Faster Onboarding**: New team members get up to speed quickly
- 🐛 **Fewer Bugs**: Understanding architecture prevents mistakes
- 💡 **Better Decisions**: ADRs prevent repeating past debates
- 🤝 **Collaboration**: Shared understanding across team
- 📈 **Scalability**: Documentation scales better than tribal knowledge

### Documentation Principles

1. **Document Decisions, Not Just Outcomes**: Explain **why**, not just **what**
2. **Show, Don't Just Tell**: Use examples, code snippets, screenshots
3. **Keep It Current**: Update docs when code changes (treat as part of development)
4. **Write for Your Future Self**: In 6 months, you won't remember why you made that choice
5. **Organize by Purpose**: Architecture ≠ Decisions ≠ Guides ≠ Roadmap

### When Documentation is Done

Documentation is **never finished**, but it's **good enough** when:
- ✅ New users can set up the system without help
- ✅ Developers understand architectural decisions
- ✅ Users can complete common tasks using guides
- ✅ Technical decisions are recorded with rationale

---

## 🎯 Quick Links

| I want to...                    | Go to...                                         |
|--------------------------------|--------------------------------------------------|
| Set up Supabase storage        | `architecture/SUPABASE_SETUP.md`                 |
| Understand the verification system | `decisions/002-quote-verification-system.md` |
| Learn how to use the app       | `guides/user-guide-sales-team.md`                |
| See what's coming next         | `roadmap/roadmap-2024-11-10.md`                  |
| Understand parallel execution  | `decisions/003-parallel-research-architecture.md`|

---

**Last Updated**: November 10, 2024
**Maintained By**: Development Team
**Questions?** Open an issue or contact the team
