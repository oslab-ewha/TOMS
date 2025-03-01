FROM python:3.9

RUN pip install numpy cryptography

COPY bootstrap.sh /bootstrap.sh
COPY compute_task.py /compute_task.py

CMD ["/bootstrap.sh", "/compute_task.py"]
