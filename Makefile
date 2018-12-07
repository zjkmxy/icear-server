msg: ndn_server/messages/request-msg.proto
	protoc --python_out=. ndn_server/messages/*.proto

clean-db:
	rm -rf ./server_cache.db
	rm -rf ./server_cache

docker_build:
	sudo docker build -t icear-server .

docker_run:
	sudo docker run --runtime=nvidia --name=icear-server1 \
	-v /var/run:/var/run -v $HOME/.ndn:/root/.ndn \
	icear-server
