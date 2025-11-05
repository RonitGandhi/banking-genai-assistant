#!/bin/bash

# Activate conda environment
source $(conda info --base)/etc/profile.d/conda.sh
conda activate hybrid_gemini_assistant

# Check if GEMINI_API_KEY is set
if [ -z "$GEMINI_API_KEY" ]; then
    echo "⚠️  Warning: GEMINI_API_KEY is not set"
    echo "   Set it with: export GEMINI_API_KEY='your-key-here'"
    echo ""
fi

# Run Streamlit app
echo "🚀 Starting Streamlit Banking Chatbot..."
echo "📱 Open your browser at http://localhost:8501"
echo ""
streamlit run app/streamlit_app.py

