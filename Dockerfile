FROM python:3.11
WORKDIR /codemodder
COPY . .

RUN pip install .

ENTRYPOINT ["codemodder"]
CMD ["--help"]
