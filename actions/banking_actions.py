import os
import logging
from typing import Any, Dict, List, Text
from datetime import datetime, timedelta
import google.generativeai as genai
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet

# Configure logging
logger = logging.getLogger(__name__)

# Configure Gemini API
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Mock banking database (replace with real API/database)
BANKING_DB = {
    "accounts": {
        "user123": {
            "checking": {"balance": 15234.56, "account_number": "****1234"},
            "savings": {"balance": 45678.90, "account_number": "****5678"},
            "credit": {"balance": -2345.67, "credit_limit": 10000, "account_number": "****9012"}
        }
    },
    "transactions": {
        "user123": [
            {"date": "2025-11-01", "description": "AMAZON PURCHASE", "amount": -45.99, "type": "debit"},
            {"date": "2025-11-02", "description": "SALARY DEPOSIT", "amount": 5000.00, "type": "credit"},
            {"date": "2025-11-03", "description": "STARBUCKS", "amount": -5.50, "type": "debit"},
            {"date": "2025-11-04", "description": "TRANSFER TO SAVINGS", "amount": -500.00, "type": "transfer"},
        ]
    }
}

class ActionBankingGeminiFallback(Action):
    """Enhanced Gemini fallback with banking context"""
    
    def name(self) -> Text:
        return "action_banking_gemini_fallback"
    
    def run(
        self, 
        dispatcher: CollectingDispatcher, 
        tracker: Tracker, 
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        user_msg = tracker.latest_message.get("text", "")
        conversation_history = self._get_conversation_history(tracker)
        
        banking_context = """You are a professional banking assistant for a major financial institution like JPMorgan Chase. 
        You help customers with:
        - Account inquiries (balance, statements, transactions)
        - Transaction history and analysis
        - Transfer requests and payments
        - Credit card information
        - General banking questions
        - Security and fraud prevention
        
        Always be professional, helpful, and security-conscious. Never share sensitive account details unless the user is authenticated.
        Keep responses concise and actionable."""
        
        try:
            model = genai.GenerativeModel("gemini-pro")
            prompt = f"""{banking_context}

Conversation History:
{conversation_history}

User: {user_msg}

Assistant:"""
            
            response = model.generate_content(prompt)
            text = getattr(response, "text", None) or (
                response.candidates[0].content.parts[0].text if response and response.candidates 
                else "I'm here to help with your banking needs. How can I assist you today?"
            )
            dispatcher.utter_message(text=text)
        except Exception as e:
            logger.error(f"Gemini fallback error: {e}")
            dispatcher.utter_message(
                text="I apologize, but I'm having trouble processing that request. "
                     "Please try again or contact customer support at 1-800-XXX-XXXX."
            )
        return []
    
    def _get_conversation_history(self, tracker: Tracker, max_turns: int = 5) -> Text:
        """Extract recent conversation history"""
        events = tracker.events[-max_turns*2:]
        history = []
        for event in events:
            if event.get("event") == "user":
                history.append(f"User: {event.get('text', '')}")
            elif event.get("event") == "bot":
                history.append(f"Assistant: {event.get('text', '')}")
        return "\n".join(history) if history else "No previous conversation."


class ActionCheckBalance(Action):
    """Check account balance"""
    
    def name(self) -> Text:
        return "action_check_balance"
    
    def run(
        self, 
        dispatcher: CollectingDispatcher, 
        tracker: Tracker, 
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        # Try to get account_type from entities first
        account_type = None
        for entity in tracker.latest_message.get("entities", []):
            if entity.get("entity") == "account_type":
                account_type = entity.get("value", "").lower()
                break
        
        # If no entity, try slot
        if not account_type:
            account_type = tracker.get_slot("account_type")
        
        # If still no account_type, try to infer from message text
        if not account_type:
            user_message = tracker.latest_message.get("text", "").lower()
            if "checking" in user_message:
                account_type = "checking"
            elif "savings" in user_message:
                account_type = "savings"
            elif "credit" in user_message:
                account_type = "credit"
            else:
                # Default to checking
                account_type = "checking"
        
        user_id = tracker.sender_id or "user123"  # In production, get from auth
        
        # Mock balance retrieval
        accounts = BANKING_DB["accounts"].get(user_id, {})
        account_data = accounts.get(account_type, {})
        
        if account_data:
            balance = account_data.get("balance", 0)
            account_num = account_data.get("account_number", "****")
            
            if account_type == "credit":
                credit_limit = account_data.get("credit_limit", 0)
                available_credit = credit_limit + balance  # balance is negative
                dispatcher.utter_message(
                    text=f"Your {account_type} account (ending in {account_num}) has a balance of ${abs(balance):,.2f}. "
                         f"Available credit: ${available_credit:,.2f} out of ${credit_limit:,.2f} limit."
                )
            else:
                dispatcher.utter_message(
                    text=f"Your {account_type} account (ending in {account_num}) balance is ${balance:,.2f}."
                )
        else:
            dispatcher.utter_message(
                text=f"I couldn't find your {account_type} account. Please verify your account type."
            )
        
        return []


class ActionGetTransactions(Action):
    """Retrieve recent transactions"""
    
    def name(self) -> Text:
        return "action_get_transactions"
    
    def run(
        self, 
        dispatcher: CollectingDispatcher, 
        tracker: Tracker, 
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        days = tracker.get_slot("days") or 7
        user_id = tracker.sender_id or "user123"
        
        # Mock transaction retrieval
        transactions = BANKING_DB["transactions"].get(user_id, [])
        
        cutoff_date = datetime.now() - timedelta(days=int(days))
        recent_transactions = [
            t for t in transactions 
            if datetime.strptime(t["date"], "%Y-%m-%d") >= cutoff_date
        ]
        
        if recent_transactions:
            transaction_list = "\n".join([
                f"{t['date']}: {t['description']} - ${abs(t['amount']):,.2f} ({t['type']})"
                for t in recent_transactions[:10]  # Limit to 10
            ])
            dispatcher.utter_message(
                text=f"Here are your recent transactions (last {days} days):\n{transaction_list}"
            )
        else:
            dispatcher.utter_message(
                text=f"No transactions found for the last {days} days."
            )
        
        return []


class ActionTransferMoney(Action):
    """Handle money transfers"""
    
    def name(self) -> Text:
        return "action_transfer_money"
    
    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict]:
        # Check if we have all required slots
        amount = tracker.get_slot("transfer_amount")
        from_acc = tracker.get_slot("from_account")
        to_acc = tracker.get_slot("to_account")
        
        if not amount:
            dispatcher.utter_message(text="How much would you like to transfer?")
            return [SlotSet("transfer_amount", None)]
        
        if not from_acc:
            dispatcher.utter_message(text="Which account would you like to transfer from?")
            return []
        
        if not to_acc:
            dispatcher.utter_message(text="Which account should I transfer to?")
            return []
        
        # In production, validate and execute transfer
        try:
            amount_float = float(amount)
            dispatcher.utter_message(
                text=f"Transfer of ${amount_float:,.2f} from {from_acc} to {to_acc} has been initiated. "
                     f"You'll receive a confirmation shortly."
            )
        except ValueError:
            dispatcher.utter_message(text="Please provide a valid amount to transfer.")
            return [SlotSet("transfer_amount", None)]
        
        return [SlotSet("transfer_amount", None), SlotSet("from_account", None), SlotSet("to_account", None)]


class ActionAnalyzeSpending(Action):
    """Analyze spending patterns using Gemini"""
    
    def name(self) -> Text:
        return "action_analyze_spending"
    
    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        user_id = tracker.sender_id or "user123"
        transactions = BANKING_DB["transactions"].get(user_id, [])
        
        # Prepare transaction summary for Gemini
        transaction_summary = "\n".join([
            f"{t['date']}: {t['description']} - ${abs(t['amount']):,.2f}"
            for t in transactions[-20:]  # Last 20 transactions
        ])
        
        try:
            model = genai.GenerativeModel("gemini-pro")
            prompt = f"""Analyze the following banking transactions and provide insights:
            
            Transactions:
            {transaction_summary}
            
            Provide:
            1. Spending categories breakdown
            2. Monthly spending trends
            3. Recommendations for saving money
            4. Any unusual patterns
            
            Keep the response concise and actionable."""
            
            response = model.generate_content(prompt)
            analysis = getattr(response, "text", None) or (
                response.candidates[0].content.parts[0].text if response and response.candidates
                else "Unable to analyze spending at this time."
            )
            
            dispatcher.utter_message(text=analysis)
        except Exception as e:
            logger.error(f"Spending analysis error: {e}")
            dispatcher.utter_message(
                text="I'm having trouble analyzing your spending right now. Please try again later."
            )
        
        return []

