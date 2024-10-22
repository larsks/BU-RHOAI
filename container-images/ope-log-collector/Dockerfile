FROM python:3.12-slim

WORKDIR /

COPY requirements.txt ./

RUN apt-get update && \
    apt-get upgrade -y && \
    apt-get install -y git

RUN pip install -r requirements.txt

RUN pip install git+https://github.com/soamicharan/kubernetes_asyncio.git@fix/rest-api-timeout

COPY . ./

CMD ["python", "collect-logs.py"]
