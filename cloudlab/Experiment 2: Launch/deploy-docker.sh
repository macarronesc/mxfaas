# Actual version:
# cnn_serving_cloudlab: 01 --> Final version with timers

service=cnn_serving
version=01


cd ./$service

docker login

docker build -t $service .

docker image tag $service macarronesc0lithops/${service}_cloudlab_knative:$version

docker image push macarronesc0lithops/${service}_cloudlab_knative:$version

cd ..