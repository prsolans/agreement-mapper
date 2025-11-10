# Agreement Map - User Guide for Sales Teams

**Version:** 1.0
**Last Updated:** November 10, 2024
**Audience:** DocuSign Sales Representatives

---

## Table of Contents

1. [What is Agreement Map?](#what-is-agreement-map)
2. [Quick Start (5 Minutes)](#quick-start-5-minutes)
3. [Running Your First Analysis](#running-your-first-analysis)
4. [Understanding Your Results](#understanding-your-results)
5. [Copy/Paste Workflow for Presentations](#copypaste-workflow-for-presentations)
6. [Working with Saved Analyses](#working-with-saved-analyses)
7. [Tips & Best Practices](#tips--best-practices)
8. [Troubleshooting](#troubleshooting)
9. [FAQ](#faq)

---

## What is Agreement Map?

Agreement Map is an AI-powered research tool that helps you **prepare for sales conversations** by automatically gathering and analyzing information about your prospects.

### What it does:

✅ **Company Profile** - Industry, size, locations, key facts
✅ **Strategic Priorities** - What matters to executives right now (with real quotes)
✅ **Business Structure** - Products, divisions, business units
✅ **Agreement Opportunities** - Where DocuSign can add value
✅ **Executive Summary** - 3-5 key bullets for quick reference
✅ **Discovery Questions** - Ready-to-use questions for meetings
✅ **Product Recommendations** - Which DocuSign products fit best

### Why use it?

- ⏱️ **Save Time**: 90 seconds vs. 2+ hours of manual research
- 🎯 **Be Prepared**: Walk into meetings with relevant insights
- 💼 **Build Credibility**: Reference real executive quotes and priorities
- 📊 **Identify Opportunities**: Understand where DocuSign solves problems

---

## Quick Start (5 Minutes)

### 1. Access the Tool

Open your browser and navigate to:
- **Local**: http://localhost:8501 (if running locally)
- **Cloud**: [Your Streamlit Cloud URL]

### 2. Enter API Keys (First Time Only)

In the sidebar under "Configuration", enter:

- **OpenAI API Key**: Required for AI analysis
  - Get one at https://platform.openai.com/api-keys
  - Starts with `sk-`

- **Tavily API Key**: Optional but recommended for web search
  - Get one at https://tavily.com
  - Starts with `tvly-`

💡 **Tip**: Your API keys are saved in your browser session; you won't need to re-enter them each time.

### 3. Run Your First Analysis

1. Enter a company name (e.g., "Salesforce", "Adobe", "Workday")
2. Click **"Analyze Company"**
3. Wait ~90 seconds while AI does the research
4. Results appear automatically!

---

## Running Your First Analysis

### Step-by-Step

#### 1. Enter Company Name

```
[Search box] → Type: "Salesforce"
```

**Tips**:
- Use the official company name (not abbreviations)
- For subsidiaries, use full name: "Instagram (Meta)"
- Public companies work best (more available data)

#### 2. Click "Analyze Company"

Watch the progress indicators:
```
✓ Company Profile - Searching web...
✓ Company Profile - Analyzing results...
✓ Business Units - Searching web...
✓ Strategic Priorities - Extracting executive quotes...
✓ Opportunity Analysis - Identifying agreement opportunities...
```

#### 3. Review Results

Results appear in two tabs:
- **Main Analysis (Copy/Paste Content)** ← Use this for sales prep
- **Background & Details** ← Additional context if needed

---

## Understanding Your Results

### Tab 1: Main Analysis (Copy/Paste Content)

This tab is organized like a **5-slide presentation deck**:

#### 📊 **Slide 1: Executive Summary**

**What it is**: 3-5 key bullet points summarizing the company

**Example**:
```
• Global CRM leader with 150,000+ customers across 200+ countries
• Strategic focus on AI-powered customer experiences and platform consolidation
• $31.4B annual revenue with 15% growth driven by digital transformation
• Managing 500M+ agreements annually across sales, service, and marketing operations
• Key pain points: Contract lifecycle delays and multi-system integration complexity
```

**How to use**:
- Copy these bullets into your intro slide
- Use as talking points in executive summaries
- Share in pre-call team briefings

---

#### 🎯 **Slide 2: Discovery Questions**

**What it is**: 5-7 targeted questions to ask in your discovery meetings

**Example**:
```
1. How are you currently managing the 500M+ agreements across your sales, service, and marketing operations?

2. What challenges are you facing with contract lifecycle management as you scale your Customer 360 platform?

3. Can you walk me through your current approval workflows for customer contracts and how they integrate with Salesforce CRM?
```

**How to use**:
- Copy these into your meeting notes
- Ask them during discovery calls
- Customize based on the specific conversation

---

#### 💡 **Slide 3: Top Strategic Priorities**

**What it is**: The company's current strategic goals with **verified executive quotes**

**Example**:
```
1. Accelerate AI Innovation Across Platform
   "We are doubling down on AI and automation to deliver
   more intelligent customer experiences."
   — Marc Benioff, CEO, Q4 2023 Earnings Call
   🟢 High confidence (0.85) | ✓ Verified

2. Drive Platform Consolidation
   "Our focus is on creating a unified platform that brings
   together all customer touchpoints."
   — Amy Weaver, CFO, Annual Investor Day 2023
   🟡 Medium confidence (0.72) | ✓ Verified
```

**Confidence Indicators**:
- 🟢 **High** (0.80+): Strong source, verified URL - safe to use
- 🟡 **Medium** (0.60-0.79): Good source - verify before using
- 🔴 **Low** (<0.60): Weak source - double-check independently

**How to use**:
- Reference these priorities in your pitch
- Connect DocuSign capabilities to their goals
- Use executive quotes to build credibility
- Check confidence scores before citing quotes

---

#### 🤝 **Slide 4: Agreement Opportunities**

**What it is**: Specific areas where DocuSign can add value

**Example**:
```
1. Contract Lifecycle Automation
   • Current Challenge: Manual contract routing and approval delays
   • Impact: 2-3 week turnaround times for customer agreements
   • DocuSign Solution: CLM + eSignature to automate end-to-end
   • Estimated Value: $2.5M annually in efficiency gains

2. Multi-System Integration
   • Current Challenge: Disconnected systems for contracts, CRM, billing
   • Impact: Data silos and manual data entry
   • DocuSign Solution: API integrations with Salesforce, SAP, ServiceNow
   • Estimated Value: 40% reduction in contract processing time
```

**How to use**:
- Focus on top 1-2 opportunities in your pitch
- Use estimated values in ROI discussions
- Reference executive quotes from Slide 3 to show alignment

---

#### 🎁 **Slide 5: DocuSign Products & Approach**

**What it is**: Which DocuSign products fit this customer's needs

**Example**:
```
Recommended Products:
• DocuSign CLM - Contract lifecycle management
• DocuSign eSignature - Digital signing
• DocuSign IAM - Identity & access management
• DocuSign Maestro - Workflow automation

Implementation Approach:
Start with eSignature for immediate wins (30 days), then expand to
CLM for enterprise-wide contract automation (90-day pilot).
```

**How to use**:
- Tailor your product demo to these recommendations
- Reference in proposal/SOW
- Use in multi-threading conversations (technical team, procurement)

---

### Tab 2: Background & Details

Additional context for deeper research:

- **Company Profile**: Full company details, history, scale
- **Business Units**: Detailed breakdown of products/divisions
- **Full Strategic Analysis**: Extended priorities and context

💡 **Use this when**: You need deeper context, preparing for executive meetings, or customizing your pitch significantly.

---

## Copy/Paste Workflow for Presentations

### Recommended Workflow

#### Before the Meeting (5-10 minutes)

1. **Run Analysis** on your prospect company
2. **Review Executive Summary** (Slide 1) - get the big picture
3. **Study Strategic Priorities** (Slide 3) - understand what execs care about
4. **Identify Top 2 Opportunities** (Slide 4) - where DocuSign fits
5. **Select Discovery Questions** (Slide 2) - pick 3-4 most relevant

#### During Pitch Deck Preparation (10-15 minutes)

**Copy content directly into your slides**:

```
Your Slide 1: "About [Company]"
→ Copy bullets from Agreement Map Slide 1 (Executive Summary)

Your Slide 3: "Your Strategic Priorities"
→ Copy priorities from Agreement Map Slide 3
→ Include executive quotes with attribution

Your Slide 5: "Where DocuSign Can Help"
→ Copy opportunities from Agreement Map Slide 4
→ Focus on top 1-2, remove others

Your Appendix: "Recommended Approach"
→ Copy products/approach from Agreement Map Slide 5
```

#### During Discovery Calls

**Keep Agreement Map open** in a second browser tab:

- Reference executive quotes during conversation
- Ask discovery questions at appropriate moments
- Note down customer responses for follow-up

#### After the Meeting

**Save your analysis**:
- Analyses are automatically saved
- Access them from the sidebar under "Saved Analyses"
- Reload anytime to refresh your memory

---

## Working with Saved Analyses

### Viewing Saved Analyses

**Sidebar → "Saved Analyses" section**

```
📊 Salesforce (Nov 10, 2024)    [Delete]
📊 Adobe (Nov 08, 2024)          [Delete]
📊 Workday (Nov 05, 2024)        [Delete]
```

Click any analysis name to reload it instantly.

### When to Re-Run an Analysis

- **Quarterly**: Before renewal conversations or QBRs
- **Major Company News**: Acquisition, leadership change, strategy shift
- **Stale Data**: Analysis is 90+ days old
- **Different Angle**: Need to research a different business unit

### Managing Storage

- Analyses are stored in **Supabase** (cloud database)
- No local files needed
- Works on any device (laptop, tablet)
- Delete old analyses to keep list organized

---

## Tips & Best Practices

### Getting the Best Results

✅ **DO:**
- Use official company names ("Salesforce" not "SFDC")
- Wait for analysis to fully complete (~90 seconds)
- Check confidence scores on executive quotes
- Cross-reference opportunities with customer pain points
- Save analyses before closing browser

❌ **DON'T:**
- Rely solely on low-confidence quotes (🔴)
- Copy/paste without reading and understanding
- Use outdated analyses (90+ days old)
- Skip the Discovery Questions - they're tailored to the company!

### Maximizing Impact

1. **Multi-Thread**: Share relevant slides with multiple stakeholders
   - Executive Summary → C-suite
   - Strategic Priorities → VP-level
   - Opportunities → Technical teams

2. **Personalize**: Use the AI analysis as a starting point, then add your own insights based on conversations

3. **Verify High-Stakes Claims**: For major deals, double-check executive quotes by visiting the source URL

4. **Combine with CRM Data**: Merge AI insights with your internal account intelligence

### Time-Saving Shortcuts

- **Batch Research**: Run analyses on 5-10 accounts during prep time
- **Template Decks**: Create a master deck template with placeholders for Agreement Map content
- **Quick Reference**: Print/save Executive Summary as 1-pager for field meetings

---

## Troubleshooting

### "Analysis failed" or errors

**Possible Causes**:
- Invalid API key
- API rate limit exceeded
- Company name not recognized

**Solutions**:
1. Check API keys in Configuration section
2. Try slightly different company name ("IBM" vs "IBM Corporation")
3. Wait 60 seconds and try again (rate limits)
4. Check your OpenAI account has credits

### "Supabase not configured"

**Cause**: Database storage not set up

**Impact**: Analyses won't be saved (but will still run)

**Solution**: Contact your admin to configure Supabase (see `docs/architecture/SUPABASE_SETUP.md`)

### Quotes seem inaccurate

**Check confidence score**:
- 🟢 High confidence: Likely accurate, verified source
- 🟡 Medium confidence: Probably accurate, verify if critical
- 🔴 Low confidence: Use with caution, verify independently

**Solution**: Click the source URL to verify the quote in context

### Analysis taking too long (>3 minutes)

**Possible Causes**:
- API slowness
- Complex company with many business units
- Network connectivity issues

**Solutions**:
1. Wait it out (it will complete eventually)
2. Refresh page and try again
3. Check your internet connection

### Results seem generic

**Possible Causes**:
- Limited public information available (private company)
- Very recent company (startup with little web presence)
- Tavily API key not configured

**Solutions**:
1. Add Tavily API key for better web search results
2. Try more specific company name
3. Use "Background & Details" tab for more depth

---

## FAQ

### Q: How much does it cost to run an analysis?

**A:** Approximately $0.60-1.00 per company in API costs (OpenAI + Tavily). This is billed to your API accounts, not a separate Agreement Map charge.

### Q: Can I analyze private companies?

**A:** Yes, but results may be less comprehensive since private companies publish less information. Public companies typically yield richer analyses.

### Q: How current is the data?

**A:** Data is pulled from the web in real-time, so it's as current as what's publicly available. News articles, earnings calls, and company websites are typically updated within days of events.

### Q: Can I customize the output?

**A:** Currently, output format is standardized. Customization features (templates, hiding sections) are on the roadmap for future releases.

### Q: Is this data accurate?

**A:** The AI sources information from public web searches and uses confidence scoring to indicate reliability. Always verify critical claims (especially low-confidence quotes) before using in high-stakes situations.

### Q: Can I share analyses with my team?

**A:** Analyses are saved to your account. To share, you can:
- Export as Word/PowerPoint document
- Share screenshots
- Send JSON export
- (Team collaboration features coming in future releases)

### Q: What if my prospect is a subsidiary?

**A:** Use the subsidiary's full name (e.g., "Instagram by Meta" or "LinkedIn by Microsoft"). The AI will focus on that specific business unit.

### Q: How often should I refresh an analysis?

**A:** Refresh quarterly, or sooner if:
- Major company news (acquisition, leadership change)
- Upcoming renewal/QBR
- Significant strategy shift announced

### Q: Can I use this for competitive intelligence?

**A:** Yes! Run analyses on competitors to understand their positioning, challenges, and strategic focus. Compare with your prospect's priorities to differentiate.

### Q: What languages are supported?

**A:** Currently English only. International company names work, but analysis is performed in English.

---

## Need Help?

### Support Resources

- **Technical Issues**: Contact your IT administrator
- **Product Feedback**: [GitHub Issues](https://github.com/your-org/agreement-map/issues)
- **Sales Methodology Questions**: Contact your sales enablement team

### Additional Documentation

- **Setup Guide**: See main README.md in project root
- **Architecture Details**: See `docs/architecture/` for technical documentation
- **Roadmap**: See `docs/roadmap/` for upcoming features

---

## Appendix: Sample Use Cases

### Use Case 1: First Discovery Call

**Scenario**: You have a first call with a VP of Sales at a mid-market company.

**Workflow**:
1. Run analysis 1 day before meeting
2. Review Executive Summary and Strategic Priorities
3. Select 3-4 Discovery Questions relevant to their role
4. During call, ask questions and listen for alignment with AI-detected priorities
5. After call, revisit Opportunities section to tailor follow-up

**Time Saved**: 90 minutes of research → 5 minutes of review

---

### Use Case 2: Executive Presentation

**Scenario**: Presenting to C-suite at enterprise account.

**Workflow**:
1. Run analysis 1 week before meeting
2. Build custom deck using:
   - Executive Summary (1 slide)
   - Strategic Priorities with quotes (2-3 slides)
   - Top 2 Opportunities mapped to DocuSign ROI (2 slides)
3. Rehearse by connecting opportunities back to quoted priorities
4. During meeting, reference CEO/CFO quotes to show you've done homework

**Time Saved**: 3-4 hours of research → 15 minutes of content curation

---

### Use Case 3: Competitive Displacement

**Scenario**: Prospect currently uses competitor (HelloSign, Adobe Sign, etc.)

**Workflow**:
1. Run analysis on prospect
2. Run analysis on competitor (understand their strengths/messaging)
3. Compare Strategic Priorities between the two
4. Identify gaps where DocuSign aligns better with prospect priorities
5. Build "Why Switch" narrative using prospect's own strategic language

**Time Saved**: 5+ hours of competitive research → 10 minutes of AI analysis

---

**Happy Selling! 🚀**
