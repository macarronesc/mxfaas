from mxnet import gluon
import dnld_blob

def lambda_handler():
    start_time = time.time()
    gluon.utils.download('https://azurecloudpublicdataset2.blob.core.windows.net/azurepublicdatasetv2/azurefunctions_dataset2020/azurefunctions-accesses-2020.csv.bz2',path='/tmp/')
    end_time = time.time()

    time = 'Time taken to execute the line: %f seconds' % (end_time - start_time)
    print(time)

    # dnld_blob.download_blob_new(blobName)

    return {"result = ":time}