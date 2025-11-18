#!/bin/bash
# Example usage script for PHC Q&A System

# Make sure API key is set
if [ -z "$GEMINI_API_KEY" ]; then
    echo "Error: GEMINI_API_KEY environment variable not set"
    echo "Get your API key from: https://makersuite.google.com/app/apikey"
    echo ""
    echo "Usage:"
    echo "  export GEMINI_API_KEY='your-api-key-here'"
    echo "  ./example_usage.sh"
    exit 1
fi

echo "=== Example 1: Single Question ==="
python3 qa_system.py --questions "What is Project Homeless Connect's mission?"

echo ""
echo "=== Example 2: Multiple Questions ==="
python3 qa_system.py --questions "What is PHC's mission?,How many people does PHC serve?,What is the EDC program?"

echo ""
echo "=== Example 3: Questions from File ==="
# Create example questions file
cat > example_questions.txt << EOF
What is Project Homeless Connect's mission?
How many participants did PHC serve in 2024-2025?
What is the Every Day Connect (EDC) program?
What are the Core Senses programs?
EOF

python3 qa_system.py --file example_questions.txt

echo ""
echo "=== Example 4: Save Results to JSON ==="
python3 qa_system.py --questions "What is PHC's mission?" --output answer.json
echo "Results saved to answer.json"

# Cleanup
rm -f example_questions.txt

