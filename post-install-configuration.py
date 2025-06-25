import requests
import json
import os
import sys

# Try to import dotenv, but don't fail if it's not available
try:
    from dotenv import load_dotenv
    load_dotenv('.mautic_env')
except ImportError:
    print("Warning: python-dotenv not installed. Loading environment from system variables.")
    pass

# --- Configuration ---
MAUTIC_URL = os.getenv("MAUTIC_URL")
MAUTIC_USER = os.getenv("MAUTIC_USER")
MAUTIC_PASSWORD = os.getenv("MAUTIC_PASSWORD")

# Email config from environment
EMAIL_CONFIG = {
    "mailer_from_name": os.getenv("MAUTIC_MAILER_FROM_NAME"),
    "mailer_from_email": os.getenv("MAUTIC_MAILER_FROM_EMAIL"),
    "mailer_transport": os.getenv("MAUTIC_MAILER_TRANSPORT"),
    "mailer_host": os.getenv("MAUTIC_MAILER_HOST"),
    "mailer_port": os.getenv("MAUTIC_MAILER_PORT"),
    "mailer_user": os.getenv("MAUTIC_MAILER_USER"),
    "mailer_password": os.getenv("MAUTIC_MAILER_PASSWORD"),
    "mailer_encryption": os.getenv("MAUTIC_MAILER_ENCRYPTION"),
    "mailer_auth_mode": os.getenv("MAUTIC_MAILER_AUTH_MODE"),
}

TEST_EMAIL_RECIPIENT = os.getenv("EMAIL_ADDRESS", os.getenv("TEST_EMAIL_RECIPIENT", "test@example.com"))
TEST_MOBILE_NUMBER = os.getenv("MOBILE_NUMBER", "+5511999999999")

def make_api_request(endpoint, method="GET", data=None):
    url = f"{MAUTIC_URL}/api/{endpoint}"
    auth = (str(MAUTIC_USER), str(MAUTIC_PASSWORD))
    try:
        if method == "GET":
            response = requests.get(url, auth=auth, timeout=30)
        elif method == "POST":
            response = requests.post(url, json=data, auth=auth, timeout=30)
        elif method == "PUT":
            response = requests.put(url, json=data, auth=auth, timeout=30)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"API Error ({endpoint}): {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
        return None

def send_test_email():
    print("\n=== Sending Test Email via Mautic API ===")
    # Create a test contact first
    test_contact_data = {
        "firstname": "Adilson",
        "lastname": "Jardim",
        "email": TEST_EMAIL_RECIPIENT,
        "mobile": TEST_MOBILE_NUMBER
    }
    print("Creating test contact...")
    contact_result = make_api_request("contacts/new", "POST", test_contact_data)
    if not contact_result:
        print("❌ Failed to create test contact")
        return False
    contact_id = contact_result.get('contact', {}).get('id')
    print(f"✅ Test contact created (ID: {contact_id})")
    # Create a test email
    test_email_data = {
        "name": "Test SendGrid Configuration",
        "subject": "Test Email via SendGrid",
        "content": """
        <h2>SendGrid Test Email</h2>
        <p>Hello {contactfield=firstname}!</p>
        <p>This is a test email to verify your SendGrid configuration in Mautic.</p>
        <p>If you receive this email, your SendGrid setup is working correctly!</p>
        <p><strong>SendGrid Configuration:</strong></p>
        <ul>
            <li>Host: smtp.sendgrid.net</li>
            <li>Port: 587</li>
            <li>Encryption: TLS</li>
            <li>From: Método Superare</li>
        </ul>
        <p>Test completed successfully!</p>
        """,
        "isPublished": True
    }
    print("Creating test email...")
    test_email_result = make_api_request("emails/new", "POST", test_email_data)
    if not test_email_result:
        print("❌ Failed to create test email")
        return False
    test_email_id = test_email_result.get('email', {}).get('id')
    print(f"✅ Test email created (ID: {test_email_id})")
    # Send the test email to the test contact
    send_email_data = {
        "email": test_email_id,
        "contact": contact_id
    }
    print("Sending test email to contact...")
    send_result = make_api_request("emails/send", "POST", send_email_data)
    if send_result:
        print("✅ Test email sent successfully!")
        print(f"📧 Email sent to: {TEST_EMAIL_RECIPIENT}")
        print("📊 Check SendGrid dashboard for delivery status")
        print("📋 Check Mautic email logs for sending confirmation")
    else:
        print("❌ Failed to send test email")
        print("This might indicate a SendGrid configuration issue")
        return False
    return True

def print_email_config():
    print("\n📧 Current Email Configuration from Environment:")
    for key, value in EMAIL_CONFIG.items():
        if value is not None and "password" in key.lower():
            print(f"  {key}: {'*' * len(value)}")
        else:
            print(f"  {key}: {value}")

def main():
    if not all([MAUTIC_URL, MAUTIC_USER, MAUTIC_PASSWORD]):
        print("ERROR: Missing required environment variables")
        print("Please set MAUTIC_URL, MAUTIC_USER, and MAUTIC_PASSWORD")
        sys.exit(1)
    print(f"Using Mautic URL: {MAUTIC_URL}")
    print(f"Using Mautic User: {MAUTIC_USER}")
    print_email_config()
    send_test_email()
    print("\n🎯 Next Steps:")
    print("1. If you did not receive the test email, check your SendGrid and Mautic logs.")
    print("2. Make sure your .mautic_env and docker-compose.yml have the correct email settings.")
    print("3. Restart your Mautic containers after changing environment variables.")
    print("4. For further troubleshooting, check the Mautic UI email settings and logs.")

if __name__ == "__main__":
    main() 