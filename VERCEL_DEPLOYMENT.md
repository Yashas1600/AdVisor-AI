# Vercel Deployment Guide for AdVisor

## Prerequisites
- GitHub repository connected to Vercel
- Supabase account with database set up
- Environment variables ready

## Steps to Deploy

### 1. Push to GitHub
```bash
git add .
git commit -m "Prepare for Vercel deployment"
git push origin main
```

### 2. Connect to Vercel
1. Go to [vercel.com](https://vercel.com)
2. Click "New Project"
3. Import your GitHub repository: `AdVisor`
4. Vercel will auto-detect Next.js

### 3. Configure Environment Variables

In Vercel dashboard, go to **Settings → Environment Variables** and add:

#### Required Variables:
```
NEXT_PUBLIC_SUPABASE_URL=https://ltsnoprnomhaoilufuhb.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Imx0c25vcHJub21oYW9pbHVmdWhiIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjE0MjE2NzYsImV4cCI6MjA3Njk5NzY3Nn0.BXXSm0MBd8LgWFBbKtI0R8QNFuaaXxYq4nZxBnaNXhw
```

**Note:** Only `NEXT_PUBLIC_*` variables are needed for the frontend. Backend variables (OPENAI_API_KEY, etc.) stay on your EC2 instance.

### 4. Build Settings (Auto-detected)
- **Framework Preset**: Next.js
- **Build Command**: `npm run build`
- **Output Directory**: `.next`
- **Install Command**: `npm install`

### 5. Deploy
Click **Deploy** and wait for build to complete (~2-3 minutes)

## Post-Deployment

### Update Supabase Redirect URLs
1. Go to Supabase Dashboard → Authentication → URL Configuration
2. Add your Vercel URL to **Site URL** and **Redirect URLs**:
   ```
   https://your-app-name.vercel.app
   https://your-app-name.vercel.app/**
   ```

### Test Your Deployment
1. Visit your Vercel URL
2. Test sign up flow
3. Test sign in flow
4. Test dashboard access

## Architecture After Deployment

```
Frontend (Vercel)
  ↓
Supabase (Authentication + Database)
  ↓
Backend API (AWS EC2) - Optional for feature extraction
  http://52.53.159.105:8000
```

## Custom Domain (Optional)
1. Go to Vercel Dashboard → Settings → Domains
2. Add your custom domain
3. Update DNS records as instructed
4. Update Supabase redirect URLs with new domain

## Troubleshooting

### Build Fails
- Check build logs in Vercel dashboard
- Ensure all dependencies are in `package.json`
- Verify TypeScript types are correct

### Authentication Issues
- Verify `NEXT_PUBLIC_SUPABASE_URL` and `NEXT_PUBLIC_SUPABASE_ANON_KEY` are set
- Check Supabase redirect URLs include Vercel domain
- Clear browser cache and cookies

### Dashboard Redirect Loop
- Check authentication logic in `/app/page.tsx`
- Verify Supabase session is being created properly

## Notes

- **Backend API**: The Python backend (FastAPI) stays on AWS EC2. Frontend makes API calls to it when needed.
- **Environment Variables**: Only frontend variables (NEXT_PUBLIC_*) are needed in Vercel
- **Supabase**: Handles all authentication and user data storage
- **Static Generation**: Next.js will use client-side rendering for dynamic routes

## Quick Deploy Checklist

- [ ] Push latest code to GitHub
- [ ] Connect repository to Vercel
- [ ] Add `NEXT_PUBLIC_SUPABASE_URL` env var
- [ ] Add `NEXT_PUBLIC_SUPABASE_ANON_KEY` env var
- [ ] Deploy project
- [ ] Update Supabase redirect URLs
- [ ] Test authentication flow
- [ ] Test dashboard functionality

Your app will be live at: `https://your-project-name.vercel.app`
