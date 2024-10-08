FROM python:3.13
WORKDIR /codemodder
COPY . .

RUN pip install .

ENTRYPOINT ["codemodder"]
CMD ["--help"]
