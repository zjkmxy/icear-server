FROM nvidia/cuda:9.0-cudnn7-devel
LABEL maintainer="Xinyu Ma <xinyuma@g.ucla.edu>"

RUN mkdir -p /app
WORKDIR /app
COPY . /app

ENV DEBIAN_FRONTEND noninteractive
RUN apt-get update
RUN apt-get install -y --no-install-recommends apt-utils
RUN apt-get install -y software-properties-common
RUN add-apt-repository ppa:deadsnakes/ppa -y
RUN apt-get update
RUN apt-get install -y git build-essential
RUN apt-get install -y python3.6 python3.6-dev python3-pip python3.6-venv
RUN apt-get install -y libsnappy-dev zlib1g-dev libbz2-dev liblz4-dev libzstd-dev
RUN git clone https://github.com/facebook/rocksdb.git \
    && cd rocksdb \
    && make shared_lib \
    && make install
RUN python3.6 -m pip install pip --upgrade
RUN python3.6 -m pip install -U setuptools
RUN python3.6 -m pip install wheel
RUN python3.6 -m pip install --no-cache-dir -r requirements.txt
ENV LD_LIBRARY_PATH /usr/local/lib:${LD_LIBRARY_PATH}

CMD ["python3.6", "./main.py"]
