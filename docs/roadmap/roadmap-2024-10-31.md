# Agreement Map - Product Roadmap

## Overview
This roadmap outlines the next three major initiatives to improve the Agreement Map application. Priorities are based on immediate technical needs, research quality improvements, and operational efficiency.

---

## Priority 1: Supabase Storage Migration

### Motivation
- **Current Issue**: Google Sheets integration is experiencing technical difficulties and not functioning reliably
- **Why Supabase**: Production-grade PostgreSQL database with built-in authentication, real-time capabilities, and Streamlit-friendly SDK
- **Benefits**:
  - Reliable persistent storage that works on Streamlit Cloud
  - Fast querying and filtering of saved analyses
  - No dependency on external spreadsheet services
  - Better error handling and connection management
  - Foundation for future collaborative features

### Technical Approach
1. **Database Schema Design**
   - `analyses` table: id, company_name, analysis_json, created_at, updated_at
   - `users` table (future): For multi-user support
   - Proper indexes on company_name and created_at for fast queries

2. **Implementation Strategy**
   - Create new `supabase_storage.py` module mirroring current `sheets_storage.py` API
   - Use `supabase-py` client library
   - Store analysis JSON in JSONB column for efficient querying
   - Add connection pooling and retry logic

3. **Migration Path**
   - Keep `sheets_storage.py` as fallback during transition
   - Add feature flag to switch between storage backends
   - Test thoroughly with local Supabase instance first

### Implementation Steps
- [ ] Set up Supabase project (free tier)
- [ ] Design database schema and create tables
- [ ] Implement `supabase_storage.py` with full CRUD operations
- [ ] Add Supabase secrets to `.streamlit/secrets.toml`
- [ ] Update `app.py` to use Supabase instead of Google Sheets
- [ ] Test save/load/delete functionality
- [ ] Remove Google Sheets dependencies
- [ ] Update documentation

### Success Metrics
- Storage operations work reliably 100% of the time
- Query performance < 500ms for list operations
- Zero data loss during migration
- Clean error messages for connection issues

### Dependencies/Blockers
- Need Supabase account (free tier sufficient initially)
- Requires `supabase-py` package (`pip install supabase`)
- Need to update Streamlit Cloud secrets configuration

---

## Priority 2: Research Enhancement - Quality & Depth

### Motivation
- **Current State**: Basic multi-stage Tavily searches with executive quote extraction
- **Opportunity**: Leverage more data sources and smarter prompting for richer insights
- **Value**: Better analyses = more actionable recommendations for users

### Technical Approach
1. **Enhanced Data Sources**
   - SEC EDGAR API for public company filings (10-K, 10-Q, 8-K)
   - Industry analyst reports (Gartner, Forrester APIs if available)
   - Company press releases and investor relations pages
   - LinkedIn company pages for org structure insights

2. **Smarter Research Strategy**
   - Add confidence scoring to extracted facts
   - Cross-reference claims across multiple sources
   - Implement source quality ranking (prioritize investor relations > news > blogs)
   - Add date-based relevance weighting (newer = more relevant)

3. **Quote & Citation Improvements**
   - Validate all executive quotes have verifiable URLs
   - Extract context around quotes (what question was asked, what event)
   - Add sentiment analysis to quotes (bullish/neutral/cautious)
   - Track quote themes across multiple sources

### Implementation Steps
- [ ] Add SEC EDGAR integration for public companies
- [ ] Implement source quality scoring system
- [ ] Add confidence scores to all research outputs
- [ ] Enhance executive quote extraction with context
- [ ] Add quote sentiment analysis
- [ ] Implement cross-referencing logic to validate facts
- [ ] Add "Research Quality Score" to analysis metadata
- [ ] Create research quality tests/benchmarks

### Success Metrics
- 90%+ of executive quotes have verified source URLs
- Research incorporates 3+ distinct data source types
- Confidence scores correlate with user-reported accuracy
- Strategic priorities include 12-month evolution tracking

### Dependencies/Blockers
- May need SEC EDGAR API access (free, but rate limited)
- Tavily API costs will increase with more searches
- Need to balance depth vs. analysis speed

---

## Priority 3: Performance - Speed & Cost Optimization

### Motivation
- **Current State**: Every analysis makes fresh API calls (expensive, slow)
- **Problem**: Repeated analyses of same company waste money and time
- **Opportunity**: Smart caching and optimization can reduce costs by 60-80%

### Technical Approach
1. **Caching Strategy**
   - Cache Tavily search results by query (TTL: 7 days)
   - Cache OpenAI responses for non-company-specific prompts
   - Store intermediate research results in Supabase
   - Implement "refresh analysis" vs "load cached" options

2. **Cost Tracking & Analytics**
   - Track OpenAI token usage per analysis
   - Track Tavily API calls per analysis
   - Calculate estimated cost per company
   - Add usage dashboard in sidebar
   - Set budget alerts/limits

3. **Execution Optimization**
   - Profile current parallel execution to find bottlenecks
   - Implement streaming responses for faster perceived performance
   - Add partial result rendering (show profile before opportunities)
   - Use GPT-4o-mini for simpler extraction tasks
   - Batch similar API calls where possible

### Implementation Steps
- [ ] Add caching layer (using Supabase or Redis)
- [ ] Implement cost tracking for OpenAI and Tavily
- [ ] Create usage analytics dashboard
- [ ] Profile research execution to find bottlenecks
- [ ] Implement streaming/progressive rendering
- [ ] Add "refresh analysis" toggle for cached results
- [ ] Test cost reduction (benchmark before/after)
- [ ] Add cost estimates before running analysis

### Success Metrics
- 70% reduction in costs for repeated company analyses
- 50% faster analysis completion through caching
- Users can see estimated cost before running analysis
- Analytics dashboard shows spend trends over time

### Dependencies/Blockers
- Supabase migration must be complete (Priority 1)
- Need to decide on caching TTL policies
- May need additional Supabase storage for cache data

---

## Implementation Order

**Phase 1 (Weeks 1-2): Supabase Migration**
- Critical path: Fix storage issues immediately
- Unblocks analytics and caching features

**Phase 2 (Weeks 3-4): Cost Optimization**
- High impact: Reduces operational costs before scaling
- Enables sustainable growth
- Requires Supabase for caching

**Phase 3 (Weeks 5-6): Research Enhancement**
- High value: Improves core product quality
- Can leverage caching infrastructure from Phase 2
- More sustainable with cost controls in place

---

## Future Considerations (Not in Current Roadmap)

### User Authentication & Multi-User
- Supabase Auth integration
- Per-user saved analyses
- Shared analyses and collaboration

### Advanced Export Features
- Custom PowerPoint templates
- PDF generation with charts
- Email/Slack integration for delivery

### API & Integrations
- REST API for programmatic access
- Zapier/Make.com integration
- CRM integrations (Salesforce, HubSpot)

### Advanced Analytics
- Company comparison mode
- Industry trend analysis
- Competitive landscape mapping
- Historical analysis tracking

---

## Notes

- Each priority can be worked on incrementally
- Priorities may shift based on user feedback
- Cost optimization becomes more important as usage grows
- Research quality is the core differentiator long-term
