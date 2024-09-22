#!/bin/bash

target="127.0.0.1:5000"

echo "extract without post:"
curl $target/extract

echo ""
echo ""
echo "extract without file:"
curl -X POST $target/extract

echo ""
echo ""
echo "extract with file:"
curl -X POST $target/extract -F "file=@test.sh"

echo ""
echo ""
echo "extract with filename and image:"
curl -X POST $target/extract -F "file=@test.pdf" -F "use_image=1"

echo ""
