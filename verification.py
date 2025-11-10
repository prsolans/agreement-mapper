"""
Quote Verification & Confidence Scoring Module

This module provides functions to verify executive quotes and calculate confidence scores
based on source credibility and URL verification.
"""

from typing import Dict, List, Optional
from urllib.parse import urlparse
import re


def score_source_credibility(source: str, url: str = "") -> float:
    """
    Score source credibility based on source type and URL domain.

    Args:
        source: Source description (e.g., "Q4 2024 earnings call")
        url: Source URL

    Returns:
        Credibility score from 0.0 to 1.0
    """
    source_lower = source.lower()

    # Extract domain from URL if provided
    domain = ""
    if url:
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
        except:
            pass

    # Tier 1: Highest credibility (1.0)
    # Investor relations, SEC filings, official company sources
    tier1_keywords = ['investor relations', 'ir.', 'investors.', 'sec filing', '10-k', '10-q', '8-k', 'proxy statement']
    tier1_domains = ['sec.gov', 'ir.', 'investors.']

    if any(keyword in source_lower for keyword in tier1_keywords):
        return 1.0
    if any(domain.startswith(d) or d in domain for d in tier1_domains):
        return 1.0

    # Tier 2: Very high credibility (0.9)
    # Earnings calls, annual reports, official press releases
    tier2_keywords = ['earnings call', 'earnings transcript', 'annual report', 'quarterly report', 'press release']
    tier2_domains = ['seekingalpha.com/article', 'fool.com/earnings']

    if any(keyword in source_lower for keyword in tier2_keywords):
        return 0.9
    if any(d in domain for d in tier2_domains):
        return 0.9

    # Tier 3: High credibility (0.8)
    # Major business news outlets, verified interviews
    tier3_keywords = ['interview', 'conference', 'keynote', 'summit']
    tier3_domains = ['wsj.com', 'ft.com', 'bloomberg.com', 'reuters.com', 'cnbc.com']

    if any(keyword in source_lower for keyword in tier3_keywords):
        return 0.8
    if any(d in domain for d in tier3_domains):
        return 0.8

    # Tier 4: Medium credibility (0.6)
    # Tech news outlets, industry publications
    tier4_domains = ['techcrunch.com', 'theverge.com', 'wired.com', 'forbes.com', 'businessinsider.com']

    if any(d in domain for d in tier4_domains):
        return 0.6

    # Tier 5: Lower credibility (0.4)
    # Blogs, general news, social media
    tier5_keywords = ['blog', 'twitter', 'linkedin post', 'facebook']
    tier5_domains = ['medium.com', 'blog.', 'twitter.com', 'linkedin.com', 'facebook.com']

    if any(keyword in source_lower for keyword in tier5_keywords):
        return 0.4
    if any(d in domain for d in tier5_domains):
        return 0.4

    # Default: Unknown source (0.5)
    return 0.5


def verify_quote_url(quote_url: str, search_results: List[Dict]) -> Dict:
    """
    Verify if a quote URL appears in the search results.

    Args:
        quote_url: URL claimed as source for the quote
        search_results: List of search result dictionaries with 'url' keys

    Returns:
        Dictionary with verification details:
        {
            'verified': bool,
            'verification_status': str,
            'matched_result': dict or None
        }
    """
    if not quote_url:
        return {
            'verified': False,
            'verification_status': 'no_url_provided',
            'matched_result': None
        }

    if not search_results:
        return {
            'verified': False,
            'verification_status': 'no_search_results',
            'matched_result': None
        }

    # Normalize quote URL for comparison
    quote_url_normalized = quote_url.lower().strip()

    # Try exact match first
    for result in search_results:
        result_url = result.get('url', '').lower().strip()
        if result_url and result_url == quote_url_normalized:
            return {
                'verified': True,
                'verification_status': 'exact_match',
                'matched_result': result
            }

    # Try domain + path match (ignore query params)
    try:
        quote_parsed = urlparse(quote_url_normalized)
        quote_domain = quote_parsed.netloc
        quote_path = quote_parsed.path.rstrip('/')

        for result in search_results:
            result_url = result.get('url', '').lower().strip()
            if result_url:
                result_parsed = urlparse(result_url)
                result_domain = result_parsed.netloc
                result_path = result_parsed.path.rstrip('/')

                if quote_domain == result_domain and quote_path == result_path:
                    return {
                        'verified': True,
                        'verification_status': 'path_match',
                        'matched_result': result
                    }
    except:
        pass

    # Try domain-only match
    try:
        quote_domain = urlparse(quote_url_normalized).netloc
        for result in search_results:
            result_url = result.get('url', '').lower().strip()
            if result_url:
                result_domain = urlparse(result_url).netloc
                if quote_domain == result_domain:
                    return {
                        'verified': True,
                        'verification_status': 'domain_match',
                        'matched_result': result
                    }
    except:
        pass

    # No match found
    return {
        'verified': False,
        'verification_status': 'not_found',
        'matched_result': None
    }


def calculate_quote_confidence(
    quote: Dict,
    search_results: List[Dict] = None
) -> float:
    """
    Calculate overall confidence score for an executive quote.

    Args:
        quote: Quote dictionary with keys: quote, executive, source, url, date
        search_results: Optional list of search results for URL verification

    Returns:
        Confidence score from 0.0 to 1.0
    """
    confidence_factors = []

    # Factor 1: Source credibility (weight: 40%)
    source = quote.get('source', '')
    url = quote.get('url', '')
    credibility_score = score_source_credibility(source, url)
    confidence_factors.append(('credibility', credibility_score, 0.4))

    # Factor 2: URL verification (weight: 30%)
    if search_results:
        verification = verify_quote_url(url, search_results)
        if verification['verified']:
            if verification['verification_status'] == 'exact_match':
                verification_score = 1.0
            elif verification['verification_status'] == 'path_match':
                verification_score = 0.9
            elif verification['verification_status'] == 'domain_match':
                verification_score = 0.7
            else:
                verification_score = 0.5
        else:
            verification_score = 0.3  # Penalty for unverified URL
    else:
        # No search results provided, neutral score
        verification_score = 0.6

    confidence_factors.append(('url_verification', verification_score, 0.3))

    # Factor 3: Quote completeness (weight: 20%)
    completeness_score = 0.0
    if quote.get('quote'):
        completeness_score += 0.3
    if quote.get('executive'):
        completeness_score += 0.2
    if quote.get('source'):
        completeness_score += 0.2
    if quote.get('url'):
        completeness_score += 0.2
    if quote.get('date'):
        completeness_score += 0.1

    confidence_factors.append(('completeness', completeness_score, 0.2))

    # Factor 4: Date recency (weight: 10%)
    date_str = quote.get('date', '')
    date_score = 0.5  # Default neutral

    if date_str:
        # Extract year from date string
        year_match = re.search(r'20\d{2}', date_str)
        if year_match:
            year = int(year_match.group())
            current_year = 2025  # Can be updated or made dynamic
            years_ago = current_year - year

            if years_ago <= 1:
                date_score = 1.0  # Very recent
            elif years_ago == 2:
                date_score = 0.8  # Recent
            elif years_ago <= 5:
                date_score = 0.6  # Somewhat recent
            else:
                date_score = 0.3  # Old

    confidence_factors.append(('recency', date_score, 0.1))

    # Calculate weighted average
    total_confidence = sum(score * weight for _, score, weight in confidence_factors)

    return round(total_confidence, 2)


def get_verification_status_display(verification_status: str) -> Dict:
    """
    Get display information for verification status.

    Args:
        verification_status: Status string from verify_quote_url

    Returns:
        Dictionary with icon, color, and label for display
    """
    status_map = {
        'exact_match': {
            'icon': '✓',
            'color': 'green',
            'label': 'Verified',
            'description': 'URL found in search results (exact match)'
        },
        'path_match': {
            'icon': '✓',
            'color': 'green',
            'label': 'Verified',
            'description': 'URL found in search results (path match)'
        },
        'domain_match': {
            'icon': '~',
            'color': 'yellow',
            'label': 'Partially Verified',
            'description': 'Domain found in search results'
        },
        'not_found': {
            'icon': '⚠',
            'color': 'orange',
            'label': 'Unverified',
            'description': 'URL not found in search results'
        },
        'no_url_provided': {
            'icon': '?',
            'color': 'gray',
            'label': 'No URL',
            'description': 'No source URL provided'
        },
        'no_search_results': {
            'icon': '?',
            'color': 'gray',
            'label': 'Cannot Verify',
            'description': 'No search results available for verification'
        }
    }

    return status_map.get(verification_status, {
        'icon': '?',
        'color': 'gray',
        'label': 'Unknown',
        'description': 'Unknown verification status'
    })


def get_confidence_level(confidence_score: float) -> Dict:
    """
    Convert confidence score to human-readable level.

    Args:
        confidence_score: Score from 0.0 to 1.0

    Returns:
        Dictionary with level, color, and icon
    """
    if confidence_score >= 0.8:
        return {
            'level': 'High',
            'color': 'green',
            'icon': '●',
            'description': 'High confidence in quote authenticity'
        }
    elif confidence_score >= 0.6:
        return {
            'level': 'Medium',
            'color': 'yellow',
            'icon': '●',
            'description': 'Medium confidence in quote authenticity'
        }
    else:
        return {
            'level': 'Low',
            'color': 'red',
            'icon': '●',
            'description': 'Low confidence - verify independently'
        }
