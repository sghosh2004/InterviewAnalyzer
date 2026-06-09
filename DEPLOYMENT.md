# Resume Analyzer - Streamlit Deployment Guide

## Prerequisites
1. **GitHub Account** - https://github.com
2. **Streamlit Account** - https://streamlit.io (free tier)
3. **Your Repository** - Already have one or create new

## Step-by-Step Deployment

### 1. Push Code to GitHub
```bash
# Initialize git (if not already done)
git init
git add .
git commit -m "Initial commit: Resume Analyzer with optimized Gemini API"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/InterviewAnalyzer.git
git push -u origin main
```

### 2. Create `.env` secrets file for Streamlit Cloud
The `.env` file should NOT be committed to GitHub (it's in .gitignore).

Instead, add secrets to Streamlit Cloud dashboard:
- Go to https://share.streamlit.io
- Click "Advanced settings" → "Secrets"
- Copy your local `.env` contents:
```
GEMINI_API_KEY=AQ.Ab8RN6ItFe5f7TYJxzYaSS4M0ZwgsZtlKQ8OryDo7jc
GEMINI_MODEL=gemini-2.5-flash
GEMINI_MAX_OUTPUT_TOKENS=1200
GEMINI_MAX_ATTEMPTS=3
GEMINI_API_TIMEOUT=60
```

### 3. Deploy on Streamlit Community Cloud
1. Go to https://share.streamlit.io
2. Click **"New app"**
3. Select:
   - **Repository**: YOUR_USERNAME/InterviewAnalyzer
   - **Branch**: main
   - **Main file path**: app.py
4. Click **Deploy**

### 4. Access Your App
- Your app will be live at: `https://share.streamlit.io/YOUR_USERNAME/InterviewAnalyzer`
- Copy and share the link!

## Important Notes
✅ **Secrets are safe** - Streamlit Cloud encrypts them  
✅ **Free tier includes** - 3 concurrent apps, 1GB disk space  
✅ **Auto-redeploy** - When you push to GitHub, it auto-redeploys  
✅ **Logs** - View logs in Streamlit Cloud dashboard  

## Troubleshooting

### App won't start
- Check Streamlit Cloud logs
- Verify `app.py` exists and is correct
- Check `requirements.txt` for all dependencies

### Gemini API errors
- Verify `GEMINI_API_KEY` is in Secrets
- Check API key is valid at https://aistudio.google.com/app/apikeys
- Look at console logs in Streamlit dashboard

### File upload not working
- Ensure PyPDF is installed (in requirements.txt ✓)
- Check file size < 10MB

## Monitoring Usage
- Check Gemini API usage: https://aistudio.google.com/app/apikeys
- Click your key → "Quotas & Limits"
- Monitor cost (~$0.08-0.32/month for 5-20 uploads/day)

## Additional Resources
- Streamlit Docs: https://docs.streamlit.io
- Deployment Guide: https://docs.streamlit.io/deploy/streamlit-community-cloud
- Secrets Management: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management
