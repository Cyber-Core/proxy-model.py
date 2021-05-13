FROM cybercoredev/solana:latest AS cli

FROM cybercoredev/evm_loader:latest AS spl

FROM ubuntu:20.04

COPY . /opt
WORKDIR /opt

RUN DEBIAN_FRONTEND=noninteractive add-apt-repository universe && \
    apt update && \
    apt -y install \
    software-properties-common \
    openssl \
    ca-certificates \
    curl \
    python3-pip \
    python3-venv && \
    rm -rf /var/lib/apt/lists/*

COPY --from=cli /opt/solana/bin/solana \
                /opt/solana/bin/solana-faucet \
                /opt/solana/bin/solana-keygen \
                /opt/solana/bin/solana-validator \
                /opt/solana/bin/solana-genesis \
                /cli/bin/

COPY --from=spl /opt/solana/bin/solana-deploy /cli/bin/

COPY --from=spl /opt/evm_loader.so /spl/bin/
COPY --from=spl /opt/neon-cli /spl/bin/
COPY --from=spl /opt/neon-cli /spl/bin/emulator

RUN python3 -m venv venv
RUN pip3 install --upgrade pip
RUN /bin/bash -c "source venv/bin/activate"

RUN pip install -r requirements.txt

ENV PATH /venv/bin:/cli/bin/:/spl/bin/:/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin
ENV SOLANA_URL="http://localhost:8899"

EXPOSE 9090/tcp
ENTRYPOINT [ "./proxy/run-proxy.sh" ]
