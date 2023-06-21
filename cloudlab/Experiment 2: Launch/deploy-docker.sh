# Actual version:
# cnn_serving_cloudlab: 01 --> Initial version
# cnn_serving_cloudlab: 02 --> Test version

service=cnn_serving_cloudlab
version=02


cd ./$service

docker login

docker build -t $service .

docker image tag $service macarronesc0lithops/${service}_knative:$version

docker image push macarronesc0lithops/${service}_knative:$version

cd ..