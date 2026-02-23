#!/bin/bash
# Setup script for lpm-validation

echo "=================================="
echo "LPM Validation Setup"
echo "=================================="
echo ""

# Check Python version
echo "Checking Python version..."
python3 --version
echo ""

# Create virtual environment (optional)
read -p "Create virtual environment? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    echo "Activating virtual environment..."
    source venv/bin/activate
    echo ""
fi

# Install package
echo "Installing lpm-validation package..."
pip install -e .
echo ""

# Verify installation
echo "Verifying installation..."
echo ""
lpm-validation --help
echo ""

echo "=================================="
echo "Setup complete!"
echo "=================================="
echo ""
echo "Next steps:"
echo "1. Configure AWS credentials (aws configure)"
echo "2. Copy config.example.yaml to config.yaml"
echo "3. Edit config.yaml with your S3 bucket and paths"
echo "4. Test connection: lpm-validation --config config.yaml --test-connection"
echo "5. Run collection: lpm-validation --config config.yaml"
echo ""
