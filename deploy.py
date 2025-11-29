from email_flow import example_email_send_message_flow

if __name__ == "__main__":
    example_email_send_message_flow.deploy(
        name="email-deployment",
        work_pool_name="prefect-managed",
        tags=["email", "automation"],
        description="Sends scheduled emails to carers with payment information",
    )

