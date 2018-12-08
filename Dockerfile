FROM zjkmxy/icear-server:base
LABEL maintainer="Xinyu Ma <xinyuma@g.ucla.edu>"

RUN mkdir -p /app
WORKDIR /app
COPY . /app

CMD ["python3.6", "./main.py"]
