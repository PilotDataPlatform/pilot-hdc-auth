#!/bin/bash
set -e

DOCKER_REGISTRY="docker-registry.ebrains.eu"

SERVICE="auth"
TAG_MESSAGE="$1"
HDC_BRANCH="hdc"

# Check for --help argument to display usage information
if [[ "$1" == "--help" ]]; then
    echo "Usage: $0 [--help]"
    echo "This script automates the process of building and pushing both the auth and alembic docker images."
    echo "You'll need to make sure that the poetry version is patched (it will fail otherwise)."
    echo "You'll also need to pass the message to be used upon creation of the git tag:"
    echo ""
    echo "  ./build_and_push.sh.sh \"Your commit message here\""
    echo ""
    echo "  # Example:"
    echo "  ./build_and_push.sh.sh \"We fixed all the bugs in this latest change.\""
    echo ""
    exit 0
fi

# make sure the git branch is $ENVIRONMENT and is up-to-date
git checkout $HDC_BRANCH
git pull origin $HDC_BRANCH

TAG=$(poetry version -s)

# Ask for user input to get the TAG if not provided
if [ -z "$TAG" ]; then
    read -p "Please provide the tag: " TAG
fi

# Exit with error if TAG is still empty
if [ -z "$TAG" ]; then
    echo "Tag must not be empty."
    exit 1
fi

# Check if the Docker image with the given TAG already exists in the registry
DOCKER_TAG_SERVICE="$DOCKER_REGISTRY/hdc-services-image/$SERVICE:$SERVICE-$TAG"
DOCKER_TAG_ALEMBIC="$DOCKER_REGISTRY/hdc-services-image/$SERVICE:alembic-$TAG"

# Using docker manifest inspect to check if the image exists. Adjust the command if needed based on your registry
if docker manifest inspect $DOCKER_TAG_SERVICE >/dev/null || docker manifest inspect $DOCKER_TAG_ALEMBIC >/dev/null; then
    echo "Docker image with tag $TAG already exists. Please update the poetry version."
    exit 1
fi

# Ask for user input to get a tag message if not provided
if [ -z "$TAG_MESSAGE" ]; then
    read -p "Please provide a tag message: " TAG_MESSAGE
fi

# Exit with error if TAG_MESSAGE is empty
if [ -z "$TAG_MESSAGE" ]; then
    echo "Tag message must not be empty."
    exit 1
fi

# exit with error if there are conflicts
if [[ $(git ls-files -u) ]]; then
    echo "There are merge conflicts. Please resolve them before continuing."
    exit 1
fi

# Build SERVICE image
docker buildx build --target $SERVICE-image --tag $DOCKER_TAG_SERVICE --platform=linux/amd64 --load .

# Build alembic-image
docker buildx build --target alembic-image --tag $DOCKER_TAG_ALEMBIC --platform=linux/amd64 --load .

docker push $DOCKER_TAG_SERVICE
docker push $DOCKER_TAG_ALEMBIC

git tag -a $TAG -m "$TAG_MESSAGE"
git push origin $TAG
