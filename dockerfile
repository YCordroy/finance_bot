  GNU nano 7.2                                              dockerfile
FROM python:3
RUN apt-get update && \
    apt-get install -y locales && \
    sed -i -e 's/# ru_RU.UTF-8 UTF-8/ru_RU.UTF-8 UTF-8/' /etc/locale.gen && \
    dpkg-reconfigure --frontend=noninteractive locales
ENV LANG ru_RU.UTF-8
ENV LC_ALL ru_RU.UTF-8
WORKDIR /usr/src/app/Finance_bot
COPY . .
RUN pip install --no-cache-dir -r requirements.txt
RUN mkdir workdir
CMD ["python", "./main.py"]
