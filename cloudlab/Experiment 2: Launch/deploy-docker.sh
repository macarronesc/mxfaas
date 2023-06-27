# Actual version:
# cnn_serving_cloudlab: 01 --> Final version with timers
# img_res_cloudlab: 01 --> Final version with timers
# img_rot_cloudlab: 01 --> Final version with timers
# ml_train_cloudlab: 01 --> Final version with timers
# vid_proc_cloudlab: 01 --> Final version with timers
# web_serve_cloudlab: 01 --> Final version with timers

service=web_serve
version=01


cd ./$service

docker login

docker build -t $service .

docker image tag $service macarronesc0lithops/${service}_cloudlab_knative:$version

docker image push macarronesc0lithops/${service}_cloudlab_knative:$version

cd ..