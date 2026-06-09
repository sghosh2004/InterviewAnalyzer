# 📄 Resume Analyzer

AI-powered resume analysis tool using Google's Gemini API with Streamlit.

## Features
- 📤 **PDF Resume Upload** - Extract text from resumes
- 🤖 **AI Analysis** - Powered by Gemini 2.5 Flash
- 📊 **Detailed Metrics**:
  - ATS Score (0-100)
  - Skills extraction
  - Experience summary
  - Education details
  - Personalized recommendations
- 📥 **Export Reports** - Download as PDF or text
- 🔗 **Easy Sharing** - Email, WhatsApp links

## Tech Stack
- **Frontend**: Streamlit
- **AI Model**: Google Gemini 2.5 Flash
- **PDF Processing**: PyPDF
- **Report Generation**: ReportLab

## Quick Start

### Local Development
```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your GEMINI_API_KEY

# Run app
streamlit run app.py
```

### Cloud Deployment
See [DEPLOYMENT.md](DEPLOYMENT.md) for step-by-step Streamlit Cloud setup.

## Environment Variables
```
GEMINI_API_KEY=<your-api-key>
GEMINI_MODEL=gemini-2.5-flash
GEMINI_MAX_OUTPUT_TOKENS=1200
GEMINI_MAX_ATTEMPTS=3
GEMINI_API_TIMEOUT=60
```

## Cost
- **~$0.0005 per resume** analyzed
- **Free tier covers thousands** of requests
- Monitor usage: https://aistudio.google.com/app/apikeys

## Live Demo
🚀 Deploy on Streamlit Cloud: https://share.streamlit.io

## API Costs Estimate
- 5-20 resumes/day: ~$0.08-0.32/month
- Free tier: Usually $300 credit (90 days)

## Support
- Documentation: See [DEPLOYMENT.md](DEPLOYMENT.md)
- Issues: Check Streamlit Cloud logs

## License
MIT
