# Google OAuth Authentication Setup Guide

## Overview
This guide shows how to set up Google OAuth for Muller App to allow only 3 authorized admin users to log in.

---

## Step 1: Create Google Cloud Project

### 1.1 Go to Google Cloud Console
```
https://console.cloud.google.com/
```

### 1.2 Create New Project
1. Click the project selector at the top
2. Click "NEW PROJECT"
3. Enter name: `Muller App`
4. Click "CREATE"
5. Wait for project creation

---

## Step 2: Enable OAuth 2.0 API

### 2.1 Go to APIs & Services
1. In left sidebar, click "APIs & Services"
2. Click "Credentials"

### 2.2 Configure OAuth Consent Screen
1. Click "OAuth consent screen" (left menu)
2. Select "External" for user type
3. Click "CREATE"
4. Fill in:
   - App name: `Muller App`
   - User support email: your@email.com
   - Developer contact: your@email.com
5. Click "SAVE AND CONTINUE"
6. On "Scopes" page, click "SAVE AND CONTINUE"
7. On "Test users" page, click "SAVE AND CONTINUE"
8. Review and click "BACK TO DASHBOARD"

---

## Step 3: Create OAuth 2.0 Credentials

### 3.1 Create Credentials
1. In "APIs & Services > Credentials"
2. Click "CREATE CREDENTIALS"
3. Select "OAuth 2.0 Client ID"

### 3.2 Configure Application Type
1. Choose application type: **Web application**
2. Name: `Muller App Web Client`

### 3.3 Add Authorized Redirect URIs

**Local Development:**
```
http://localhost:5000/auth/callback
```

**Production (Vercel):**
```
https://your-project.vercel.app/auth/callback
```

Example (replace with your actual domain):
```
https://muller-app.vercel.app/auth/callback
```

### 3.4 Create Credentials
Click "CREATE"

---

## Step 4: Copy OAuth Credentials

You'll see a modal with:
- **Client ID** (long string starting with numbers)
- **Client Secret** (alphanumeric string)

**IMPORTANT:** Copy both immediately!

---

## Step 5: Add to .env File

### 5.1 Update `.env` File
```env
GOOGLE_CLIENT_ID=1234567890-abcdefghijklmnop.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=GOCSPX-xxxxxxxxxxxxxxxxxxxx
ADMIN_EMAILS=admin1@gmail.com,admin2@gmail.com,admin3@gmail.com
SECRET_KEY=your-secret-key-change-in-production
```

### 5.2 Install Required Package
```bash
pip install google-auth-oauthlib google-auth-httplib2 google-auth
```

Or update `requirements.txt`:
```
google-auth==2.25.0
google-auth-oauthlib==1.2.0
google-auth-httplib2==0.2.0
```

Then:
```bash
pip install -r requirements.txt
```

---

## Step 6: Test Locally

### 6.1 Start Flask App
```bash
python app.py

# Output should show:
# ✅ Base de datos conectada
# ✅ Servidor iniciado en: http://localhost:5000
```

### 6.2 Test Login
1. Go to http://localhost:5000
2. Should redirect to http://localhost:5000/auth/login
3. See Google login button
4. Click button → Select your account
5. If email in ADMIN_EMAILS → Login successful ✓
6. If email NOT in ADMIN_EMAILS → Error message

---

## Step 7: Deploy to Vercel

### 7.1 Update Redirect URI in Google Console
1. Go to https://console.cloud.google.com/
2. APIs & Services → Credentials
3. Find "Muller App Web Client"
4. Click pencil to edit
5. Add new Authorized redirect URI:
   ```
   https://your-domain.vercel.app/auth/callback
   ```
6. Click "SAVE"

### 7.2 Add Environment Variables to Vercel

1. Go to https://vercel.com/dashboard
2. Select your project
3. Settings → Environment Variables
4. Add:
   - `GOOGLE_CLIENT_ID` = (your Client ID)
   - `GOOGLE_CLIENT_SECRET` = (your Client Secret)
   - `ADMIN_EMAILS` = (comma-separated list)
   - `SECRET_KEY` = (random string, e.g., `$(openssl rand -base64 32)`)

5. Save and redeploy

### 7.3 Test Production
```
https://your-domain.vercel.app/

Should redirect to login, then work same as local
```

---

## How It Works

### Login Flow
```
1. User visits app
   ↓
2. Checks if logged in (session cookie)
   ↓
3. If NOT logged in → Redirect to /auth/login
   ↓
4. User clicks "Sign in with Google"
   ↓
5. Google prompt appears
   ↓
6. User selects account
   ↓
7. Google OAuth token sent to backend
   ↓
8. Backend verifies token with Google
   ↓
9. Check if email in ADMIN_EMAILS whitelist
   ↓
10. If YES → Create session, redirect to dashboard
    If NO → Show error message
```

### Session Management
- Login valid for 7 days
- Session stored in Flask server
- Logout clears session
- Can't access app without valid session

---

## Security Features

✅ **3-User Whitelist**
```python
ADMIN_EMAILS=admin1@gmail.com,admin2@gmail.com,admin3@gmail.com
```
Only these 3 emails can log in

✅ **OAuth Token Verification**
Token verified with Google servers before accepting

✅ **HTTPS in Production**
Vercel auto-enables HTTPS

✅ **Session Expiry**
Sessions expire after 7 days of inactivity

✅ **Secret Key**
Random secret key prevents session tampering

---

## Troubleshooting

### "GOOGLE_CLIENT_ID not set in .env"
**Fix:**
1. Create `.env` file with credentials
2. Restart Flask app
3. Try again

### "Token invalid" or "Invalid token"
**Fix:**
1. Make sure GOOGLE_CLIENT_ID is correct
2. Check token format
3. Try logging out and logging back in

### "Not authorized" after login
**Cause:** Email not in ADMIN_EMAILS list
**Fix:**
1. Add email to ADMIN_EMAILS in .env
2. Restart app
3. Try again

### "Redirect URI mismatch"
**Cause:** App URI not in Google credentials
**Fix:**
1. Go to console.cloud.google.com
2. Edit OAuth credentials
3. Add redirect URI exactly as it appears in error
4. Save and try again

### OAuth button not appearing
**Cause:** No GOOGLE_CLIENT_ID
**Fix:**
1. Check .env file has GOOGLE_CLIENT_ID
2. Restart Flask app
3. Hard refresh browser (Ctrl+Shift+R)

---

## Adding/Removing Admin Users

### Add New Admin
Edit `.env`:
```env
ADMIN_EMAILS=admin1@gmail.com,admin2@gmail.com,admin3@gmail.com,admin4@gmail.com
```
Restart app. New user can now login.

### Remove Admin
Edit `.env`:
```env
ADMIN_EMAILS=admin1@gmail.com,admin3@gmail.com
```
Restart app. admin2@gmail.com now blocked.

### Emergency Access
If you lose access:
1. SSH into server / Connect to Vercel
2. Edit `.env` to add your email
3. Restart app
4. Log in to regain access

---

## Environment Variables Reference

| Variable | Example | Description |
|----------|---------|-------------|
| `GOOGLE_CLIENT_ID` | `123...xyz.apps.googleusercontent.com` | From Google Cloud Console |
| `GOOGLE_CLIENT_SECRET` | `GOCSPX-...` | From Google Cloud Console |
| `ADMIN_EMAILS` | `a@gmail.com,b@gmail.com` | Comma-separated authorized emails |
| `SECRET_KEY` | `random-string-here` | Flask session secret |
| `DATABASE_URL` | `postgresql://...` | PostgreSQL connection (Neon) |
| `FLASK_ENV` | `production` or `development` | App environment |

---

## Testing Checklist

- [ ] Created Google Cloud project
- [ ] Enabled OAuth 2.0 API
- [ ] Added authorized redirect URIs (local + Vercel)
- [ ] Copied credentials to `.env`
- [ ] Installed dependencies: `pip install -r requirements.txt`
- [ ] Flask app starts without errors
- [ ] Can visit http://localhost:5000/auth/login
- [ ] Google login button appears
- [ ] Can sign in with authorized email
- [ ] Dashboard loads after login
- [ ] Can log out
- [ ] Logout redirects to login page
- [ ] Unauthorized email shows error
- [ ] Session persists across page reloads
- [ ] Environment variables set in Vercel
- [ ] Production deployment works

---

## Quick Reference Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
python app.py

# Test login
# Visit http://localhost:5000
# Click login button

# Logout
# Visit http://localhost:5000/auth/logout
```

---

## Support

- Google OAuth Issues: https://developers.google.com/identity/gsi/web
- Flask-Sessions: https://flask.palletsprojects.com/en/sessions/
- Vercel Env Vars: https://vercel.com/docs/concepts/projects/environment-variables

**Your app is now secure with authenticated access!** 🔐
