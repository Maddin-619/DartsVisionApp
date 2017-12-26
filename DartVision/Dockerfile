FROM jjanzic/docker-python3-opencv:latest

LABEL maintailer="martin.brenner94@gmail.com"

WORKDIR /usr/src/app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY DartVision.py /usr/src/app

CMD [ "python", "./DartVision.py" ]