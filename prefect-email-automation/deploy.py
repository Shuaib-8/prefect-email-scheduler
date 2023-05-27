from email_flow import example_email_send_message_flow
from prefect.deployments import Deployment

deployment = Deployment.build_from_flow(
    flow=example_email_send_message_flow,
    name="ec2-deployment", 
    version=1, 
    # work_queue_name="demo",
    work_pool_name="default-agent-pool",
)
deployment.apply()
