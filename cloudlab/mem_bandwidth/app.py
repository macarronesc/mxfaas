from mxnet import gluon
import os
import time

def lambda_handler():
    myfile = "/tmp/azurefunctions-accesses-2020.csv.bz2"
    # If file exists, delete it.
    if os.path.isfile(myfile):
        os.remove(myfile)

    start_time = time.time()
    gluon.utils.download('https://azurecloudpublicdataset2.blob.core.windows.net/azurepublicdatasetv2/azurefunctions_dataset2020/azurefunctions-accesses-2020.csv.bz2',path='/tmp/')
    end_time = time.time()

    time = 'Time taken to execute the line: %f seconds' % (end_time - start_time)
    print(time)

    return {"result = ":time}