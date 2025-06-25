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

# SendGrid Configuration - Update these values
SENDGRID_CONFIG = {
    "mailer_from_name": "Método Superare",
    "mailer_from_email": "noreply@superare.com.br",
    "mailer_transport": "smtp",
    "mailer_host": "smtp.sendgrid.net",
    "mailer_port": "587",
    "mailer_user": "apikey",  # SendGrid always uses "apikey" as username
    "mailer_password": os.getenv("SENDGRID_API_KEY", "YOUR_SENDGRID_API_KEY"),  # Get from GitHub Actions secrets
    "mailer_encryption": "tls",
    "mailer_auth_mode": "login"
}

# Test email configuration
TEST_EMAIL_RECIPIENT = os.getenv("EMAIL_ADDRESS", os.getenv("TEST_EMAIL_RECIPIENT", "test@example.com"))  # Get from GitHub Actions EMAIL_ADDRESS or fallback
TEST_MOBILE_NUMBER = os.getenv("MOBILE_NUMBER", "+5511999999999")  # Get from GitHub Actions MOBILE_NUMBER or fallback

def make_api_request(endpoint, method="GET", data=None):
    """Make API request with proper error handling"""
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

def configure_sendgrid_via_api():
    """Configure SendGrid email settings via Mautic API"""
    print("=== Configuring SendGrid Email Settings via API ===")
    
    # Get current configuration
    config_result = make_api_request("config")
    
    if config_result:
        print("✅ Current configuration retrieved")
        
        # Update email settings
        email_settings = {
            "config": SENDGRID_CONFIG
        }
        
        update_result = make_api_request("config/edit", "PUT", email_settings)
        
        if update_result:
            print("✅ SendGrid email settings updated via API")
            return True
        else:
            print("❌ Failed to update via API")
            return False
    else:
        print("❌ Failed to retrieve current configuration")
        return False

def test_sendgrid_configuration():
    """Test the SendGrid email configuration"""
    print("\n=== Testing SendGrid Email Configuration ===")
    
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

def get_sendgrid_setup_instructions():
    """Provide SendGrid setup instructions"""
    print("\n=== SendGrid Setup Instructions ===")
    print("📋 To get your SendGrid API key:")
    print("1. Go to https://sendgrid.com and create an account")
    print("2. Navigate to Settings → API Keys")
    print("3. Create a new API key with 'Mail Send' permissions")
    print("4. Copy the API key (it starts with 'SG.')")
    print("5. Add it to GitHub Actions secrets as 'SENDGRID_API_KEY")
    
    print("\n🔧 SendGrid SMTP Settings:")
    print("Host: smtp.sendgrid.net")
    print("Port: 587")
    print("Encryption: TLS")
    print("Username: apikey")
    print("Password: From GitHub Actions secrets (SENDGRID_API_KEY)")
    
    print("\n📊 SendGrid Free Tier:")
    print("- 100 emails/day")
    print("- 40,000 emails/month")
    print("- Professional deliverability")
    print("- Email analytics and tracking")
    
    print("\n🔐 GitHub Actions Setup:")
    print("1. Go to your repository → Settings → Secrets and variables → Actions")
    print("2. Add new repository secret: SENDGRID_API_KEY")
    print("3. Paste your SendGrid API key as the value")
    print("4. The script will automatically use this secret")

def main():
    """Main function"""
    if not all([MAUTIC_URL, MAUTIC_USER, MAUTIC_PASSWORD]):
        print("ERROR: Missing required environment variables")
        print("Please set MAUTIC_URL, MAUTIC_USER, and MAUTIC_PASSWORD")
        sys.exit(1)
    
    print(f"Configuring SendGrid for Mautic at: {MAUTIC_URL}")
    print(f"Using user: {MAUTIC_USER}")
    
    # Show SendGrid configuration
    print("\n📧 SendGrid Configuration:")
    for key, value in SENDGRID_CONFIG.items():
        if "password" in key.lower():
            print(f"  {key}: {'*' * len(value)}")
        else:
            print(f"  {key}: {value}")
    
    # Provide setup instructions
    get_sendgrid_setup_instructions()
    
    # Ask for confirmation
    print("\n⚠️  IMPORTANT: Make sure SENDGRID_API_KEY is set in GitHub Actions secrets!")
    print("The script will automatically use the API key from secrets.")
    
    response = input("\nDo you want to proceed with the configuration? (y/N): ")
    if response.lower() != 'y':
        print("Please add SENDGRID_API_KEY to GitHub Actions secrets and run the script again.")
        sys.exit(0)
    
    # Configure via API
    if configure_sendgrid_via_api():
        print("\n✅ SendGrid configuration completed via API!")
        
        # Test configuration
        test_sendgrid_configuration()
        
        print("\n🎯 Next Steps:")
        print("1. Update SENDGRID_CONFIG with your real API key")
        print("2. Run this script again to apply real settings")
        print("3. Test email sending with a real contact")
        print("4. Monitor SendGrid dashboard for delivery status")
    else:
        print("\n❌ SendGrid configuration failed!")
        print("Please check your Mautic API access and try again.")
        sys.exit(1)

if __name__ == "__main__":
    main() 