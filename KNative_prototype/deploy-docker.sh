docker login

docker build -t trtest .

docker image tag trtest USER/trtest:latest

docker image push USER/trtest:latest