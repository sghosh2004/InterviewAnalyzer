# 🚀 Streamlit Cloud Deployment - Complete Guide

## ✅ Pre-Deployment Checklist

Your project is **ready to deploy**! Here's what's included:

```
✓ app.py                    - Main Streamlit application
✓ requirements.txt          - All dependencies
✓ .streamlit/config.toml    - Streamlit configuration
✓ .gitignore               - Excludes secrets from git
✓ services/                - Gemini & document services
✓ README.md                - Project documentation
✓ DEPLOYMENT.md            - Detailed deployment guide
✓ QUICK_DEPLOY.md          - Quick start (this file)
```

---

## 🎯 Deployment in 3 Steps

### Step 1️⃣ Create GitHub Repository

**Option A: Using GitHub Web Interface (Easiest)**
1. Go to https://github.com/new
2. Repository name: `InterviewAnalyzer`
3. Description: "AI-powered resume analysis with Gemini"
4. Choose **Public** (for free tier)
5. Click **Create repository**

**Option B: Using Git Command Line**
```bash
# Navigate to project
cd "c:\AI Projects 2026\InterviewAnalyzer"

# Add all files
git add .

# Create initial commit
git commit -m "Initial commit: Resume Analyzer with Gemini API"

# Add remote (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/InterviewAnalyzer.git
git branch -M main
git push -u origin main
```

### Step 2️⃣ Deploy on Streamlit Cloud

1. **Sign in** to https://share.streamlit.io (use your GitHub account)

2. **Click "New app"**

3. **Select your repository**:
   - Repository: `YOUR_USERNAME/InterviewAnalyzer`
   - Branch: `main`
   - Main file path: `app.py`

4. **⚠️ IMPORTANT: Add Secrets BEFORE deploying**
   - Click **Advanced settings** (gear icon)
   - Go to **Secrets** tab
   - Paste this in the text area:
   ```
   GEMINI_API_KEY=AQ.Ab8RN6ItFe5f7TYJxzYaSS4M0ZwgsZtlKQ8OryDo7jcC_Ln-Ew
   GEMINI_MODEL=gemini-2.5-flash
   GEMINI_MAX_OUTPUT_TOKENS=1200
   GEMINI_MAX_ATTEMPTS=3
   GEMINI_API_TIMEOUT=60
   ```
   - Click **Save**

5. **Deploy!**
   - Click **Deploy** button
   - Wait 2-3 minutes for deployment
   - Your app URL: `https://share.streamlit.io/YOUR_USERNAME/InterviewAnalyzer`

### Step 3️⃣ Test Your App

1. Open your app URL (appears on dashboard)
2. Upload a test PDF resume
3. Wait for analysis (~5-10 seconds)
4. Verify results appear correctly

---

## 📊 Deployment Architecture

```
Your Local Machine
       ↓
    Git Push
       ↓
  GitHub Repository
       ↓
Streamlit Cloud Detects Changes
       ↓
Builds & Deploys App
       ↓
Live App: https://share.streamlit.io/YOUR_USERNAME/InterviewAnalyzer
```

---

## 🔑 Secrets Management

**Local Development** (`.env` file - NOT pushed to GitHub):
```
GEMINI_API_KEY=your_key_here
```

**Streamlit Cloud** (Secrets in dashboard):
- Encrypted & secure
- Never visible in logs
- Auto-loaded as environment variables

✅ Your `.env` is in `.gitignore` so it won't be committed accidentally!

---

## 📈 Monitoring & Logs

### View Logs
1. Go to https://share.streamlit.io
2. Click your app
3. **Settings** (gear icon) → **View logs**

### Monitor API Costs
1. Go to https://aistudio.google.com/app/apikeys
2. Click your API key
3. **View quotas** to see usage
4. Expected cost: **~$0.08-0.32/month** (very cheap!)

---

## 🐛 Troubleshooting

### App won't start
**Error**: "ModuleNotFoundError: No module named 'X'"
- **Fix**: Check `requirements.txt` has all dependencies ✓

### Gemini API errors
**Error**: "401 Unauthorized" or "Invalid API key"
- **Fix**: 
  1. Check API key at https://aistudio.google.com/app/apikeys
  2. Update Secrets in Streamlit Cloud dashboard
  3. Redeploy (Settings → Reboot app)

**Error**: "503 Service Unavailable"
- **Fix**: Temporary - API is overloaded. Retries automatically.

### File upload fails
**Error**: "Only PDF resumes are supported"
- **Fix**: Upload a `.pdf` file (not `.docx` or `.txt`)

---

## 🔄 Auto-Redeploy on Updates

Every time you push to GitHub:
```bash
git add .
git commit -m "Your message"
git push origin main
```

Streamlit Cloud automatically:
1. Detects the push
2. Rebuilds the app
3. Redeploys (takes 1-2 minutes)

---

## 💡 Pro Tips

1. **Share Your App**
   - Copy URL: `https://share.streamlit.io/YOUR_USERNAME/InterviewAnalyzer`
   - Share with colleagues/recruiters

2. **Custom Domain** (Pro tier)
   - Streamlit Cloud Pro: $12/month
   - Maps app to your domain

3. **Monitor Usage**
   - Dashboard shows active users
   - API logs available in Settings

4. **Performance**
   - First load: ~10-15 seconds (cold start)
   - Subsequent loads: ~2-3 seconds
   - Analysis: ~5-10 seconds per resume

---

## 🎓 Learning Resources

- **Streamlit Docs**: https://docs.streamlit.io
- **Deployment**: https://docs.streamlit.io/deploy/streamlit-community-cloud
- **Secrets**: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management
- **Gemini API**: https://ai.google.dev

---

## ✨ After Deployment

✅ Your app is live!  
✅ Share the URL with anyone  
✅ Monitor usage and costs  
✅ Update code anytime (auto-redeploys)  
✅ Scale as needed  

---

## 📞 Support

- Stuck? Check: https://docs.streamlit.io
- API issues? Check: https://aistudio.google.com/app/apikeys
- Streamlit Cloud issues? Go to: https://discuss.streamlit.io

---

## 🎉 You're All Set!

**Next action:** Push to GitHub and deploy!

```bash
git add .
git commit -m "Ready for Streamlit Cloud deployment"
git push origin main
```

Then go to https://share.streamlit.io and deploy! 🚀
