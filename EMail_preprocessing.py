import imaplib
import email
from email.header import decode_header
import os
import requests
import uuid  # To generate unique folder names
from dotenv import load_dotenv

load_dotenv()

class EmailPreprocessingAgent:
    def __init__(self, email_server, email_user, email_password, output_directory, ai_agent_url):
        """
        Initialize the email preprocessing agent.

        Args:
            email_server (str): The IMAP server (e.g., imap.gmail.com).
            email_user (str): The email account username.
            email_password (str): The email account password.
            output_directory (str): Directory to save extracted text and images.
            ai_agent_url (str): URL of the AI Processing Agent.
        """
        self.email_server = email_server
        self.email_user = email_user
        self.email_password = email_password
        self.output_directory = output_directory
        self.ai_agent_url = ai_agent_url
        self.mail = None

    def connect_to_email_server(self):
        """Connect to the IMAP email server and log in."""
        try:
            self.mail = imaplib.IMAP4_SSL(self.email_server)
            self.mail.login(self.email_user, self.email_password)
            self.mail.select("inbox")  # Select the inbox folder
            print("Connected to email server successfully.")
        except Exception as e:
            print(f"Error connecting to email server: {e}")

    def fetch_emails(self):
        """Fetch unread emails."""
        try:
            _, messages = self.mail.search(None, 'UNSEEN')
            email_ids = messages[0].split()
            print(f"Found {len(email_ids)} unread emails.")
            return email_ids
        except Exception as e:
            print(f"Error fetching emails: {e}")
            return []

    def process_email(self, email_id):
        """Process a single email."""
        try:
            _, msg_data = self.mail.fetch(email_id, '(RFC822)')
            for response_part in msg_data:
                if isinstance(response_part, tuple):
                    # Parse email content
                    msg = email.message_from_bytes(response_part[1])

                    # Get email subject
                    subject, encoding = decode_header(msg["Subject"])[0]
                    if isinstance(subject, bytes):
                        subject = subject.decode(encoding if encoding else "utf-8")
                    print(f"Processing email with subject: {subject}")

                    # Get email sender
                    from_ = msg.get("From")
                    print(f"From: {from_}")

                    # Generate a unique folder for this email
                    unique_folder_name = str(uuid.uuid4())
                    email_folder = os.path.join(self.output_directory, unique_folder_name)
                    os.makedirs(email_folder, exist_ok=True)

                    # Extract email text and attachments
                    email_text = ""
                    images = []
                    if msg.is_multipart():
                        for part in msg.walk():
                            if part.get_content_type() == "text/plain":
                                email_text = part.get_payload(decode=True).decode()
                                # Save email text in the unique folder
                                text_file_path = os.path.join(email_folder, "email_text.txt")
                                with open(text_file_path, "w") as text_file:
                                    text_file.write(email_text)
                            elif part.get_content_disposition() in ("inline", "attachment"):
                                filename = part.get_filename()
                                if filename:
                                    filepath = os.path.join(email_folder, filename)
                                    with open(filepath, "wb") as f:
                                        f.write(part.get_payload(decode=True))
                                    images.append(filepath)
                    else:
                        # If the email is not multipart
                        email_text = msg.get_payload(decode=True).decode()
                        # Save email text in the unique folder
                        text_file_path = os.path.join(email_folder, "email_text.txt")
                        with open(text_file_path, "w") as text_file:
                            text_file.write(email_text)

                    print(f"Extracted text saved to: {text_file_path}")
                    print(f"Extracted images saved to: {images}")

                    # Send email text and images to AI Processing Agent
                    self.send_to_ai_agent(email_text, images, unique_folder_name)

        except Exception as e:
            print(f"Error processing email: {e}")

    def send_to_ai_agent(self, email_text, images, unique_folder_name):
        """Send extracted email text and images to AI Processing Agent."""
        try:
            files = [("images", (os.path.basename(image), open(image, "rb"), "image/jpeg")) for image in images]
            data = {
                "email_text": email_text,
                "unique_id": unique_folder_name  # Send unique ID for tracking
            }
        except Exception as e:
            print(f"Error sending data to AI agent: {e}")

    def run(self):
        """Run the agent to process emails."""
        self.connect_to_email_server()
        email_ids = self.fetch_emails()
        for email_id in email_ids:
            self.process_email(email_id)


# Example Usage
if __name__ == "__main__":
    # Get environment variables
    email_server = os.getenv("EMAIL_SERVER")
    email_user = os.getenv("EMAIL_USER")
    email_password = os.getenv("EMAIL_PASSWORD")
    output_directory = os.getenv("OUTPUT_DIRECTORY")  
    ai_agent_url = os.getenv("AI_AGENT_URL")  

    # Create output directory if it doesn't exist
    os.makedirs(output_directory, exist_ok=True)

    # Initialize and run the agent
    agent = EmailPreprocessingAgent(email_server, email_user, email_password, output_directory, ai_agent_url)
    agent.run()
