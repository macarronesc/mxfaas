# Actual version:
# mem_bandwidth: 
# 01: Initial version
# 02: Test version with only 1 download
# 03: Final version with only 1 download
# 04: Final version adding multiple downloads
# 05: Added links from AWS public dataset

service=mem_bandwidth
version=05


cd ./$service

docker login

docker build -t $service .

docker image tag $service macarronesc0lithops/mem_bandwidth_knative:$version

docker image push macarronesc0lithops/mem_bandwidth_knative:$version

cd ..