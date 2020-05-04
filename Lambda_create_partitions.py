import boto3
import time
from datetime import datetime
from datetime import timedelta

athena = boto3.client('athena')
""" :type : pyboto3.athena """

def lambda_handler(event, context):
    
    dbname = ""　＃Athenaのdatabase名 
    table_name = '' #Athenaのtable名
    result_location = '' #格納するバケット名
    bucket = '' #wafのログが格納されるバケット名
    start = datetime(2020, 5, 1)
    end = datetime(2020, 5, 3)
    
    MAX_RETRY = 10
    
    days = (end - start).days
    for i in range(0, days):
        for j in range(0, 24):
            if j < 10:
                Hstr='0'+str(j)
            else:
                Hstr=str(j)
            
            dt = start + timedelta(days=i)
            
            if dt.day < 10:
                Dstr = '0'+str(dt.day)
            else:
                Dstr = str(dt.day)
                
            if dt.month < 10:
                Mstr = '0'+str(dt.month)
            else:
                Mstr = str(dt.month)
            
            sql = 'ALTER TABLE {} ADD IF NOT EXISTS PARTITION (partition_0={},partition_1={},partition_2={}, partition_3={}) location \'{}\'' \
                .format(table_name, dt.year, Mstr, Dstr, Hstr, bucket + dt.strftime('/%Y/%m/%d/') + Hstr + '/')
        
            query = athena.start_query_execution(
                QueryString=sql,
                QueryExecutionContext={'Database': dbname},
                ResultConfiguration={'OutputLocation': result_location}
            )
            query_execution_id = query['QueryExecutionId']
        
            counter = 1
            while True:
                time.sleep(1)
                query_execution = athena.get_query_execution(QueryExecutionId=query_execution_id)
                state = query_execution['QueryExecution']['Status']['State']
        
                if state == 'SUCCEEDED':
                    print(state + ': ' + sql)
                    break
                elif state == 'FAILED':
                    print(state + ': ' + sql)
                    break
                elif counter >= MAX_RETRY:
                    print('Retry Error: ' + sql)
                    break
                else:
                    counter += 1
                    continue
