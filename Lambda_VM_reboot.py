import boto3
from datetime import datetime
 
def lambda_handler(event, context):
    awsRegions = boto3.client('ec2').describe_regions()['Regions']
 
    for region in awsRegions:
        awsregion = region['RegionName']
        ec2 = boto3.resource('ec2', region_name=awsregion)
 
        instances = ec2.instances.all()
        #時間帯に応じてのPriorityを格納
        priority = event['Priority']
        #時間帯に応じてのActionoを格納
        action = event['Action']

 
        start_list = []
        stop_list = []
 
        for i in instances:
            if i.tags != None:
                for t in i.tags:
                    #タグのKeyにEc2StartStop2、Valueに各時間帯のPriorityと一致すれば起動
                    if t['Key'] == 'Ec2StartStop2' and t['Value'] == priority:
                        if action == 'Start' and i.state['Name'] == 'stopped':
                            start_list.append(i.instance_id)
                    #タグのKeyにEc2StartStop2、ValueにPriorityの文字列が含まれていたら停止
                    elif t['Key'] == 'Ec2StartStop2' and priority in t['Value'] :    
                        if action == 'Stop' and i.state['Name'] == 'running':
                            stop_list.append(i.instance_id)
                    #タグのKeyにEc2StartStop2、ValueのStopと一致すれば停止
                    elif t['Key'] == 'Ec2StartStop2' and t['Value'] == action:
                        if action == 'Stop' and i.state['Name'] == 'running':
                            stop_list.append(i.instance_id)
 
        if start_list:
            print('Starting', len(start_list), 'instances', start_list)
            ec2.instances.filter(InstanceIds=start_list).start()
 
        elif stop_list:
            print('Stopping', len(stop_list), 'instances', stop_list)
            ec2.instances.filter(InstanceIds=stop_list).stop()
