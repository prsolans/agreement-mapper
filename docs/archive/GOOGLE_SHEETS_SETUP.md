# Google Sheets Storage Setup

This guide explains how to set up Google Sheets as a database for storing company analyses.

## Why Google Sheets?

- ✅ **Free** - No database hosting costs
- ✅ **Easy** - No complex database setup
- ✅ **Works Everywhere** - Streamlit Cloud, local dev, etc.
- ✅ **Shareable** - View/edit analyses in Google Sheets directly
- ✅ **5M Cell Limit** - Plenty for hundreds of analyses

## Setup Steps

### Step 1: Create a Google Sheet

1. Go to [Google Sheets](https://sheets.google.com)
2. Create a new blank spreadsheet
3. Name it "Agreement Map Analyses" (or whatever you prefer)
4. Create a worksheet named **"analyses"** (exactly this name)
5. Add column headers in row 1:
   - Column A: `company_name`
   - Column B: `timestamp`
   - Column C: `analysis_json`

Your sheet should look like this:
```
| company_name | timestamp | analysis_json |
|--------------|-----------|---------------|
|              |           |               |
```

### Step 2: Share the Sheet

1. Click "Share" button (top right)
2. Change "Restricted" to **"Anyone with the link"**
3. Set permission to **"Editor"**
4. Copy the share link (e.g., `https://docs.google.com/spreadsheets/d/1ABC...XYZ/edit`)

### Step 3: Configure Streamlit (Local Development)

If running locally, create a `.streamlit/secrets.toml` file:

```bash
mkdir -p .streamlit
cat > .streamlit/secrets.toml << 'EOF'
# Google Sheets Connection
[connections.gsheets]
spreadsheet = "YOUR_SPREADSHEET_URL_HERE"
type = "service_account"
EOF
```

Replace `YOUR_SPREADSHEET_URL_HERE` with your Google Sheets URL.

### Step 4: Configure Streamlit Cloud

1. Go to your Streamlit Cloud dashboard
2. Click on your app → **Settings** → **Secrets**
3. Add this configuration:

```toml
[connections.gsheets]
spreadsheet = "YOUR_SPREADSHEET_URL_HERE"
type = "service_account"
```

4. Click "Save"
5. Your app will automatically redeploy

### Step 5: Test It!

1. Run your Streamlit app
2. Analyze a company
3. You should see: "Analysis complete and saved to Google Sheets!"
4. Check your Google Sheet - the analysis should appear in a new row
5. The sidebar should show "Saved Analyses" with your analysis listed

## Troubleshooting

### "Google Sheets not configured" message

**Problem**: The connection isn't set up correctly

**Solutions**:
- Check that `.streamlit/secrets.toml` exists (local) or secrets are set (cloud)
- Verify the spreadsheet URL is correct
- Make sure the sheet has a worksheet named exactly "analyses"

### "Permission denied" or "403 error"

**Problem**: Streamlit can't access your Google Sheet

**Solutions**:
- Make sure the sheet is shared with "Anyone with the link"
- Verify permission is set to "Editor" (not "Viewer")
- Try regenerating the share link

### Analyses not appearing

**Problem**: Save is succeeding but you don't see them

**Solutions**:
- Refresh the Streamlit app
- Check the Google Sheet directly - is data there?
- Make sure worksheet is named "analyses" (lowercase, no extra spaces)

## Advanced: Service Account (Production)

For production deployments, you may want to use a Google Service Account instead of "Anyone with the link":

1. Create a service account in Google Cloud Console
2. Download the JSON credentials file
3. Share your Google Sheet with the service account email
4. Add the JSON credentials to Streamlit secrets:

```toml
[connections.gsheets]
spreadsheet = "YOUR_SPREADSHEET_URL"
type = "service_account"

[connections.gsheets.service_account]
type = "service_account"
project_id = "your-project"
private_key_id = "key-id"
private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
client_email = "your-service-account@project.iam.gserviceaccount.com"
client_id = "123456789"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/..."
```

## How It Works

**When you analyze a company:**
1. Research runs → generates JSON result
2. App saves JSON to Google Sheets as new row
3. Success message shows "saved to Google Sheets"

**When you load an analysis:**
1. Sidebar shows list of saved analyses
2. Click button → loads JSON from Google Sheet
3. Analysis appears in main view

**When you delete:**
1. Click delete button (🗑️)
2. Row removed from Google Sheet
3. List refreshes automatically

## Data Structure

Each row in the Google Sheet contains:

- **company_name**: "Docusign", "Stripe", etc.
- **timestamp**: ISO format (e.g., "2025-10-31T01:23:45")
- **analysis_json**: Complete analysis as JSON string

The JSON includes everything: company profile, priorities, opportunities, matrix, etc.

## Limitations

- **5M cells total** in Google Sheets (~500-1000 analyses depending on size)
- **No real-time collaboration** (one write at a time)
- **Not a real database** (no complex queries, joins, etc.)

For most use cases, these limitations don't matter!

## Need Help?

Check the Streamlit docs: https://docs.streamlit.io/develop/api-reference/connections/st.connection
