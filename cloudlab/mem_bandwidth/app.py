from mxnet import gluon
import os
import time

def lambda_handler():
    start_time = time.time()

    files = ["/tmp/bach-busoni.tiff", "/tmp/liszt-weinen.tiff", "/tmp/reger-albumblatt.tiff", "/tmp/schubert-marsch.tiff", "/tmp/wagner-lohengrin.tiff"]

    for file in files:
        if os.path.isfile(file):
            os.remove(file)
    
    end_time = time.time()

    # Subtract the time to delete the file (this is not the fault of the original architecture)
    elapsed_time = end_time - start_time
    print(elapsed_time)
    
    gluon.utils.download('https://github.com/Josef-Friedrich/test-files/raw/master/tiff/bach-busoni.tiff',path='/tmp/')
    gluon.utils.download('https://github.com/Josef-Friedrich/test-files/blob/master/tiff/liszt-weinen.tiff',path='/tmp/')
    gluon.utils.download('https://github.com/Josef-Friedrich/test-files/blob/master/tiff/reger-albumblatt.tiff',path='/tmp/')
    gluon.utils.download('https://github.com/Josef-Friedrich/test-files/blob/master/tiff/schubert-marsch.tiff',path='/tmp/')
    gluon.utils.download('https://github.com/Josef-Friedrich/test-files/blob/master/tiff/wagner-lohengrin.tiff',path='/tmp/')

    return {"result = ":elapsed_time}