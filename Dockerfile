FROM python:3.11
COPY requirements/codemodder.txt .
RUN pip install -r codemodder.txt
WORKDIR /codemodder
COPY . .
CMD python -m codemodder --help
