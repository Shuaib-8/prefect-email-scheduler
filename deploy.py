from email_flow import example_email_send_message_flow

if __name__ == "__main__":
    example_email_send_message_flow.serve(
        name="email-deployment",
        tags=["email", "automation"],
        description="Sends scheduled emails to carers with payment information",
    )

