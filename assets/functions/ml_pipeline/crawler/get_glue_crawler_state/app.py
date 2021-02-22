import boto3

GLUE = boto3.client('glue')


def lambda_handler(event, context):
    crawler_name = event["crawler_name"]

    crawler_info = GLUE.get_crawler(Name=crawler_name)
    crawler_state = crawler_info['Crawler']['State']

    return {**event, 'crawler_state': crawler_state}
