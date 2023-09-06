FROM python:3.11
WORKDIR /codemodder
COPY . .

RUN pip install .
CMD codemodder --help
