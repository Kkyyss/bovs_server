FROM python:3.6.4

RUN mkdir -p /home/project/bovs
WORKDIR /home/project/bovs
COPY requirements.txt /home/project/bovs
RUN pip install --no-cache-dir -r requirements.txt

COPY . /home/project/bovs
