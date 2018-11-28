msg: ndn_server/messages/request-msg.proto
	protoc --python_out=. ndn_server/messages/*.proto

clean-db:
	rm -rf ./server_cache.db
	rm -rf ./server_cache
