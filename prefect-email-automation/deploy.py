import sys
from pathlib import Path

# Add parent directory to path for importing email_flow
sys.path.insert(0, str(Path(__file__).parent.parent))

from email_flow import example_email_send_message_flow

if __name__ == "__main__":
    # Serve the flow - this creates a deployment and starts listening for scheduled runs
    # Compatible with Prefect 3 and the Hobby tier (Prefect-managed infrastructure)
    example_email_send_message_flow.serve(
        name="email-deployment",
        tags=["email", "automation"],
        description="Sends scheduled emails to carers with payment information",
    )
