# Experiment Results

Unfortunately, the experiment could not be completed successfully. Although what was mentioned in the original paper does not correspond to the code shown, it does parallel the downloads from `dnld_blob` and the corresponding function in `runner.py` called `performIO`.

In this case, by doing:
  - The call to the function explicitly (`download_blob_new` or `upload_blob_new`).
  - Download and upload files only from Azure.
Two restrictions that differ from what is mentioned in the paper, if it behaves like a parallel download.

This experiment deals from the point of view, without the use of those specific functions and classes, testing the interceptor by simply calling `boto3` from the worker, which doesn't work.
