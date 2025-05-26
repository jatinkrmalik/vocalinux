#!/bin/bash

# Build script for static website deployment
echo "🚀 Building Vocalinux website for static deployment..."

# Navigate to web directory
cd "$(dirname "$0")/web" || exit 1

# Install dependencies
echo "📦 Installing dependencies with npm..."
npm install

# Build the static site
echo "🔨 Building static site..."
npm run deploy

# Fix asset paths for relative deployment
echo "🔧 Fixing asset paths..."
cd "$(dirname "$0")" || exit 1
./fix-paths.sh

# Check if build was successful
if [ -d "out" ]; then
    echo "✅ Build successful! Static files are in web/out/"
    echo "📁 Contents of out directory:"
    ls -la out/
    echo ""
    echo "🌐 You can now deploy the 'web/out' directory to any static hosting service"
    echo "📋 For GitHub Pages:"
    echo "   1. Push your changes to GitHub"
    echo "   2. Go to Settings > Pages in your GitHub repository"
    echo "   3. Select 'GitHub Actions' as the source"
    echo "   4. The workflow will automatically deploy your site"
else
    echo "❌ Build failed! Please check the error messages above."
    exit 1
fi
