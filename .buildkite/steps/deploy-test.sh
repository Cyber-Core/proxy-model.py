#!/bin/bash
set -euo pipefail

wait-for-proxy()
{
  PROXY_URL="$1"

  for i in {1..40}; do
      if curl -s --header "Content-Type: application/json" --data '{"method":"eth_blockNumber","params":[],"id":93,"jsonrpc":"2.0"}' $PROXY_URL > /dev/null;
      then
        echo `date +%H:%M:%S`" proxy is available"
        return 0
      fi
      echo `date +%H:%M:%S`" proxy is unavailable - sleeping"
      sleep 15
  done

  echo `date +%H:%M:%S`" proxy is unavailable - time is over"
  return 9847
}

while getopts t: option; do
case "${option}" in
    t) IMAGETAG=${OPTARG};;
    *) echo "Usage: $0 [OPTIONS]. Where OPTIONS can be:"
       echo "    -t <IMAGETAG>  tag for cybercoredev/proxy Docker-image"
       exit 1;;
esac
done

export REVISION=$(git rev-parse HEAD)
PROXY_IMAGE=cybercoredev/proxy:${IMAGETAG:-$REVISION}

UNISWAP_V2_CORE_IMAGE=cybercoredev/uniswap-v2-core:stable
# Refreshing uniswap-v2-core image is required to run .buildkite/steps/deploy-test.sh locally
docker pull $UNISWAP_V2_CORE_IMAGE

docker-compose -f proxy/docker-compose-test.yml up -d

function cleanup_docker {
    docker logs proxy >proxy.log 2>&1
    docker logs solana >solana.log 2>&1
    grep 'get_measurements' <proxy.log >measurements.log
    echo "Cleanup docker-compose..."
    docker-compose -f proxy/docker-compose-test.yml down
    echo "Cleanup docker-compose done."

    if grep '\[E\] get_measurements' <measurements.log; then
        echo 'Failed to get measurements'
        exit 1
    fi
}
trap cleanup_docker EXIT
sleep 10

export PROXY_URL=http://127.0.0.1:9090/solana

echo "Wait proxy..." && wait-for-proxy "$PROXY_URL"

echo "Run proxy tests..."
docker run --rm -ti --network=host \
     -e PROXY_URL \
     --entrypoint ./proxy/deploy-test.sh \
     ${EXTRA_ARGS:-} \
     $PROXY_IMAGE \

echo "Run uniswap-v2-core tests..."
docker run --rm -ti --network=host \
     --entrypoint ./deploy-test.sh \
     ${EXTRA_ARGS:-} \
     $UNISWAP_V2_CORE_IMAGE \

echo "Run tests return"
exit 0
