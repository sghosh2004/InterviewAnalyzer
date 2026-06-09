# Streamlit Cloud Deployment - Quick Steps

## ⚡ 3-Step Deployment

### Step 1: Create GitHub Repository
```bash
# You're in: c:\AI Projects 2026\InterviewAnalyzer
# Git is already initialized

# Stage all files
git add .

# Commit
git commit -m "Resume Analyzer: AI-powered resume analysis with Gemini API"

# Create repository on GitHub: https://github.com/new
# Then run:
git remote add origin https://github.com/YOUR_USERNAME/InterviewAnalyzer.git
git branch -M main
git push -u origin main
```

### Step 2: Add Secrets to Streamlit Cloud
1. Go to: https://share.streamlit.io
2. Sign in with GitHub
3. Click **"New app"**
4. Select your repo
5. **BEFORE deploying**, click **"Advanced settings"**
6. Go to **"Secrets"** tab
7. Paste your `.env` contents:
```
GEMINI_API_KEY=AQ.Ab8RN6ItFe5f7TYJxzYaSS4M0ZwgsZtlKQ8OryDo7jcC_L
GEMINI_MODEL=gemini-2.5-flash
GEMINI_MAX_OUTPUT_TOKENS=1200
GEMINI_MAX_ATTEMPTS=3
GEMINI_API_TIMEOUT=60
```

### Step 3: Deploy
1. In Streamlit Cloud, set:
   - **Repository**: YOUR_USERNAME/InterviewAnalyzer
   - **Branch**: main
   - **Main file**: app.py
2. Click **"Deploy"**
3. Wait 2-3 minutes ⏳
4. Your app will be live! 🎉

## 📍 Your Live App URL
```
https://share.streamlit.io/YOUR_USERNAME/InterviewAnalyzer
```

## ✅ Verify Deployment
- Upload a test resume
- Check results appear
- Monitor logs in dashboard

## 🔧 Troubleshooting

### "ModuleNotFoundError"
→ All required packages are in `requirements.txt` ✓

### "Gemini API error"
→ Check API key in Secrets is correct
→ Go to https://aistudio.google.com/app/apikeys

### "File upload fails"
→ Ensure file is PDF and < 10MB
→ Check PyPDF version in requirements.txt

## 💰 Monitor Costs
- Expected: **~$0.08-0.32/month** (very cheap!)
- Free tier: **Thousands of requests included**
- Dashboard: https://aistudio.google.com/app/apikeys

## 🎯 Next Steps
✅ Files ready for deployment  
✅ requirements.txt ✓  
✅ .streamlit/config.toml ✓  
✅ README.md ✓  
✅ DEPLOYMENT.md ✓  

**Just push to GitHub and deploy! 🚀**
