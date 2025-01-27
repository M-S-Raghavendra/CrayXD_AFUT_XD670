FROM ubuntu:latest

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-requests-toolbelt \
    ansible \
    vim \
    git \
    curl \
    ipmitool \
    && apt-get clean

WORKDIR /app

COPY . /app

CMD ["/bin/bash"]
