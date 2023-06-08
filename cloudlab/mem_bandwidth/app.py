import os
import time
import boto3
from botocore import UNSIGNED
from botocore.config import Config

def lambda_handler():
    start_time = time.time()

    files = ["/tmp/part-17", "/tmp/part-18", "/tmp/part-19", "/tmp/part-20", "/tmp/part-21"]

    for file in files:
        if os.path.isfile(file):
            os.remove(file)
    
    end_time = time.time()

    # Subtract the time to delete the file (this is not the fault of the original architecture)
    elapsed_time = end_time - start_time
    print(elapsed_time)
    
    s3 = boto3.client('s3', config=Config(signature_version=UNSIGNED))

    bucket_name = "gnomad-public-us-east-1"
    bucket_dir = "truth-sets/hail-0.2/1000G.GRCh38.genotypes.20170504.mt/rows/rows/parts/"
    s3.download_file(Filename='part-17', Bucket=bucket_name, Key=bucket_dir + 'part-17')
    s3.download_file(Filename='part-18', Bucket=bucket_name, Key=bucket_dir + 'part-18')
    s3.download_file(Filename='part-19', Bucket=bucket_name, Key=bucket_dir + 'part-19')
    s3.download_file(Filename='part-20', Bucket=bucket_name, Key=bucket_dir + 'part-20')
    s3.download_file(Filename='part-21', Bucket=bucket_name, Key=bucket_dir + 'part-21')
    
    return {"result = ":elapsed_time}