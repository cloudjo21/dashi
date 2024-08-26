#!/bin/bash
set -e

export GIT_TAG_VERSION=$(git describe --tags --abbrev=0)

aws ecr get-login-password --region YOUR_REGION | docker login --username AWS --password-stdin YOUR_DKR_ECR_ID.dkr.ecr.YOUR_REGION.amazonaws.com/YOUR_REPO_NAME:dashi-nnc
docker tag dashi-nnc:$GIT_TAG_VERSION YOUR_DKR_ECR_ID.dkr.ecr.YOUR_REGION.amazonaws.com/YOUR_REPO_NAME:dashi-nnc-$GIT_TAG_VERSION
docker push YOUR_DKR_ECR_ID.dkr.ecr.YOUR_REGION.amazonaws.com/YOUR_REPO_NAME:dashi-nnc-$GIT_TAG_VERSION

