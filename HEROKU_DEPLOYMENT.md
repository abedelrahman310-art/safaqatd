# Heroku Deployment Guide for Safakat

## Prerequisites
- Heroku CLI installed (`brew install heroku` or download from heroku.com)
- Git configured and your project under version control
- Heroku account created

## Step 1: Generate Secret Key
Run this locally to generate a secure Django SECRET_KEY:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

Copy the output for use in Step 3.

## Step 2: Initialize Git & Commit
```bash
cd project_root
git init
git add .
git commit -m "Initial commit for Heroku deployment"
```

## Step 3: Create Heroku App
```bash
heroku login
heroku create your-app-name
```

Replace `your-app-name` with your desired app name (must be unique on Heroku).

## Step 4: Set Environment Variables
Set all configuration on Heroku:

```bash
# Core Django
heroku config:set SECRET_KEY="<paste-the-key-from-step-1>"
heroku config:set DEBUG=False
heroku config:set ALLOWED_HOSTS="your-app-name.herokuapp.com,www.your-app-name.herokuapp.com"

# Email (Gmail example)
heroku config:set EMAIL_HOST=smtp.gmail.com
heroku config:set EMAIL_PORT=587
heroku config:set EMAIL_USE_TLS=True
heroku config:set EMAIL_HOST_USER="your-email@gmail.com"
heroku config:set EMAIL_HOST_PASSWORD="your-app-specific-password"

# CORS (adjust domains as needed)
heroku config:set CORS_ALLOWED_ORIGINS="https://your-app-name.herokuapp.com,https://www.your-app-name.herokuapp.com"
```

**Note on Gmail Password:** Use an [App-Specific Password](https://support.google.com/accounts/answer/185833), not your regular Gmail password.

## Step 5: Add PostgreSQL Database
```bash
heroku addons:create heroku-postgresql:mini
```

This automatically sets `DATABASE_URL`. Verify:
```bash
heroku config:get DATABASE_URL
```

## Step 6: Deploy
```bash
git push heroku main
```

(Use `master` if your branch is not `main`)

Heroku will:
- Install Python and dependencies from `requirements.txt`
- Run `release.sh` (collectstatic, migrate)
- Start the web dyno with Gunicorn

## Step 7: Verify Deployment
```bash
heroku open
```

Or check logs:
```bash
heroku logs --tail
```

## Step 8: Create Superuser (Admin)
```bash
heroku run python manage.py createsuperuser
```

Follow the prompts. Access admin at:
```
https://your-app-name.herokuapp.com/admin/
```

## Useful Heroku Commands

### View Config
```bash
heroku config
```

### View Live Logs
```bash
heroku logs --tail
heroku logs --tail -p web
```

### Run One-Off Commands
```bash
heroku run python manage.py shell
heroku run python manage.py migrate
heroku run python manage.py seed_data  # if you have a script
```

### Scale Dynos
```bash
heroku ps:scale web=1
```

### Database Operations
```bash
heroku pg:info
heroku pg:backups
heroku pg:backups:capture
```

### Restart App
```bash
heroku restart
```

## Troubleshooting

### "Application error" on opening URL
Check logs:
```bash
heroku logs --tail
```

### Database migration errors
Run migrations manually:
```bash
heroku run python manage.py migrate --no-input
```

### Static files not loading
Collect them:
```bash
heroku run python manage.py collectstatic --no-input
```

### Out of memory (H12 error)
Consider upgrading dyno type or optimizing code:
```bash
heroku ps:type hobby-standard
```

### Email not sending
Verify credentials:
```bash
heroku config:get EMAIL_HOST_USER
heroku config:get EMAIL_HOST_PASSWORD
```

Test with Heroku shell:
```bash
heroku run python manage.py shell
>>> from django.core.mail import send_mail
>>> send_mail('Test', 'This is a test', 'your-email@gmail.com', ['recipient@example.com'])
```

## Custom Domain (Optional)
```bash
heroku domains:add www.yourdomain.com
heroku domains:add yourdomain.com
```

Then update your DNS records (CNAME or A record) to point to your Heroku app.

## Scale for Production
- **Dyno:** Upgrade from `Eco` to `Standard-1X` or higher
- **Database:** Start with `mini`, upgrade to `standard` for production
- **CDN:** Enable Heroku CDN for static files
- **Monitoring:** Use Heroku New Relic add-on

## Notes
- Dyno hours reset at 08:00 UTC daily
- Database backups are automatic (free plan: 7 days retention)
- Media files uploaded by users need external storage (AWS S3 recommended)
- Logs are retained for 1500 lines; consider Papertrail for persistent logging
