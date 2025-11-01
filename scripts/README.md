# Scripts Directory

Utility scripts for building and maintaining data resources.

## Build DocuSign Product Catalog

**Script:** `build_docusign_catalog.py`

### Purpose
One-time script to research DocuSign's current product offerings using Tavily web search and GPT-4 extraction. Creates a structured JSON catalog that can be used as context in company analysis.

### Usage

```bash
# Make sure you're in the project root directory
cd /path/to/agreement-map

# Run the script
python scripts/build_docusign_catalog.py
```

### Requirements

- **OpenAI API Key**: Set in `.env` file as `OPENAI_API_KEY`
- **Tavily API Key**: Set in `.env` file as `TAVILY_API_KEY`

### Output

The script generates `data/docusign_products.json` with this structure:

```json
{
  "catalog_metadata": {
    "generated_at": "2025-10-31T...",
    "source": "Tavily Web Search + GPT-4 Extraction",
    "version": "1.0",
    "product_count": 20
  },
  "products": [
    {
      "name": "DocuSign CLM",
      "category": "Contract Lifecycle Management",
      "description": "End-to-end contract management platform...",
      "value_statement": "Automate contract workflows and reduce risk...",
      "key_capabilities": ["Contract authoring", "Workflow automation", ...],
      "typical_buyers": ["Legal teams", "Procurement", ...],
      "use_cases": ["Enterprise contracts", "Vendor agreements", ...],
      "source_url": "https://..."
    }
  ]
}
```

### How It Works

1. **Multi-Stage Search**: Runs 5 targeted Tavily searches for different DocuSign product areas:
   - CLM (Contract Lifecycle Management)
   - eSignature products
   - IAM (Intelligent Agreement Management)
   - Gen, Navigator, Analyzer products
   - API and integrations

2. **GPT-4 Extraction**: Sends all search results to GPT-4 with a structured prompt to extract:
   - Product names and categories
   - Descriptions and value statements
   - Key capabilities and use cases
   - Buyer personas
   - Source URLs for verification

3. **JSON Output**: Saves to `data/docusign_products.json` for use as context

### Cost Estimate

- **Tavily**: ~25 searches × $0.002 = $0.05
- **GPT-4**: ~10K tokens input + 3K tokens output ≈ $0.15
- **Total**: ~$0.20 per run

### When to Re-run

- **Quarterly**: DocuSign releases major updates every quarter
- **After announcements**: New product launches or major feature releases
- **Before campaigns**: When you need the latest product info

### Integration

The generated catalog is automatically loaded by `research_agent.py` when:
- Analyzing company strategic priorities
- Identifying optimization opportunities
- Generating product recommendations

See `research_agent.py` for implementation details.
