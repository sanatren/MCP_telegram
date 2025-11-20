#!/bin/bash
# Start Gemma Dashboard

# Get script directory
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$DIR"

echo "🌐 Starting Gemma Dashboard..."

# Use conda environment  
export PATH="/opt/homebrew/Caskroom/miniconda/base/bin:$PATH"
source /opt/homebrew/Caskroom/miniconda/base/etc/profile.d/conda.sh
conda activate base

# Start dashboard
python dashboard.py