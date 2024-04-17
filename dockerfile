FROM python:3
WORKDIR /usr/src/app/Finance_bot
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY main.py ./
COPY new_func.py ./
COPY Keyboards.py ./
COPY handlers.py ./
COPY datab.py ./
COPY Create_table.py ./
COPY workdir ./
CMD ["python", "./main.py"]
