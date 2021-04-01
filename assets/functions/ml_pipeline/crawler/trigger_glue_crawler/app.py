import boto3

GLUE = boto3.client('glue')


def lambda_handler(event, context):
    crawler_name = event["crawler_name"]

    crawler_info = GLUE.get_crawler(Name=crawler_name)
    current_state = crawler_info['Crawler']['State']

    if current_state == 'READY':
        GLUE.start_crawler(Name=crawler_name)
        print("Crawler [{}] started".format(crawler_name))
    else:
        print("Crawler [{}] currently in state [{}], could not trigger a new run.".format(crawler_name, current_state))

    return {**event}
