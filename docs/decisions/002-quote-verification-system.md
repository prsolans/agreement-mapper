# ADR 002: Quote Verification & Confidence Scoring System

**Date:** November 10, 2024
**Status:** Implemented
**Decision Maker:** Product Team

---

## Context

Agreement Map extracts executive quotes from web sources using GPT-4 to identify strategic statements. However, LLMs can:

1. **Hallucinate quotes** - Generate plausible but fabricated statements
2. **Misattribute sources** - Assign quotes to wrong executives or events
3. **Provide invalid URLs** - Generate URLs that don't exist or don't contain the quote
4. **Extract out-of-context quotes** - Miss important nuance or context

**User Problem**: Sales reps using these analyses need to trust the quotes when presenting to prospects. Low-quality or fabricated quotes damage credibility and trust.

**Business Impact**: Quote accuracy is critical for:
- Sales presentations to executive buyers
- Due diligence before customer meetings
- Competitive positioning discussions
- Internal strategy reviews

## Decision

We decided to implement a **multi-factor quote verification and confidence scoring system** that:

1. **Scores source credibility** based on domain and source type (5-tier hierarchy)
2. **Verifies URLs** by checking if they appear in actual search results
3. **Calculates confidence scores** combining multiple signals
4. **Displays visual indicators** in the UI (🟢 High / 🟡 Medium / 🔴 Low)

### Design Principles

1. **Transparent Scoring**: Users should understand why a quote has high or low confidence
2. **Multi-Factor Analysis**: No single factor determines confidence; weighted combination
3. **Verification, Not Validation**: We verify the source exists, not that the quote is word-perfect
4. **Conservative Bias**: Err on the side of caution (lower scores) rather than false confidence

## Implementation

### 1. Source Credibility Scoring (5-Tier Hierarchy)

```python
def score_source_credibility(source: str, url: str = "") -> float:
    # Tier 1: Investor Relations, SEC Filings (1.0)
    # Tier 2: Earnings Calls, Annual Reports (0.9)
    # Tier 3: Major Business News, Interviews (0.8)
    # Tier 4: Tech News, Industry Publications (0.6)
    # Tier 5: Blogs, Social Media (0.4)
    # Default: Unknown sources (0.5)
```

**Rationale**: Official company sources (IR, SEC) are most trustworthy; social media is least trustworthy.

### 2. URL Verification

```python
def verify_quote_url(quote_url: str, search_results: List[Dict]) -> Dict:
    # Exact Match: Full URL matches search result (1.0)
    # Path Match: Domain + path match (0.9)
    # Domain Match: Same domain found (0.7)
    # Not Found: URL not in search results (0.3 penalty)
```

**Rationale**: If the URL appears in our Tavily search results, it's more likely to be real and relevant.

### 3. Confidence Score Calculation

Weighted combination of four factors:

```python
def calculate_quote_confidence(quote: Dict, search_results: List[Dict]) -> float:
    # Factor 1: Source credibility (40% weight)
    # Factor 2: URL verification (30% weight)
    # Factor 3: Quote completeness (20% weight)
    # Factor 4: Date recency (10% weight)

    return weighted_average(factors)
```

**Threshold Levels**:
- **High** (≥ 0.8): Green indicator, high trust
- **Medium** (≥ 0.6): Yellow indicator, moderate trust
- **Low** (< 0.6): Red indicator, verify independently

### 4. UI Indicators

```
🟢 High confidence (0.85) | ✓ Verified
🟡 Medium confidence (0.72) | ✓ Verified
🔴 Low confidence (0.45) | ⚠ Unverified
```

Displayed inline with each executive quote in Slides 3 & 4.

## Alternatives Considered

### 1. No Verification (Status Quo)
- ❌ Risk of hallucinated quotes
- ❌ No way to assess quality
- ✅ Simplest implementation
- ✅ Fastest execution

**Rejected**: Unacceptable for sales use case; credibility is critical.

### 2. Manual Verification
- ✅ Highest accuracy
- ❌ Not scalable
- ❌ Defeats automation purpose
- ❌ Slow and expensive

**Rejected**: Defeats the purpose of automated research.

### 3. Simple Binary Check (Verified/Not Verified)
- ✅ Easy to understand
- ❌ Loses nuance (IR quote vs. blog quote)
- ❌ Doesn't capture confidence levels

**Rejected**: Too simplistic; doesn't help users make judgments.

### 4. LLM-Based Fact-Checking
- ✅ Could be very accurate
- ❌ Expensive (additional API calls)
- ❌ Slow (adds latency)
- ❌ Still susceptible to hallucination

**Rejected**: Too expensive and slow; doesn't solve core problem.

### 5. Multi-Factor Scoring (CHOSEN)
- ✅ Balances multiple signals
- ✅ Transparent and explainable
- ✅ No additional API costs
- ✅ Fast (runs on existing data)
- ⚠️ More complex implementation

**Selected**: Best balance of accuracy, cost, and transparency.

## Factor Weight Rationale

### Source Credibility (40%)
**Highest weight** because source type is the strongest predictor of accuracy:
- Investor Relations and SEC filings are legally mandated
- Earnings calls are transcribed verbatim
- Blogs and social media have no editorial oversight

### URL Verification (30%)
**High weight** because verification against actual search results confirms the source exists and is relevant to the search query.

### Completeness (20%)
**Medium weight** because complete quotes (with executive, source, URL, date) are more likely to be real and usable.

### Recency (10%)
**Lowest weight** because older quotes can still be accurate and valuable, but recent quotes are generally more relevant for current strategy.

## Consequences

### Positive

- ✅ **Increased Trust**: Users can assess quote reliability at a glance
- ✅ **Better Decisions**: Sales reps know which quotes to use in presentations
- ✅ **Quality Signal**: Low confidence scores flag potential hallucinations
- ✅ **Transparency**: Visual indicators make scoring immediately visible
- ✅ **No Added Cost**: Verification uses existing search result data
- ✅ **Fast**: No additional API calls or latency

### Negative

- ❌ **Not Perfect**: Confidence scores are heuristics, not guarantees
- ❌ **False Negatives**: Real quotes from lesser-known sources may score low
- ❌ **URL Dependency**: If Tavily doesn't return a source, URL verification fails
- ❌ **Maintenance**: Scoring tiers need periodic review and adjustment

### Risks & Mitigations

**Risk 1: False Confidence (High score for fake quote)**
- **Impact**: User trusts fabricated quote
- **Mitigation**: Conservative scoring; multiple factors required for high confidence
- **Status**: Implemented conservative thresholds

**Risk 2: False Alarm (Low score for real quote)**
- **Impact**: User discards valuable insight
- **Mitigation**: Show all quotes regardless of score; let users decide
- **Status**: All quotes displayed with confidence indicator

**Risk 3: Gaming the System (LLM learns to fake high-scoring quotes)**
- **Impact**: Verification becomes less effective
- **Mitigation**: Periodic review of scoring logic; cross-reference against manual checks
- **Status**: To be monitored

**Risk 4: URL Verification Fails (Source not in Tavily results)**
- **Impact**: Real quotes get lower scores
- **Mitigation**: Use neutral score (0.6) when verification unavailable, not penalty
- **Status**: Implemented in code

## Validation & Testing

### Approach
- Analyzed 20 sample analyses across public and private companies
- Manually verified 50+ executive quotes
- Compared confidence scores to manual assessment

### Results
- **90% alignment**: Confidence scores matched manual assessment
- **5% false negatives**: Real quotes from lesser-known blogs scored low
- **5% false positives**: Hallucinated quotes with plausible URLs scored medium

### Adjustments Made
- Lowered threshold for "High" from 0.85 to 0.80 (more inclusive)
- Added "Medium" tier at 0.60 (was binary High/Low)
- Reduced penalty for unverified URLs from 0.1 to 0.3

## Follow-Up Actions

- [x] Implement `verification.py` module
- [x] Integrate into `research_agent.py` research pipeline
- [x] Add UI indicators in `app.py`
- [x] Test with sample companies
- [ ] Monitor false positive/negative rates in production
- [ ] Periodic review of scoring thresholds (quarterly)
- [ ] Consider expanding to paragraph/statement verification (future)
- [ ] User feedback mechanism for "Report Incorrect Quote" (future)

## Future Enhancements

### Short Term
1. **Verification Details**: Show specific factors in tooltip (hover over confidence score)
2. **Filter by Confidence**: Allow users to hide low-confidence quotes
3. **Export Confidence**: Include confidence scores in Word/PowerPoint exports

### Medium Term
1. **Cross-Reference Validation**: Check if same quote appears in multiple sources
2. **Sentiment Analysis**: Add "bullish/neutral/cautious" sentiment to quotes
3. **Quote Context**: Extract surrounding context (what question was asked)

### Long Term
1. **LLM Fact-Checking**: Use cheaper models for secondary validation
2. **Historical Tracking**: Compare quote accuracy over time
3. **User Feedback Loop**: Learn from user corrections

## References

- Implementation: `verification.py`
- Integration: `research_agent.py:227-242` (verification logic)
- UI Display: `app.py:359-377` (Slide 3), `app.py:450-468` (Slide 4)
- Original Roadmap: `docs/roadmap/roadmap-2024-10-31.md` (Priority 2: Research Enhancement)

## Metrics

### Success Criteria
- ✅ 90%+ of executive quotes have verified source URLs
- ✅ Confidence scores align with manual assessment
- ⏳ User feedback indicates quotes are trustworthy (to be measured)
- ⏳ Low-confidence quotes flagged before sales meetings (to be measured)

### Monitoring
- Track distribution of confidence scores (High/Medium/Low)
- Monitor false positive rate (user reports of inaccurate quotes)
- Track usage: Do users prefer high-confidence quotes?

---

**Related ADRs:**
- ADR 001: Supabase Storage Migration (enables quote metadata storage)
- ADR 003: Parallel Research Architecture (quote extraction pipeline)
