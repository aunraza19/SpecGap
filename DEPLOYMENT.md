# SpecGap Deployment Guide

## 🚀 Quick Deploy to Render

### Option 1: Blueprint Deploy (Recommended)

1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Add Docker deployment configuration"
   git push origin main
   ```

2. **Connect to Render**
   - Go to [Render Dashboard](https://dashboard.render.com)
   - Click "New" → "Blueprint"
   - Connect your GitHub repository
   - Select the `render.yaml` file
   - Click "Apply"

3. **Set Environment Variables**
   After deployment, go to your service settings and add:
   ```
   GEMINI_API_KEY=your_primary_key
   GEMINI_API_KEY_ROUND1=your_round1_key
   GEMINI_API_KEY_ROUND2=your_round2_key
   GEMINI_API_KEY_ROUND3=your_round3_key
   ```

### Option 2: Manual Docker Deploy

1. **Create Web Service**
   - Go to Render Dashboard
   - Click "New" → "Web Service"
   - Connect your GitHub repo
   - Select "Docker" as runtime
   - Set the following:
     - **Name**: specgap
     - **Region**: Oregon (or closest to you)
     - **Branch**: main
     - **Plan**: Free (for testing)

2. **Configure Environment**
   Add these environment variables in Render:
   ```
   ENV=production
   DEBUG=false
   LOG_LEVEL=INFO
   CORS_ORIGINS=*
   GEMINI_API_KEY=your_key
   GEMINI_API_KEY_ROUND1=your_key_1
   GEMINI_API_KEY_ROUND2=your_key_2
   GEMINI_API_KEY_ROUND3=your_key_3
   QUEUE_ENABLED=true
   MAX_CONCURRENT_SESSIONS=1
   ```

3. **Deploy**
   - Click "Create Web Service"
   - Wait for build to complete (~5-10 minutes)

---

## 🐳 Local Docker Testing

### Prerequisites
- Docker Desktop installed
- Git

### Build and Run

```bash
# Clone the repo
cd hackathon

# Create .env file with your API keys
cp specgap/.env.example .env
# Edit .env and add your GEMINI_API_KEY values

# Build and run
docker-compose up --build

# Access the app
# Frontend: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

### Build Only (no compose)

```bash
# Build the image
docker build -t specgap .

# Run the container
docker run -p 8000:8000 \
  -e GEMINI_API_KEY=your_key \
  -e GEMINI_API_KEY_ROUND1=your_key_1 \
  -e GEMINI_API_KEY_ROUND2=your_key_2 \
  -e GEMINI_API_KEY_ROUND3=your_key_3 \
  specgap
```

---

## 📁 Project Structure

```
hackathon/
├── Dockerfile           # Multi-stage build (frontend + backend)
├── docker-compose.yml   # Local development
├── docker-entrypoint.sh # Container startup script
├── nginx.conf           # Nginx config (not used in simple mode)
├── render.yaml          # Render deployment blueprint
├── Frontend/            # React + Vite frontend
│   ├── src/
│   └── package.json
└── specgap/             # FastAPI backend
    ├── app/
    ├── requirements.txt
    └── run_backend.py
```

---

## 🔧 Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `ENV` | Environment mode | `development` |
| `DEBUG` | Enable debug mode | `true` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `GEMINI_API_KEY` | Primary Gemini API key | Required |
| `GEMINI_API_KEY_ROUND1` | Round 1 API key | Falls back to primary |
| `GEMINI_API_KEY_ROUND2` | Round 2 API key | Falls back to primary |
| `GEMINI_API_KEY_ROUND3` | Round 3 API key | Falls back to primary |
| `CORS_ORIGINS` | Allowed CORS origins | `*` |
| `DATABASE_URL` | SQLite/PostgreSQL URL | `sqlite:///./specgap_audits.db` |
| `QUEUE_ENABLED` | Enable request queue | `true` |
| `MAX_CONCURRENT_SESSIONS` | Max parallel sessions | `1` |

---

## 🌐 Endpoints

After deployment, your app will have:

- **Frontend**: `https://your-app.onrender.com/`
- **API Docs**: `https://your-app.onrender.com/docs`
- **Health Check**: `https://your-app.onrender.com/api/v1/health`

### API Routes

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/audit/council-session` | Quick analysis (flashcards) |
| POST | `/api/v1/audit/council-session/stream` | Real-time streaming analysis |
| POST | `/api/v1/audit/deep-analysis` | Deep audit mode |
| POST | `/api/v1/audit/full-spectrum` | Combined council + deep |
| GET | `/api/v1/audits` | List audit history |
| GET | `/api/v1/queue/status` | Queue status |

---

## ⚠️ Free Tier Limitations

Render Free Tier has limitations:
- **Spin Down**: Service sleeps after 15 mins of inactivity (first request takes ~30s)
- **Memory**: 512MB RAM
- **Build Time**: 10 min limit

Gemini Free Tier:
- **5 RPM per project** (why we use 3 API keys)
- **20 requests per day per project**

### Tips for Demo
1. Create 3 Google Cloud projects, each with its own API key
2. Queue system ensures only 1 analysis at a time
3. Test locally before inviting teammates

---

## 🐛 Troubleshooting

### Build Fails
```bash
# Check Docker logs
docker logs specgap

# Rebuild without cache
docker-compose build --no-cache
```

### API Errors
- Check environment variables are set correctly
- Verify API keys are valid
- Check Render logs for detailed errors

### Rate Limits
- Wait 1 minute between requests
- Use the queue system (frontend shows wait time)
- Check if daily quota (20 requests) is exhausted

---

## 📞 Support

For issues:
1. Check Render service logs
2. Review backend logs at `/docs` endpoint
3. Open an issue on GitHub

