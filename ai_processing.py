import os
import pytesseract
from PIL import Image
import openai
import json
from flask import Flask, jsonify
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set OpenAI API key
openai.api_key = os.getenv("OPENAI_API_KEY")

# Base directory for attachments
ATTACHMENTS_DIR = "./attachments"

# Initialize Flask app
app = Flask(__name__)

# Function to process email text using OpenAI
def process_text_with_openai(email_text):
    """Extract username and UTR from email text using OpenAI."""
    try:
        prompt = f"""
        Extract the following details from the email body:
        - Username
        - UTR (Transaction Reference Number)

        Email Body:
        {email_text}
        """
        print("Prompt sent to OpenAI (Text Processing):", prompt)

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt},
            ]
        )

        extracted_data = response['choices'][0]['message']['content'].strip()
        print("OpenAI Response (Text):", extracted_data)

        # Parse the extracted details
        username, utr = None, None
        for line in extracted_data.splitlines():
            if "Username" in line:
                username = line.split(":")[-1].strip()
            if "UTR" in line or "Transaction Reference Number" in line:
                utr = line.split(":")[-1].strip()

        return {"username": username, "utr": utr}
    except Exception as e:
        print(f"Error processing text with OpenAI: {e}")
        return {"username": None, "utr": None}

# Function to extract text from images using Tesseract OCR
def extract_text_from_image(image_path):
    """Extract text from a transaction image using Tesseract OCR and replace misread symbols."""
    try:
        print(f"Extracting text from image: {image_path}")
        image = Image.open(image_path)
        extracted_text = pytesseract.image_to_string(image)
        print("Raw Extracted Text from Image:", extracted_text)

        # Replace common misread symbols and remove INR or pound symbol
        corrected_text = extracted_text.replace("\u20b9", "").replace("\u00a3", "")
        print("Corrected Text:", corrected_text)

        return corrected_text
    except Exception as e:
        print(f"Error extracting text from image: {e}")
        return None

# Function to process transaction image using OpenAI
def process_image_with_openai(image_path):
    """Extract transaction ID and amount from transaction image using OCR and OpenAI."""
    try:
        extracted_text = extract_text_from_image(image_path)
        if not extracted_text:
            return {"transaction_id": None, "transaction_amount": None}

        # Send the extracted text to OpenAI for structured data extraction
        prompt = f"""
        Extract the following details from the transaction receipt:
        - Transaction ID
        - Transaction Amount

        Extracted Text:
        {extracted_text}
        """
        print("Prompt sent to OpenAI (Image Processing):", prompt)

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user", "content": prompt},
            ]
        )

        extracted_data = response['choices'][0]['message']['content'].strip()
        print("OpenAI Response (Image):", extracted_data)

        # Parse the extracted details
        transaction_id, transaction_amount = None, None
        for line in extracted_data.splitlines():
            if "Transaction ID" in line:
                transaction_id = line.split(":")[-1].strip()
            if "Transaction Amount" in line:
                transaction_amount = line.split(":")[-1].strip()

        return {"transaction_id": transaction_id, "transaction_amount": transaction_amount}
    except Exception as e:
        print(f"Error processing image with OpenAI: {e}")
        return {"transaction_id": None, "transaction_amount": None}

# Function to process a single folder in the attachments directory
def process_folder(folder_path):
    """Process a single folder to extract and process email text and transaction image."""
    try:
        print(f"Processing folder: {folder_path}")

        # Path to output.json
        output_file = os.path.join(folder_path, "output.json")

        # Load existing data from output.json if it exists
        existing_data = {}
        if os.path.exists(output_file):
            with open(output_file, "r") as f:
                try:
                    existing_data = json.load(f)
                except json.JSONDecodeError:
                    print(f"Error decoding JSON from {output_file}. Resetting file.")
                    existing_data = {}

        # Process email text
        email_text_file = os.path.join(folder_path, "email_text.txt")
        email_text_data = {"username": None, "utr": None}
        if os.path.exists(email_text_file):
            with open(email_text_file, "r") as f:
                email_text = f.read()
            email_text_data = process_text_with_openai(email_text)

        # Process transaction image
        transaction_image = next(
            (os.path.join(folder_path, file_name) for file_name in os.listdir(folder_path)
             if file_name.lower().endswith((".png", ".jpg", ".jpeg"))),
            None
        )

        transaction_image_data = {"transaction_id": None, "transaction_amount": None}
        if transaction_image:
            transaction_image_data = process_image_with_openai(transaction_image)

        # Merge new data with existing data
        updated_data = {**existing_data, **email_text_data, **transaction_image_data}

        # Save updated data to output.json
        with open(output_file, "w") as f:
            json.dump(updated_data, f, indent=4)

        print(f"Processed data saved to: {output_file}")
        return updated_data
    except Exception as e:
        print(f"Error processing folder {folder_path}: {e}")
        return None

# Main script to run the agent
if __name__ == "__main__":
    print("Starting Agent with Tesseract OCR and OpenAI...")
    try:
        # Process all attachments
        results = []
        for folder_name in os.listdir(ATTACHMENTS_DIR):
            folder_path = os.path.join(ATTACHMENTS_DIR, folder_name)
            if os.path.isdir(folder_path):  # Only process directories
                result = process_folder(folder_path)
                if result:
                    results.append(result)

        # Print results for debugging
        print("Processing Results:")
        for result in results:
            print(result)

    except Exception as e:
        print(f"Error running Agent: {e}")
    print("Agent completed.")
