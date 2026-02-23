#!/bin/bash
# Test runner script for lpm-validation

echo "=================================="
echo "Running LPM Validation Tests"
echo "=================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Parse arguments
RUN_UNIT=true
RUN_INTEGRATION=true
RUN_COVERAGE=true
VERBOSE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --unit-only)
            RUN_INTEGRATION=false
            shift
            ;;
        --integration-only)
            RUN_UNIT=false
            shift
            ;;
        --no-coverage)
            RUN_COVERAGE=false
            shift
            ;;
        --verbose|-v)
            VERBOSE=true
            shift
            ;;
        --help|-h)
            echo "Usage: ./run_tests.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --unit-only          Run only unit tests"
            echo "  --integration-only   Run only integration tests"
            echo "  --no-coverage        Skip coverage report"
            echo "  --verbose, -v        Verbose output"
            echo "  --help, -h           Show this help message"
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            echo "Use --help for usage information"
            exit 1
            ;;
    esac
done

# Build pytest command
PYTEST_CMD="pytest"

if [ "$RUN_COVERAGE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD --cov=lpm_validation --cov-report=html --cov-report=term"
fi

if [ "$VERBOSE" = true ]; then
    PYTEST_CMD="$PYTEST_CMD -vv"
else
    PYTEST_CMD="$PYTEST_CMD -v"
fi

# Run tests
if [ "$RUN_UNIT" = true ] && [ "$RUN_INTEGRATION" = true ]; then
    echo "Running all tests..."
    $PYTEST_CMD tests/
    TEST_RESULT=$?
elif [ "$RUN_UNIT" = true ]; then
    echo "Running unit tests only..."
    $PYTEST_CMD tests/unit/
    TEST_RESULT=$?
elif [ "$RUN_INTEGRATION" = true ]; then
    echo "Running integration tests only..."
    $PYTEST_CMD tests/integration/
    TEST_RESULT=$?
fi

echo ""

# Report results
if [ $TEST_RESULT -eq 0 ]; then
    echo -e "${GREEN}✓ All tests passed!${NC}"
    
    if [ "$RUN_COVERAGE" = true ]; then
        echo ""
        echo "Coverage report generated:"
        echo "  HTML: htmlcov/index.html"
    fi
else
    echo -e "${RED}✗ Some tests failed${NC}"
fi

echo ""
echo "=================================="

exit $TEST_RESULT
