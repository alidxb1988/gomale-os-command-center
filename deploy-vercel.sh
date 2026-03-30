#!/bin/bash
# Deploy GOMALE OS to Vercel

echo "🚀 GOMALE OS Vercel Deployment"
echo "=============================="

# Check if already logged in
if ! vercel whoami > /dev/null 2>&1; then
    echo ""
    echo "❌ Not logged in to Vercel"
    echo ""
    echo "To deploy, you need to:"
    echo "1. Get a Vercel token from https://vercel.com/account/tokens"
    echo "2. Run: export VERCEL_TOKEN=your_token_here"
    echo "3. Run this script again"
    echo ""
    echo "Or login interactively:"
    echo "  vercel login"
    exit 1
fi

echo "✅ Logged in as: $(vercel whoami)"
echo ""
echo "Deploying..."

# Deploy
vercel deploy --prod --yes

echo ""
echo "✅ Deployment complete!"
