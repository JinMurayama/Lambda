import json
import boto3
import os
import logging
from urllib.request import Request, urlopen
import re

# Log設定
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# slackの基本情報設定
hockUrl = os.environ["hockUrl"]
slackChannel = os.environ["slackChannel"]

# 評価結果
def get_findingArns(assessmentRunArn):
    client = boto3.client('inspector')

    findingArns = []
    nextToken = ""

    while(True):
        if(nextToken != ""):
            response = client.list_findings(
                assessmentRunArns=[
                    assessmentRunArn,
                ],
                maxResults=500,
                nextToken=nextToken
            )
        else:
            response = client.list_findings(
                assessmentRunArns=[
                    assessmentRunArn,
                ],
                maxResults=500
            )

        if("nextToken" not in response):
            for arn in response["findingArns"]:
                findingArns.append(arn)
            break
        else:
            for arn in response["findingArns"]:
                findingArns.append(arn)
            nextToken = response["nextToken"]

    return findingArns


# main
def lambda_handler(event, context):

    client = boto3.client('inspector')

    # RunArn
    obj = event["Records"][0]["Sns"]["Message"]
    obj = json.loads(obj)
    assessmentRunArn = obj["run"]
    assessmentTemplateArn = assessmentRunArn.rsplit("/", 2)[0]

    # findingArns
    findingArns = get_findingArns(assessmentRunArn)
    size = 100
    output = ""
    describe_findings = []
    findingArns_split = [findingArns[x:x + size] for x in range(0, len(findingArns), size)]
    for findingArns_100 in findingArns_split:
        describe_findings = describe_findings + client.describe_findings(findingArns=findingArns_100, locale='EN_US')["findings"]
    # 脆弱性の詳細内の"severity" = "Informational"以外の条件に合致した内容から以下の項目抜粋
    for finding in describe_findings:
        if finding["severity"] != "Informational": 
            title = finding["title"].replace("  ", "")
            title = title.replace("\n\n", "\n")
            ec2name = finding["assetAttributes"]["hostname"]
            cveid = finding["id"]
            severity = finding["severity"]
            color = decision_color(severity)
            recommendation = finding["recommendation"]
            recommendation = str(recommendation).replace("\t", "")
            recommendation = recommendation.replace("\n", "")
            
            # output = '*ami Id* : ' + str(amiId) + \
            #     '\n *ec2 name* : ' + str(ec2name) + \
            #     '\n *vulnerability id* : ' + str(cveid) + \
            #     '\n *severity* : ' + str(severity) + \
            #     '\n *recommendation* : ' + recommendation
                
            output = '*ec2 name* : ' + str(ec2name) + \
                '\n *vulnerability id* : ' + str(cveid) + \
                '\n *severity* : ' + str(severity) + \
                '\n *recommendation* : ' + recommendation

            post_slack(output, title, color)
            
            output = ""
        
#Slackの発報時の色を決める
def decision_color(severity):

    #highは赤色、lowは青色、mediumは黄色
    if "Low" in severity:
        color = "#4169e1"
    elif "High" in severity:
        color = "#A30100"
    else:
        color = "#DAA038"

    return color

#Slack通知処理
def post_slack(output, title, color):

    # Slack通知設定をセット
    slackMessage = {
        'channel': slackChannel,
        'username':"inspector",
        'attachments': [
    	    {  
    	        "title": title,
    			"color": color,
			    "text": output,
    	    }
        ],
    }


    req = Request(hockUrl, json.dumps(slackMessage).encode('utf-8'), method = "POST")

    # Slackへの通知
    try:
        response = urlopen(req)
        response.read()
        logger.info("Message posted to %s", slackChannel)
    except HTTPError as e:
        logger.error("Request failed: %d %s", e.code, e.reason)
    except URLError as e:
        logger.error("Server connection failed: %s", e.reason)
