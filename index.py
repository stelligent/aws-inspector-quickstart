import json, os, logging, boto3, urllib.request, shutil
from datetime import datetime as dt

logger = logging.getLogger('InspectorQuickstart')
logger.setLevel(logging.DEBUG)

inspectorClient = boto3.client('inspector')
cloudformationClient = boto3.client('cloudformation')
s3Client = boto3.client('s3')
snsClient = boto3.client('sns')
reports_bucket = os.environ["REPORTS_BUCKET"]
notification_topic = os.environ["REPORT_COMPLETE_SNS"]


def get_template_user_attributes(assement_template_arn):
    user_attributes = {}
    response = inspectorClient.describe_assessment_templates(
        assessmentTemplateArns=[
            assement_template_arn,
        ]
    )
    logger.info(response)
    if "assessmentTemplates" in response:
        for template in response["assessmentTemplates"]:
            for user_att in template["userAttributesForFindings"]:
                user_attributes[user_att["key"]] = user_att["value"]

    return user_attributes

def generate_report(run_arn):
    while True:
        response = inspectorClient.get_assessment_report(
            assessmentRunArn=run_arn,
            reportFileFormat="HTML",
            reportType="FULL",
        )
        if "url" in response:
            break
    url = response["url"]
    logger.info(url)
    return url

def download_report(url, user_attributes):
    report_name = user_attributes["AMI_ID"] + "-inspector-report.html"
    temp_file = "/tmp/" + report_name
    
    with urllib.request.urlopen(url=url) as response,  open(temp_file, "wb") as out_file:
        shutil.copyfileobj(response, out_file)
    logger.info(response)

    current_date = dt.now().strftime("%m-%d-%Y")

    report_to_upload = open(temp_file, "rb")
    s3_report_key = current_date + "/" + user_attributes["CommitId"] + "/" + report_name
    s3_response = s3Client.put_object(
        Bucket=reports_bucket,
        Key=s3_report_key,
        Body=report_to_upload,
    )
    logger.info(s3_response)

    s3_report_location = "s3://" + reports_bucket + "/" + s3_report_key
    logger.info("Report Location: %s", s3_report_location)

    return s3_report_location

def notify_scan_completion(ami_id, report_location):
    subject = "Inspector Scan Completion for AMI: " + ami_id
    message = "Scan Results for " + ami_id + " are located at: " + report_location
    response = snsClient.publish(
        TopicArn=notification_topic,
        Message=message,
        Subject=subject,
    )
    logger.info(response)
    return response

def cleanup_scan_resources(stack_name):
    response = cloudformationClient.delete_stack(
        StackName=stack_name,
    )
    return response

def handler(event, context):
    print("Event: %s" % json.dumps(event))
    for record in event["Records"]:
        message = json.loads(record["Sns"]["Message"])
        
    if message["event"] == "ENABLE_ASSESSMENT_NOTIFICATIONS":
        response = { 'message' : "Scan is not complete" }  
    elif message["event"] == "ASSESSMENT_RUN_COMPLETED":
        user_attributes = get_template_user_attributes(assement_template_arn=message["template"])
        report_url = generate_report(run_arn=message["run"])
        report_location = download_report(url=report_url, user_attributes=user_attributes)
        sns_response = notify_scan_completion(ami_id=user_attributes["AMI_ID"], report_location=report_location)
        cleanup_response = cleanup_scan_resources(stack_name=user_attributes["StackName"])
        return cleanup_response

    return response