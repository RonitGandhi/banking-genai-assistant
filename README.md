# Banking GenAI Conversational Assistant

A production-ready banking conversational AI system built with **Rasa 3.x** and **Google Gemini**, designed for enterprise financial institutions like JPMorgan Chase.

## Features

### Core Banking Capabilities
- **Account Management**: Check balances, view account details, account summaries
- **Transaction Services**: View transaction history, analyze spending patterns, categorize expenses
- **Money Transfers**: Initiate transfers between accounts with form validation
- **Financial Insights**: AI-powered spending analysis using Gemini
- **Security Features**: Fraud reporting, PIN management, account security

### GenAI Integration
- **Gemini-Powered Fallback**: Intelligent responses for unhandled queries with banking context
- **Contextual Conversations**: Maintains conversation history for natural dialogue
- **Spending Analysis**: Uses Gemini to analyze transaction patterns and provide insights
- **Banking Knowledge Base**: Gemini handles general banking questions and FAQs

### Production Features
- **Enhanced NLU Pipeline**: DIET classifier with entity recognition and synonym mapping
- **Voice & Chat Support**: Ready for both text and voice interfaces
- **Form Validation**: Secure multi-step forms for sensitive operations
- **Error Handling**: Comprehensive error handling and logging
- **Latency Optimization**: Efficient model configuration for production

## Architecture

```
User → FastAPI (/chat) → Rasa Server → Action Server → Gemini API
                                      ↓
                                  Custom Actions
                                      ↓
                              Banking Database/API
```

## Quickstart

### 1. Install Dependencies

```bash
conda activate hybrid_gemini_assistant
pip install -r requirements.txt
```

### 2. Set Environment Variables

```bash
export GEMINI_API_KEY="your-api-key-here"
```

Or create a `.env` file:
```
GEMINI_API_KEY=your-api-key-here
```

### 3. Train the Model

```bash
rasa train
```

### 4. Run the Services

**Option A: Streamlit Web Interface (Recommended)**

**Terminal 1 - Action Server:**
```bash
conda activate hybrid_gemini_assistant
rasa run actions
```

**Terminal 2 - Rasa Server:**
```bash
conda activate hybrid_gemini_assistant
rasa run --enable-api
```

**Terminal 3 - Streamlit App:**
```bash
conda activate hybrid_gemini_assistant
streamlit run app/streamlit_app.py
```

Or use the convenience script:
```bash
./run_streamlit.sh
```

Then open your browser at `http://localhost:8501`

**Option B: FastAPI Service (for API usage)**

**Terminal 3 - FastAPI Service:**
```bash
uvicorn app.main:app --reload
```

## Usage Examples

### Check Balance
```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"what is my checking account balance"}'
```

### Get Transactions
```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"show me my recent transactions"}'
```

### Analyze Spending
```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"analyze my spending patterns"}'
```

### Transfer Money
```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"I want to transfer 500 dollars from checking to savings"}'
```

### Banking Questions (Gemini Fallback)
```bash
curl -X POST http://127.0.0.1:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"what is overdraft protection"}'
```

## Banking Intents Supported

- `check_balance` - Check account balances
- `get_transactions` - View transaction history
- `transfer_money` - Transfer funds between accounts
- `analyze_spending` - AI-powered spending analysis
- `ask_about_account` - Account information queries
- `report_fraud` - Fraud reporting
- `request_statement` - Request account statements
- `ask_banking_question` - General banking questions (handled by Gemini)

## Custom Actions

### `action_check_balance`
Retrieves and displays account balance for checking, savings, or credit accounts.

### `action_get_transactions`
Retrieves recent transactions with optional date filtering.

### `action_analyze_spending`
Uses Gemini to analyze spending patterns and provide insights.

### `action_banking_gemini_fallback`
Enhanced fallback with banking context for intelligent responses.

### `transfer_form`
Multi-step form for secure money transfers with validation.

## Production Deployment

### Docker Deployment

```bash
docker build -t banking-chatbot .
docker run --env GEMINI_API_KEY=$GEMINI_API_KEY \
  -p 5005:5005 -p 8000:8000 banking-chatbot
```

### Voice Interface Integration

The system is ready for voice integration through:
- **Twilio Voice**: Use Twilio connector for voice calls
- **Telephony Channels**: Integrate with telephony providers
- **Speech-to-Text**: Use Google Speech-to-Text or AWS Transcribe
- **Text-to-Speech**: Use Google TTS or AWS Polly

### Scaling Considerations

1. **Model Optimization**: Tune DIET epochs and confidence thresholds
2. **Caching**: Implement response caching for common queries
3. **Database Integration**: Replace mock database with real banking APIs
4. **Authentication**: Add user authentication and authorization
5. **Monitoring**: Add logging, metrics, and error tracking
6. **Latency**: Optimize model size and response times

## Extending the System

### Adding New Banking Features

1. **Add Intent**: Update `data/nlu.yml` with examples
2. **Create Action**: Add action in `actions/banking_actions.py`
3. **Update Domain**: Add intent and action to `domain.yml`
4. **Create Stories**: Add conversation flows to `data/stories.yml`
5. **Retrain**: Run `rasa train` to update model

### Integrating with Banking APIs

Replace the mock `BANKING_DB` in `actions/banking_actions.py` with:
- REST API calls to banking backend
- Database queries
- Microservice communication
- Secure authentication tokens

## Security Considerations

- **Authentication**: Implement OAuth2 or JWT authentication
- **PII Handling**: Encrypt sensitive data in transit and at rest
- **Audit Logging**: Log all financial transactions and queries
- **Rate Limiting**: Implement rate limits on API endpoints
- **Input Validation**: Validate all user inputs
- **Compliance**: Ensure PCI-DSS and banking regulations compliance

## Technology Stack

- **Rasa 3.6.x**: NLU and dialogue management
- **Google Gemini**: Generative AI for intelligent responses
- **FastAPI**: High-performance API framework
- **Python 3.10**: Programming language
- **TensorFlow**: ML backend for Rasa models

## Notes

- Replace mock banking database with real API integration
- Add authentication and authorization for production
- Implement proper error handling and logging
- Add monitoring and analytics
- Ensure compliance with banking regulations
- Optimize for latency and response quality
- Consider voice interface optimizations for telephony
