#!/bin/bash
# Lambda용 zip 자동 생성 (arm64) - zip 바이너리 없이 Python으로 압축
set -e

ZIP_NAME="publisher.zip"
BUILD_DIR="build"
IMAGE="public.ecr.aws/lambda/python:3.12-arm64"

echo "🧹 Clean up..."
rm -rf "$BUILD_DIR" "$ZIP_NAME"

echo "🐳 Building inside Docker..."
docker run --rm \
  --entrypoint /bin/bash \
  -v "$PWD":/var/task \
  -w /var/task \
  "$IMAGE" \
  -lc "
    set -e
    python -m pip install --upgrade pip
    mkdir -p $BUILD_DIR
    pip install fastapi requests mangum python-dotenv -t $BUILD_DIR
    cp -r app $BUILD_DIR/
    python - <<'PY'
import os, zipfile
zip_path = 'publisher.zip'
with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as z:
    for root, _, files in os.walk('build'):
        for f in files:
            p = os.path.join(root, f)
            z.write(p, os.path.relpath(p, 'build'))
print('✅ created', zip_path)
PY
  "

echo "✅ Done: $ZIP_NAME"