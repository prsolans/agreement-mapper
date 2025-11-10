# ADR 001: Migrate from Google Sheets to Supabase for Persistent Storage

**Date:** November 10, 2024
**Status:** Implemented
**Decision Maker:** Product Team

---

## Context

Agreement Map initially used Google Sheets for persistent storage of company analyses via the `st-gsheets-connection` Streamlit integration. While this worked for local development, several issues emerged:

1. **Reliability Issues**: Google Sheets integration wasn't functioning reliably ("isn't working but haven't debugged it" - user feedback)
2. **Cloud Deployment**: Local JSON file storage doesn't work on Streamlit Cloud (no persistent filesystem)
3. **Scalability**: Google Sheets has cell/row limits that could constrain growth
4. **Performance**: API calls to Google Sheets were slow for list/load operations
5. **Querying**: No native support for filtering, searching, or complex queries

## Decision

We decided to migrate to **Supabase (PostgreSQL + JSONB)** as the primary persistent storage backend.

### Why Supabase?

**Technical Advantages:**
- Production-grade PostgreSQL database with ACID guarantees
- JSONB column type allows flexible schema for analysis data
- Built-in REST API for easy integration
- Fast indexed queries for company name and timestamps
- Native support for full-text search
- No row/cell limits

**Operational Advantages:**
- Works seamlessly with Streamlit Cloud
- Free tier sufficient for initial deployment (500 MB database, 2 GB file storage)
- Built-in authentication system for future multi-user features
- Real-time subscriptions for collaborative features
- Automatic backups included

**Developer Experience:**
- Simple Python SDK (`supabase-py`)
- Well-documented API
- Easy local development with Supabase CLI
- Generous free tier for testing

### Alternatives Considered

1. **Google Sheets (Status Quo)**
   - ❌ Reliability issues
   - ❌ Slow performance
   - ❌ Limited querying capabilities
   - ✅ Easy to inspect data manually
   - ✅ No additional account needed

2. **Local JSON Files**
   - ❌ Doesn't work on Streamlit Cloud
   - ❌ No multi-user support
   - ❌ No query capabilities
   - ✅ Simple implementation
   - ✅ No external dependencies

3. **AWS DynamoDB**
   - ✅ Highly scalable
   - ✅ Production-ready
   - ❌ More complex setup
   - ❌ Less generous free tier
   - ❌ Steeper learning curve
   - ❌ Overkill for current scale

4. **Firebase/Firestore**
   - ✅ Real-time capabilities
   - ✅ Good free tier
   - ❌ NoSQL (less familiar paradigm)
   - ❌ Complex querying
   - ❌ Vendor lock-in concerns

5. **PostgreSQL (Self-hosted)**
   - ✅ Full control
   - ✅ No vendor lock-in
   - ❌ Requires infrastructure management
   - ❌ Additional hosting costs
   - ❌ Backup/maintenance overhead

## Implementation

### Database Schema

```sql
CREATE TABLE analyses (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    company_name TEXT NOT NULL,
    timestamp TIMESTAMPTZ NOT NULL,
    analysis_json JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_analyses_company_name ON analyses(company_name);
CREATE INDEX idx_analyses_created_at ON analyses(created_at DESC);
```

### Key Design Decisions

1. **UUID Primary Keys**: More stable than auto-incrementing integers; easier for distributed systems
2. **JSONB Column**: Entire analysis stored as JSON for flexibility; no need to migrate schema when adding new fields
3. **Separate Timestamps**: Both analysis timestamp (user-facing) and database timestamps (created_at/updated_at)
4. **Indexes**: Optimized for common queries (list by company, sort by date)

### Storage Manager API

Maintained backward-compatible API with previous `SheetsStorageManager`:

```python
class SupabaseStorageManager:
    def is_configured() -> bool
    def save_analysis(company_name: str, analysis_data: Dict) -> bool
    def list_analyses() -> List[Dict]
    def load_analysis(analysis_id: str) -> Optional[Dict]
    def delete_analysis(analysis_id: str) -> bool
    def search_analyses(search_term: str) -> List[Dict]
    def update_analysis(analysis_id: str, analysis_data: Dict) -> bool
```

**Key Change**: Uses UUID `analysis_id` instead of integer `row_index`

## Consequences

### Positive

- ✅ **Reliable Storage**: Analyses persist correctly on Streamlit Cloud
- ✅ **Fast Queries**: Sub-500ms response times for list operations
- ✅ **Flexible Schema**: Can add new fields to analysis JSON without migrations
- ✅ **Foundation for Growth**: Authentication, real-time, and collaboration features available
- ✅ **Better UX**: Users see saved analyses immediately in sidebar
- ✅ **Cost-Effective**: Free tier sufficient for 100s of analyses

### Negative

- ❌ **Additional Setup**: Users must create Supabase account and configure credentials
- ❌ **Vendor Lock-In**: Migration to another database would require code changes (though SQL is portable)
- ❌ **External Dependency**: Reliance on Supabase service availability
- ❌ **Learning Curve**: Team needs to understand Supabase dashboard and SQL basics

### Risks & Mitigations

**Risk 1: Supabase Service Outage**
- **Mitigation**: Implement graceful degradation; app still functions without storage (no save/load)
- **Status**: Implemented - app shows "Supabase not configured" message

**Risk 2: Free Tier Limits**
- **Mitigation**: Monitor usage; free tier supports 500 MB (thousands of analyses); upgrade path available
- **Status**: To be monitored

**Risk 3: Data Loss**
- **Mitigation**: Supabase provides automatic backups on free tier; can export data as JSON
- **Status**: Backups automatic; export functionality exists

**Risk 4: Security**
- **Mitigation**: Use Row Level Security (RLS) policies when adding authentication; anon key safe for public read/write
- **Status**: RLS disabled for anonymous access (acceptable for single-user prototype)

## Follow-Up Actions

- [x] Create `supabase_storage.py` module
- [x] Update `app.py` to use Supabase
- [x] Create setup documentation (`SUPABASE_SETUP.md`)
- [x] Update `.streamlit/secrets.toml.example`
- [x] Archive Google Sheets documentation
- [ ] Remove `sheets_storage.py` (pending user confirmation)
- [ ] Remove `st-gsheets-connection` from requirements.txt
- [ ] Monitor Supabase usage and performance
- [ ] Implement Row Level Security when adding authentication

## References

- [Supabase Documentation](https://supabase.com/docs)
- [supabase-py SDK](https://github.com/supabase-community/supabase-py)
- [PostgreSQL JSONB Documentation](https://www.postgresql.org/docs/current/datatype-json.html)
- Implementation: `supabase_storage.py`
- Setup Guide: `docs/architecture/SUPABASE_SETUP.md`
- Migration Discussion: Previous roadmap (October 31, 2024)

## Lessons Learned

1. **Start with Cloud-Native**: Building for cloud deployment from the start would have saved migration effort
2. **External Dependencies Need Fallbacks**: Always implement graceful degradation for external services
3. **Schema Flexibility Matters**: JSONB approach allows rapid iteration without database migrations
4. **Documentation is Critical**: Good setup docs (SUPABASE_SETUP.md) reduce friction for new users

---

**Next ADRs:**
- ADR 002: Quote Verification & Confidence Scoring System
- ADR 003: Parallel Research Architecture
