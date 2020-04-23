import boto3
import botocore.exceptions
import logging
import os
import sys

logger = logging.getLogger('Acceptance Test')

cloudformationClient = boto3.client('cloudformation')

stack_output_names = set(["CodePipelineName", "LambdaFunctionName", "NotificationSNS", "ReportsBucket"])

def get_stack_outputs(stack_name):
    outputs = {}
    try:
        response = cloudformationClient.describe_stacks(StackName=stack_name)
        if "Stacks" in response:
            for stack in response["Stacks"]:
                for output in stack["Outputs"]:
                    outputs[output["OutputKey"]] = output["OutputValue"]

        logger.debug(outputs)

        for key in outputs.keys():
            if key in stack_output_names:
                pass
            else:
                raise KeyError
        
        logger.info("Printing Resources to terminal")
        
        for key in outputs.keys():
            logger.info(" %s: %s", key, outputs[key])

        return outputs

    except botocore.exceptions.ClientError:
        logger.error("Invalid stack name Provided, Please provide stack name of your Inspector Pipeline Stack")
        exit(1)

    except KeyError:
        logger.error("Invalid stack name Provided, Please provide stack name of your Inspector Pipeline Stack")
        exit(1)


if __name__== "__main__":
    logging.basicConfig(level=logging.INFO)
    logger.info("Verifying Resources")
    try:
        stack_name = sys.argv[1]
    except IndexError as e:
        logger.error("Please Provide a value for stack_name")
        exit(1)
    
    
    outputs = get_stack_outputs(stack_name=stack_name)