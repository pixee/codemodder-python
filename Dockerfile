FROM python:3.12
WORKDIR /codemodder
COPY . .

RUN pip install .

ENTRYPOINT ["codemodder"]
CMD ["--help"]
