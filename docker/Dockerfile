FROM python:3.7
RUN git clone --branch test https://github.com/adaamko/wikt2def/
WORKDIR /wikt2def
RUN pip install -r requirements.txt
CMD ["python" , "service.py"]