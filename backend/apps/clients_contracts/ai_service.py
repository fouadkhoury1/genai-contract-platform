import requests
import os
import time
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
import concurrent.futures
import re
import json

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"
DEEPSEEK_MODEL = "deepseek-reasoner"

# Configure retry strategy
retry_strategy = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
)

adapter = HTTPAdapter(max_retries=retry_strategy)
session = requests.Session()
session.mount("https://", adapter)
session.mount("http://", adapter)

class AIService:
    @staticmethod
    def test_api_connection() -> bool:
        """Test if the DeepSeek API is accessible."""
        try:
            headers = {
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": DEEPSEEK_MODEL,
                "messages": [
                    {
                        "role": "user",
                        "content": "Hello"
                    }
                ],
                "max_tokens": 10
            }
            
            response = session.post(DEEPSEEK_API_URL, json=payload, headers=headers, timeout=10)
            
            if response.status_code == 200:
                return True
            else:
                return False
                
        except Exception as e:
            return False

    @staticmethod
    def analyze_contract(contract_text: str) -> dict:
        """Analyze contract text and extract clauses, risks, and obligations."""
        def chunk_text(text, chunk_size=20000):
            return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }

        if len(contract_text) > 50000:
            chunks = chunk_text(contract_text, 20000)
            all_analyses = []
            errors = []

            def process_chunk(idx_chunk):
                idx, chunk = idx_chunk
                payload = {
                    "model": DEEPSEEK_MODEL,
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "You are a legal AI agent specialized in contract analysis. "
                                "Given a contract text, identify clauses, detect potential risks, summarize obligations, "
                                "and evaluate legal soundness. Highlight anything unusual, missing, or inconsistent. "
                                "Respond clearly and concisely, suitable for both legal and non-legal readers. "
                                "Note: This is part of a larger contract, focus on analyzing this section."
                            )
                        },
                        {
                            "role": "user",
                            "content": chunk
                        }
                    ]
                }

                try:
                    response = session.post(DEEPSEEK_API_URL, json=payload, headers=headers, timeout=60)
                    response.raise_for_status()
                    result = response.json()
                    return (result["choices"][0]["message"]["content"], None)
                except requests.exceptions.Timeout:
                    return (None, f"Chunk {idx+1}: Request timed out")
                except requests.exceptions.ConnectionError:
                    return (None, f"Chunk {idx+1}: Connection error")
                except Exception as e:
                    return (None, f"Chunk {idx+1}: {str(e)}")

            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                results = list(executor.map(process_chunk, enumerate(chunks)))

            for analysis, error in results:
                if analysis:
                    all_analyses.append(analysis)
                if error:
                    errors.append(error)

            if not all_analyses:
                return {
                    "analysis": "Contract analysis failed: No successful chunk analyses.",
                    "model_used": "Fallback Response"
                }

            # Combine all analyses
            combined_analysis = "\n\n".join([
                f"Section {i+1} Analysis:\n{analysis}"
                for i, analysis in enumerate(all_analyses)
            ])

            return {
                "analysis": combined_analysis,
                "model_used": "DeepSeek Reasoning Model (Live) - Chunked Analysis"
            }
        else:
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
                response = session.post(DEEPSEEK_API_URL, json=payload, headers=headers, timeout=60)
                response.raise_for_status()
                result = response.json()
                model_reply = result["choices"][0]["message"]["content"]
                return {
                    "analysis": model_reply,
                    "model_used": "DeepSeek Reasoning Model (Live)"
                }
            except requests.exceptions.Timeout:
                return {
                    "analysis": "Contract analysis temporarily unavailable due to network timeout. Please try again later.",
                    "model_used": "Fallback Response"
                }
            except requests.exceptions.ConnectionError as e:
                return {
                    "analysis": "Contract analysis temporarily unavailable due to connection issues. Please try again later.",
                    "model_used": "Fallback Response"
                }
            except Exception as e:
                return {
                    "analysis": f"Contract analysis failed: {str(e)}. Please try again later.",
                    "model_used": "Fallback Response"
                }

    @staticmethod
    def extract_clauses(contract_text: str) -> dict:
        """Extract and classify contract clauses with metadata. Use deepseek-chat (V3-0324) for speed."""
        print(f"[DEBUG] extract_clauses: contract_text length = {len(contract_text) if contract_text else 0}")
        def chunk_text(text, chunk_size=20000):
            return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }
        CHAT_MODEL = "deepseek-chat"  # Fastest model per DeepSeek docs

        if len(contract_text) > 50000:
            chunks = chunk_text(contract_text, 20000)
            all_clauses = []
            errors = []
            def process_chunk(idx_chunk):
                idx, chunk = idx_chunk
                payload = {
                    "model": CHAT_MODEL,
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "You are a legal AI specialized in contract clause extraction and classification. "
                                "Given a contract text, extract all clauses and classify them by type. "
                                "For each clause, provide: type, content, risk_level (low/medium/high), and obligations. "
                                "Return ONLY a valid JSON array with this structure:\n"
                                "[\n"
                                "  {\n"
                                "    \"type\": \"clause_type\",\n"
                                "    \"content\": \"full clause text\",\n"
                                "    \"risk_level\": \"low|medium|high\",\n"
                                "    \"obligations\": [\"obligation1\", \"obligation2\"]\n"
                                "  }\n"
                                "]\n"
                                "Common clause types: Termination, Payment Terms, Liability, Confidentiality, "
                                "Intellectual Property, Force Majeure, Dispute Resolution, Non-Compete, "
                                "Data Protection, Service Level Agreement, etc."
                            )
                        },
                        {
                            "role": "user",
                            "content": chunk
                        }
                    ]
                }
                try:
                    print(f"[DEBUG] [Chunk {idx+1}/{len(chunks)}] Sending request to DeepSeek...")
                    response = session.post(DEEPSEEK_API_URL, json=payload, headers=headers, timeout=120)
                    print(f"[DEBUG] [Chunk {idx+1}] DeepSeek HTTP status: {response.status_code}")
                    response.raise_for_status()
                    result = response.json()
                    print(f"[DEBUG] [Chunk {idx+1}] DeepSeek raw response: {result}")
                    model_reply = result["choices"][0]["message"]["content"]
                    print(f"[DEBUG] [Chunk {idx+1}] DeepSeek model_reply: {model_reply[:500]}... (truncated)")
                    clauses = json.loads(model_reply)
                    if isinstance(clauses, list):
                        return (clauses, None)
                    else:
                        return ([], f"Chunk {idx+1}: Response is not a list")
                except json.JSONDecodeError as e:
                    print(f"[DEBUG] [Chunk {idx+1}] JSONDecodeError: {str(e)}")
                    print(f"[DEBUG] [Chunk {idx+1}] model_reply: {model_reply[:500]}... (truncated)")
                    return ([], f"Chunk {idx+1}: JSONDecodeError: {str(e)}")
                except requests.exceptions.Timeout as e:
                    print(f"[DEBUG] [Chunk {idx+1}] Timeout: {str(e)}")
                    return ([], f"Chunk {idx+1}: Request timed out")
                except requests.exceptions.ConnectionError as e:
                    print(f"[DEBUG] [Chunk {idx+1}] ConnectionError: {str(e)}")
                    return ([], f"Chunk {idx+1}: Connection error")
                except Exception as e:
                    print(f"[DEBUG] [Chunk {idx+1}] Exception: {str(e)}")
                    return ([], f"Chunk {idx+1}: {str(e)}")
            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                results = list(executor.map(process_chunk, enumerate(chunks)))
            for clauses, error in results:
                all_clauses.extend(clauses)
                if error:
                    errors.append(error)
            print(f"[DEBUG] All chunk errors: {errors}")
            return {
                "clauses": all_clauses,
                "clause_count": len(all_clauses),
                "model_used": CHAT_MODEL,
                "error": "; ".join(errors) if errors else None
            }
        else:
            payload = {
                "model": CHAT_MODEL,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "You are a legal AI specialized in contract clause extraction and classification. "
                            "Given a contract text, extract all clauses and classify them by type. "
                            "For each clause, provide: type, content, risk_level (low/medium/high), and obligations. "
                            "Return ONLY a valid JSON array with this structure:\n"
                            "[\n"
                            "  {\n"
                            "    \"type\": \"clause_type\",\n"
                            "    \"content\": \"full clause text\",\n"
                            "    \"risk_level\": \"low|medium|high\",\n"
                            "    \"obligations\": [\"obligation1\", \"obligation2\"]\n"
                            "  }\n"
                            "]\n"
                            "Common clause types: Termination, Payment Terms, Liability, Confidentiality, "
                            "Intellectual Property, Force Majeure, Dispute Resolution, Non-Compete, "
                            "Data Protection, Service Level Agreement, etc."
                        )
                    },
                    {
                        "role": "user",
                        "content": contract_text
                    }
                ]
            }
            try:
                print("[DEBUG] Sending request to DeepSeek for clause extraction...")
                response = session.post(DEEPSEEK_API_URL, json=payload, headers=headers, timeout=120)
                print(f"[DEBUG] DeepSeek HTTP status: {response.status_code}")
                response.raise_for_status()
                result = response.json()
                print(f"[DEBUG] DeepSeek raw response: {result}")
                model_reply = result["choices"][0]["message"]["content"]
                print(f"[DEBUG] DeepSeek model_reply: {model_reply[:500]}... (truncated)")
                clauses = json.loads(model_reply)
                if not isinstance(clauses, list):
                    raise ValueError("Response is not a list")
                return {
                    "clauses": clauses,
                    "clause_count": len(clauses),
                    "model_used": CHAT_MODEL
                }
            except json.JSONDecodeError as e:
                print(f"[DEBUG] JSONDecodeError: {str(e)}")
                print(f"[DEBUG] model_reply: {model_reply[:500]}... (truncated)")
                # Try to recover partial clauses using regex
                clause_pattern = re.compile(r'\{[^\{\}]*\}')
                matches = clause_pattern.findall(model_reply)
                partial_clauses = []
                for m in matches:
                    try:
                        obj = json.loads(m)
                        partial_clauses.append(obj)
                    except Exception as ex:
                        continue
                if partial_clauses:
                    return {
                        "clauses": partial_clauses,
                        "clause_count": len(partial_clauses),
                        "error": f"Partial extraction: {str(e)}",
                        "raw_response": model_reply,
                        "model_used": CHAT_MODEL
                    }
                return {
                    "clauses": [],
                    "clause_count": 0,
                    "error": f"Failed to parse AI response as JSON: {str(e)}",
                    "raw_response": model_reply,
                    "model_used": CHAT_MODEL
                }
            except requests.exceptions.Timeout as e:
                return {
                    "clauses": [],
                    "clause_count": 0,
                    "error": "Clause extraction temporarily unavailable due to network timeout.",
                    "model_used": "Fallback Response"
                }
            except requests.exceptions.ConnectionError as e:
                return {
                    "clauses": [],
                    "clause_count": 0,
                    "error": "Clause extraction temporarily unavailable due to connection issues.",
                    "model_used": "Fallback Response"
                }
            except Exception as e:
                print(f"[DEBUG] Exception in extract_clauses: {str(e)}")
                raise

    @staticmethod
    def evaluate_contract(contract_text: str) -> dict:
        """Evaluate contract health and return approval status with reasoning."""
        def chunk_text(text, chunk_size=20000):
            return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

        headers = {
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }

        if len(contract_text) > 50000:
            chunks = chunk_text(contract_text, 20000)
            all_evaluations = []
            errors = []

            def process_chunk(idx_chunk):
                idx, chunk = idx_chunk
                payload = {
                    "model": DEEPSEEK_MODEL,
                    "messages": [
                        {
                            "role": "system",
                            "content": (
                                "You are a legal AI responsible for evaluating the overall health of a contract. "
                                "Given a contract text section, identify whether it meets standard legal expectations. "
                                "Check for clarity, completeness of clauses, risk balance between parties, and enforceability. "
                                "Note: This is part of a larger contract, focus on evaluating this section. "
                                "Identify any issues that would make this section NOT APPROVED."
                            )
                        },
                        {
                            "role": "user",
                            "content": chunk
                        }
                    ]
                }

                try:
                    response = session.post(DEEPSEEK_API_URL, json=payload, headers=headers, timeout=60)
                    response.raise_for_status()
                    result = response.json()
                    reply = result["choices"][0]["message"]["content"]
                    approved = "not approved" not in reply.lower()
                    return ({
                        "approved": approved,
                        "reasoning": reply.strip()
                    }, None)
                except requests.exceptions.Timeout:
                    return (None, f"Chunk {idx+1}: Request timed out")
                except requests.exceptions.ConnectionError:
                    return (None, f"Chunk {idx+1}: Connection error")
                except Exception as e:
                    return (None, f"Chunk {idx+1}: {str(e)}")

            with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
                results = list(executor.map(process_chunk, enumerate(chunks)))

            for evaluation, error in results:
                if evaluation:
                    all_evaluations.append(evaluation)
                if error:
                    errors.append(error)

            if not all_evaluations:
                return {
                    "approved": False,
                    "reasoning": "Contract evaluation failed: No successful chunk evaluations."
                }

            # If any section is not approved, the whole contract is not approved
            approved = all(eval["approved"] for eval in all_evaluations)
            
            # Combine all evaluations
            combined_reasoning = "\n\n".join([
                f"Section {i+1} Evaluation:\n{eval['reasoning']}"
                for i, eval in enumerate(all_evaluations)
            ])

            if errors:
                combined_reasoning += f"\n\nWarning: Some sections had errors: {'; '.join(errors)}"

            return {
                "approved": approved,
                "reasoning": combined_reasoning
            }
        else:
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
                response = session.post(DEEPSEEK_API_URL, json=payload, headers=headers, timeout=60)
                response.raise_for_status()
                result = response.json()
                reply = result["choices"][0]["message"]["content"]
                approved = "not approved" not in reply.lower()
                return {
                    "approved": approved,
                    "reasoning": reply.strip()
                }
            except requests.exceptions.Timeout:
                return {
                    "approved": False,
                    "reasoning": "Contract evaluation temporarily unavailable due to network timeout. Please try again later."
                }
            except requests.exceptions.ConnectionError as e:
                return {
                    "approved": False,
                    "reasoning": "Contract evaluation temporarily unavailable due to connection issues. Please try again later."
                }
            except Exception as e:
                return {
                    "approved": False,
                    "reasoning": f"Contract evaluation failed: {str(e)}. Please try again later."
                } 