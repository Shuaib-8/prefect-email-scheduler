from prefect import flow

if __name__ == "__main__":
    flow.from_source(
        source="https://github.com/Shuaib-8/prefect-email-scheduler.git",
        entrypoint="email_flow.py:example_email_send_message_flow"
    ).deploy(
        name="email-deployment",
        work_pool_name="managed-prefect-workpool",
        tags=["email", "automation"],
        description="Sends scheduled emails to carers with payment information",
        job_variables={
            "pip_packages": ["prefect-email"],
            "env": {"EXTRA_PIP_PACKAGES": "prefect-email"}
        }
    )
