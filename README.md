# Agreement Map

AI-powered company analysis tool for mapping agreement landscapes and identifying optimization opportunities.
 
## Overview

Agreement Map uses parallel AI research agents to automatically analyze companies and generate comprehensive reports on their agreement/contract landscape, business structure, and optimization opportunities.

### Key Features

- **Parallel Research**: 4 concurrent AI agents research different aspects simultaneously (3x faster)
- **Persistent Storage**: All analyses automatically saved to local files
- **CRUD Operations**: Create, Read, Update, and Delete company analyses
- **Company Profile Analysis**: Legal structure, financials, business model, strategic initiatives
- **Business Units Mapping**: Revenue breakdown, agreement types, complexity analysis
- **Agreement Landscape**: Volume estimates, categories, renewal patterns
- **Optimization Opportunities**: ROI-quantified improvement initiatives
- **Edit Mode**: Full JSON editing capability for manual adjustments
- **Interactive Visualization**: Dynamic HTML visualization of results
- **JSON Export**: Download structured analysis data

## Quick Start

### Prerequisites

- Python 3.8 or higher
- OpenAI API key ([Get one here](https://platform.openai.com/api-keys))

### Installation

1. **Clone the repository** (or download the files)
   ```bash
   cd agreement-map
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure API key** (optional for local development)
   ```bash
   cp .env.example .env
   # Edit .env and add your OpenAI API key
   ```

4. **Run the application**
   ```bash
   streamlit run app.py
   ```

5. **Open your browser**
   - Streamlit will automatically open `http://localhost:8501`
   - If not, navigate to the URL shown in your terminal

### Usage

**Creating New Analyses:**
1. Enter your OpenAI API key in the sidebar (if not using .env)
2. Enter a company name (e.g., "Salesforce", "Microsoft")
3. Click "Analyze Company"
4. Watch the parallel research agents work in real-time
5. Analysis is automatically saved to `analyses/` folder

**Managing Saved Analyses:**
- **View All**: Check the "Saved Analyses" section in the sidebar
- **Search**: Use the search box to filter by company name
- **Load**: Click the 📂 button to open a saved analysis
- **Delete**: Click the 🗑️ button to remove an analysis
- **Edit**: Toggle "Edit Mode" when viewing a saved analysis
- **Save Edits**: Click "Save Changes" after editing

**Editing Analyses:**
1. Load a saved analysis from the sidebar
2. Toggle "Edit Mode" (top right)
3. Edit the JSON in the text area
4. Click "Save Changes" when done
5. Changes are persisted to the file immediately

## Deployment

### Deploy to Streamlit Cloud (Free)

1. **Push to GitHub**
   ```bash
   git init
   git add .
   git commit -m "Initial commit"
   git remote add origin https://github.com/yourusername/agreement-map.git
   git push -u origin main
   ```

2. **Deploy on Streamlit Cloud**
   - Go to [share.streamlit.io](https://share.streamlit.io)
   - Click "New app"
   - Select your repository
   - Set main file path: `app.py`
   - Click "Deploy"

3. **Configure Secrets**
   - In Streamlit Cloud dashboard, go to "Settings" > "Secrets"
   - Add your OpenAI API key:
     ```toml
     OPENAI_API_KEY = "sk-your-key-here"
     ```

### Deploy to Other Platforms

**Heroku:**
```bash
# Create Procfile
echo "web: streamlit run app.py --server.port=$PORT" > Procfile

# Deploy
heroku create your-app-name
git push heroku main
```

**Google Cloud Run:**
```bash
# Create Dockerfile
gcloud run deploy --source .
```

**AWS / Azure:**
- Use standard Python web app deployment
- Set environment variable: `OPENAI_API_KEY`
- Run command: `streamlit run app.py --server.port=8080`

## Project Structure

```
agreement-map/
├── app.py                          # Main Streamlit application
├── research_agent.py               # Parallel OpenAI research engine
├── storage_manager.py              # Local file storage manager (CRUD operations)
├── company-analysis-template.json  # Analysis template structure
├── visualization.html              # Interactive visualization
├── analyses/                       # Saved company analyses (auto-created)
│   ├── salesforce_20251031_120000.json
│   └── microsoft_20251031_130000.json
├── requirements.txt                # Python dependencies
├── .env.example                    # Environment variable template
├── .gitignore                      # Git ignore rules
└── README.md                       # This file
```

## How It Works

### Parallel Research Architecture

The tool uses **asyncio** to run 4 research agents in parallel:

```
Sequential (Old):        Parallel (New):
Profile      [===]       Profile      [===]
Units          [====]    Units        [====]
Landscape       [==]     Landscape    [==]
Opportunities    [===]   Opportunities [===]
────────────────────     ───────────────
Total: ~4 minutes        Total: ~90 seconds
```

### Research Pipeline

1. **Company Profile Agent**
   - Legal name, industry, ownership
   - Revenue, employees, locations
   - Business model analysis
   - Strategic initiatives

2. **Business Units Agent**
   - Identify major divisions
   - Revenue contribution analysis
   - Agreement types and volumes
   - Complexity assessment

3. **Agreement Landscape Agent**
   - Total agreement estimates
   - Category breakdowns
   - Renewal pattern analysis

4. **Optimization Opportunities Agent**
   - Process improvement identification
   - ROI quantification
   - Implementation planning
   - Value prioritization

### Data Sources

The AI agents use publicly available information:
- Company websites
- Investor relations materials
- Public filings (if available)
- Industry benchmarks
- News articles and press releases

**Note:** For private companies, estimates are based on industry standards and company size.

## Configuration

### API Keys

**Option 1: Environment Variable (Local)**
```bash
export OPENAI_API_KEY="sk-your-key-here"
streamlit run app.py
```

**Option 2: .env File (Local)**
```bash
cp .env.example .env
# Edit .env and add your key
```

**Option 3: Streamlit Sidebar (Any)**
- Enter API key directly in the app sidebar

**Option 4: Streamlit Secrets (Cloud)**
```toml
# .streamlit/secrets.toml
OPENAI_API_KEY = "sk-your-key-here"
```

### Customization

**Modify Research Prompts:**
Edit `research_agent.py` to customize:
- Research questions
- Data fields
- Analysis depth
- Industry-specific focus

**Adjust AI Model:**
Change in `research_agent.py`:
```python
self.model = "gpt-4-turbo-preview"  # or "gpt-3.5-turbo" for cost savings
```

**Customize Template:**
Edit `company-analysis-template.json` to modify output structure.

## Cost Estimates

OpenAI API costs (approximate):

| Model | Cost per Analysis | Speed |
|-------|------------------|-------|
| GPT-4 Turbo | $0.50 - $1.50 | Fast |
| GPT-3.5 Turbo | $0.10 - $0.30 | Very Fast |

*Costs vary based on company complexity and data availability*

**Cost Optimization Tips:**
- Use GPT-3.5 Turbo for demos/testing
- Switch to GPT-4 for production analyses
- Implement caching for repeat analyses
- Add rate limiting for public deployments

## Roadmap

### Phase 1 - Current Release ✅
- [x] Parallel research agents
- [x] Company profile analysis
- [x] Business units mapping
- [x] Agreement landscape
- [x] Optimization opportunities
- [x] Interactive visualization
- [x] JSON export

### Phase 2 - Fast Follow 🚀
- [ ] Google Slides export
- [ ] PowerPoint (PPTX) generation
- [ ] Custom branding templates
- [ ] Slide deck customization

### Phase 3 - Future Enhancements 💡
- [ ] Multi-company comparison
- [ ] Industry benchmarking
- [ ] Historical tracking
- [ ] PDF report generation
- [ ] Email delivery
- [ ] API endpoints
- [ ] User authentication
- [ ] Analysis caching

## Troubleshooting

**"No module named 'streamlit'"**
```bash
pip install -r requirements.txt
```

**"OpenAI API error: Invalid API key"**
- Verify your API key is correct
- Check it starts with `sk-`
- Ensure billing is enabled on your OpenAI account

**"Research taking too long"**
- Normal time: 60-90 seconds
- Check your internet connection
- Try with GPT-3.5 Turbo for faster results

**"Rate limit exceeded"**
- OpenAI has rate limits by tier
- Wait a few minutes and try again
- Upgrade your OpenAI account tier

**Visualization not loading**
- Ensure `visualization.html` is in the project directory
- Check browser console for JavaScript errors
- Try refreshing the page

## Support

For issues, questions, or feature requests:
- Create an issue on GitHub
- Contact: [your-email@example.com]

## License

MIT License - feel free to use and modify for your needs.

## Acknowledgments

- Built with [Streamlit](https://streamlit.io)
- Powered by [OpenAI](https://openai.com)
- Async research using Python asyncio

---

Made with ❤️ for better contract intelligence
