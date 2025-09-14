# 🚀 Production Deployment Guide

This guide covers deploying the Academic Chatbot to various cloud platforms.

## 📋 Prerequisites

Before deploying, ensure you have:

1. **OpenAI API Key**: Get from [OpenAI Platform](https://platform.openai.com/api-keys)
2. **Pinecone API Key**: Get from [Pinecone Console](https://app.pinecone.io/)
3. **Pinecone Environment**: Your Pinecone environment (e.g., `us-east-1-aws`)

## 🚄 Railway Deployment (Recommended)

Railway provides the easiest deployment with automatic Redis setup.

### 1. Deploy to Railway

[![Deploy on Railway](https://railway.app/button.svg)](https://railway.app/template/your-template)

Or manually:

1. Fork this repository
2. Connect your GitHub repo to Railway
3. Add environment variables (see below)
4. Deploy!

### 2. Environment Variables

Set these in Railway dashboard:

```bash
OPENAI_API_KEY=your_openai_api_key_here
PINECONE_API_KEY=your_pinecone_api_key_here
PINECONE_ENVIRONMENT=us-east-1-aws
CHAT_MODEL=gpt-3.5-turbo
EMBEDDING_MODEL=text-embedding-ada-002
```

### 3. Redis Setup

Railway automatically provisions Redis. No additional setup needed!

### 4. Access Your App

- **Web UI**: `https://your-app.railway.app/`
- **API Docs**: `https://your-app.railway.app/docs`
- **Health Check**: `https://your-app.railway.app/health`

## 🌐 Render Deployment

### 1. Deploy to Render

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

### 2. Manual Setup

1. Connect your GitHub repository
2. Use `render.yaml` configuration
3. Set environment variables
4. Deploy with Redis add-on

### 3. Configuration

The `render.yaml` file is already configured. Just set your environment variables.

## ☁️ Heroku Deployment

### 1. Deploy to Heroku

[![Deploy](https://www.herokucdn.com/deploy/button.svg)](https://heroku.com/deploy)

### 2. Manual Setup

```bash
# Install Heroku CLI and login
heroku create your-app-name

# Set environment variables
heroku config:set OPENAI_API_KEY=your_key_here
heroku config:set PINECONE_API_KEY=your_key_here
heroku config:set PINECONE_ENVIRONMENT=us-east-1-aws

# Add Redis addon
heroku addons:create heroku-redis:mini

# Deploy
git push heroku main
```

## 🐳 Docker Deployment

### 1. Build and Run

```bash
# Build the image
docker build -t academic-chatbot .

# Run with environment variables
docker run -p 8000:8000 \
  -e OPENAI_API_KEY=your_key \
  -e PINECONE_API_KEY=your_key \
  -e PINECONE_ENVIRONMENT=us-east-1-aws \
  academic-chatbot
```

### 2. Docker Compose

```bash
# Start all services (app + Redis)
docker-compose up -d
```

## 🔧 Environment Variables Reference

| Variable               | Required | Default                  | Description            |
| ---------------------- | -------- | ------------------------ | ---------------------- |
| `OPENAI_API_KEY`       | ✅       | -                        | Your OpenAI API key    |
| `PINECONE_API_KEY`     | ✅       | -                        | Your Pinecone API key  |
| `PINECONE_ENVIRONMENT` | ✅       | -                        | Pinecone environment   |
| `CHAT_MODEL`           | ❌       | `gpt-3.5-turbo`          | OpenAI chat model      |
| `EMBEDDING_MODEL`      | ❌       | `text-embedding-ada-002` | OpenAI embedding model |
| `REDIS_URL`            | ❌       | -                        | Redis connection URL   |
| `PORT`                 | ❌       | `8000`                   | Server port            |

## 🌍 Custom Domain Setup

### Railway

1. Go to your Railway project settings
2. Add your custom domain
3. Update DNS records as instructed

### Render

1. Go to your service settings
2. Add custom domain
3. Configure DNS with provided CNAME

## 🔍 Troubleshooting

### Common Issues

1. **"Service not initialized"**

   - Check API keys are set correctly
   - Verify Pinecone environment/region

2. **"Redis connection failed"**

   - Ensure Redis addon is provisioned
   - Check REDIS_URL environment variable

3. **"Model not found"**
   - Verify OpenAI API key has access to model
   - Check billing/quota on OpenAI account

### Health Check

Visit `/health` to check service status:

```json
{
	"status": "healthy",
	"services": {
		"chat_service": true,
		"document_service": true,
		"cache_service": true
	}
}
```

## 📊 Monitoring

### Built-in Stats

- Visit `/stats` for system metrics
- Web UI shows live performance data
- Response times and cache hit rates

### Logging

- All platforms provide log access
- Set `LOG_LEVEL=DEBUG` for detailed logs
- Monitor for OpenAI/Pinecone API errors

## 🔒 Security

### Production Checklist

- [ ] API keys stored as environment variables
- [ ] CORS configured appropriately
- [ ] Rate limiting enabled
- [ ] HTTPS enforced by platform
- [ ] Regular dependency updates

### API Security

The API is designed to be publicly accessible for the web UI, but consider:

- Adding authentication for sensitive deployments
- Implementing rate limiting per IP
- Monitoring for abuse patterns

## 🚀 Performance

### Optimization Tips

1. **Caching**: Redis improves response times by 50%+
2. **Model Selection**: `gpt-3.5-turbo` is faster and cheaper than GPT-4
3. **Chunk Size**: Adjust `CHUNK_SIZE` based on document types
4. **Concurrent Requests**: Platform handles multiple users automatically

### Scaling

- **Railway**: Auto-scales based on traffic
- **Render**: Upgrade to higher tiers for more resources
- **Heroku**: Scale dynos as needed

## 💰 Cost Estimation

### API Costs (per 1000 queries)

- **OpenAI**: ~$0.50-2.00 (depending on model)
- **Pinecone**: ~$0.10-0.50 (depending on index size)
- **Platform**: $5-20/month (depending on provider/tier)

### Cost Optimization

1. Use `gpt-3.5-turbo` instead of GPT-4
2. Implement caching (already included)
3. Optimize chunk sizes to reduce tokens
4. Monitor usage in OpenAI/Pinecone dashboards

---

## 🎯 Quick Start Summary

1. **Choose Platform**: Railway (easiest) → Render → Heroku
2. **Set Environment Variables**: OpenAI + Pinecone keys
3. **Deploy**: One-click or git push
4. **Test**: Visit your app URL
5. **Monitor**: Check `/health` and logs

Your Academic Chatbot is now live! 🎉
