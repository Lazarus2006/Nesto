# Hostinger VPS deployment

This guide targets a **Hostinger VPS running a clean Ubuntu 24.04 LTS image**.
It uses Nginx for HTTPS and static/media files, Gunicorn for Django, and
PostgreSQL on the VPS. It is not a guide for Hostinger shared web hosting or
hPanel-managed WordPress hosting.

Hostinger also advertises a preconfigured Django VPS template using
OpenLiteSpeed. This guide deliberately uses Nginx instead; choose a clean
Ubuntu 24.04 image rather than combining these Nginx instructions with an
OpenLiteSpeed template. Hostinger references:

- [Django VPS hosting](https://www.hostinger.com/vps/django-hosting)
- [Connect to a VPS with SSH](https://www.hostinger.com/support/5723772-how-to-connect-to-your-vps-via-ssh-at-hostinger/)
- [Set up a Hostinger VPS firewall](https://www.hostinger.com/support/4805502-how-to-set-up-a-firewall-at-vps/)
- [Point a domain to a VPS](https://www.hostinger.com/support/1583227-how-to-point-a-domain-to-your-vps-at-hostinger/)
- [Install SSL with Certbot on a VPS](https://www.hostinger.com/support/6865487-how-to-install-ssl-on-vps-using-certbot-at-hostinger/)

The first section is for testing locally. Finish it and verify the site before
provisioning or deploying the VPS.

## 1. Rotate credentials before testing or deployment

Credentials were pasted into a chat. Treat them as compromised, even though
your `.env` file is git-ignored and has restrictive local permissions:

1. Generate a new Django `SECRET_KEY`. Do not reuse the disclosed key.
2. Change the PostgreSQL password for the disclosed database role. If that
   role has other uses, create a dedicated Nesto role instead.
3. Rotate/restrict the Mapbox public token. Configure URL/referrer restrictions
   for your local development origin and, later, your production domain. A
   browser-visible Mapbox public token is not a server secret, but it should
   still be restricted.
4. Search the GitHub repository/history and any logs or deployment settings
   for accidentally committed/copied credentials; revoke anything exposed.
5. Update only your local `.env` with the newly issued local values. Do not
   paste secrets into chat or commit `.env`.

The checked-in `.env.example` contains local development defaults and
placeholders, not production credentials.

## 2. Run and test on localhost first

The project is at `Django/Nesto/`. From the repository root:

```bash
cd Django/Nesto
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
```

Copy `.env.example` to the repository root as `.env`, then edit it with the
rotated local credentials for your local PostgreSQL database and Mapbox token.
Keep `DEBUG=True`, and use `localhost,127.0.0.1` for `ALLOWED_HOSTS`. Leave
`CSRF_TRUSTED_ORIGINS` empty for localhost HTTP development.
The app requires an explicitly set `SECRET_KEY`; `.env.example` includes
instructions to generate one.

The Django settings load the repository-root `.env`. They accept either a
`DATABASE_URL` or the separate `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`,
and `DB_PORT` settings. If using the individual PostgreSQL settings, make sure
PostgreSQL is running and the database and role already exist.

Run the schema and checks:

```bash
.venv/bin/python manage.py migrate
.venv/bin/python manage.py check
.venv/bin/python manage.py test pages core
.venv/bin/python manage.py runserver
```

Open <http://127.0.0.1:8000/>. Confirm registration/login, city selection,
comment replies, service request creation, responses, accepting an offer,
private messaging, uploaded images, and the City Guide/map with your local
Mapbox token.

The regular username/password login is always available on `/login/`. Google
sign-in appears when the Google `SocialApp` is configured in Django admin and
attached to the active Django Site. This project already uses a database-backed
SocialApp; do not also add a second Google app via environment settings. In
`/admin/socialaccount/socialapp/`, check the existing "Google Login" app and
make sure its Sites include the domain you are using. The Site domain must
match the request host including its port in local development (for example
`127.0.0.1:8000`).

In
[Google Cloud Console](https://console.cloud.google.com/apis/credentials),
configure the OAuth consent screen/test users, and register the exact redirect
URI that matches the host you use:

```text
http://127.0.0.1:8000/accounts/google/login/callback/
```

If you use `http://localhost:8000`, register that exact callback too and add
`localhost:8000` to the Django Site's domain associations. With
`SOCIALACCOUNT_LOGIN_ON_GET=True`, selecting "Continue with Google" redirects
directly to Google rather than showing Allauth's intermediate confirmation.

For a quick configuration check that does not use your local database, run:

```bash
env DEBUG=True SECRET_KEY=local-check-only DATABASE_URL=sqlite:///:memory: \
  .venv/bin/python manage.py check
env DEBUG=True SECRET_KEY=local-check-only DATABASE_URL=sqlite:///:memory: \
  .venv/bin/python manage.py test pages core
```

The temporary test database is disposable. These commands do not migrate or
modify your configured PostgreSQL database.

## 3. Prepare the Hostinger VPS

In Hostinger hPanel, provision a clean Ubuntu 24.04 LTS VPS and note its public IP.
Point your domain's DNS `A` records for the root name and (if used) `www` to
that IP; wait for DNS to resolve before requesting HTTPS certificates.

SSH into the VPS as the Hostinger-provided administrator and install the
runtime:

```bash
sudo apt update
sudo apt upgrade -y
sudo apt install -y python3 python3-venv python3-dev build-essential \
  libpq-dev postgresql postgresql-contrib nginx
sudo adduser --system --group --home /opt/nesto nesto
```

Use Hostinger's firewall controls and/or UFW to allow SSH and web traffic only.
Do not expose PostgreSQL port 5432 publicly. Prefer SSH keys; disable password
SSH only after confirming key-based access works in a second session.

Create a dedicated database and role. Use a newly generated password and keep
it private:

```bash
sudo -u postgres psql
```

In the PostgreSQL prompt (replace the example role/database names as needed):

```sql
CREATE USER nesto_app WITH PASSWORD 'REPLACE_WITH_A_NEW_UNIQUE_PASSWORD';
CREATE DATABASE nesto_db OWNER nesto_app;
\q
```

## 4. Install the application

Clone the repository into `/opt/nesto/src` using your deployment process, then
give the service account read access and write access only to uploads and
collected static files:

```bash
sudo -u nesto git clone YOUR_GIT_REPOSITORY_URL /opt/nesto/src
cd /opt/nesto/src/Django/Nesto
sudo -u nesto python3 -m venv /opt/nesto/venv
sudo -u nesto /opt/nesto/venv/bin/pip install -r requirements.txt
sudo install -d -o nesto -g nesto /opt/nesto/src/Django/Nesto/media
sudo install -d -o nesto -g nesto /opt/nesto/src/Django/Nesto/staticfiles
```

Do not put the `.env` file in the Git repository. Create a separate
root-readable environment file on the VPS:

```bash
sudo install -d -m 750 -o root -g nesto /etc/nesto
sudo install -m 640 -o root -g nesto /dev/null /etc/nesto/nesto.env
sudoedit /etc/nesto/nesto.env
```

Set the following values in `/etc/nesto/nesto.env`, filling in real values
directly on the VPS. Do not use the disclosed values:

```ini
SECRET_KEY=GENERATE_A_NEW_LONG_RANDOM_DJANGO_SECRET
DEBUG=False
ALLOWED_HOSTS=example.com,www.example.com
CSRF_TRUSTED_ORIGINS=https://example.com,https://www.example.com
DB_NAME=nesto_db
DB_USER=nesto_app
DB_PASSWORD=NEW_UNIQUE_DATABASE_PASSWORD
DB_HOST=127.0.0.1
DB_PORT=5432
MAPBOX_TOKEN=RESTRICTED_MAPBOX_PUBLIC_TOKEN
TRUST_PROXY_SSL_HEADER=True
SECURE_SSL_REDIRECT=True
SECURE_HSTS_SECONDS=31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS=False
SECURE_HSTS_PRELOAD=False
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST=YOUR_SMTP_HOST
EMAIL_PORT=587
EMAIL_HOST_USER=YOUR_SMTP_USERNAME
EMAIL_HOST_PASSWORD=YOUR_SMTP_PASSWORD
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=Nesto <noreply@example.com>
```

Replace domain examples with the actual domain. `TRUST_PROXY_SSL_HEADER=True`
is appropriate here because Nginx on this VPS is the trusted TLS-terminating
proxy. Never set it when clients can supply the forwarded-protocol header
directly. Set HSTS subdomain/preload options only after verifying all affected
domains can remain HTTPS-only.

Generate a new Django secret on the VPS without printing or storing it in
shell history:

```bash
sudo /opt/nesto/venv/bin/python -c \
  'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

Paste the generated output directly into the protected environment file.
Alternatively use a secret manager. Set real SMTP credentials before relying
on account email or password recovery.

In Django admin, ensure the existing Google SocialApp is associated with the
production Site whose domain is the actual hostname. Register
`https://yourdomain.com/accounts/google/login/callback/` in Google Cloud
Console (plus the `www` callback if used). Keep the Google client secret in the
database-backed SocialApp configuration; do not create a duplicate Google app
in environment settings.

## 5. Collect static files and migrate

Run management commands from the Django project directory with the production
environment loaded. Use systemd-run to run one-off commands as the application
user while systemd reads the protected environment file (replace the unit name
for each separate command):

```bash
sudo systemd-run --wait --pipe --collect --unit=nesto-check-deploy \
  --property=User=nesto \
  --property=Group=nesto \
  --property=WorkingDirectory=/opt/nesto/src/Django/Nesto \
  --property=EnvironmentFile=/etc/nesto/nesto.env \
  /opt/nesto/venv/bin/python manage.py check --deploy
sudo systemd-run --wait --pipe --collect --unit=nesto-migrate \
  --property=User=nesto \
  --property=Group=nesto \
  --property=WorkingDirectory=/opt/nesto/src/Django/Nesto \
  --property=EnvironmentFile=/etc/nesto/nesto.env \
  /opt/nesto/venv/bin/python manage.py migrate --noinput
sudo systemd-run --wait --pipe --collect --unit=nesto-collectstatic \
  --property=User=nesto \
  --property=Group=nesto \
  --property=WorkingDirectory=/opt/nesto/src/Django/Nesto \
  --property=EnvironmentFile=/etc/nesto/nesto.env \
  /opt/nesto/venv/bin/python manage.py collectstatic --noinput
```

Do not print or put the contents of the environment file in shell history or a
command-line argument. Keep it root-owned and unreadable to other users. Run
migrations once per release, not once per Gunicorn worker. Django's deployment
check may report HSTS warnings if subdomain/preload options are intentionally
disabled; only enable them when their security requirements are satisfied.

## 6. Run Gunicorn with systemd

Create `/etc/systemd/system/nesto.service`:

```ini
[Unit]
Description=Nesto Django application
After=network.target postgresql.service

[Service]
User=nesto
Group=nesto
WorkingDirectory=/opt/nesto/src/Django/Nesto
EnvironmentFile=/etc/nesto/nesto.env
ExecStart=/opt/nesto/venv/bin/gunicorn --workers 3 --bind 127.0.0.1:8000 --access-logfile - --error-logfile - Nesto.wsgi:application
Restart=on-failure
RestartSec=5
PrivateTmp=true
NoNewPrivileges=true

[Install]
WantedBy=multi-user.target
```

Activate and check it:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now nesto
sudo systemctl status nesto
sudo journalctl -u nesto -n 100 --no-pager
```

If the VPS has limited memory, reduce Gunicorn workers (for example to 2).
Gunicorn must listen on localhost only; Nginx is the public web server.

## 7. Configure Nginx and HTTPS

Create `/etc/nginx/sites-available/nesto` with your actual domain:

```nginx
server {
    listen 80;
    listen [::]:80;
    server_name example.com www.example.com;

    client_max_body_size 10m;

    location /static/ {
        alias /opt/nesto/src/Django/Nesto/staticfiles/;
        access_log off;
        expires 7d;
    }

    location /media/ {
        alias /opt/nesto/src/Django/Nesto/media/;
        add_header X-Content-Type-Options nosniff always;
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 60s;
    }
}
```

Enable the site and check the configuration:

```bash
sudo ln -s /etc/nginx/sites-available/nesto /etc/nginx/sites-enabled/nesto
sudo nginx -t
sudo systemctl reload nginx
```

After DNS points to the VPS and HTTP works, install a certificate:

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d example.com -d www.example.com
sudo certbot renew --dry-run
```

The Nginx `media/` directory must be persistent and readable by Nginx. Back up
uploaded files as well as PostgreSQL. Local filesystem media is appropriate
for a single VPS only; it is not shared across multiple app servers.

## 8. Production operations

- Create an administrator with `manage.py createsuperuser`.
- In Django admin, set the Sites domain to the real HTTPS domain and configure
  the site metadata. Make sure the configured Google SocialApp is associated
  with this Site.
- Verify SMTP delivery, account recovery, registration, HTTPS redirects,
  uploaded media, and static assets.
- Back up PostgreSQL and `Django/Nesto/media/`, and test restoring them.
- Apply code updates through a release process: install dependencies, run
  migrations once, collect static files, then restart `nesto`.
- Monitor `journalctl -u nesto` and Nginx logs; configure VPS monitoring and
  automated backups.

Do not consider the deployment production-ready until the exposed credentials
have been rotated, the production environment file contains real values,
domain DNS and HTTPS work, database migrations have been applied, and backups
and SMTP have been tested. Google sign-in additionally needs valid OAuth
credentials and the exact HTTPS callback URI registered in Google Cloud.

## Useful checks

```bash
sudo systemctl status nesto
sudo journalctl -u nesto -f
sudo nginx -t
sudo systemctl status nginx
```
