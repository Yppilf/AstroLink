# Local installation and deployment
## Setup venv
- python3 -m venv venv
- source venv/bin/activate
- pip install -r requirements.txt

## Setup environment variables
cp .env.example .env

Generate the APPLICATION_SECRET_KEY
```
python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
```

Generate the DJANGO_BACKUP_ENCRYPTION_KEY and CONTRACT_AUTHENTICITY_KEY
```
openssl rand -base64 32
```

For DJANGO_ENV use 'development'

The Brevo API key you can leave blank for local testing. You can log the email attempts from the send_dynamic_email() function in astrolink/dynamic_email.py

## Setting up PostgreSQL database
Install postgresql
- sudo apt update
- sudo apt install postgresql postgresql-contrib libpq-dev
- sudo -u postgres psql

Inside psql:
- CREATE DATABASE astrolink;
- CREATE USER astrolink_user WITH PASSWORD 'strong_password';
- GRANT ALL PRIVILEGES ON DATABASE astrolink TO astrolink_user;

Fill in .env with the used variables

## Setup database
Note: All .env values must be filled before running migrations except for the API key

python manage.py migrate
python manage.py setup_roles
python manage.py collectstatic --noinput
python manage.py create_admin_user

## Special LaTeX engine dependency
This project requires a full TeX Live installation for PDF generation.

The system uses:
- pdflatex
- xelatex
- lualatex

Install with:
sudo apt install texlive-full

## Running a server locally
Verify installation:
python manage.py check
Can throw warnings: "Auto-created primary key used when not defining a primary key type, by default 'django.db.models.AutoField'." 

python manage.py runserver
This will run a server on localhost, tied to the linked psql database. 

