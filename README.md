# Prefect Email Scheduler


Using Prefect to schedule emails - example of how to use Prefect to schedule emails such as for periodic payment confirmation emails to accounts receivable staff to confirm payroll payments.

There are a components to this project to be aware of:

1. The email_flow.py file is the main file that contains the flow for sending the emails.
2. The email_template.py file contains the templates for the emails.
3. The deploy.py file is used to deploy the flow to Prefect Cloud.
