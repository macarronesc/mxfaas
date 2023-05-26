from mxnet import gluon
import time

# MxFaaS

start_time = time.time()
lblPath = utils.download('http://data.mxnet.io/models/imagenet/synset.txt', path='/tmp/')
end_time = time.time()

print(f'Time taken to execute the line: {end_time - start_time} seconds')



# Lithops