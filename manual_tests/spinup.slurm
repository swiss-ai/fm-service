#!/bin/bash
#SBATCH --job-name=sp-apertus-70b-dev-10t
#SBATCH --container-writable
#SBATCH --environment=/capstor/store/cscs/swissai/a09/xyao/llm_service/sp-dev.toml
#SBATCH --time=6:00:00
#SBATCH --ntasks-per-node=1
#SBATCH --account=a-infra02
#SBATCH --dependency=singleton

export NCCL_SOCKET_IFNAME=lo
export GLOO_SOCKET_IFNAME=lo
export PROMETHEUS_MULTIPROC_DIR=/ocfbin/scratch
# export IPFS_LOGGING=debug
export SP_NCCL_SO_PATH=/usr/lib/x86_64-linux-gnu/

# Fetch bootstrap addresses from the API
BOOTSTRAP_RESPONSE=$(curl -s 148.187.108.172:8092/v1/dnt/bootstraps)
echo "Bootstrap response: $BOOTSTRAP_RESPONSE"
# Extract the first bootstrap address from the JSON response
BOOTSTRAP_ADDR=$(echo "$BOOTSTRAP_RESPONSE" | python3 -c "import sys, json; data = json.load(sys.stdin); print(data['bootstraps'][0] if data.get('bootstraps') else '')")

if [ -z "$BOOTSTRAP_ADDR" ]; then
    echo "Error: Could not retrieve bootstrap address from API"
    exit 1
fi

echo "Using bootstrap address: $BOOTSTRAP_ADDR"

/ocfbin/ocf-v2 start --bootstrap.addr "$BOOTSTRAP_ADDR" --subprocess "sp serve /capstor/store/cscs/swissai/infra01/swiss-alignment/checkpoints/Apertus3-70B_iter_858000-tulu3-sft/checkpoint-13446 --served-model-name swissai/apertus3-70b-10T-sft --max-prefill-tokens 8192 --context-length 8192  --tp-size 4 --host 0.0.0.0 --port 8080" --service.name llm --service.port 8080