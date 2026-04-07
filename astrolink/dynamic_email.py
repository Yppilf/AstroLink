import os, csv
from dotenv import load_dotenv
from datetime import date, datetime, timedelta
import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException

load_dotenv()
BREVO_API_KEY = os.getenv('BREVO_API_KEY')
LOG_FILE = "unsent_emails.csv"  # Keep track of emails unsent due to daily limit or exception

def log_unsent_email(recipients, template_id, dynamic_data, reason):
    """Log unsent emails in a CSV file."""
    file_exists = os.path.exists(LOG_FILE)
    with open(LOG_FILE, "a", newline="") as file:
        writer = csv.writer(file)
        if not file_exists:
            writer.writerow(["date", "recipients", "template_id", "dynamic_data", "reason"])
        writer.writerow([datetime.today().strftime("%Y-%m-%d"), recipients, template_id, dynamic_data, reason])

def log_email_attempt(recipients, template_id, dynamic_data, status, error=None):
    """Log every email attempt, including successes and failures."""
    log_exists = os.path.exists("email_attempts.csv")
    with open("email_attempts.csv", "a", newline="") as file:
        writer = csv.writer(file)
        if not log_exists:
            writer.writerow(["date", "recipients", "template_id", "dynamic_data", "status", "error"])
        writer.writerow([
            datetime.today().strftime("%Y-%m-%d"),
            recipients,
            template_id,
            dynamic_data,
            status,
            error or ""
        ])

def send_dynamic_email(recipients, template_id, dynamic_data):
    """Send email via Brevo if within limit, otherwise log it."""
    # [DEBUG] to avoid sending unnecessary emails while testing
    print(f"Email triggered to {recipients} with template {template_id}")
    return

    try:
        # Ensure list
        if isinstance(recipients, str):
            recipients = [recipients]

        # Configure Brevo API client
        configuration = sib_api_v3_sdk.Configuration()
        configuration.api_key['api-key'] = BREVO_API_KEY
        api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
            sib_api_v3_sdk.ApiClient(configuration)
        )

        # Build the email payload
        send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
            to=[{"email": email} for email in recipients],
            sender={"email": "noreply@siriusa.nl", "name": "Sirius A"},
            reply_to={"email": "astrolink@siriusa.nl"},
            template_id=template_id,
            params=dynamic_data  # Matches {{ params.key }} in template
        )

        # Send the email
        response = api_instance.send_transac_email(send_smtp_email)

        # Update counters & log
        log_email_attempt(recipients, template_id, dynamic_data, "sent", f"Message ID: {response.message_id}")
        print(f"Email sent! Message ID: {response.message_id}")
        return response

    except ApiException as e:
        error_message = f"Brevo API error: {e}"
        log_unsent_email(recipients, template_id, dynamic_data, error_message)
        log_email_attempt(recipients, template_id, dynamic_data, "error", error_message)
        print(f"An error occurred: {error_message}. Email logged for retry.")
        return None
    
    except Exception as e:
        error_message = str(e)
        log_unsent_email(recipients, template_id, dynamic_data, error_message)
        log_email_attempt(recipients, template_id, dynamic_data, "error", error_message)
        print(f"An unexpected error occurred: {error_message}. Email logged for retry.")
        return None