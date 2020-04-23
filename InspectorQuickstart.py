import boto3
import logging
import os
from time import sleep

class InspectorQuickstart:
    def __init__(self):
        self.logger = logging.getLogger('InspectorQuickstart')
        self.logger.setLevel(logging.DEBUG)
        self.inspectorClient = boto3.client('inspector')
        self.cloudformationClient = boto3.client('cloudformation')
        self.stack_name = os.environ["STACK_NAME"]
        self.commit_id = os.environ["COMMIT_ID"]
        self.topic_arn = os.environ["SNS_TOPIC_ARN"]
        self.full_stack_name = self.stack_name + "-" + self.commit_id
        self.inspector_stack_output = self.get_stack_outputs()
    
    def get_stack_outputs(self):
        outputs = {}
        response = self.cloudformationClient.describe_stacks(StackName=self.full_stack_name)
        self.logger.info(response)
        if "Stacks" in response:
            for stack in response["Stacks"]:
                for output in stack["Outputs"]:
                    outputs[output["OutputKey"]] = output["OutputValue"]

        self.logger.info(outputs)

        return outputs

    def subscribe_to_sns(self):
        response = self.inspectorClient.subscribe_to_event(
            resourceArn=self.inspector_stack_output["AssessmentTemplate"],
            event="ASSESSMENT_RUN_COMPLETED",
            topicArn=self.topic_arn,
        )
        self.logger.info(response)

        return response

    def start_run(self):
        while True:
            try:
                response = self.inspectorClient.start_assessment_run(assessmentTemplateArn=self.inspector_stack_output["AssessmentTemplate"])
                assessment_run_arn = response["assessmentRunArn"]
                self.logger.info(assessment_run_arn)
                break
            except:
                sleep(5)

        return assessment_run_arn