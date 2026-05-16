#!/usr/bin/env bash
# build_and_push.sh
# Builds the Docker image and pushes it to Docker Hub.
#
# Usage:
#   ./build_and_push.sh              # builds & pushes :latest
#   ./build_and_push.sh 1.0.0        # builds & pushes :1.0.0 AND :latest

set -euo pipefail

DOCKER_USER="rodro167"
IMAGE_NAME="restmovies"
FULL_IMAGE="${DOCKER_USER}/${IMAGE_NAME}"
TAG="${1:-latest}"

echo "==> Building ${FULL_IMAGE}:${TAG} ..."
docker build -t "${FULL_IMAGE}:${TAG}" .

# Always tag as latest as well (unless we're already building latest)
if [ "${TAG}" != "latest" ]; then
  docker tag "${FULL_IMAGE}:${TAG}" "${FULL_IMAGE}:latest"
fi

echo "==> Pushing ${FULL_IMAGE}:${TAG} ..."
docker push "${FULL_IMAGE}:${TAG}"

if [ "${TAG}" != "latest" ]; then
  echo "==> Pushing ${FULL_IMAGE}:latest ..."
  docker push "${FULL_IMAGE}:latest"
fi

echo ""
echo "Done! Image available at:"
echo "  docker pull ${FULL_IMAGE}:${TAG}"
