# Actual version:
# mem_bandwidth: 
# 01: Initial version
# 02: Test version
# 03: Final version

service=mem_bandwidth
version=03


cd ./$service

docker login

docker build -t $service .

docker image tag $service macarronesc0lithops/mem_bandwidth_knative:$version

docker image push macarronesc0lithops/mem_bandwidth_knative:$version

cd ..