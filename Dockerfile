FROM prefecthq/prefect:3-python3.13
WORKDIR /
COPY ./requirements.txt /
RUN pip install --no-cache-dir --upgrade -r /requirements.txt