# ADR 003: Parallel Research Architecture with Async Execution

**Date:** October 31, 2024 (Original Design)
**Updated:** November 10, 2024
**Status:** Implemented
**Decision Maker:** Product Team

---

## Context

Agreement Map performs comprehensive company research across multiple dimensions:

1. **Company Profile** - Basic information, industry, scale
2. **Business Units** - Product lines, divisions, organizational structure
3. **Strategic Priorities** - Goals, initiatives, executive quotes
4. **Opportunity Analysis** - Agreement/contract optimization potential

**Problem**: Sequential execution of research phases would be slow:
- Each phase requires multiple API calls (Tavily search + OpenAI analysis)
- Total time: 4-6 minutes per company (unacceptable UX)
- API calls are mostly independent (no data dependencies between phases)

**Goal**: Reduce analysis time to under 90 seconds while maintaining quality.

## Decision

We decided to implement a **parallel research architecture** using Python `asyncio` to execute independent research phases concurrently.

### Key Design Principles

1. **Maximize Parallelism**: Run independent research phases simultaneously
2. **Respect Dependencies**: Execute dependent phases sequentially
3. **Fail Gracefully**: Individual phase failures don't crash entire analysis
4. **Progress Transparency**: Show real-time progress for each phase
5. **Cost Efficiency**: Parallelism should not increase API costs

## Architecture

### Research Phases (4 Phases)

```
Phase 1: Company Profile
  ├─ Search web for company info
  └─ Extract profile with GPT-4

Phase 2: Business Analysis (runs in parallel)
  ├─ Business Units
  │   ├─ Search for product lines
  │   └─ Extract business units with GPT-4
  │
  ├─ Strategic Priorities
  │   ├─ Search for strategy & goals
  │   ├─ Extract priorities with GPT-4
  │   └─ Verify quotes with verification.py
  │
  └─ Opportunity Analysis
      ├─ Search for agreements & contracts
      └─ Extract opportunities with GPT-4

Phase 3: Optimization Analysis (depends on Phase 2)
  └─ Analyze opportunities from Phase 2

Phase 4: Sales Enablement Content (depends on Phases 1-3)
  ├─ Generate Executive Summary
  ├─ Generate Discovery Questions
  └─ Aggregate Product Recommendations
```

### Execution Flow

```python
async def run_research():
    # Phase 1: Profile (sequential - needed as context)
    profile = await research_company_profile()

    # Phase 2: Parallel execution of independent research
    business_units, priorities, opportunities = await asyncio.gather(
        research_business_units(),
        research_strategic_priorities(),
        research_opportunity_analysis()
    )

    # Phase 3: Optimization (depends on opportunities)
    optimizations = await research_optimization_opportunities(opportunities)

    # Phase 4: Sales content (depends on all previous)
    summary, questions, products = await asyncio.gather(
        generate_executive_summary(profile, priorities, opportunities),
        generate_discovery_questions(profile, priorities),
        aggregate_product_recommendations(opportunities)
    )

    return complete_analysis
```

### Parallelism Strategy

**Parallel Execution** (Phase 2):
- Business Units ∥ Strategic Priorities ∥ Opportunity Analysis
- **Rationale**: No data dependencies; all query company independently
- **Speedup**: 3x faster (3 phases in time of 1)

**Sequential Dependencies**:
- Phase 1 → Phase 2: Profile provides context for searches
- Phase 2 → Phase 3: Opportunities needed for optimization analysis
- Phase 3 → Phase 4: All data needed for sales content

## Implementation Details

### Async/Await Pattern

```python
class CompanyResearchAgent:
    def __init__(self, api_key: str, tavily_key: str):
        self.openai_client = openai.AsyncOpenAI(api_key=api_key)
        # Note: Tavily client is synchronous, wrapped in asyncio.to_thread()

    async def _search_web(self, query: str) -> List[Dict]:
        # Wrap synchronous Tavily call in thread
        results = await asyncio.to_thread(
            self.tavily_client.search,
            query=query
        )
        return results

    async def _get_completion(self, messages: List[Dict]) -> str:
        # Native async OpenAI call
        response = await self.openai_client.chat.completions.create(
            model="gpt-4o",
            messages=messages
        )
        return response.choices[0].message.content
```

### Progress Reporting

```python
def progress_callback(message: str):
    """Called by research agent to report progress"""
    # Updates Streamlit UI in real-time
    progress_container.markdown(f"✓ {message}")
```

**Progress Updates**:
- "Company Profile - Searching web..."
- "Company Profile - Analyzing results..."
- "Business Units - Searching web..."
- "Strategic Priorities - Extracting executive quotes..."
- "Strategic Priorities - Verifying quotes..."

### Error Handling

```python
try:
    results = await asyncio.gather(
        research_business_units(),
        research_strategic_priorities(),
        research_opportunity_analysis(),
        return_exceptions=True  # Don't fail entire analysis on one error
    )

    for result in results:
        if isinstance(result, Exception):
            logging.error(f"Phase failed: {result}")
            # Continue with partial results
except Exception as e:
    # Catastrophic failure
    raise AnalysisError(f"Research failed: {e}")
```

## Alternatives Considered

### 1. Sequential Execution (Status Quo Before)
```python
profile = research_company_profile()
business_units = research_business_units()
priorities = research_strategic_priorities()
opportunities = research_opportunity_analysis()
```

- ❌ Slowest: 4-6 minutes per analysis
- ✅ Simplest to implement
- ✅ Easiest to debug
- ❌ Poor user experience

**Rejected**: Unacceptable for sales team use case; too slow for real-time use.

### 2. Threading (multiprocessing.ThreadPoolExecutor)
```python
with ThreadPoolExecutor(max_workers=3) as executor:
    futures = [
        executor.submit(research_business_units),
        executor.submit(research_strategic_priorities),
        executor.submit(research_opportunity_analysis)
    ]
    results = [f.result() for f in futures]
```

- ✅ Parallel execution
- ⚠️ GIL contention for CPU-bound tasks
- ❌ More complex error handling
- ❌ Doesn't work well with async OpenAI client

**Rejected**: Asyncio is more natural for I/O-bound API calls.

### 3. Multiprocessing (multiprocessing.Pool)
```python
with Pool(processes=3) as pool:
    results = pool.starmap(research_phase, phases)
```

- ✅ True parallelism (no GIL)
- ❌ High overhead for process spawning
- ❌ Serialization required for data passing
- ❌ Complex state management

**Rejected**: Overkill for I/O-bound work; adds unnecessary complexity.

### 4. Asyncio with asyncio.gather() (CHOSEN)
```python
results = await asyncio.gather(
    research_business_units(),
    research_strategic_priorities(),
    research_opportunity_analysis()
)
```

- ✅ Excellent for I/O-bound API calls
- ✅ Natural async/await syntax
- ✅ Easy progress tracking
- ✅ Works natively with OpenAI async client
- ⚠️ Requires wrapping synchronous Tavily client

**Selected**: Best fit for API-heavy workload; clean code; fast execution.

### 5. Celery/Task Queue
```python
@celery.task
def research_phase(company, phase):
    return perform_research()
```

- ✅ Production-grade task management
- ✅ Retries and monitoring
- ❌ Requires Redis/RabbitMQ infrastructure
- ❌ Adds deployment complexity
- ❌ Overkill for single-user application

**Rejected**: Too much infrastructure for current scale.

## Performance Results

### Benchmark (10 companies, average)

**Sequential Execution** (Before):
- Total Time: 4.2 minutes
- API Calls: 18-22 calls
- User Wait: Entire 4.2 minutes

**Parallel Execution** (After):
- Total Time: 1.3 minutes
- API Calls: 18-22 calls (same)
- User Wait: 1.3 minutes
- **Speedup**: 3.2x faster

### Cost Impact

- **Cost per Analysis**: ~$0.60-1.00 (unchanged)
- **API Calls**: Same total count
- **Conclusion**: Parallelism improves speed without increasing cost

### Resource Usage

- **Memory**: +15 MB (multiple concurrent requests)
- **CPU**: Minimal (I/O-bound)
- **Network**: 3 concurrent connections max

## Consequences

### Positive

- ✅ **3x Faster**: Analysis completes in ~90 seconds vs 4+ minutes
- ✅ **Better UX**: Users see progress updates in real-time
- ✅ **Same Cost**: No additional API calls
- ✅ **Scalable**: Can add more parallel phases easily
- ✅ **Maintainable**: Clean async/await code
- ✅ **Responsive**: UI remains interactive during research

### Negative

- ❌ **Complexity**: Async code is harder to debug than sequential
- ❌ **Tavily Wrapper**: Synchronous client requires `asyncio.to_thread()` wrapper
- ❌ **Concurrency Limits**: API rate limits could cause issues at scale
- ❌ **State Management**: Must be careful with shared state in async context

### Risks & Mitigations

**Risk 1: API Rate Limits**
- **Impact**: Concurrent requests trigger rate limiting
- **Mitigation**: Respect API limits; add retry logic with exponential backoff
- **Status**: Not yet encountered; OpenAI and Tavily limits are generous

**Risk 2: Race Conditions**
- **Impact**: Concurrent phases modify shared state incorrectly
- **Mitigation**: Avoid shared mutable state; use immutable data structures; careful locking if needed
- **Status**: No shared state currently; each phase returns independent results

**Risk 3: Partial Failures**
- **Impact**: One phase fails, others succeed; incomplete analysis
- **Mitigation**: Use `return_exceptions=True` in `asyncio.gather()`; handle partial results gracefully
- **Status**: Implemented; user sees what succeeded

**Risk 4: Debugging Difficulty**
- **Impact**: Async stack traces are harder to read
- **Mitigation**: Extensive logging; progress callbacks; structured error messages
- **Status**: Good logging in place; room for improvement

## Follow-Up Actions

- [x] Implement async research phases
- [x] Add progress callbacks
- [x] Wrap synchronous Tavily client
- [x] Error handling for partial failures
- [x] Benchmark performance
- [ ] Add retry logic for API failures
- [ ] Implement rate limiting awareness
- [ ] Monitor for race conditions in production
- [ ] Consider caching to further reduce API calls (Priority 1 in roadmap)

## Future Enhancements

### Short Term
1. **Streaming Results**: Show partial results as phases complete (not waiting for all)
2. **Configurable Parallelism**: Allow users to adjust concurrency level
3. **Better Error Recovery**: Retry failed phases without restarting entire analysis

### Medium Term
1. **Caching Layer**: Cache search results to reduce API calls (see ADR 004 - Future)
2. **Progressive Rendering**: Display profile while other phases run
3. **Background Processing**: Queue analyses for batch processing overnight

### Long Term
1. **Distributed Execution**: Use Celery for true background tasks
2. **Smart Scheduling**: Batch similar queries to optimize API usage
3. **Adaptive Parallelism**: Adjust concurrency based on API response times

## References

- Implementation: `research_agent.py:129-195` (run_complete_analysis)
- Progress Callbacks: `app.py:1095-1161` (research execution with progress containers)
- Error Handling: `research_agent.py` (various methods with try/except)
- Performance Benchmarks: Internal testing (October 2024)

## Lessons Learned

1. **Asyncio is Great for APIs**: Natural fit for I/O-bound workloads; clean code
2. **Progress Updates Matter**: Users tolerate wait times better with real-time feedback
3. **Partial Results are Valuable**: Better to show 80% complete than fail entirely
4. **Dependencies Constrain Parallelism**: Profile must complete before other phases (context needed)
5. **Debugging Async is Hard**: Invest in logging and structured errors upfront

---

**Related ADRs:**
- ADR 002: Quote Verification System (runs in Strategic Priorities phase)
- Future ADR 004: Caching Strategy (will reduce API calls further)
