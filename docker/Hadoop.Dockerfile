FROM apache/hadoop:3.4.2
RUN sudo apt-get update && sudo apt-get install -y --no-install-recommends python3 && sudo rm -rf /var/lib/apt/lists/*
