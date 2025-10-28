#!/bin/bash
# Install dependencies for AdVisor Knowledge Graph + Vector Database

echo "========================================="
echo "AdVisor KG + Vector DB Setup"
echo "========================================="
echo ""

# Check if pip is available
if ! command -v pip &> /dev/null; then
    echo "❌ pip not found. Please install Python and pip first."
    exit 1
fi

echo "✓ pip found"

# Check if requirements.txt exists
if [ ! -f "requirements.txt" ]; then
    echo "❌ requirements.txt not found"
    exit 1
fi

echo "✓ requirements.txt found"
echo ""

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

if [ $? -eq 0 ]; then
    echo ""
    echo "========================================="
    echo "✅ Dependencies installed successfully!"
    echo "========================================="
    echo ""
    echo "Next steps:"
    echo "1. Update .env with your Supabase credentials"
    echo "2. Run SQL schemas in Supabase:"
    echo "   - sql/01_knowledge_graph_schema.sql"
    echo "   - sql/02_vector_database_schema.sql"
    echo "3. Test connection:"
    echo "   python test_supabase.py"
    echo "4. Run examples:"
    echo "   python examples/kg_vector_example.py"
    echo ""
else
    echo ""
    echo "❌ Installation failed. Please check the error messages above."
    exit 1
fi
