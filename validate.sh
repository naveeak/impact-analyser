#!/bin/bash
# Simple deployment test - validates setup without running containers

set -e

echo "Impact Analyzer - Pre-Deployment Validation"
echo "=============================================="
echo ""

# Counter for checks
checks_passed=0
checks_failed=0

# Helper function for checks
check() {
    if eval "$1" > /dev/null 2>&1; then
        echo "✅ $2"
        ((checks_passed++))
    else
        echo "❌ $2"
        ((checks_failed++))
    fi
}

# Helper function for file checks
check_file() {
    if [ -f "$1" ]; then
        echo "✅ $1 exists"
        ((checks_passed++))
    else
        echo "❌ $1 MISSING"
        ((checks_failed++))
    fi
}

# Helper function for directory checks
check_dir() {
    if [ -d "$1" ]; then
        echo "✅ $1/ exists"
        ((checks_passed++))
    else
        echo "❌ $1/ MISSING"
        ((checks_failed++))
    fi
}

echo "Configuration Files:"
check_file ".env"
check_file "docker-compose.yml"
check_file ".env.example"

echo ""
echo "Dockerfiles:"
check_file "services/repository-scanner/Dockerfile"
check_file "services/impact-analyzer/Dockerfile"
check_file "services/ai-orchestrator/Dockerfile"

echo ""
echo "Source Code:"
check_file "services/repository-scanner/src/main.py"
check_file "services/impact-analyzer/src/main.py"
check_file "services/ai-orchestrator/src/main.py"

echo ""
echo "Requirements:"
check_file "services/repository-scanner/requirements.txt"
check_file "services/impact-analyzer/requirements.txt"
check_file "services/ai-orchestrator/requirements.txt"

echo ""
echo "Documentation:"
check_file "README.md"
check_file "API_REFERENCE.md"
check_file "DEPLOYMENT_GUIDE.md"
check_file "QUICK_REFERENCE.md"

echo ""
echo "Directories:"
check_dir "services/repository-scanner"
check_dir "services/impact-analyzer"
check_dir "services/ai-orchestrator"
check_dir "config"
check_dir "tests"

echo ""
echo "=============================================="
echo "Validation Summary"
echo "=============================================="
echo "✅ Passed: $checks_passed"
echo "❌ Failed: $checks_failed"
echo ""

if [ $checks_failed -eq 0 ]; then
    echo "🎉 All checks passed! Ready to deploy."
    echo ""
    echo "Next steps:"
    echo "1. Review .env configuration"
    echo "2. Run: docker-compose up -d"
    echo "3. Wait 30 seconds for services to start"
    echo "4. Test: curl http://localhost:8001/health"
    exit 0
else
    echo "⚠️  Please fix missing files before deploying."
    exit 1
fi
