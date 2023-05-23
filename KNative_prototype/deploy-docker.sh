# Actual version:
# cnn_serving: 03
# img_res: 01

service=cnn_serving
version=03


cd ./$service

docker login

docker build -t $service .

docker image tag $service macarronesc0lithops/${service}_knative:$version

docker image push macarronesc0lithops/${service}_knative:$version

cd ..