# Actual version:
# mem_bandwidth: 01: Initial version

service=mem_bandwidth
version=01


cd ./$service

docker login

docker build -t $service .

docker image tag $service macarronesc0lithops/mem_bandwidth_knative:$version

docker image push macarronesc0lithops/mem_bandwidth_knative:$version

cd ..