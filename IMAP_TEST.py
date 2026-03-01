import imaplib, json

# Replace with your email provider's IMAP server (e.g., imap.gmail.com, outlook.office365.com)


try:
    with open('info.json', 'r') as f:
        data = json.load(f)

    IMAP_SERVER = "imap.gmail.com" 
    EMAIL = "michi@certifiedleadkings.com"
    PASSWORD = "Certified1!"

    print(f"Attempting to connect to {IMAP_SERVER}...")
    # Connect to the server
    mail = imaplib.IMAP4_SSL(IMAP_SERVER)
    
    # Try to log in
    mail.login(EMAIL, PASSWORD)
    print("✅ SUCCESS: IMAP is enabled and your credentials work!")
    
    # Log out cleanly
    mail.logout()

except imaplib.IMAP4.error as e:
    print(f"❌ LOGIN FAILED: {e}")
    print("This usually means IMAP is disabled, OR you need an 'App Password'.")
except Exception as e:
    print(f"❌ CONNECTION FAILED: {e}")