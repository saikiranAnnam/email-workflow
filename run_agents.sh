#!/bin/bash

# Define script paths for each agent
AGENT1_SCRIPT="Email_preprocessing.py"
AGENT2_SCRIPT="ai_processing.py"
AGENT3_SCRIPT="update_processing.py"

# Python executable (adjust if needed, e.g., python3 or virtual environment path)
PYTHON_EXEC="python3"

# Step 1: Run Agent 1
echo "Running Agent 1: Fetching unread emails and saving data..."
$PYTHON_EXEC $AGENT1_SCRIPT
if [ $? -ne 0 ]; then
  echo "Error: Agent 1 failed. Exiting workflow."
  exit 1
fi
echo "Agent 1 completed successfully."

# Step 2: Run Agent 2
echo "Running Agent 2: Processing attachments and generating output.json..."
$PYTHON_EXEC $AGENT2_SCRIPT
if [ $? -ne 0 ]; then
  echo "Error: Agent 2 failed. Exiting workflow."
  exit 1
fi
echo "Agent 2 completed successfully."

# # Step 3: Run Agent 3
echo "Running Agent 3: Updating DynamoDB with processed data..."
$PYTHON_EXEC $AGENT3_SCRIPT
if [ $? -ne 0 ]; then
  echo "Error: Agent 3 failed. Exiting workflow."
  exit 1
fi
echo "Agent 3 completed successfully."

# Final message
echo "Workflow completed successfully!"
