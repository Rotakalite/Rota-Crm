#!/bin/bash
# Railway Deploy Optimization Script

echo "🚀 Starting optimized Railway deploy..."

# Set memory limits
export NODE_OPTIONS="--max-old-space-size=4096"

# Clear caches
echo "🧹 Clearing caches..."
rm -rf /app/frontend/node_modules/.cache
rm -rf /app/frontend/.next
rm -rf /app/backend/__pycache__

# Build with optimizations
echo "📦 Building with optimizations..."
cd /app/frontend
yarn cache clean
yarn install --frozen-lockfile --non-interactive

echo "✅ Deploy optimization complete!"
echo "🎯 Use: yarn build:fast for faster builds"