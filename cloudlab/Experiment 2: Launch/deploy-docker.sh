# Actual version:
# cnn_serving: 01 --> Initial version

service=cnn_serving
version=01


cd ./$service

docker login

docker build -t $service .

docker image tag $service macarronesc0lithops/${service}_knative:$version

docker image push macarronesc0lithops/${service}_knative:$version

cd ..