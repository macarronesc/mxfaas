from mxnet import gluon
import os
import time

def lambda_handler():
    start_time = time.time()

    myfile = "/tmp/azurefunctions-accesses-2020.csv.bz2"
    # If file exists, delete it.
    if os.path.isfile(myfile):
        os.remove(myfile)
    
    end_time = time.time()

    # Subtract the time to delete the file (this is not the fault of the original architecture)
    elapsed_time = end_time - start_time
    print(elapsed_time)
    
    gluon.utils.download('https://azurecloudpublicdataset2.blob.core.windows.net/azurepublicdatasetv2/azurefunctions_dataset2020/azurefunctions-accesses-2020.csv.bz2',path='/tmp/')

    return {"result = ":elapsed_time}