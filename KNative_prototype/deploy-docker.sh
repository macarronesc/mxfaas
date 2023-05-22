docker login

docker build -t trtest .

docker image tag trtest macarronesc0lithops/trtest:latest

docker image push macarronesc0lithops/trtest:latest