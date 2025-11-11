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
from verification import (
    score_source_credibility,
    verify_quote_url,
    calculate_quote_confidence
)


class CompanyResearchAgent:
    """Orchestrates parallel research using OpenAI API with Tavily web search"""

    def __init__(self, api_key: str, tavily_api_key: Optional[str] = None):
        self.client = AsyncOpenAI(api_key=api_key)
        self.model = "gpt-4-turbo-preview"
        self.tavily = TavilyClient(api_key=tavily_api_key) if tavily_api_key else None
        self.product_catalog = self._load_product_catalog()
        self.research_cache = self._load_research_cache()

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

    def _load_research_cache(self) -> Dict:
        """
        Load research cache for industry benchmarks and company findings

        Returns:
            Cache dict or empty structure if not available
        """
        try:
            cache_path = Path(__file__).parent / "data" / "research_cache.json"

            if not cache_path.exists():
                return {
                    "industry_benchmarks": {},
                    "company_findings": {},
                    "software_stack_patterns": {}
                }

            with open(cache_path, 'r') as f:
                cache = json.load(f)

            return cache

        except Exception as e:
            # Silently fail - cache is optional
            return {
                "industry_benchmarks": {},
                "company_findings": {},
                "software_stack_patterns": {}
            }

    def _save_research_cache(self):
        """Save research cache to disk"""
        try:
            cache_path = Path(__file__).parent / "data" / "research_cache.json"

            with open(cache_path, 'w') as f:
                json.dump(self.research_cache, f, indent=2)

        except Exception as e:
            # Silently fail - cache save is not critical
            print(f"Warning: Could not save research cache: {e}")

    def _is_cache_valid(self, cached_at: str, max_age_days: int) -> bool:
        """
        Check if cached data is still valid

        Args:
            cached_at: ISO format date string
            max_age_days: Maximum age in days

        Returns:
            True if cache is still valid
        """
        try:
            cached_date = datetime.fromisoformat(cached_at.replace('Z', '+00:00'))
            age_days = (datetime.now() - cached_date).days
            return age_days < max_age_days
        except:
            return False

    def _search_web_raw(self, query: str, max_results: int = 5) -> List[Dict]:
        """
        Search the web using Tavily and return raw results

        Args:
            query: Search query
            max_results: Maximum number of results to return

        Returns:
            List of result dictionaries with url, title, content
        """
        if not self.tavily:
            return []

        try:
            response = self.tavily.search(
                query=query,
                search_depth="advanced",
                max_results=max_results
            )

            return response.get('results', [])

        except Exception as e:
            print(f"Tavily search error: {e}")
            return []

    def _search_web(self, query: str, max_results: int = 5) -> str:
        """
        Search the web using Tavily and return formatted results

        Args:
            query: Search query
            max_results: Maximum number of results to return

        Returns:
            Formatted string with search results
        """
        raw_results = self._search_web_raw(query, max_results)

        if not raw_results:
            return "Web search not available (Tavily API key not provided)" if not self.tavily else "No results found"

        results = []
        for result in raw_results:
            results.append(f"""
Source: {result.get('url', 'N/A')}
Title: {result.get('title', 'N/A')}
Content: {result.get('content', 'N/A')}
---""")

        return '\n'.join(results) if results else "No results found"

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

        exec_search_results_raw = self._search_web_raw(
            f"{company_name} CEO CFO interview 2024 2025 strategy vision keynote",
            max_results=7
        )
        exec_search_results = self._search_web(
            f"{company_name} CEO CFO interview 2024 2025 strategy vision keynote",
            max_results=7
        )

        # Stage 2: Earnings call transcripts
        if progress_callback:
            progress_callback("Strategic Priorities - Searching earnings transcripts...")

        earnings_search_results_raw = self._search_web_raw(
            f"{company_name} earnings call transcript Q3 Q4 2024 strategic priorities initiatives",
            max_results=7
        )
        earnings_search_results = self._search_web(
            f"{company_name} earnings call transcript Q3 Q4 2024 strategic priorities initiatives",
            max_results=7
        )

        # Stage 3: Historical for evolution tracking (12 months back)
        if progress_callback:
            progress_callback("Strategic Priorities - Analyzing evolution...")

        historical_search_results_raw = self._search_web_raw(
            f"{company_name} strategic initiatives announcements expansion 2023 2024",
            max_results=6
        )
        historical_search_results = self._search_web(
            f"{company_name} strategic initiatives announcements expansion 2023 2024",
            max_results=6
        )

        # Combine all search results (formatted for GPT)
        search_results = f"""
=== EXECUTIVE INTERVIEWS & STATEMENTS (2024-2025) ===
{exec_search_results}

=== EARNINGS CALL TRANSCRIPTS (Q3/Q4 2024) ===
{earnings_search_results}

=== HISTORICAL CONTEXT (2023-2024) ===
{historical_search_results}
"""

        # Combine raw search results (for verification)
        all_search_results_raw = exec_search_results_raw + earnings_search_results_raw + historical_search_results_raw

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

        # Verify executive quotes
        priorities = result.get('priorities', [])
        if progress_callback:
            progress_callback("Strategic Priorities - Verifying executive quotes...")

        for priority in priorities:
            executive_quotes = priority.get('executive_quotes', [])
            for quote in executive_quotes:
                # Calculate confidence score using verification
                confidence = calculate_quote_confidence(quote, all_search_results_raw)
                quote['confidence_score'] = confidence

                # Get source credibility
                source = quote.get('source', '')
                url = quote.get('url', '')
                credibility = score_source_credibility(source, url)
                quote['source_credibility'] = credibility

                # Verify URL against search results
                verification = verify_quote_url(url, all_search_results_raw)
                quote['verification_status'] = verification['verification_status']
                quote['verified'] = verification['verified']

        # Log token usage
        if progress_callback and hasattr(response, 'usage'):
            usage = response.usage
            progress_callback(f"[✓] Strategic priorities complete | Tokens: {usage.total_tokens} (prompt: {usage.prompt_tokens}, completion: {usage.completion_tokens})")

        return priorities

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

    def _parse_job_postings_for_stack(self, search_results: List[Dict]) -> List[Dict]:
        """
        Parse job postings to extract software stack mentions

        Args:
            search_results: Raw search results from Tavily

        Returns:
            List of systems found with sources
        """
        # Common business systems to look for
        systems_keywords = {
            "Salesforce": ["Salesforce", "SFDC", "Sales Cloud", "Service Cloud"],
            "SAP": ["SAP", "S/4HANA", "SAP ERP"],
            "Workday": ["Workday", "Workday HCM", "Workday Financial"],
            "Oracle": ["Oracle", "Oracle ERP", "Oracle Cloud"],
            "NetSuite": ["NetSuite", "Net Suite"],
            "Coupa": ["Coupa"],
            "Ariba": ["Ariba", "SAP Ariba"],
            "ServiceNow": ["ServiceNow", "Service Now"],
            "Microsoft Dynamics": ["Dynamics 365", "Dynamics CRM", "Microsoft Dynamics"],
            "DocuSign": ["DocuSign"],
            "Adobe Sign": ["Adobe Sign", "EchoSign"],
            "Tableau": ["Tableau"],
            "Power BI": ["Power BI", "PowerBI"],
        }

        systems_found = {}

        for result in search_results:
            content = result.get('content', '') + ' ' + result.get('title', '')
            url = result.get('url', '')

            for system_name, keywords in systems_keywords.items():
                for keyword in keywords:
                    if keyword.lower() in content.lower():
                        if system_name not in systems_found:
                            systems_found[system_name] = {
                                "system": system_name,
                                "category": self._categorize_system(system_name),
                                "mentions": 0,
                                "sources": [],
                                "confidence": "high"
                            }

                        systems_found[system_name]["mentions"] += 1
                        if url and url not in systems_found[system_name]["sources"]:
                            systems_found[system_name]["sources"].append(url)

        # Convert to list and add evidence snippets
        result_list = []
        for system_name, data in systems_found.items():
            if data["mentions"] > 0:
                data["evidence"] = f"Found in {data['mentions']} job posting(s)"
                data["source"] = data["sources"][0] if data["sources"] else "Job postings"
                result_list.append(data)

        return result_list

    def _categorize_system(self, system_name: str) -> str:
        """Categorize a system by type"""
        categories = {
            "Salesforce": "CRM",
            "Microsoft Dynamics": "CRM/ERP",
            "SAP": "ERP",
            "Oracle": "ERP",
            "NetSuite": "ERP",
            "Workday": "HCM",
            "Coupa": "Procurement",
            "Ariba": "Procurement",
            "ServiceNow": "ITSM",
            "DocuSign": "CLM/eSignature",
            "Adobe Sign": "eSignature",
            "Tableau": "Analytics",
            "Power BI": "Analytics",
        }
        return categories.get(system_name, "Business Software")

    async def deep_research_company(
        self,
        company_name: str,
        company_profile: Dict,
        business_units: List[Dict],
        progress_callback: Optional[Callable] = None
    ) -> Dict:
        """
        Perform deep research to discover:
        - Strategic goals with executive quotes and sources
        - Software stack via job postings
        - Pain points from reviews and news
        - Industry benchmarks (cached where possible)

        Args:
            company_name: Company name
            company_profile: Company profile dict
            business_units: List of business units
            progress_callback: Progress callback function

        Returns:
            Dict with strategic_goals, software_stack, pain_points, industry_benchmarks
        """
        if not self.tavily:
            # No Tavily = no deep research
            return {
                "strategic_goals": [],
                "software_stack": [],
                "pain_points": [],
                "industry_benchmarks": {},
                "cache_used": False
            }

        if progress_callback:
            progress_callback("Deep Research - Initializing...")

        industry = company_profile.get('industry', 'Unknown')
        revenue = company_profile.get('scale', {}).get('annual_revenue', 'Unknown')

        # Check cache for company-specific findings (expires after 7 days)
        cache_key = company_name.lower().replace(' ', '_')
        cached_findings = self.research_cache.get('company_findings', {}).get(cache_key, {})

        if cached_findings and self._is_cache_valid(cached_findings.get('cached_at', ''), max_age_days=7):
            if progress_callback:
                progress_callback("Deep Research - Using cached findings")
            return cached_findings.get('data', {})

        deep_research_data = {
            "strategic_goals": [],
            "software_stack": [],
            "pain_points": [],
            "industry_benchmarks": {},
            "cache_used": False
        }

        # === 1. SOFTWARE STACK FROM JOB POSTINGS ===
        if progress_callback:
            progress_callback("Deep Research - Analyzing job postings for software stack...")

        job_queries = [
            f"site:linkedin.com/jobs {company_name} Salesforce OR SAP OR Workday OR Oracle",
            f"site:greenhouse.io OR site:lever.co {company_name} required skills CRM ERP",
            f"{company_name} job posting software engineer required skills systems"
        ]

        all_job_results = []
        for query in job_queries:
            results = self._search_web_raw(query, max_results=3)
            all_job_results.extend(results)

        software_stack = self._parse_job_postings_for_stack(all_job_results)
        deep_research_data["software_stack"] = software_stack

        # === 2. STRATEGIC GOALS (additional targeted search beyond what strategic_priorities already found) ===
        if progress_callback:
            progress_callback("Deep Research - Searching for strategic context...")

        strategic_queries = [
            f"{company_name} strategic priorities 2024 2025 initiatives goals",
            f"{company_name} digital transformation automation efficiency"
        ]

        strategic_results_text = ""
        for query in strategic_queries:
            results = self._search_web(query, max_results=3)
            strategic_results_text += results + "\n\n"

        # Parse strategic goals using GPT-4 (lightweight extraction, not full analysis like strategic_priorities)
        strategic_prompt = f"""Based on these search results about {company_name}, extract any mentions of strategic goals, initiatives, or business priorities.

SEARCH RESULTS:
{strategic_results_text}

Return as JSON:
{{
  "goals_found": [
    {{
      "goal": "Brief description of goal",
      "source": "Source URL if available",
      "confidence": "high/medium/low"
    }}
  ]
}}

If no clear goals found, return empty array."""

        try:
            strategic_response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a research analyst extracting strategic information."},
                    {"role": "user", "content": strategic_prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )

            strategic_data = json.loads(strategic_response.choices[0].message.content)
            deep_research_data["strategic_goals"] = strategic_data.get("goals_found", [])
        except Exception as e:
            print(f"Error extracting strategic goals: {e}")
            deep_research_data["strategic_goals"] = []

        # === 3. PAIN POINTS FROM REVIEWS AND NEWS ===
        if progress_callback:
            progress_callback("Deep Research - Identifying pain points...")

        pain_queries = [
            f"{company_name} contract management challenges issues",
            f"{company_name} sales cycle procurement process pain points"
        ]

        pain_results_text = ""
        for query in pain_queries:
            results = self._search_web(query, max_results=2)
            pain_results_text += results + "\n\n"

        # Parse pain points using GPT-4
        pain_prompt = f"""Based on these search results about {company_name}, identify any contract management or operational pain points.

SEARCH RESULTS:
{pain_results_text}

Look for:
- Contract cycle time issues
- Manual processes
- System integration gaps
- Compliance challenges

Return as JSON:
{{
  "pain_points": [
    {{
      "pain": "Brief description",
      "source": "Source URL if available",
      "confidence": "high/medium/low"
    }}
  ]
}}

If no clear pain points found, return empty array."""

        try:
            pain_response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You are a research analyst identifying business challenges."},
                    {"role": "user", "content": pain_prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )

            pain_data = json.loads(pain_response.choices[0].message.content)
            deep_research_data["pain_points"] = pain_data.get("pain_points", [])
        except Exception as e:
            print(f"Error extracting pain points: {e}")
            deep_research_data["pain_points"] = []

        # === 4. INDUSTRY BENCHMARKS (CACHED) ===
        if progress_callback:
            progress_callback("Deep Research - Applying industry benchmarks...")

        # Create cache key for industry + revenue band
        benchmark_key = f"{industry.lower().replace(' ', '_')}_{self._revenue_band(revenue)}"
        cached_benchmarks = self.research_cache.get('industry_benchmarks', {}).get(benchmark_key, {})

        if cached_benchmarks and self._is_cache_valid(cached_benchmarks.get('cached_at', ''), max_age_days=90):
            deep_research_data["industry_benchmarks"] = cached_benchmarks.get('data', {})
            deep_research_data["cache_used"] = True
        else:
            # Search for industry benchmarks
            benchmark_query = f"{industry} companies typical sales cycle contract volume procurement benchmarks"
            benchmark_results = self._search_web(benchmark_query, max_results=3)

            benchmark_prompt = f"""Based on these search results, extract typical benchmarks for {industry} companies at {revenue} revenue scale.

SEARCH RESULTS:
{benchmark_results}

Look for:
- Typical sales cycle time
- Contract volumes
- Procurement contract counts
- Agreement management metrics

Return as JSON:
{{
  "sales_cycle_time": "12-18 days (or Unknown)",
  "contract_volume": "8,000-12,000 (or Unknown)",
  "source": "Source description",
  "applies_to": "{industry} companies"
}}"""

            try:
                benchmark_response = await self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are a research analyst extracting industry benchmarks."},
                        {"role": "user", "content": benchmark_prompt}
                    ],
                    temperature=0.3,
                    response_format={"type": "json_object"}
                )

                benchmark_data = json.loads(benchmark_response.choices[0].message.content)
                deep_research_data["industry_benchmarks"] = benchmark_data

                # Cache the benchmarks
                if 'industry_benchmarks' not in self.research_cache:
                    self.research_cache['industry_benchmarks'] = {}

                self.research_cache['industry_benchmarks'][benchmark_key] = {
                    'data': benchmark_data,
                    'cached_at': datetime.now().isoformat()
                }
                self._save_research_cache()

            except Exception as e:
                print(f"Error extracting industry benchmarks: {e}")
                deep_research_data["industry_benchmarks"] = {}

        # Cache the complete findings for this company
        if 'company_findings' not in self.research_cache:
            self.research_cache['company_findings'] = {}

        self.research_cache['company_findings'][cache_key] = {
            'data': deep_research_data,
            'cached_at': datetime.now().isoformat()
        }
        self._save_research_cache()

        if progress_callback:
            progress_callback("[✓] Deep research complete")

        return deep_research_data

    def _revenue_band(self, revenue_str: str) -> str:
        """Convert revenue string to band for caching"""
        if 'billion' in revenue_str.lower() or 'B' in revenue_str:
            return '1B_plus'
        elif 'million' in revenue_str.lower() or 'M' in revenue_str:
            try:
                amount = float(''.join(c for c in revenue_str if c.isdigit() or c == '.'))
                if amount >= 500:
                    return '500M_1B'
                elif amount >= 100:
                    return '100M_500M'
                else:
                    return 'under_100M'
            except:
                return 'unknown'
        else:
            return 'unknown'

    async def research_optimization_opportunities(
        self,
        company_name: str,
        company_profile: Dict,
        business_units: List[Dict],
        landscape: Dict,
        strategic_priorities: List[Dict],
        deep_research_context: Optional[Dict] = None,
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

        # Build deep research context if available
        deep_context = ""
        if deep_research_context:
            software_stack = deep_research_context.get('software_stack', [])
            pain_points = deep_research_context.get('pain_points', [])
            benchmarks = deep_research_context.get('industry_benchmarks', {})

            if software_stack or pain_points or benchmarks:
                deep_context = "\n\n=== DEEP RESEARCH FINDINGS ===\n"

                if software_stack:
                    deep_context += "\nSoftware Stack (discovered from job postings):\n"
                    for system in software_stack:
                        deep_context += f"- {system['system']} ({system['category']})\n"
                        deep_context += f"  Source: {system['source']}\n"
                        deep_context += f"  Evidence: {system['evidence']}\n"

                if pain_points:
                    deep_context += "\nIdentified Pain Points:\n"
                    for pain in pain_points:
                        deep_context += f"- {pain['pain']}\n"
                        if pain.get('source'):
                            deep_context += f"  Source: {pain['source']}\n"

                if benchmarks:
                    deep_context += "\nIndustry Benchmarks:\n"
                    for key, value in benchmarks.items():
                        if key not in ['source', 'applies_to']:
                            deep_context += f"- {key}: {value}\n"
                    if benchmarks.get('source'):
                        deep_context += f"  Source: {benchmarks['source']}\n"

        context = f"""
Company: {company_name}
Revenue: {company_profile.get('scale', {}).get('annual_revenue', 'Unknown')}
Industry: {company_profile.get('industry', 'Unknown')}

Strategic Priorities (with Executive Quotes):
{json.dumps(priorities_summary, indent=2)}

Business Functions & Pain Points:
{json.dumps(functions_summary, indent=2)}
{deep_context}
{product_context}
"""

        # Create few-shot examples to guide the AI
        few_shot_examples = '''
# EXAMPLE 1: Sales Contract Acceleration

For a $5B software company with strategic priority to "accelerate revenue growth":

{
  "opportunity_id": "opp_001",
  "title": "Sales Contract Cycle Time Reduction",
  "use_case_name": "Accelerate Quote-to-Cash",
  "description": "Automate MSA and order form generation to reduce sales cycle time by 75% and accelerate revenue recognition.",
  "business_function": "Sales",
  "agreement_types": ["Master Service Agreements", "Order Forms", "Statements of Work", "Non-Disclosure Agreements"],
  "capabilities": "Enable sales reps to generate, negotiate, and execute customer agreements in days instead of weeks. Self-service contract generation from approved templates reduces legal review bottlenecks and provides real-time visibility into deal status.",
  "systems_impacted": ["Salesforce CRM", "DocuSign CLM", "NetSuite ERP"],
  "business_units_impacted": ["Enterprise Sales", "Mid-Market Sales", "Sales Operations"],
  "strategic_alignment": ["Accelerate revenue growth by reducing sales cycle time", "Scale sales operations without proportional headcount growth"],
  "executive_alignment": {
    "priority_name": "Accelerate Revenue Growth",
    "executive_champion": "Sarah Chen, Chief Revenue Officer",
    "alignment_statement": "This directly addresses the CRO's mandate to shorten sales cycles and accelerate time-to-revenue. By automating contract generation and approval, sales reps spend less time on administrative tasks and more time selling.",
    "supporting_quote": "We need to reduce friction in our quote-to-cash process to hit our $7B revenue target next year."
  },
  "current_state": {
    "process_description": "Sales reps manually create contracts by copying from previous deals, then route through email for legal review. Average 15-20 days from quote to signed contract, with frequent errors requiring rework.",
    "cycle_time": "15-20 days",
    "pain_points": [
      "Manual contract creation from scratch causes inconsistencies and errors",
      "Email-based legal reviews create bottlenecks during quarter-end",
      "No visibility into where contracts are stuck in approval process"
    ]
  },
  "future_state": {
    "process_description": "Sales reps generate contracts from approved templates in Salesforce, automatically routed through CLM for reviews based on deal size. Standard deals approved in hours, complex deals in 3-4 days.",
    "target_cycle_time": "3-4 days",
    "key_capabilities": ["Automated contract generation from templates", "Workflow-based approvals with escalation", "Real-time deal tracking in Salesforce"]
  },
  "risk_reduction": "Standardized contract language reduces negotiation risk and ensures compliance with corporate policies. Automated approval workflows prevent unauthorized discounting.",
  "compliance_benefits": "Complete audit trail of all contract changes and approvals. Automated retention and searchability for regulatory inquiries.",
  "value_quantification": {
    "time_savings": "12 days per contract",
    "agreements_affected": "~3,200 contracts annually",
    "revenue_acceleration": "$15M from faster deal closure",
    "cost_savings": "$450K in reduced legal review costs",
    "total_annual_value": "$15.45M",
    "implementation_cost": "$500K",
    "roi_percentage": "2,990%",
    "payback_period": "2-3 months"
  },
  "metrics": [
    {"label": "faster contract cycle time", "value": "75%", "type": "efficiency"},
    {"label": "ROI", "value": "2,990%", "type": "financial"},
    {"label": "revenue acceleration", "value": "$15M", "type": "financial"}
  ],
  "implementation": {
    "priority": "high",
    "timeline": "4-6 months",
    "complexity": "medium",
    "dependencies": ["Salesforce integration", "Template library creation", "Approval workflow design"]
  },
  "recommended_docusign_products": [
    {
      "product_name": "DocuSign CLM",
      "category": "CLM",
      "why_recommended": "Provides contract authoring, workflow automation, and obligation tracking needed for sales contract lifecycle",
      "key_capabilities_used": ["Contract authoring with clause library", "Workflow automation and approvals", "Salesforce integration"]
    },
    {
      "product_name": "DocuSign Integration for Salesforce",
      "category": "Integration",
      "why_recommended": "Native Salesforce integration enables reps to generate and track contracts without leaving CRM",
      "key_capabilities_used": ["Send for signature directly from Opportunity", "Real-time status tracking in Salesforce"]
    }
  ],
  "sources": "Industry benchmark: 70-80% cycle time reduction typical for sales contract automation",
  "confidence": "high"
}

# EXAMPLE 2: Vendor Contract Visibility

For a manufacturing company with strategic priority to "optimize operational efficiency":

{
  "opportunity_id": "opp_002",
  "title": "Vendor Contract Centralization & Auto-Renewal Prevention",
  "use_case_name": "Eliminate Value Leakage from Missed Renewals",
  "description": "Consolidate scattered vendor contracts into centralized repository with automated renewal tracking to prevent unfavorable auto-renewals and reduce supplier costs by 10-15%.",
  "business_function": "Procurement",
  "agreement_types": ["Vendor Master Agreements", "Purchase Orders", "SaaS Subscriptions", "Equipment Leases", "Maintenance Contracts"],
  "capabilities": "Provide procurement team with complete visibility into all vendor commitments, renewal dates, and pricing terms. AI-powered extraction identifies opportunities to renegotiate or exit unfavorable contracts 90 days before auto-renewal.",
  "systems_impacted": ["Coupa Procurement", "DocuSign Navigator", "SAP ERP"],
  "business_units_impacted": ["Global Procurement", "IT", "Facilities", "Manufacturing Operations"],
  "strategic_alignment": ["Reduce operational costs through better vendor management", "Improve compliance with procurement policies"],
  "executive_alignment": {
    "priority_name": "Optimize Operational Efficiency",
    "executive_champion": "David Kumar, Chief Procurement Officer",
    "alignment_statement": "This directly supports the CPO's initiative to reduce vendor spend by improving visibility into contract commitments. Preventing just 5 unfavorable auto-renewals would save $2-3M annually.",
    "supporting_quote": "We're leaving millions on the table because we don't know what contracts we have or when they renew."
  },
  "current_state": {
    "process_description": "Vendor contracts stored across email, SharePoint, and individual file systems. No centralized tracking of renewal dates. Procurement discovers auto-renewals after they occur, missing renegotiation opportunities.",
    "cycle_time": "N/A - reactive discovery of renewals",
    "pain_points": [
      "Estimated 40% of vendor contracts have unknown renewal dates",
      "Auto-renewals at 3-5% annual increases without negotiation",
      "Cannot quickly answer 'What do we pay Vendor X?' across all agreements"
    ]
  },
  "future_state": {
    "process_description": "All vendor contracts ingested into Navigator with AI-extracted metadata. Automated alerts 90 days before renewal enable proactive renegotiation. Dashboard shows total spend by vendor across all contracts.",
    "target_cycle_time": "90 days proactive notification",
    "key_capabilities": ["AI metadata extraction from legacy contracts", "Automated renewal notifications", "Vendor spend analytics dashboard"]
  },
  "risk_reduction": "Reduce risk of unexpected budget overruns from forgotten renewals. Improved compliance with approved vendor lists and pricing terms.",
  "compliance_benefits": "Centralized repository ensures all vendor contracts accessible for audits. Obligation tracking ensures compliance with contractual commitments.",
  "value_quantification": {
    "time_savings": "20 hours per week in contract search time",
    "agreements_affected": "~800 vendor contracts",
    "revenue_acceleration": "N/A",
    "cost_savings": "$2.4M from prevented auto-renewals and renegotiation",
    "total_annual_value": "$2.4M",
    "implementation_cost": "$300K",
    "roi_percentage": "700%",
    "payback_period": "2 months"
  },
  "metrics": [
    {"label": "cost avoidance", "value": "$2.4M", "type": "financial"},
    {"label": "ROI", "value": "700%", "type": "financial"},
    {"label": "contract visibility", "value": "100%", "type": "efficiency"}
  ],
  "implementation": {
    "priority": "high",
    "timeline": "3-4 months",
    "complexity": "medium",
    "dependencies": ["Historical contract ingestion", "AI training for metadata extraction", "Integration with procurement systems"]
  },
  "recommended_docusign_products": [
    {
      "product_name": "DocuSign Navigator",
      "category": "Agreement Storage and Analysis",
      "why_recommended": "Centralized repository with AI search and renewal tracking perfectly addresses the vendor contract visibility gap",
      "key_capabilities_used": ["AI-powered contract search", "Custom data extractions", "Obligation and commitment tracking"]
    },
    {
      "product_name": "DocuSign IAM",
      "category": "Intelligent Agreement Management",
      "why_recommended": "AI-powered contract analysis accelerates extraction of renewal dates and pricing terms from legacy contracts",
      "key_capabilities_used": ["AI-powered contract analysis", "Automated metadata extraction", "Risk and obligation identification"]
    }
  ],
  "sources": "Industry benchmark: Companies typically achieve 10-15% vendor cost reduction from improved contract visibility",
  "confidence": "high"
}

---

Now, apply this same thinking to the company below. Generate EXACTLY 3 opportunities following the pattern above.
'''

        prompt = f"""{few_shot_examples}

# YOUR TASK: Analyze this company and generate 3 similar opportunities

{context}

{"PRODUCT CATALOG: When recommending DocuSign products, reference the catalog above and explain why each product fits the opportunity." if self.product_catalog else ""}

CRITICAL REQUIREMENTS:
1. Each opportunity MUST directly support one of the Strategic Priorities listed above
2. Each opportunity MUST reference specific executive quotes from the priorities (if available)
3. Map each opportunity to the executive who would champion it
4. Follow the EXACT same JSON structure as the examples above
5. Be specific to THIS company's industry, scale, and priorities - don't just copy the examples

Follow the EXACT same JSON structure as the examples above. Each opportunity must include all fields shown in the examples:
- opportunity_id, title, use_case_name, description
- business_function, agreement_types, capabilities
- systems_impacted, business_units_impacted
- strategic_alignment, executive_alignment (with priority_name, executive_champion, alignment_statement, supporting_quote)
- current_state (process_description, cycle_time, pain_points)
- future_state (process_description, target_cycle_time, key_capabilities)
- risk_reduction, compliance_benefits
- value_quantification (time_savings, agreements_affected, revenue_acceleration, cost_savings, total_annual_value, implementation_cost, roi_percentage, payback_period)
- metrics (2-4 metrics mixing financial and efficiency)
- implementation (priority, timeline, complexity, dependencies)
{f'''- recommended_docusign_products (1-3 products with product_name, category, why_recommended, key_capabilities_used)''' if self.product_catalog else ''}
- sources, confidence

KEY DIFFERENCES FROM EXAMPLES:
- Tailor opportunities to THIS company's specific industry, scale, pain points, and strategic priorities
- Use the company's actual business functions and systems from the context above
- Reference the specific executive quotes and priorities provided
- Recommend DocuSign products that logically fit this company's needs

Return as valid JSON:
{{
  "opportunities": [
    {{ /* opportunity 1 */ }},
    {{ /* opportunity 2 */ }},
    {{ /* opportunity 3 */ }}
  ]
}}
"""

        system_message = """You are a DocuSign CLM specialist and business value consultant. Your expertise includes:

1. CONTRACT LIFECYCLE MANAGEMENT: Deep knowledge of how enterprises manage agreements across sales, procurement, legal, HR, and operations
2. PROCESS OPTIMIZATION: Identifying high-ROI opportunities to automate contract workflows and reduce cycle times
3. EXECUTIVE ALIGNMENT: Connecting operational improvements to strategic business priorities and executive mandates
4. VALUE QUANTIFICATION: Using industry benchmarks to estimate realistic ROI, cost savings, and efficiency gains

METHODOLOGY:
- Start with the company's strategic priorities and executive statements
- Identify specific process bottlenecks causing measurable business pain
- Recommend DocuSign solutions that directly address those pain points
- Quantify value using conservative industry benchmarks (cite sources)
- Ensure each opportunity has a clear executive champion

QUALITY STANDARDS:
- Be specific: "15-day sales cycle" not "slow process"
- Be realistic: Use industry benchmark ranges, not aspirational best-case
- Be relevant: Tailor to company's industry, scale, and actual pain points
- Be actionable: Include implementation timeline and dependencies

Always return EXACTLY 3 opportunities in valid JSON format."""

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_message},
                {"role": "user", "content": prompt}
            ],
            temperature=0.4,
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

Identify the top 15 agreement types most relevant to {company_name} based on their industry, operations, and common practices. Include both internal (within company) and external (with customers, vendors, regulators) agreements.

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

IMPORTANT: Return EXACTLY 15 agreement types.

Return as valid JSON with structure:
{{
  "agreement_types": [...array of exactly 15 agreement type objects...],
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

        # Phase 2.5: Run deep research (needs profile and business_units)
        deep_research_findings = await self.deep_research_company(
            company_name,
            profile,
            business_units,
            callbacks.get('deep_research')
        )

        # Phase 3: Run optimization opportunities (needs priorities, landscape, and deep research)
        opportunities = await self.research_optimization_opportunities(
            company_name,
            profile,
            business_units,
            landscape,
            strategic_priorities,
            deep_research_findings,
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
            "deep_research_findings": deep_research_findings,
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

        # Phase 4: Generate sales enablement content (executive summary, discovery questions, product aggregation)
        print("Generating executive summary...")
        executive_summary = await self.generate_executive_summary(analysis)
        analysis['executive_summary'] = executive_summary

        print("Generating discovery questions...")
        discovery_questions = await self.generate_discovery_questions(analysis)
        analysis['discovery_questions'] = discovery_questions

        print("Aggregating DocuSign product recommendations...")
        docusign_product_summary = self.aggregate_product_recommendations(analysis)
        analysis['docusign_product_summary'] = docusign_product_summary

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

    async def generate_executive_summary(self, analysis_data: Dict) -> Dict:
        """
        Generate executive summary bullets from completed analysis

        Args:
            analysis_data: Complete analysis dictionary

        Returns:
            Dictionary with "bullets" list containing 3-5 summary points
        """
        profile = analysis_data.get('company_profile', {})
        scale = profile.get('scale', {})
        business_units = analysis_data.get('business_units', [])
        opportunities = analysis_data.get('optimization_opportunities', [])
        portfolio = analysis_data.get('portfolio_summary', {})
        strategic_priorities = analysis_data.get('strategic_priorities', [])
        landscape_summary = analysis_data.get('agreement_landscape_summary', {})

        # Build context for GPT
        context = f"""
Company: {analysis_data.get('_meta', {}).get('company_name', 'Unknown')}
Industry: {profile.get('industry', 'Unknown')}
Revenue: {scale.get('annual_revenue', 'N/A')}
Employees: {scale.get('employees', 'N/A')}
Countries: {scale.get('countries', 'N/A')}
Business Units: {len(business_units)}

Top Strategic Priorities:
{chr(10).join([f"- {p.get('priority_name', 'Unknown')}: {p.get('priority_description', '')}" for p in strategic_priorities[:3]])}

Optimization Opportunities: {portfolio.get('total_opportunities', 0)} opportunities totaling {portfolio.get('total_annual_value', 'N/A')} annual value
ROI: {portfolio.get('portfolio_roi', 'N/A')}
Payback: {portfolio.get('portfolio_payback', 'N/A')}

Agreement Landscape: {landscape_summary.get('total_estimated_agreements', 'Unknown')} total agreements

Key Pain Points:
{chr(10).join([f"- {opp.get('title', 'Unknown')}" for opp in opportunities[:3]])}
"""

        # Few-shot examples for better executive summaries
        examples = '''
# EXAMPLE 1: Software Company

CONTEXT: $5.2B SaaS company, 12,000 employees, 40 countries. Strategic priority: "Accelerate revenue growth to $7B". Opportunities: $15.4M value, 2,990% ROI, 2-3 month payback. Agreements: ~18,000 contracts. Pain: 15-day sales cycle, missed renewals, scattered contracts.

GOOD SUMMARY:
- "Enterprise SaaS leader with $5.2B revenue across 40 countries, targeting $7B by accelerating quote-to-cash and scaling operations efficiently"
- "Opportunity portfolio delivers $15.4M in annual value (2,990% ROI, 2-3 month payback) by addressing sales contract delays, vendor spend leakage, and legal capacity constraints"
- "Managing ~18,000 agreements across sales, procurement, and HR with limited visibility: 15-day sales cycles create revenue delays, while missed vendor renewals leak $2-3M annually"

BAD SUMMARY (too generic, checkbox-style):
- "Large software company with $5.2B in revenue and 12,000 employees operating in 40 countries"
- "Has strategic priority to accelerate revenue growth to $7B"
- "Identified 3 opportunities with $15.4M annual value and 2,990% ROI"
- "Manages approximately 18,000 agreements"

# EXAMPLE 2: Manufacturing Company

CONTEXT: $12B industrial manufacturer, 35,000 employees, 15 countries. Strategic priority: "Optimize operational efficiency". Opportunities: $8.2M value, 1,250% ROI, 3 months payback. Agreements: ~25,000 contracts. Pain: Procurement contract chaos, compliance risk, supplier cost overruns.

GOOD SUMMARY:
- "$12B global manufacturer with 35,000 employees seeking operational efficiency gains to fund growth initiatives and improve margins"
- "Contract optimization portfolio worth $8.2M annually (1,250% ROI, 3-month payback) focuses on procurement spend management, compliance risk reduction, and supplier relationship optimization"
- "Fragmented agreement landscape of ~25,000 contracts creates procurement blind spots: 40% of vendor contracts have unknown renewal dates, causing $3-5M in preventable auto-renewal cost overruns"

---
'''

        prompt = f"""{examples}

# YOUR TASK: Create an executive summary for this company

{context}

Generate 3-5 compelling bullet points following these guidelines:

**STRUCTURE (follow the examples above):**
1. **Company Context + Strategic Direction**: Scale (revenue, employees, geography) + top strategic priority
2. **Opportunity Value Proposition**: Total value, ROI, payback + what opportunities address (pain points)
3. **Agreement Landscape + Key Challenges**: Contract volume + specific pain points with business impact

**VOICE & TONE:**
- Professional but engaging (not boring checkbox bullets)
- Lead with business outcomes, not just facts
- Connect challenges to strategic priorities
- Use specific numbers and metrics (avoid vague "large" or "many")
- Show cause-and-effect: "X creates Y" not just "has X and Y"

**WHAT TO AVOID:**
- Generic descriptions ("large company", "many employees")
- Listing facts without connecting them ("has X. has Y. has Z.")
- Vague language ("significant opportunities", "various challenges")
- Checkbox-style bullets that just restate data points

Return as JSON:
{{
  "bullets": [
    "Compelling bullet 1...",
    "Compelling bullet 2...",
    "Compelling bullet 3..."
  ]
}}

Each bullet should be 1-2 sentences that tell a story, not just list facts."""

        try:
            system_message = """You are a senior business strategist who crafts compelling executive summaries for C-suite audiences.

Your summaries:
- Lead with strategic context and business outcomes, not just facts
- Connect challenges to opportunities to create a narrative arc
- Use specific metrics to build credibility (avoid vague language)
- Show cause-and-effect relationships ("X creates Y" not "has X and Y")
- Balance professional rigor with engaging storytelling

Your audience is busy executives who need to:
1. Quickly understand the company's strategic direction
2. Assess the business case for investment (ROI, payback, value)
3. See how contract management challenges impact strategic goals

Write in an active, confident voice. Avoid checkbox-style bullets that just list information. Instead, craft narrative bullets that connect the dots between scale, strategy, challenges, and opportunities."""

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.5
            )

            content = response.choices[0].message.content.strip()

            # Extract JSON from response
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            summary = json.loads(content)

            return summary

        except Exception as e:
            print(f"Error generating executive summary: {e}")
            # Return fallback summary
            return {
                "bullets": [
                    f"{scale.get('annual_revenue', 'N/A')} revenue company with {scale.get('employees', 'N/A')} employees",
                    f"{portfolio.get('total_opportunities', 0)} opportunities totaling {portfolio.get('total_annual_value', 'N/A')} annual value",
                    f"Agreement landscape spans {landscape_summary.get('total_estimated_agreements', 'Unknown')} contracts"
                ]
            }

    async def generate_discovery_questions(self, analysis_data: Dict) -> List[str]:
        """
        Generate discovery questions based on analysis findings

        Args:
            analysis_data: Complete analysis dictionary

        Returns:
            List of 5-7 discovery questions
        """
        profile = analysis_data.get('company_profile', {})
        strategic_priorities = analysis_data.get('strategic_priorities', [])
        business_units = analysis_data.get('business_units', [])
        opportunities = analysis_data.get('optimization_opportunities', [])
        landscape_summary = analysis_data.get('agreement_landscape_summary', {})

        # Build context
        context = f"""
Company: {analysis_data.get('_meta', {}).get('company_name', 'Unknown')}
Industry: {profile.get('industry', 'Unknown')}

Strategic Priorities:
{chr(10).join([f"- {p.get('priority_name', 'Unknown')}: {p.get('priority_description', '')}" for p in strategic_priorities[:3]])}

Pain Points Identified:
{chr(10).join([f"- {opp.get('title', 'Unknown')}: {opp.get('current_state', {}).get('pain_points', [])[0] if opp.get('current_state', {}).get('pain_points') else ''}" for opp in opportunities[:3]])}

Business Units:
{chr(10).join([f"- {bu.get('name', 'Unknown')}: {bu.get('description', '')}" for bu in business_units[:3]])}

Agreement Volume: {landscape_summary.get('total_estimated_agreements', 'Unknown')}
"""

        # Build MEDDPICC-aligned prompt with examples
        meddpicc_examples = '''
# MEDDPICC Discovery Framework Examples

For a $5B software company with strategic priority "accelerate revenue growth" and pain point "15-day sales cycle":

**METRICS (Quantify Business Impact)**
- "You mentioned accelerating revenue growth as a priority. What's the financial impact of reducing your sales contract cycle time from 15 days to 3-4 days? How many deals would that help close each quarter?"

**ECONOMIC BUYER (Budget Authority)**
- "Who owns the budget for contract management and legal operations initiatives? Are they involved in evaluating solutions that impact quote-to-cash speed?"

**DECISION CRITERIA (Evaluation Priorities)**
- "When you evaluate solutions to accelerate sales contracts, what matters most: cycle time reduction, integration with Salesforce, legal team capacity, or something else?"

**DECISION PROCESS (Approval Workflow)**
- "Walk me through how you typically evaluate and approve a contract management solution. Who needs to be involved, and what's the typical timeline?"

**PAPER PROCESS (Legal/Procurement)**
- "What does your internal procurement process look like for software purchases in this price range? Any compliance or security requirements we should be aware of?"

**IDENTIFY PAIN (Current Challenges)**
- "You mentioned email-based legal reviews create bottlenecks. Can you describe what happens during quarter-end? How many contracts are stuck in review right now?"

**CHAMPION (Internal Advocate)**
- "Who internally is most frustrated by the current contract process? Who would be the biggest advocate for changing how sales contracts are managed?"

**COMPETITION (Alternatives)**
- "Are you currently evaluating any other contract management solutions? What's driving you to look at options now versus six months ago?"

---
'''

        prompt = f"""{meddpicc_examples}

# YOUR TASK: Generate MEDDPICC-aligned discovery questions for this company

{context}

Generate 7-9 discovery questions following the MEDDPICC framework:

1. **METRICS**: Questions about quantifiable business impact (revenue, cost, time savings)
2. **ECONOMIC BUYER**: Questions about budget owners and financial decision-makers
3. **DECISION CRITERIA**: Questions about evaluation priorities and success criteria
4. **DECISION PROCESS**: Questions about approval workflow and timeline
5. **PAPER PROCESS**: Questions about procurement, legal, and contracting requirements
6. **IDENTIFY PAIN**: Questions that probe current challenges and pain points
7. **CHAMPION**: Questions about internal advocates and stakeholders
8. **COMPETITION**: Questions about alternatives and urgency drivers

Each question should:
- Reference specific findings from the analysis (strategic priorities, pain points, business units)
- Be open-ended to encourage detailed responses
- Be conversational and consultative in tone
- Be 1-2 sentences maximum

CRITICAL: Include at least ONE question for EACH of the 8 MEDDPICC elements. Aim for 7-9 questions total.

Return as JSON array:
[
  "Metrics question referencing specific finding...",
  "Economic Buyer question...",
  "Decision Criteria question...",
  "Decision Process question...",
  "Paper Process question...",
  "Identify Pain question...",
  "Champion question...",
  "Competition question...",
  "Optional 9th question..."
]"""

        try:
            system_message = """You are a DocuSign sales specialist trained in MEDDPICC methodology.

Your discovery questions help sales reps:
1. Qualify opportunities by uncovering key stakeholders, budget, and decision process
2. Build business cases by quantifying pain points and value
3. Navigate complex enterprise sales cycles by understanding evaluation criteria
4. Position DocuSign CLM solutions effectively

MEDDPICC Framework:
- METRICS: Quantify the cost of current problems and value of solving them
- ECONOMIC BUYER: Identify who controls the budget for this initiative
- DECISION CRITERIA: Understand what matters most in evaluation
- DECISION PROCESS: Map out the approval workflow and timeline
- PAPER PROCESS: Understand procurement, legal, security requirements
- IDENTIFY PAIN: Probe deeply into current challenges and their business impact
- CHAMPION: Find internal advocates who will sell for you
- COMPETITION: Understand alternatives, incumbents, and urgency drivers

Your questions should be consultative, not interrogative. Reference specific findings from the analysis to show you've done your homework."""

            response = await self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.6
            )

            content = response.choices[0].message.content.strip()

            # Extract JSON from response
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            questions = json.loads(content)

            return questions if isinstance(questions, list) else []

        except Exception as e:
            print(f"Error generating discovery questions: {e}")
            # Return fallback MEDDPICC questions
            return [
                f"What's the business impact of your current contract management process? For example, how much revenue is delayed by slow contract cycles, or what does manual work cost annually?",  # METRICS
                "Who owns the budget for legal operations, contract management, or sales enablement initiatives? Is there allocated budget for improvements this year?",  # ECONOMIC BUYER
                "When evaluating contract management solutions, what matters most to your team: cycle time, cost savings, risk reduction, or something else?",  # DECISION CRITERIA
                "Walk me through how your organization typically evaluates and approves enterprise software. Who needs to be involved, and what's the timeline?",  # DECISION PROCESS
                "What does your procurement process look like for software in the $100K-$500K range? Any security, compliance, or legal requirements we should know about?",  # PAPER PROCESS
                f"Can you describe your most painful contract management scenario? For example, what happens during quarter-end, or when a key contract is about to renew?",  # IDENTIFY PAIN
                "Who in your organization is most frustrated by the current contract process? Who would be the biggest advocate for improving how agreements are managed?",  # CHAMPION
                "Are you currently looking at other contract management solutions? What's driving you to explore options now?",  # COMPETITION
            ]

    def aggregate_product_recommendations(self, analysis_data: Dict) -> Dict:
        """
        Aggregate DocuSign product recommendations from all opportunities

        Args:
            analysis_data: Complete analysis dictionary

        Returns:
            Dictionary with aggregated product information
        """
        opportunities = analysis_data.get('optimization_opportunities', [])

        # Collect all recommended products
        product_map = {}

        for opp in opportunities:
            recommended_products = opp.get('recommended_docusign_products', [])
            use_case_name = opp.get('use_case_name', opp.get('title', 'Unknown'))

            for product in recommended_products:
                product_name = product.get('product_name', 'Unknown')

                if product_name not in product_map:
                    product_map[product_name] = {
                        'product_name': product_name,
                        'category': product.get('category', 'Unknown'),
                        'use_cases_enabled': [],
                        'key_capabilities_relevant': set(),
                        'estimated_value_enabled': 0,
                        'why_recommended_list': []
                    }

                # Add use case
                if use_case_name not in product_map[product_name]['use_cases_enabled']:
                    product_map[product_name]['use_cases_enabled'].append(use_case_name)

                # Add capabilities
                for cap in product.get('key_capabilities_used', []):
                    product_map[product_name]['key_capabilities_relevant'].add(cap)

                # Add value (parse from opportunity)
                value_str = opp.get('value_quantification', {}).get('total_annual_value', '0')
                value = self._parse_currency(value_str)
                product_map[product_name]['estimated_value_enabled'] += value

                # Collect reasons
                why = product.get('why_recommended', '')
                if why and why not in product_map[product_name]['why_recommended_list']:
                    product_map[product_name]['why_recommended_list'].append(why)

        # Convert to final format
        products_list = []
        for product_name, data in product_map.items():
            products_list.append({
                'product_name': product_name,
                'category': data['category'],
                'use_cases_enabled': data['use_cases_enabled'],
                'key_capabilities_relevant': list(data['key_capabilities_relevant']),
                'estimated_value_enabled': self._format_currency(data['estimated_value_enabled']),
                'why_recommended': ' '.join(data['why_recommended_list'])
            })

        # Sort by value (descending)
        products_list.sort(key=lambda p: self._parse_currency(p['estimated_value_enabled']), reverse=True)

        return {
            'products': products_list,
            'total_products_recommended': len(products_list),
            'implementation_approach': self._generate_implementation_approach(products_list, opportunities)
        }

    def _generate_implementation_approach(self, products: List[Dict], opportunities: List[Dict]) -> str:
        """Generate implementation approach recommendation"""
        if not opportunities:
            return "Contact DocuSign for implementation planning."

        # Sort opportunities by priority
        high_priority = [o for o in opportunities if o.get('implementation', {}).get('priority') == 'high']
        medium_priority = [o for o in opportunities if o.get('implementation', {}).get('priority') == 'medium']

        approach_parts = []

        if high_priority:
            use_case = high_priority[0].get('use_case_name', high_priority[0].get('title', 'Unknown'))
            timeline = high_priority[0].get('implementation', {}).get('timeline', '6-9 months')
            approach_parts.append(f"Start with {use_case} (high priority, {timeline})")

        if medium_priority:
            use_case = medium_priority[0].get('use_case_name', medium_priority[0].get('title', 'Unknown'))
            timeline = medium_priority[0].get('implementation', {}).get('timeline', '4-6 months')
            if approach_parts:
                approach_parts.append(f"then expand to {use_case} (medium priority, {timeline})")
            else:
                approach_parts.append(f"Start with {use_case} (medium priority, {timeline})")

        if len(products) > 1:
            product_names = [p['product_name'] for p in products[:2]]
            approach_parts.append(f"Integrate {' and '.join(product_names)} throughout")

        return "Phased rollout: " + ", ".join(approach_parts) + "." if approach_parts else "Contact DocuSign for implementation planning."
