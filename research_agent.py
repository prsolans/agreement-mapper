"""
Research Agent: Parallel OpenAI-powered company analysis with Tavily web search
"""
import asyncio
import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Callable
from pathlib import Path
from openai import AsyncOpenAI
from tavily import TavilyClient


class CompanyResearchAgent:
    """Orchestrates parallel research using OpenAI API with Tavily web search"""

    def __init__(self, api_key: str, tavily_api_key: Optional[str] = None):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = "gpt-4-turbo-preview"
        self.tavily = TavilyClient(api_key=tavily_api_key) if tavily_api_key else None
        self.product_catalog = self._load_product_catalog()

    def _load_product_catalog(self) -> Optional[Dict]:
        """
        Load DocuSign product catalog for context injection

        Returns:
            Product catalog dict or None if not available
        """
        try:
            catalog_path = Path(__file__).parent / "data" / "docusign_products.json"

            if not catalog_path.exists():
                return None

            with open(catalog_path, 'r') as f:
                catalog = json.load(f)

            return catalog

        except Exception as e:
            # Silently fail - catalog is optional
            return None

    def _search_web(self, query: str, max_results: int = 5) -> str:
        """
        Search the web using Tavily and return formatted results

        Args:
            query: Search query
            max_results: Maximum number of results to return

        Returns:
            Formatted string with search results
        """
        if not self.tavily:
            return "Web search not available (Tavily API key not provided)"

        try:
            response = self.tavily.search(
                query=query,
                search_depth="advanced",
                max_results=max_results
            )

            results = []
            for result in response.get('results', []):
                results.append(f"""
Source: {result.get('url', 'N/A')}
Title: {result.get('title', 'N/A')}
Content: {result.get('content', 'N/A')}
---""")

            return '\n'.join(results) if results else "No results found"
        except Exception as e:
            return f"Web search error: {str(e)}"

    async def research_company_profile(
        self,
        company_name: str,
        progress_callback: Optional[Callable] = None
    ) -> Dict:
        """Research company profile information using Tavily web search"""

        if progress_callback:
            progress_callback("Company Profile - Searching web...")

        # Search the web for company information
        search_results = self._search_web(
            f"{company_name} company profile headquarters revenue employees industry business model",
            max_results=5
        )

        if progress_callback:
            progress_callback("Company Profile - Analyzing results...")

        prompt = f"""Based on the following web search results about {company_name}, provide detailed information in JSON format:

WEB SEARCH RESULTS:
{search_results}

Using the above search results, extract and structure the following information:

Required fields:
- legal_name: Official registered company name
- brand_names: Array of brand names used
- industry: Primary industry classification
- year_founded: Year established
- headquarters: City and country location
- ownership_structure: Public/Private/Family-owned/etc
- scale:
  - annual_revenue: Latest annual revenue (with $ symbol)
  - revenue_numeric: Revenue as number
  - employees: Employee count
  - locations: Number of office locations
  - countries: Countries of operation
  - customers: Customer count or description
- business_model:
  - primary_revenue_model: How the company makes money
  - key_differentiators: Array of 3-5 competitive advantages
  - customer_segments: Array of target customer types
- strategic_initiatives: Array of current strategic initiatives with:
  - initiative: Name/description
  - timeline: Expected timeframe
  - priority: high/medium/low
  - investment: Investment amount if known
  - impact_areas: Array of business areas impacted
- sources: Array of data sources used
- confidence: high/medium/low based on data availability

Return ONLY valid JSON. Use web search and public information. If data is not available, use "N/A" or null.
"""

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a business research analyst. Provide accurate, structured data about companies using publicly available information. Always return valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )

        result = json.loads(response.choices[0].message.content)

        # Log token usage
        if progress_callback and hasattr(response, 'usage'):
            usage = response.usage
            progress_callback(f"[✓] Profile complete | Tokens: {usage.total_tokens} (prompt: {usage.prompt_tokens}, completion: {usage.completion_tokens})")

        return result

    async def research_brand_colors(
        self,
        company_name: str,
        company_profile: Dict,
        progress_callback: Optional[Callable] = None
    ) -> Dict:
        """Research company's brand colors"""

        if progress_callback:
            progress_callback("Brand Colors")

        prompt = f"""Research the brand colors for {company_name}.

Based on their website, marketing materials, and brand guidelines, identify:

Required fields (return as hex codes):
- primary_color: Main brand color (hex format, e.g., "#FF0000")
- secondary_color: Secondary brand color (hex format)
- accent_color: Accent or tertiary color (hex format)
- text_color: Primary text color (hex format)
- background_color: Background color (hex format)

Return ONLY valid JSON with hex color codes. Use publicly available information from the company's website and brand materials.
If specific colors cannot be determined with confidence, use industry-appropriate defaults based on the company's industry: {company_profile.get('industry', 'N/A')}.
"""

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a brand design analyst. Research company brand colors from public sources and return hex color codes in JSON format."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )

        result = json.loads(response.choices[0].message.content)

        # Log token usage
        if progress_callback and hasattr(response, 'usage'):
            usage = response.usage
            progress_callback(f"[✓] Brand colors complete | Tokens: {usage.total_tokens} (prompt: {usage.prompt_tokens}, completion: {usage.completion_tokens})")

        return result

    async def research_strategic_priorities(
        self,
        company_name: str,
        progress_callback: Optional[Callable] = None
    ) -> List[Dict]:
        """Research company's top strategic priorities using multi-stage Tavily web search with executive insights"""

        # Stage 1: Executive interviews and statements
        if progress_callback:
            progress_callback("Strategic Priorities - Searching executive interviews...")

        exec_search_results = self._search_web(
            f"{company_name} CEO CFO interview 2024 2025 strategy vision keynote",
            max_results=7
        )

        # Stage 2: Earnings call transcripts
        if progress_callback:
            progress_callback("Strategic Priorities - Searching earnings transcripts...")

        earnings_search_results = self._search_web(
            f"{company_name} earnings call transcript Q3 Q4 2024 strategic priorities initiatives",
            max_results=7
        )

        # Stage 3: Historical for evolution tracking (12 months back)
        if progress_callback:
            progress_callback("Strategic Priorities - Analyzing evolution...")

        historical_search_results = self._search_web(
            f"{company_name} strategic initiatives announcements expansion 2023 2024",
            max_results=6
        )

        # Combine all search results
        search_results = f"""
=== EXECUTIVE INTERVIEWS & STATEMENTS (2024-2025) ===
{exec_search_results}

=== EARNINGS CALL TRANSCRIPTS (Q3/Q4 2024) ===
{earnings_search_results}

=== HISTORICAL CONTEXT (2023-2024) ===
{historical_search_results}
"""

        if progress_callback:
            progress_callback("Strategic Priorities - Synthesizing insights...")

        prompt = f"""Based on the following web search results about {company_name}, identify their top 3 strategic business priorities.

WEB SEARCH RESULTS:
{search_results}

Using the above search results, analyze the company's:
- Current strategic initiatives and public announcements
- Recent earnings calls and investor presentations
- Industry trends and competitive positioning
- Business model and growth areas
- Executive leadership focus areas
- How priorities have evolved over the past 12 months

CRITICAL INSTRUCTIONS FOR EXECUTIVE QUOTES:
- Extract direct quotes from named executives (CEO, CFO, COO, etc.)
- ONLY include quotes where you can identify a verifiable source URL from the search results above
- Each quote MUST include: exact quote text, executive name/title, source name, date, and source URL
- If you cannot verify the source URL from the search results, DO NOT include the quote

For each priority, provide in JSON format:
- priority_id: Unique identifier (e.g., "priority_001")
- priority_name: Short, impactful name (2-4 words, e.g., "Growing the Core", "Entering New Markets")
- priority_description: Detailed description of what the company is trying to achieve (15-25 words, specific metrics if available)
- business_impact: Why this priority matters to the business
- related_initiatives: Array of related strategic initiatives or programs
- urgency: high/medium/low
- executive_owner: Name and title of the executive who owns this priority (from search results if available)
- executive_responsibility: Brief description of why this executive owns this priority (10-15 words)
- executive_quotes: Array of direct quotes (ONLY with verified URLs from search results):
  - executive: "Name, Title" (e.g., "Jane Smith, CEO")
  - quote: Exact quote text from the source
  - source: Name of source document/interview
  - date: Date of statement (e.g., "Oct 2024", "Q3 2024")
  - url: Full source URL from search results above
- evolution: How this priority has changed over past 12 months:
  - current_focus: What the priority focuses on now (2024-2025)
  - previous_focus: What it was 12 months ago, if different (2023)
  - change_indicator: "New priority" / "Increased emphasis" / "Shifted focus" / "Consistent focus"
- sources: Array of 2-3 specific sources

Focus on priorities that would benefit from intelligent agreement management and automation.

Return ONLY valid JSON with an array of 3 priorities under the key "priorities".
"""

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a strategic business analyst. Analyze company information and identify top strategic priorities that drive business growth."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )

        result = json.loads(response.choices[0].message.content)

        # Log token usage
        if progress_callback and hasattr(response, 'usage'):
            usage = response.usage
            progress_callback(f"[✓] Strategic priorities complete | Tokens: {usage.total_tokens} (prompt: {usage.prompt_tokens}, completion: {usage.completion_tokens})")

        return result.get('priorities', [])

    async def research_business_units(
        self,
        company_name: str,
        progress_callback: Optional[Callable] = None
    ) -> List[Dict]:
        """Research business units and divisions using Tavily web search"""

        if progress_callback:
            progress_callback("Business Units - Searching web...")

        # Search for business units and organizational structure
        search_results = self._search_web(
            f"{company_name} business units divisions organizational structure segments revenue breakdown",
            max_results=5
        )

        if progress_callback:
            progress_callback("Business Units - Analyzing results...")

        prompt = f"""Based on the following web search results about {company_name}, analyze their business structure and identify 2-4 major business units or divisions.

WEB SEARCH RESULTS:
{search_results}

Using the above search results, identify the major business units or divisions:

For each business unit, provide in JSON format:
- unit_id: Unique identifier (e.g., "bu_001")
- name: Business unit name
- description: What this unit does (1-2 sentences)
- revenue_contribution: Revenue amount with $ (estimate if needed)
- revenue_percentage: Percentage of total company revenue
- agreement_volume: Estimated number of agreements (e.g., "5,000+")
- agreement_volume_numeric: Numeric estimate
- complexity_level: 1-5 scale (1=simple, 5=highly complex)
- complexity_notes: Why this complexity rating
- key_agreement_types: Array of 2-4 main agreement types with:
  - type: Agreement type name
  - volume: Estimated count
  - avg_value: Average contract value
  - avg_term: Typical contract duration
  - renewal_rate: Renewal percentage if known
- primary_counterparties: Array of who they contract with
- systems_used: Array of systems/tools for contract management (use common acronyms like CRM, ERP, CLM, CDMS, HCM, SCM, PLM, etc.)
- pain_points: Array of 2-3 likely contract/agreement challenges
- sources: Data sources
- confidence: high/medium/low

Return array of business units as valid JSON.
"""

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a business analyst specializing in organizational structure and operations. Provide detailed, realistic estimates based on company size and industry."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4,
            response_format={"type": "json_object"}
        )

        result = json.loads(response.choices[0].message.content)

        # Log token usage
        if progress_callback and hasattr(response, 'usage'):
            usage = response.usage
            progress_callback(f"[✓] Business units complete | Tokens: {usage.total_tokens} (prompt: {usage.prompt_tokens}, completion: {usage.completion_tokens})")

        # Handle if response wraps units in an object
        if "business_units" in result:
            return result["business_units"]
        elif isinstance(result, list):
            return result
        else:
            return [result]

    async def research_agreement_landscape(
        self,
        company_name: str,
        business_units: List[Dict],
        progress_callback: Optional[Callable] = None
    ) -> Dict:
        """Research agreement landscape organized by business function"""

        if progress_callback:
            progress_callback("Agreement Landscape")

        # Prepare business units context
        units_summary = json.dumps([{
            'unit_id': u.get('unit_id'),
            'name': u.get('name'),
            'description': u.get('description'),
            'revenue': u.get('revenue_contribution'),
            'systems': u.get('systems_used', [])
        } for u in business_units], indent=2)

        prompt = f"""Analyze {company_name}'s agreement/contract landscape organized by BUSINESS FUNCTION.

Business Units Context:
{units_summary}

Based on the business units above, identify AT LEAST 5 major BUSINESS FUNCTIONS (minimum 5, maximum 8). Common functions include: Sales, Marketing, Procurement, HR, Legal, IT, Operations, Finance, Customer Success. Map agreements to each function.

For EACH business function, provide in JSON format:
- function_name: Name of the business function (e.g., "Sales", "Procurement")
- description: 1-2 sentence description of what this function does
- business_units: Array of business unit names that belong to this function
- systems_used: Array of systems/tools this function uses for agreements (use common acronyms like CRM, ERP, CLM, CDMS, HCM, SCM, PLM, etc. based on business units data)
- agreement_types: Array of 3-5 key agreement types with:
  - type: Agreement type name (e.g., "Customer Master Service Agreement")
  - volume: Estimated count (e.g., "2,000+")
  - avg_value: Average contract value if applicable
  - avg_term: Typical contract duration
  - managed_in: Which system(s) manage this agreement type
  - renewal_pattern: "quarterly"/"annual"/"multi-year"/"evergreen"
- total_agreements: Total agreement count for this function
- complexity: Complexity rating (1-5, where 5 is most complex)
- pain_points: Array of 2-3 typical challenges for this function

Also include a summary:
- total_estimated_agreements: Total across all functions
- total_functions: Count of functions

Return as valid JSON with structure:
{{
  "functions": [...array of function objects...],
  "summary": {{...}}
}}
"""

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a contract management expert specializing in organizational analysis. Map agreements to business functions based on typical company structures and the business units provided."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4,
            response_format={"type": "json_object"}
        )

        result = json.loads(response.choices[0].message.content)

        # Log token usage
        if progress_callback and hasattr(response, 'usage'):
            usage = response.usage
            progress_callback(f"[✓] Agreement landscape complete | Tokens: {usage.total_tokens} (prompt: {usage.prompt_tokens}, completion: {usage.completion_tokens})")

        return result

    async def research_optimization_opportunities(
        self,
        company_name: str,
        company_profile: Dict,
        business_units: List[Dict],
        landscape: Dict,
        strategic_priorities: List[Dict],
        progress_callback: Optional[Callable] = None
    ) -> List[Dict]:
        """Identify 2-3 contract optimization opportunities tied to functions/systems and strategic priorities"""

        if progress_callback:
            progress_callback("Optimization Opportunities")

        # Extract functions and their pain points for context
        functions_summary = []
        if 'functions' in landscape:
            for func in landscape['functions']:
                functions_summary.append({
                    'function': func.get('function_name'),
                    'systems': func.get('systems_used', []),
                    'agreements': func.get('total_agreements'),
                    'pain_points': func.get('pain_points', [])
                })

        # Extract priorities with executive quotes for context
        priorities_summary = []
        for priority in strategic_priorities:
            priority_summary = {
                'name': priority.get('priority_name'),
                'description': priority.get('priority_description'),
                'executive_owner': priority.get('executive_owner'),
                'urgency': priority.get('urgency'),
                'executive_quotes': priority.get('executive_quotes', [])
            }
            priorities_summary.append(priority_summary)

        # Build product catalog context if available
        product_context = ""
        if self.product_catalog:
            products = self.product_catalog.get('products', [])
            product_summaries = []
            for product in products[:15]:  # Limit to top 15 to keep prompt manageable
                product_summaries.append({
                    'name': product.get('name'),
                    'category': product.get('category'),
                    'value_statement': product.get('value_statement'),
                    'key_capabilities': product.get('key_capabilities', [])[:3]
                })

            product_context = f"""

DocuSign Product Catalog (for recommendation context):
{json.dumps(product_summaries, indent=2)}
"""

        context = f"""
Company: {company_name}
Revenue: {company_profile.get('scale', {}).get('annual_revenue', 'Unknown')}
Industry: {company_profile.get('industry', 'Unknown')}

Strategic Priorities (with Executive Quotes):
{json.dumps(priorities_summary, indent=2)}

Business Functions & Pain Points:
{json.dumps(functions_summary, indent=2)}
{product_context}
"""

        prompt = f"""Based on this company context:
{context}

Identify EXACTLY 3 high-value contract/agreement optimization opportunities.

{"PRODUCT CONTEXT: Use the DocuSign Product Catalog above to recommend specific products that address each opportunity." if self.product_catalog else ""}

CRITICAL REQUIREMENTS:
1. Each opportunity MUST directly support one of the Strategic Priorities listed above
2. Each opportunity MUST reference specific executive quotes from the priorities (if available)
3. Map each opportunity to the executive who would champion it

Each opportunity should be tied to specific business functions, systems, and agreement types.

For each opportunity, provide in JSON format:
- opportunity_id: Unique ID (e.g., "opp_001")
- title: Concise title (e.g., "Sales Contract Cycle Time Reduction")
- use_case_name: Clear use case name for presentation (e.g., "Maximize Value Negotiated", "Accelerate Contract Onboarding")
- description: One sentence description
- business_function: Primary business function that benefits (e.g., "Sales", "Procurement")
- agreement_types: Array of specific agreement types affected (e.g., ["SaaS Subscription", "MSAs", "Payment Processing", "Order Forms", "Hardware Purchasing"])
- capabilities: 2-3 sentence description of what this opportunity enables
- systems_impacted: Array of systems that need changes (e.g., ["Salesforce", "DocuSign"])
- business_units_impacted: Array of business unit IDs that benefit
- strategic_alignment: Array of 2 strategic benefits
- executive_alignment: How this opportunity maps to executive statements:
  - priority_name: Which strategic priority this supports
  - executive_champion: Name and title of executive who would champion this (from priorities)
  - alignment_statement: 2-3 sentence explanation of how this addresses the executive's stated priority
  - supporting_quote: Direct executive quote from priorities that this opportunity addresses (if available)
- current_state:
  - process_description: Current process (2-3 sentences)
  - cycle_time: Current timeframe
  - pain_points: Array of 3 specific problems
- future_state:
  - process_description: Improved process
  - target_cycle_time: Target timeframe
  - key_capabilities: Array of 3 required capabilities/tools
- risk_reduction: Describe how this reduces risk for the specific agreement types (e.g., "10% reduced value leakage", "Improved obligation tracking")
- compliance_benefits: Describe compliance improvements by agreement type (e.g., "Enhanced audit trail for regulatory compliance", "Automated renewals reduce expiration risk")
- value_quantification:
  - time_savings: Time saved per transaction
  - agreements_affected: Annual volume
  - revenue_acceleration: Revenue impact (if applicable)
  - cost_savings: Cost reduction
  - total_annual_value: Combined annual value
  - implementation_cost: Estimated cost
  - roi_percentage: ROI as percentage
  - payback_period: Payback timeframe
- metrics: Array of 2-4 mixed metrics for presentation (combine financial and efficiency):
  - Each metric: {{"label": "reduced value leakage", "value": "10%", "type": "financial"}} or {{"label": "faster cycle time", "value": "71-95%", "type": "efficiency"}}
  - Include at least 1 financial (ROI, cost reduction, revenue) and 1 efficiency (cycle time, speed, volume) metric
  - Examples: "reduced value leakage: 10%", "improved conversion: 8-20%", "faster cycle time: 71-95%", "cost savings: $450K"
- implementation:
  - priority: high/medium/low
  - timeline: Implementation duration
  - complexity: high/medium/low
  - dependencies: Array of prerequisites
{f'''- recommended_docusign_products: Array of 1-3 DocuSign products that address this opportunity:
  - product_name: Name from catalog
  - category: Category from catalog
  - why_recommended: 1-2 sentence explanation of fit
  - key_capabilities_used: Array of 2-3 capabilities from the product that apply''' if self.product_catalog else ''}
- sources: Data sources
- confidence: high/medium/low

Focus on opportunities that address the pain points identified in the business functions above.

IMPORTANT: You MUST return EXACTLY 3 opportunities in your response.

Return as valid JSON with this exact structure:
{{
  "opportunities": [
    {{ /* opportunity 1 with all fields above */ }},
    {{ /* opportunity 2 with all fields above */ }},
    {{ /* opportunity 3 with all fields above */ }}
  ]
}}
"""

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a business process consultant specializing in contract lifecycle optimization. Provide realistic value estimates based on industry benchmarks. Always return EXACTLY 3 opportunities."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=4096,
            response_format={"type": "json_object"}
        )

        result = json.loads(response.choices[0].message.content)

        # Log token usage
        if progress_callback and hasattr(response, 'usage'):
            usage = response.usage
            progress_callback(f"[✓] Opportunities complete | Tokens: {usage.total_tokens} (prompt: {usage.prompt_tokens}, completion: {usage.completion_tokens})")

        # Handle if response wraps opportunities in an object
        if "opportunities" in result:
            return result["opportunities"]
        elif "optimization_opportunities" in result:
            return result["optimization_opportunities"]
        elif isinstance(result, list):
            return result
        else:
            return [result]

    async def research_agreement_matrix(
        self,
        company_name: str,
        company_profile: Dict,
        business_units: List[Dict],
        progress_callback: Optional[Callable] = None
    ) -> Dict:
        """Research agreement types matrix for visualization"""

        if progress_callback:
            progress_callback("Agreement Matrix")

        # Prepare context
        industry = company_profile.get('industry', 'N/A')
        scale = company_profile.get('scale', {})

        prompt = f"""I'm creating an agreement matrix for {company_name} in the {industry} industry.

Company Scale:
- Revenue: {scale.get('annual_revenue', 'N/A')}
- Employees: {scale.get('employees', 'N/A')}

The matrix will use:
- X-axis: Volume (how frequently the agreement type is used/signed) - Scale 1-10
- Y-axis: Complexity (clauses, stakeholders, legal review, customization) - Scale 1-10

Identify the top 20 agreement types most relevant to {company_name} based on their industry, operations, and common practices. Include both internal (within company) and external (with customers, vendors, regulators) agreements.

For EACH agreement type, provide in JSON format:
- type: Agreement type name (e.g., "Non-Disclosure Agreements", "Master Service Agreements")
- volume: Numeric score 1-10 (1=rarely used, 5=moderate, 10=used constantly)
- complexity: Numeric score 1-10 (1=simple template, 5=moderate negotiation, 10=highly complex/customized)
- classification: "Internal" or "External"
- business_unit: Primary owner (e.g., "Legal", "HR", "Sales", "Procurement", "Operations", "IT", "Finance")
- description: Brief 1-sentence description of this agreement type
- estimated_annual_volume: Approximate number per year (e.g., "500+", "2,000+")

Also provide:
- matrix_metadata:
  - total_types: Count of agreement types
  - highest_volume_type: Name of agreement with highest volume
  - highest_complexity_type: Name of agreement with highest complexity
  - quadrant_distribution: Count in each quadrant (high_vol_high_complex, high_vol_low_complex, low_vol_high_complex, low_vol_low_complex)

Base suggestions on what is typical for companies in this industry if exact internal details are unavailable.

Return as valid JSON with structure:
{{
  "agreement_types": [...array of 20 agreement type objects...],
  "matrix_metadata": {{...}}
}}
"""

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a contract management expert specializing in agreement lifecycle analysis. Provide realistic volume and complexity rankings based on industry standards and company size."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4,
            response_format={"type": "json_object"}
        )

        result = json.loads(response.choices[0].message.content)

        # Log token usage
        if progress_callback and hasattr(response, 'usage'):
            usage = response.usage
            progress_callback(f"[✓] Agreement matrix complete | Tokens: {usage.total_tokens} (prompt: {usage.prompt_tokens}, completion: {usage.completion_tokens})")

        return result

    async def research_company_full(
        self,
        company_name: str,
        progress_callbacks: Optional[Dict[str, Callable]] = None,
        status_obj = None
    ) -> Dict:
        """
        Execute all research tasks in parallel and combine results

        Args:
            company_name: Name of company to research
            progress_callbacks: Dict mapping task names to callback functions
            status_obj: Streamlit status object for updating the status label

        Returns:
            Complete company analysis matching template structure
        """

        callbacks = progress_callbacks or {}

        # Set initial status
        if status_obj:
            status_obj.update(label="Running parallel research agents...")

        # Phase 1: Execute profile, business units, and priorities in parallel (no dependencies)
        profile_task = self.research_company_profile(
            company_name,
            callbacks.get('profile')
        )
        units_task = self.research_business_units(
            company_name,
            callbacks.get('business_units')
        )
        priorities_task = self.research_strategic_priorities(
            company_name,
            callbacks.get('priorities')
        )

        # Wait for Phase 1 to complete
        profile, business_units, strategic_priorities = await asyncio.gather(
            profile_task,
            units_task,
            priorities_task
        )

        # Phase 2: Run landscape and matrix in parallel (depend on profile + business_units)
        landscape_task = self.research_agreement_landscape(
            company_name,
            business_units,
            callbacks.get('landscape')
        )
        matrix_task = self.research_agreement_matrix(
            company_name,
            profile,
            business_units,
            callbacks.get('matrix')
        )

        # Wait for Phase 2 to complete
        landscape, agreement_matrix = await asyncio.gather(
            landscape_task,
            matrix_task
        )

        # Phase 3: Run optimization opportunities (needs priorities and landscape)
        opportunities = await self.research_optimization_opportunities(
            company_name,
            profile,
            business_units,
            landscape,
            strategic_priorities,
            callbacks.get('opportunities')
        )

        # Update status to complete
        if status_obj:
            status_obj.update(label="Research complete!", state="complete")

        # Map priorities to capabilities
        priority_mappings = self._map_priorities_to_capabilities(strategic_priorities, opportunities)

        # Calculate portfolio summary
        portfolio_summary = self._calculate_portfolio_summary(opportunities)

        # Combine into template structure
        analysis = {
            "_meta": {
                "template_version": "2.0",
                "company_name": company_name,
                "analysis_date": datetime.now().strftime("%Y-%m-%d"),
                "last_updated": datetime.now().strftime("%Y-%m-%d"),
                "analyst": "AI Research Agent",
                "research_status": "completed",
                "notes": "Generated via automated research agent with function-based agreement mapping"
            },
            "company_profile": profile,
            "business_units": business_units,
            "strategic_priorities": strategic_priorities,
            "priority_mappings": priority_mappings,
            "agreement_landscape_by_function": landscape,
            "optimization_opportunities": opportunities,
            "agreement_matrix": agreement_matrix,
            "portfolio_summary": portfolio_summary,
            "research_notes": {
                "key_findings": [
                    "Analysis generated via AI research agent",
                    "Data sourced from publicly available information",
                    "Agreements mapped to business functions and systems",
                    "Estimates based on industry benchmarks and company size"
                ],
                "data_gaps": [
                    "Exact agreement counts by type",
                    "Current CLM vendor details",
                    "Internal process metrics"
                ],
                "next_steps": [
                    "Validate findings with company stakeholders",
                    "Review sample agreements for each function",
                    "Refine financial assumptions",
                    "Confirm systems usage by function"
                ]
            }
        }

        return analysis

    def _map_priorities_to_capabilities(
        self,
        priorities: List[Dict],
        opportunities: List[Dict]
    ) -> List[Dict]:
        """
        Map strategic priorities to optimization capabilities/opportunities.

        Creates a 1:1 mapping between priorities and capabilities for presentation.
        If counts don't match, uses best-fit logic.
        """

        if not priorities or not opportunities:
            return []

        mappings = []

        # Simple 1:1 mapping - match by index if counts are equal
        if len(priorities) == len(opportunities):
            for i, priority in enumerate(priorities):
                mappings.append({
                    "priority_id": priority.get("priority_id"),
                    "priority_name": priority.get("priority_name"),
                    "priority_description": priority.get("priority_description"),
                    "capability_id": opportunities[i].get("id"),
                    "capability_name": opportunities[i].get("use_case_name", opportunities[i].get("title")),
                    "capability_description": opportunities[i].get("capabilities", opportunities[i].get("description")),
                    "business_impact": priority.get("business_impact"),
                    "urgency": priority.get("urgency")
                })
        else:
            # If counts don't match, map first N priorities to first N opportunities
            min_count = min(len(priorities), len(opportunities))
            for i in range(min_count):
                priority = priorities[i]
                opportunity = opportunities[i]
                mappings.append({
                    "priority_id": priority.get("priority_id"),
                    "priority_name": priority.get("priority_name"),
                    "priority_description": priority.get("priority_description"),
                    "capability_id": opportunity.get("id"),
                    "capability_name": opportunity.get("use_case_name", opportunity.get("title")),
                    "capability_description": opportunity.get("capabilities", opportunity.get("description")),
                    "business_impact": priority.get("business_impact"),
                    "urgency": priority.get("urgency")
                })

        return mappings

    def _calculate_portfolio_summary(self, opportunities: List[Dict]) -> Dict:
        """Calculate summary metrics across all opportunities"""

        if not opportunities:
            return {
                "total_opportunities": 0,
                "total_annual_value": "$0",
                "total_implementation_cost": "$0",
                "portfolio_roi": "N/A",
                "portfolio_payback": "N/A",
                "high_priority_opportunities": 0,
                "medium_priority_opportunities": 0,
                "low_priority_opportunities": 0
            }

        total_value = 0
        total_cost = 0
        priority_counts = {"high": 0, "medium": 0, "low": 0}

        for opp in opportunities:
            # Extract numeric values from strings like "$12M"
            value_str = opp.get("value_quantification", {}).get("total_annual_value", "0")
            cost_str = opp.get("value_quantification", {}).get("implementation_cost", "0")

            value = self._parse_currency(value_str)
            cost = self._parse_currency(cost_str)

            total_value += value
            total_cost += cost

            priority = opp.get("implementation", {}).get("priority", "medium").lower()
            if priority in priority_counts:
                priority_counts[priority] += 1

        # Calculate portfolio ROI
        roi = ((total_value - total_cost) / total_cost * 100) if total_cost > 0 else 0
        payback_months = (total_cost / (total_value / 12)) if total_value > 0 else 0

        return {
            "total_opportunities": len(opportunities),
            "total_annual_value": self._format_currency(total_value),
            "total_implementation_cost": self._format_currency(total_cost),
            "portfolio_roi": f"{roi:.0f}%",
            "portfolio_payback": f"{payback_months:.0f} months" if payback_months < 12 else f"{payback_months/12:.1f} years",
            "high_priority_opportunities": priority_counts["high"],
            "medium_priority_opportunities": priority_counts["medium"],
            "low_priority_opportunities": priority_counts["low"]
        }

    @staticmethod
    def _parse_currency(value_str: str) -> float:
        """Parse currency string like '$12M' to numeric value"""
        if not value_str or value_str == "N/A":
            return 0.0

        value_str = str(value_str).upper().replace("$", "").replace(",", "").strip()

        multiplier = 1
        if "B" in value_str:
            multiplier = 1_000_000_000
            value_str = value_str.replace("B", "")
        elif "M" in value_str:
            multiplier = 1_000_000
            value_str = value_str.replace("M", "")
        elif "K" in value_str:
            multiplier = 1_000
            value_str = value_str.replace("K", "")

        try:
            return float(value_str) * multiplier
        except:
            return 0.0

    @staticmethod
    def _format_currency(value: float) -> str:
        """Format numeric value to currency string"""
        if value >= 1_000_000_000:
            return f"${value/1_000_000_000:.1f}B"
        elif value >= 1_000_000:
            return f"${value/1_000_000:.1f}M"
        elif value >= 1_000:
            return f"${value/1_000:.0f}K"
        else:
            return f"${value:.0f}"
