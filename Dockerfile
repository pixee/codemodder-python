FROM python:3.15
WORKDIR /codemodder
COPY . .

RUN pip install .

ENTRYPOINT ["codemodder"]
CMD ["--help"]
