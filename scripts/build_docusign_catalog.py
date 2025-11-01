"""
DocuSign Product Catalog Builder
One-time script to research DocuSign products via Tavily and create structured JSON catalog
"""
import os
import json
from datetime import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import after dotenv to ensure environment is loaded
from tavily import TavilyClient
from openai import OpenAI


def search_docusign_products(tavily_client: TavilyClient) -> str:
    """
    Search for comprehensive DocuSign product information

    Returns:
        Combined search results from multiple queries
    """
    print("🔍 Searching for DocuSign product information...")

    # Multi-stage search strategy
    search_queries = [
        "DocuSign CLM contract lifecycle management products features 2024 2025",
        "DocuSign eSignature products offerings pricing tiers 2024",
        "DocuSign IAM Intelligent Agreement Management products 2024",
        "DocuSign Gen Navigator Analyzer analytics products features",
        "DocuSign API Connect integrations products catalog"
    ]

    all_results = []

    for i, query in enumerate(search_queries, 1):
        print(f"  [{i}/{len(search_queries)}] Searching: {query[:60]}...")

        try:
            response = tavily_client.search(
                query=query,
                search_depth="advanced",
                max_results=5
            )

            for result in response.get('results', []):
                all_results.append({
                    'query': query,
                    'url': result.get('url', 'N/A'),
                    'title': result.get('title', 'N/A'),
                    'content': result.get('content', 'N/A')
                })

        except Exception as e:
            print(f"    ⚠️ Error searching: {e}")
            continue

    print(f"✅ Found {len(all_results)} search results\n")

    # Format results for GPT
    formatted_results = "\n\n---\n\n".join([
        f"Source: {r['url']}\nTitle: {r['title']}\nContent: {r['content']}"
        for r in all_results
    ])

    return formatted_results


def extract_product_catalog(openai_client: OpenAI, search_results: str) -> dict:
    """
    Use GPT-4 to extract structured product catalog from search results

    Returns:
        Structured product catalog dictionary
    """
    print("🤖 Extracting structured product data with GPT-4...")

    extraction_prompt = f"""You are a DocuSign product expert. Based on the web search results below, create a comprehensive product catalog.

Extract 15-25 DocuSign products/modules with the following structure:

{{
  "catalog_metadata": {{
    "generated_at": "{datetime.now().isoformat()}",
    "source": "Tavily Web Search + GPT-4 Extraction",
    "version": "1.0",
    "product_count": <number>
  }},
  "products": [
    {{
      "name": "Product name",
      "category": "Category (CLM, eSignature, IAM, Analytics, Integration, etc.)",
      "description": "2-3 sentence description of what it does",
      "value_statement": "1-2 sentence value proposition for buyers",
      "key_capabilities": ["capability 1", "capability 2", "capability 3"],
      "typical_buyers": ["buyer persona 1", "buyer persona 2"],
      "use_cases": ["use case 1", "use case 2"],
      "source_url": "URL from search results where this product was found"
    }}
  ]
}}

IMPORTANT:
- Include core products like CLM, eSignature, and major modules/add-ons
- Focus on products mentioned in the search results with verified URLs
- Group related features into logical product entries
- Provide clear, concise descriptions
- Only include products you can verify from the search results

WEB SEARCH RESULTS:
{search_results}

Return ONLY the JSON structure, no other text."""

    try:
        response = openai_client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=[
                {"role": "system", "content": "You are a precise product data extraction assistant. Return only valid JSON."},
                {"role": "user", "content": extraction_prompt}
            ],
            temperature=0.3,
            response_format={"type": "json_object"}
        )

        catalog_json = response.choices[0].message.content
        catalog = json.loads(catalog_json)

        product_count = len(catalog.get('products', []))
        print(f"✅ Extracted {product_count} products\n")

        return catalog

    except Exception as e:
        print(f"❌ Error extracting products: {e}")
        raise


def save_catalog(catalog: dict, output_path: Path):
    """Save catalog to JSON file"""
    print(f"💾 Saving catalog to {output_path}...")

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w') as f:
        json.dump(catalog, f, indent=2)

    file_size = output_path.stat().st_size / 1024  # KB
    print(f"✅ Catalog saved ({file_size:.1f} KB)\n")


def print_summary(catalog: dict):
    """Print summary of generated catalog"""
    products = catalog.get('products', [])

    print("=" * 60)
    print("📊 DOCUSIGN PRODUCT CATALOG SUMMARY")
    print("=" * 60)
    print(f"Total Products: {len(products)}")
    print(f"Generated: {catalog.get('catalog_metadata', {}).get('generated_at', 'N/A')}")
    print("\nProducts by Category:")

    # Group by category
    categories = {}
    for product in products:
        cat = product.get('category', 'Unknown')
        categories[cat] = categories.get(cat, 0) + 1

    for cat, count in sorted(categories.items()):
        print(f"  - {cat}: {count}")

    print("\nProduct List:")
    for i, product in enumerate(products, 1):
        print(f"  {i:2d}. {product.get('name', 'Unknown')} ({product.get('category', 'Unknown')})")

    print("=" * 60)


def main():
    """Main execution"""
    print("\n" + "=" * 60)
    print("🚀 DOCUSIGN PRODUCT CATALOG BUILDER")
    print("=" * 60 + "\n")

    # Check API keys
    openai_key = os.environ.get('OPENAI_API_KEY')
    tavily_key = os.environ.get('TAVILY_API_KEY')

    if not openai_key:
        print("❌ Error: OPENAI_API_KEY not found in environment")
        print("   Set it in .env file or environment variables")
        return

    if not tavily_key:
        print("❌ Error: TAVILY_API_KEY not found in environment")
        print("   Set it in .env file or environment variables")
        return

    # Initialize clients
    tavily_client = TavilyClient(api_key=tavily_key)
    openai_client = OpenAI(api_key=openai_key)

    # Execute pipeline
    try:
        # Step 1: Search
        search_results = search_docusign_products(tavily_client)

        # Step 2: Extract
        catalog = extract_product_catalog(openai_client, search_results)

        # Step 3: Save
        output_path = Path(__file__).parent.parent / "data" / "docusign_products.json"
        save_catalog(catalog, output_path)

        # Step 4: Summary
        print_summary(catalog)

        print("\n✅ SUCCESS! Product catalog generated successfully.")
        print(f"   Location: {output_path}")
        print("\n💡 You can now use this catalog as context in your research agent.\n")

    except Exception as e:
        print(f"\n❌ FAILED: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
