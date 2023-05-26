# Actual version:
# cnn_serving: 04 --> Only added prints
# cnn_serving: 05 --> Added a single download
# img_res: 01

service=cnn_serving
version=05


cd ./$service

docker login

docker build -t $service .

docker image tag $service macarronesc0lithops/${service}_knative:$version

docker image push macarronesc0lithops/${service}_knative:$version

cd ..