import os
from google.cloud import bigquery

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = 'DONT LEAK THIS'
client = bigquery.Client()

query = "SELECT CURRENT_TIMESTAMP()"
query_job = client.query(query)
result = query_job.result()
for row in result:
    print(row)
