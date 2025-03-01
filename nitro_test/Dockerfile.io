FROM python:3.9

RUN pip install requests pandas

COPY bootstrap.sh /bootstrap.sh
COPY io_task.py /io_task.py

CMD ["/bootstrap.sh", "/io_task.py"]
