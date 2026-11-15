.PHONY: run publish dashboard scrape test clean

# Run full discovery pipeline and automatically publish to GitHub Pages
run:
	.venv/bin/python zurich_finance_radar.py --publish

# Fast run without slow aggregators
fast:
	.venv/bin/python zurich_finance_radar.py --skip-jobspy --publish

# Regenerate dashboard/index from SQLite database and publish to GitHub Pages (no scraping)
publish:
	.venv/bin/python zurich_finance_radar.py --dashboard-only --publish --no-browser

# Regenerate dashboard locally without publishing
dashboard:
	.venv/bin/python zurich_finance_radar.py --dashboard-only

# Rescore all database jobs with Gemini and publish
rescore:
	.venv/bin/python zurich_finance_radar.py --rescore --publish

# Rescore only heuristic fallback jobs with Gemini Flash
rescore-heuristic:
	.venv/bin/python zurich_finance_radar.py --rescore-heuristic --publish --no-browser

# List available Gemini models for your API key
check-models:
	.venv/bin/python -c "from src.config import cfg; from google import genai; c = genai.Client(api_key=cfg.GEMINI_API_KEY); print('Available Flash models:'); [print(f'  • {m.name:<30} ({m.display_name})') for m in sorted(c.models.list(), key=lambda x: x.name) if 'generateContent' in m.supported_actions and 'flash' in m.name and 'image' not in m.name]"

# Test sending email digest with top recent jobs
test-email:
	.venv/bin/python zurich_finance_radar.py --test-email

# Load and activate 8:00 AM daily job in macOS launchd
schedule:
	cp config/com.vnahodil.financeradar.plist ~/Library/LaunchAgents/com.vnahodil.financeradar.plist
	launchctl load ~/Library/LaunchAgents/com.vnahodil.financeradar.plist
	launchctl list | grep -i financeradar

# Check status of daily schedule
status-schedule:
	launchctl list | grep -i financeradar

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
