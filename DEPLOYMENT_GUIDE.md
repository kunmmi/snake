# 🚀 BearTech Bot - Render Deployment Guide

This guide will help you deploy your BearTech Token Analysis Bot to Render.

## 📋 Prerequisites

1. **GitHub Repository**: Your code should be in a GitHub repository
2. **Render Account**: Sign up at [render.com](https://render.com)
3. **API Keys**: Gather your required API keys

## 🔑 Required API Keys

You'll need to set up these environment variables in Render:

### Required:

-   `TELEGRAM_BOT_TOKEN` - Your Telegram bot token from @BotFather

### Optional (with defaults):

-   `GOPLUS_API_KEY` - GoPlus Security API key (default provided)
-   `ETHERSCAN_API_KEY` - Etherscan API key for Ethereum data
-   `BASESCAN_API_KEY` - BaseScan API key for Base chain data

## 🚀 Deployment Steps

### Step 1: Prepare Your Repository

1. **Push your code to GitHub** with all the deployment files:
    - `render.yaml` - Render configuration
    - `requirements.txt` - Python dependencies
    - `start_production.py` - Production startup script
    - `health_check.py` - Health check endpoint

### Step 2: Create Render Service

1. **Go to Render Dashboard**: [dashboard.render.com](https://dashboard.render.com)
2. **Click "New +"** → **"Web Service"**
3. **Connect your GitHub repository**
4. **Configure the service**:
    - **Name**: `beartech-bot`
    - **Environment**: `Python 3`
    - **Build Command**: `pip install -r requirements.txt`
    - **Start Command**: `python start_production.py`
    - **Plan**: Free (or upgrade as needed)

### Step 3: Set Environment Variables

In the Render dashboard, go to **Environment** tab and add:

```
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
GOPLUS_API_KEY=Y0ZVbTgCm8G40GbczyAD
ETHERSCAN_API_KEY=your_etherscan_api_key_here
BASESCAN_API_KEY=your_basescan_api_key_here
```

### Step 4: Deploy

1. **Click "Create Web Service"**
2. **Wait for deployment** (usually 2-5 minutes)
3. **Check the logs** for any errors

## 🔍 Health Check

Your bot will be available at:

-   **Health Check**: `https://your-service-name.onrender.com/health`
-   **Status**: `https://your-service-name.onrender.com/status`

## 📊 Monitoring

### Logs

-   View logs in Render dashboard under **"Logs"** tab
-   Monitor for errors and bot activity

### Health Monitoring

-   Render will automatically monitor the `/health` endpoint
-   Service will restart if health checks fail

## 🛠️ Troubleshooting

### Common Issues:

1. **Bot not responding**:

    - Check `TELEGRAM_BOT_TOKEN` is set correctly
    - Verify bot is running in logs

2. **API errors**:

    - Check API keys are valid
    - Monitor rate limits

3. **Deployment fails**:
    - Check `requirements.txt` for missing dependencies
    - Verify Python version compatibility

### Debug Commands:

```bash
# Check service status
curl https://your-service-name.onrender.com/health

# View detailed status
curl https://your-service-name.onrender.com/status
```

## 🔄 Updates

To update your bot:

1. **Push changes to GitHub**
2. **Render will auto-deploy** (if auto-deploy is enabled)
3. **Or manually deploy** from Render dashboard

## 💰 Costs

-   **Free Plan**: 750 hours/month (enough for 24/7 operation)
-   **Paid Plans**: Start at $7/month for always-on service

## 🔒 Security

-   **Environment variables** are encrypted in Render
-   **API keys** are not exposed in logs
-   **HTTPS** is automatically enabled

## 📈 Scaling

-   **Free Plan**: Service sleeps after 15 minutes of inactivity
-   **Paid Plans**: Always-on service with better performance
-   **Auto-scaling**: Available on higher plans

## 🆘 Support

If you encounter issues:

1. **Check Render logs** for error messages
2. **Verify environment variables** are set correctly
3. **Test locally** before deploying
4. **Contact Render support** for platform issues

## 🎉 Success!

Once deployed, your BearTech bot will be:

-   ✅ Running 24/7 on Render
-   ✅ Automatically restarting if it crashes
-   ✅ Monitoring health and performance
-   ✅ Accessible via Telegram

Your bot is now live and ready to analyze tokens! 🚀
