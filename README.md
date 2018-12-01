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


Structure
---------


TODOs
-----
- Dockerization.
- Continue unfinished work after start.
- Use Interest parameters.
- Signature verification.
- A time estimator.
