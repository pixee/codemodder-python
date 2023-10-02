FROM python:3.11
WORKDIR /codemodder
COPY . .

# Install Rust (temporary workaround for libcst dependency)
RUN apt-get update && \
    apt-get install -y curl && \
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y && \
    apt-get remove -y curl && \
    apt-get autoremove -y && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*
ENV PATH="/root/.cargo/bin:${PATH}"

RUN pip install .

ENTRYPOINT ["codemodder"]
CMD ["--help"]
