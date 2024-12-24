import os
import json
import boto3
from botocore.exceptions import BotoCoreError, NoCredentialsError
from dotenv import load_dotenv

load_dotenv()

aws_access_key = os.getenv("AWS_ACCESS_KEY_ID")
aws_secret_key = os.getenv("AWS_SECRET_ACCESS_KEY")
aws_region = os.getenv("AWS_DEFAULT_REGION")
dynamodb_table_name = os.getenv("DYNAMODB_TABLE")

ATTACHMENTS_DIR = "attachments"

#Initialize DynamoDB
dynamodb = boto3.resource(
    'dynamodb', 
    aws_access_key_id=aws_access_key,
    aws_secret_access_key=aws_secret_key,
    region_name=aws_region
)

table = dynamodb.Table(dynamodb_table_name)

def read_output_json(folder_path):
    """
    Read output.json from the given folder.
    """
    output_file = os.path.join(folder_path, "output.json")
    if os.path.exists(output_file):
        try:
            with open(output_file, "r") as f:
                data = json.load(f)
            print(f"Read data from {output_file}: {data}")
            return data
        except Exception as e:
            print(f"Error reading {output_file}: {e}")
            return None
    else:
        print(f"No output.json found in {folder_path}.")
        return None


def update_dynamodb(data):
    """
    Check if the username exists in the DynamoDB table, update the transaction_amount,
    and update or insert other fields from the given data.
    """
    try:
        # Check if the username exists in the table
        username = data.get("username")
        if not username:
            return {"success": False, "error": "Username not found in input data"}

        # Query DynamoDB for the username
        response = table.get_item(Key={"username": username})
        if "Item" in response:
            # Existing item found
            existing_item = response["Item"]
            print(f"Existing item found: {existing_item}")

            # Clean the transaction_amount fields
            def clean_amount(amount):
                """
                Remove non-numeric characters (e.g., ₹ symbol) from the amount and convert to float.
                """
                # Filter digits and periods only
                cleaned = ''.join(ch for ch in str(amount) if ch.isdigit() or ch == '.')
                return float(cleaned) if cleaned else 0.0

            # Get the existing and new transaction amounts
            existing_amount = clean_amount(existing_item.get("transaction_amount", "0"))
            new_amount = clean_amount(data.get("transaction_amount", "0"))

            # Calculate the updated transaction_amount
            updated_amount = existing_amount + new_amount
            existing_item["transaction_amount"] = str(updated_amount)

            # Add or update other fields from the input data
            for key, value in data.items():
                if key != "username" and key != "transaction_amount":  # Don't overwrite the primary key or recalculate amount
                    existing_item[key] = value

            # Write the updated item back to the table
            table.put_item(Item=existing_item)
            print(f"Updated item: {existing_item}")
            return {"success": True, "message": "DynamoDB item updated successfully"}
        else:
            # Insert the new item if username does not exist
            def clean_amount(amount):
                return float(''.join(ch for ch in str(amount) if ch.isdigit() or ch == '.'))
            if "transaction_amount" in data:
                data["transaction_amount"] = str(clean_amount(data["transaction_amount"]))
            table.put_item(Item=data)
            print(f"New item inserted: {data}")
            return {"success": True, "message": "DynamoDB item created successfully"}
    except (BotoCoreError, NoCredentialsError) as e:
        print(f"Error updating DynamoDB: {e}")
        return {"success": False, "error": str(e)}
    except ValueError as e:
        print(f"Error processing transaction amount: {e}")
        return {"success": False, "error": "Invalid transaction amount"}


def process_attachments():
    """
    Process all folders in the attachments directory and update DynamoDB.
    """
    results = []
    for folder_name in os.listdir(ATTACHMENTS_DIR):
        folder_path = os.path.join(ATTACHMENTS_DIR, folder_name)
        if os.path.isdir(folder_path):  # Only process directories
            print(f"Processing folder: {folder_path}")
            
            # Read output.json
            data = read_output_json(folder_path)
            if data:
                # Update DynamoDB
                result = update_dynamodb(data)
                results.append({
                    "folder": folder_name,
                    "result": result
                })
            else:
                results.append({
                    "folder": folder_name,
                    "result": {"success": False, "error": "output.json not found or invalid"}
                })

    return results

if __name__ == "__main__":
    # Run the script
    print("Starting to process attachments...")
    results = process_attachments()
    print("\nProcessing Results:")
    for result in results:
        print(result)