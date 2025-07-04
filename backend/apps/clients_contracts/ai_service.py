import requests
import os

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_MODEL = "deepseek-reasoner"

class AIService:
    @staticmethod
    def analyze_contract(contract_text: str) -> dict:
        """Analyze contract text and extract clauses, risks, and obligations."""
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": DEEPSEEK_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a legal AI agent specialized in contract analysis. "
                        "Given a contract text, identify clauses, detect potential risks, summarize obligations, "
                        "and evaluate legal soundness. Highlight anything unusual, missing, or inconsistent. "
                        "Respond clearly and concisely, suitable for both legal and non-legal readers."
                    )
                },
                {
                    "role": "user",
                    "content": contract_text
                }
            ]
        }

        try:
            response = requests.post(DEEPSEEK_API_URL, json=payload, headers=headers)
            response.raise_for_status()
            result = response.json()
            model_reply = result["choices"][0]["message"]["content"]
            return {
                "analysis": model_reply,
                "model_used": "DeepSeek Reasoning Model (Live)"
            }
        except Exception as e:
            raise Exception(f"AI analysis failed: {str(e)}")

    @staticmethod
    def evaluate_contract(contract_text: str) -> dict:
        """Evaluate contract health and return approval status with reasoning."""
        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }
        payload = {
            "model": DEEPSEEK_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You are a legal AI responsible for evaluating the overall health of a contract. "
                        "Given a full contract text, identify whether it meets standard legal expectations. "
                        "Check for clarity, completeness of clauses, risk balance between parties, and enforceability. "
                        "Then answer clearly if the contract should be APPROVED or NOT APPROVED, and explain your reasoning."
                    )
                },
                {
                    "role": "user",
                    "content": contract_text
                }
            ]
        }

        try:
            response = requests.post(DEEPSEEK_API_URL, json=payload, headers=headers)
            response.raise_for_status()
            result = response.json()
            reply = result["choices"][0]["message"]["content"]
            approved = "not approved" not in reply.lower()
            return {
                "approved": approved,
                "reasoning": reply.strip()
            }
        except Exception as e:
            raise Exception(f"Contract evaluation failed: {str(e)}") 