# Tavily Web Search Integration

This branch integrates Tavily API for real-time web search to enhance research quality.

## What Changed

### Dependencies
- Added `tavily-python==0.3.9` to requirements.txt

### Research Agent (`research_agent.py`)
- Updated to use Tavily API for web search
- Added `_search_web()` method for fetching real-time web data
- Updated research methods to use web search results:
  - `research_company_profile()` - searches for company info, revenue, structure
  - `research_strategic_priorities()` - searches for earnings calls, investor presentations
  - `research_business_units()` - searches for organizational structure

### App Configuration (`app.py`)
- Added Tavily API key input in sidebar
- Supports both .env file and manual entry
- Shows status indicator for web search availability
- Works gracefully without Tavily key (falls back to GPT knowledge only)

## How It Works

1. **Web Search First**: When Tavily key is provided, the agent searches the web for relevant company information
2. **Structured Analysis**: GPT-4 analyzes the search results and structures them into JSON format
3. **Real-time Data**: Gets current information from the web rather than relying solely on GPT's training data

## Setup

### Get a Tavily API Key
1. Visit https://tavily.com
2. Sign up for an account
3. Get your API key from the dashboard

### Configure the App

**Option 1: .env file (recommended)**
```bash
OPENAI_API_KEY=sk-...
TAVILY_API_KEY=tvly-...
```

**Option 2: UI Input**
- Enter your Tavily API key in the sidebar when running the app
- Optional - app will work without it using GPT knowledge only

## Benefits

- **Current Information**: Access to latest company news, earnings reports, announcements
- **Better Accuracy**: Real web sources instead of GPT's training data cutoff
- **Source Attribution**: Search results include URLs and sources
- **Fallback Support**: Works without Tavily, just with reduced data freshness

## Testing

To test the integration:
1. Add your Tavily API key to `.env` or enter it in the UI
2. Run the app: `streamlit run app.py`
3. Analyze a company and watch for "Searching web..." progress messages
4. Compare results with/without Tavily key to see the difference
