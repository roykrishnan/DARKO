import os
from google.cloud import bigquery

os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = '/Users/rohitkrishnan/Desktop/kmedved/api_keys/pristine-nebula-408601-e0808f746e2e.json'
client = bigquery.Client()

query = "SELECT CURRENT_TIMESTAMP()"
query_job = client.query(query)
result = query_job.result()
for row in result:
    print(row)
