# AstroLink System Specifications

**Document Version:** June 2026
**Application:** AstroLink

## Infrastructure

### Operating System

| Component    | Value              |
| ------------ | ------------------ |
| Distribution | Ubuntu 22.04.2 LTS |
| Kernel       | 5.15.0-179-generic |

### CPU

| Property         | Value                                |
| ---------------- | ------------------------------------ |
| Model            | Intel Xeon Processor (Skylake, IBRS) |
| CPU Family       | 6                                    |
| Model Number     | 85                                   |
| Threads per Core | 1                                    |
| Cores per Socket | 1                                    |
| Sockets          | 1                                    |

### Storage

Current application footprint (source code and static assets):

```text
157 MB
```

### Core Services

| Service    | Version                               |
| ---------- | ------------------------------------- |
| Nginx      | 1.18.0 (Ubuntu)                       |
| Gunicorn   | 26.0.0                                |
| PostgreSQL | 14.23 (Ubuntu 14.23-0ubuntu0.22.04.1) |

---

# Nginx Configuration

The application is served through Nginx with Gunicorn acting as the upstream WSGI server.

## Virtual Host

```nginx
server {
    server_name astrolink.siriusa.nl;

    client_max_body_size 100M;

    location /static/ {
        alias /var/www/siriusa/static_astrolink/;
        expires 30d;
        access_log off;
    }

    location / {
        proxy_pass http://127.0.0.1:8003;

        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        proxy_set_header X-Forwarded-Port $server_port;
    }

    listen 443 ssl;

    ssl_certificate /etc/letsencrypt/live/astrolink.siriusa.nl/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/astrolink.siriusa.nl/privkey.pem;

    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;
}

server {
    if ($host = astrolink.siriusa.nl) {
        return 301 https://$host$request_uri;
    }

    listen 80;
    server_name astrolink.siriusa.nl;

    return 404;
}
```

### Notes

* Static files are served directly by Nginx.
* Dynamic requests are proxied to Gunicorn on port `8003`.
* TLS certificates are managed using Certbot.
* Maximum upload size is configured as `100 MB`.

---

# Gunicorn Configuration

Systemd service definition:

```ini
[Unit]
Description=Gunicorn for astrolink
After=network.target

[Service]
User=siriusa
Group=www-data
WorkingDirectory=/home/siriusa/astrolink
EnvironmentFile=/home/siriusa/astrolink/config/.env

ExecStart=/home/siriusa/astrolink/venv_py311/bin/gunicorn \
    --workers 3 \
    --bind 127.0.0.1:8003 \
    config.wsgi:application

Restart=always

[Install]
WantedBy=multi-user.target
```

### Notes

* Gunicorn listens only on localhost.
* Nginx acts as the public-facing reverse proxy.
* Three worker processes are configured.
* Automatic restart is enabled.

---

# TLS Certificate

Managed using Certbot.

| Property         | Value                                                      |
| ---------------- | ---------------------------------------------------------- |
| Certificate Name | astrolink.siriusa.nl                                       |
| Key Type         | RSA                                                        |
| Domain           | astrolink.siriusa.nl                                       |
| Certificate Path | `/etc/letsencrypt/live/astrolink.siriusa.nl/fullchain.pem` |
| Private Key Path | `/etc/letsencrypt/live/astrolink.siriusa.nl/privkey.pem`   |

### Notes

Certificate renewal is handled by Certbot.

---

# Firewall Configuration

Firewall is managed through UFW.

## Default Policy

| Direction | Policy   |
| --------- | -------- |
| Incoming  | Deny     |
| Outgoing  | Allow    |
| Routed    | Disabled |

## Allowed Services

| Port    | Service |
| ------- | ------- |
| 22/tcp  | OpenSSH |
| 80/tcp  | HTTP    |
| 443/tcp | HTTPS   |

### Notes

Only SSH and web traffic are exposed publicly.

---

# LaTeX Dependencies

AstroLink supports PDF generation through a locally installed TeX Live distribution.

## pdfTeX

```text
pdfTeX 3.141592653-2.6-1.40.22
TeX Live 2022
```

## Installed TeX Live Packages

* texlive-base
* texlive-binaries
* texlive-fonts-extra
* texlive-fonts-extra-links
* texlive-fonts-recommended
* texlive-lang-english
* texlive-lang-french
* texlive-latex-base
* texlive-latex-extra
* texlive-latex-recommended
* texlive-luatex
* texlive-pictures
* texlive-plain-generic
* texlive-xetex

### Notes

* No custom fonts are required.
* LaTeX document templates are stored and managed through the AstroLink user interface.
* Template maintenance can be performed without server-side modifications.

---

# Backup and Restore

AstroLink uses PostgreSQL native backups.

## Backup Process

```text
PostgreSQL
    ↓
pg_dump
    ↓
AES Encryption
    ↓
Download
```

## Restore Process

```text
Upload
    ↓
AES Decryption
    ↓
pg_restore
    ↓
Database Restored
```

### Characteristics

* Constant memory usage.
* PostgreSQL-native backup format.
* Suitable for large databases.
* Encrypted backup files.

```
```
