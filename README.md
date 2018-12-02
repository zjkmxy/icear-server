IceAR Server
============================================
IceAR Server is the cloud calculation module for IceAR project.

Prerequisites
-------------
- Required: Python 3.5 or later
- Required: Protobuf
- Required: Python packages in requirements.txt.

Usage
-----
- Compile protobuf message
```bash
make msg
```
- Start server
Make sure model files are there before start.
```bash
./main.py
```
Start parameters are in `config.py`.
- Use examples to test
```bash
examples/test_producer.py
./main.py
examples/test_trigger.py
examples/test_consumer.py
```
- Clean up database
```bash
make clean-db
```

Protocol
--------
Command Interest:
```text
Name: <server-prefix>/calc/<Parameters>
Parameters format:
name: The prefix of frames.
start_frame: Start frame number.
end_frame: End frame number.
operations: List of operations.
```

The format of frames follows generalized-object:
```text
MetaInfo: <frame-prefix>/<frame-no>/_meta
FrameImageSegments: <frame-prefix>/<frame-no>/<segment-no>
```

The format of results also follows generalized-object:
```text
MetaInfo: <server-prefix>/result/<frame-prefix>/<frame-no>/<operation>/_meta
Segments: <server-prefix>/result/<frame-prefix>/<frame-no>/<operation>/<segment-no>
```

Results with a status code will be:
```text
RetCode: The status code.
RetryAfter[optional]: Milliseconds estimated before operations are finished.
```

Results with status code can be sent in the following cases:
```text
1. A Data packet replying to a Command Interest.
2. An application NACK replying to a result Interest. 
   In this case, the consumer must test if the reply is NACK or Data.
```

Result codes:

Codes | Value | Meaning
--- | --- | ---
RET_RETRY_AFTER | 100 | Request exists, but not finished yet.
RET_OK | 200 | Request succeeded.
RET_NO_REQUEST | 400 | No such request for specified frame & process.
RET_NOT_SUPPORTED | 401 | Operation is not supported.
RET_EXECUTION_FAILED | 402 | The execution failed.
RET_NO_INPUT | 403 | Cannot fetch specified frame.
RET_MALFORMED_COMMAND | 404 | Malformed command.

(To be continued...)

Structure
---------

The application contains 4 parts: server, fetcher, storage and workers.
```text
                +---------+
                | Server  |
                +---------+
                     |
     +---------------+---------------+
     |               |               |
+---------+     +---------+     +---------+
| Fetcher | ==> | Storage | <== | Workers |
+---------+     +---------+     +---------+
     |               |
+---------+     +---------+
| PyNDN2  |     | rocksdb |
+---------+     +---------+
```

### Storage
The storage is a thread-safe key-value database.
All frames, results and status data are stored here.
The storage is not a repo.
If there is no sufficient space, the storage can erase any data. (not implemented)
When the program starts, it first loads all status from the storage and
try to restore unfinished work. (not implemented)

### Workers
There are two workers, deeplab and fast-style-transfer.
Workers are serving in their own threads, getting requests from a Queue and process them one by one.
The server can specify the number of threads and GPU id for each thread.

### Fetcher
The fetcher gets fetch request from the server, tries to fetch frames, 
assembles segments and tells the server the result, whether success or failure.
To simplify the flow, the fetcher assigns a coroutine for each frame.

### Server
The server watches on Interests and satisfies them.
It coordinates the fetcher and the workers by assigning work 
and receiving notifications via callbacks.


TODOs
-----
- Dockerization (current Dockerfile cannot work).
- Continue unfinished work after start.
- Use Interest parameters.
- Signature verification.
- A time estimator.
