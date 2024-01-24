FROM quay.io/operate-first/opf-toolbox:v0.8.0

# Create the destination directory
RUN mkdir -p /scripts

# Copy the script to the destination directory
COPY src/python/group-sync/group-sync.py /scripts/

# Set the working directory
WORKDIR /scripts
