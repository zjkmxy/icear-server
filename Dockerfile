FROM python:3.6-stretch

RUN mkdir -p /app
WORKDIR /app
COPY . /app

RUN apt-get update
RUN DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends apt-utils
RUN apt-get install -y git build-essential
RUN apt-get install -y libsnappy-dev zlib1g-dev libbz2-dev liblz4-dev libzstd-dev
RUN git clone https://github.com/facebook/rocksdb.git \
    && cd rocksdb \
    && make shared_lib \
    && make install
RUN pip install --no-cache-dir -r requirements.txt
ENV LD_LIBRARY_PATH /usr/local/lib:${LD_LIBRARY_PATH}

CMD ["python3", "./main.py"]
