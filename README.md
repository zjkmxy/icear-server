IceAR Server
============================================
IceAR Server is the cloud calculation module for IceAR project.

Prerequisites
-------------
- Required: Python 3.5 or later
- Required: Protobuf
- Required: Python packages in requirements.txt.
- Required: [NFD](https://named-data.net/doc/NFD/current/INSTALL.html) should be installed and started.

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
An overview is like this:
```text
Requester     Server             Repo
    |           |                 |
    |  Command  |                 |
    |---------->|                 |
    | Response  |                 |
    |<----------|    Interest     |
    |           |---------------->|
    |           |  Frame Data     |
    |           |<----------------|
    |        +--+----+            |
    |        |Process| Interest   |
    |        |       |----------->|
    |        |  in   |Frame Data  |
    |        |       |<-----------|
    |        |  GPU  |   .....    |
    |        +-------+            |
    |        |       |            |
    |        +-------+            |
    |Interest|       |            |
    |------->|       |            |
    | Retry  +-------+            |
    | After  |       |
    |<-------+-------+
    |        |       |
    |        +--+----+
    |           |
    | Interest  |
    |---------->|
    |Result Data|
    |<----------|
```
The requester sends an Interest to trigger the calculation on server.
The server responses with an estimated time, and then starts fetching frames from the repo.
Whenever a frame arrives, the server performs specified operations on it.
GPU computations and frames fetching are done simultaneously.
The requester can send Interests for results at any time.
If the result is not ready yet, the server sends an application NACK back,
carrying a RetryAfter field which is the estimated remaining time.
If the result is ready, the server sends the data back.
Frame data and result data can be segmented.


Command Interests are in the following format:
```text
Name:
  <server-prefix>/calc/<Parameters>

Parameters format:
  name: The prefix of frames.
  start_frame: Start frame number.
  end_frame: End frame number.
  operations: List of operations.
```

The name of frames follows generalized-object namespace:
```text
Names: 
  Prefix: <frame-prefix>/<frame-no>
  MetaInfo: <frame-prefix>/<frame-no>/_meta
  FrameImageSegments: <frame-prefix>/<frame-no>/<segment-no>
```

The name of results also follows generalized-object:
```text
Names:
  Prefix: <server-prefix>/result/<frame-prefix>/<frame-no>/<operation>
  MetaInfo: <server-prefix>/result/<frame-prefix>/<frame-no>/<operation>/_meta
  Segments: <server-prefix>/result/<frame-prefix>/<frame-no>/<operation>/<segment-no>
```

Results with status code can be sent in the following cases:
```text
1. A Data packet replying to a Command Interest.
2. An application NACK replying to a result Interest. 
   In this case, the consumer must test if the reply is NACK or Data.
```

Results with a status code carry the following data:
```text
RetCode: The status code.
RetryAfter[optional]: Milliseconds estimated before operations are finished.
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

TLV Type Encoding Number:

Type | Number
--- | ---
Model | 200
FLags | 201
Operation | 203
Start frame id | 220
End frame id | 221
Operations list | 222
Command interest | 210
Return code | 230
Retry after | 231
Response with code | 211

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
- Continue unfinished work after start.
- Use Interest parameters.
- Signature verification.
- A time estimator.
