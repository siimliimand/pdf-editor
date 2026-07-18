#!/bin/bash

# Test script to upload a PDF and verify image positioning

echo "======================================"
echo "Testing PDF Image Position Detection"
echo "======================================"
echo ""

# Check if test PDF exists
TEST_PDF="temp/test_pdfs/1010054315.pdf"

if [ ! -f "$TEST_PDF" ]; then
    echo "Error: Test PDF not found at $TEST_PDF"
    echo "Available PDFs:"
    ls -la temp/test_pdfs/*.pdf 2>/dev/null || echo "  No PDFs found in temp/test_pdfs/"
    exit 1
fi

echo "Using test PDF: $TEST_PDF"
echo ""

# Upload PDF to backend
echo "Uploading PDF to backend..."
echo ""

RESPONSE=$(curl -s -X POST \
  http://localhost:8085/upload \
  -F "file=@$TEST_PDF" \
  -w "\nHTTP_STATUS:%{http_code}")

HTTP_STATUS=$(echo "$RESPONSE" | grep "HTTP_STATUS" | cut -d: -f2)

if [ "$HTTP_STATUS" = "200" ]; then
    echo "✅ Upload successful!"
    echo ""
    echo "Check the uvicorn terminal for debug logs showing:"
    echo "  [Image Matching] messages with position deltas"
    echo ""
else
    echo "❌ Upload failed with status: $HTTP_STATUS"
    echo "Response: $RESPONSE"
fi
