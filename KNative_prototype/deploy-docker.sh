# Actual version:
# cnn_serving: 01 --> Final version with timers
# img_res: 01 --> Final version with timers
# img_rot: 01 --> Final version with timers
# ml_train: 01 --> Final version with timers
# vid_proc: 01 --> Final version with timers
# web_serve: 01 --> Final version with timers

service=web_serve
version=01


cd ./$service

docker login

docker build -t $service .

docker image tag $service macarronesc0lithops/${service}_knative:$version

docker image push macarronesc0lithops/${service}_knative:$version

cd ..