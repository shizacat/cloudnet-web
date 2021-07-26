FROM ubuntu:20.04

RUN apt-get	update && \
	apt-get install -y --no-install-recommends tzdata vim wget unzip && \
	apt-get install -y --no-install-recommends \
		python3 python3-pip \
	pip3 install --no-cache-dir -r requirements.txt && \
	apt-get remove -y python3-dev build-essential && \
	apt-get -y autoremove && \
	rm -rf /var/lib/apt/lists/*

