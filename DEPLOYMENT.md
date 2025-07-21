# Deployment Guide

## Quick Deploy to Vercel

### Prerequisites
- A DeepSeek API key from [platform.deepseek.com](https://platform.deepseek.com/)
- A GitHub account
- A Vercel account (free tier available)

### Step-by-Step Deployment

1. **Fork this repository** to your GitHub account

2. **Get your DeepSeek API Key**:
   - Go to https://platform.deepseek.com/
   - Sign up/login and create an API key
   - Copy the API key (starts with `sk-`)

3. **Deploy to Vercel**:
   - Go to [vercel.com](https://vercel.com) and login
   - Click "New Project"
   - Import your forked repository
   - Vercel will auto-detect it as a Python project

4. **Configure Environment Variables**:
   - In your Vercel project settings, go to "Environment Variables"
   - Add: `DEEPSEEK_API_KEY` = `your_api_key_here`
   - Click "Deploy"

5. **Access your deployed app**:
   - Your app will be available at `https://your-project-name.vercel.app`
   - The deployment typically takes 2-3 minutes

### Environment Variables

Only one environment variable is required for deployment:

| Variable | Required | Description |
|----------|----------|-------------|
| `DEEPSEEK_API_KEY` | Yes | Your DeepSeek API key |

All other variables have sensible defaults configured in `vercel.json`.

### Troubleshooting Deployment

**Build fails?**
- Check the build logs in Vercel dashboard
- Ensure your API key is correctly set
- Try redeploying

**App loads but gives errors?**
- Verify your DeepSeek API key is valid
- Check the function logs in Vercel dashboard

**Need help?**
- Check the main README.md for more details
- Review Vercel's Python deployment documentation

## Alternative Deployment Options

### Deploy to Railway
1. Fork the repository
2. Connect to Railway
3. Set `DEEPSEEK_API_KEY` environment variable
4. Deploy

### Deploy to Render
1. Fork the repository
2. Connect to Render
3. Set `DEEPSEEK_API_KEY` environment variable
4. The `Procfile` will be used automatically

### Deploy to Heroku
1. Fork the repository
2. Create a new Heroku app
3. Set `DEEPSEEK_API_KEY` config var
4. Deploy from GitHub

## Production Considerations

- **Rate Limiting**: Consider implementing rate limiting
- **Monitoring**: Set up error tracking and monitoring
- **Data Persistence**: For user uploads, integrate cloud storage
- **Security**: Review CORS settings and add authentication if needed
