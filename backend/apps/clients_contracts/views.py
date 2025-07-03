from rest_framework.views import APIView 
from rest_framework.response import Response 
from rest_framework import status 
from config.mongo import db 
from datetime import datetime
from bson import ObjectId 
from bson.errors import InvalidId
import os
import requests
from rest_framework.permissions import IsAuthenticated
import time
from functools import wraps
from django.utils.decorators import method_decorator

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
contracts_collection = db["contracts"] 

request_count = 0
cumulative_latency = 0.0

def track_metrics_dispatch(self, request, *args, **kwargs):
    global request_count, cumulative_latency
    start = time.time()
    response = super(self.__class__, self).dispatch(request, *args, **kwargs)
    latency = time.time() - start
    request_count += 1
    cumulative_latency += latency
    return response

class ContractListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    def dispatch(self, request, *args, **kwargs):
        return track_metrics_dispatch(self, request, *args, **kwargs)
    def get(self, request): 
        contracts = list(contracts_collection.find({}, {'_id': 0}))
        return Response(contracts)
    
    def post(self, request): 
        data = request.data 
        
        required_fields = ['title', 'client', 'signed', 'text']
        missing_fields = [field for field in required_fields if field not in data]
        
        if missing_fields: 
            return Response(
                 {"error": f"Missing fields: {', '.join(missing_fields)}"},
                 status=status.HTTP_400_BAD_REQUEST       
            )
        
        if 'date' not in data:
            data['date'] = datetime.now().strftime('%Y-%m-%d')
            
        try: 
            datetime.strptime(data['date'], '%Y-%m-%d')
        except ValueError: 
            return Response(
                {"error": "Date must be in YYYY-MM-DD format."},
                status=status.HTTP_400_BAD_REQUEST               
            )         
        
        # Add timestamps
        data['created_at'] = datetime.now().isoformat()
        data['updated_at'] = datetime.now().isoformat()
        
        try:
            analysis_result = analyze_contract(data['text'])
            data['analysis'] = analysis_result['analysis']
            data['model_used'] = analysis_result['model_used']
            data['analysis_date'] = datetime.now().isoformat()
        except Exception as e:
            return Response(
                {"error": f"Contract analysis failed: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        result = contracts_collection.insert_one(data)
        data['_id'] = str(result.inserted_id)
        
        return Response({
            'message': 'Contract Created and Analyzed!',
            'contract_id': str(result.inserted_id),
            'analysis': data['analysis']
        }, status=status.HTTP_201_CREATED)


class ContractDetailView(APIView):
    permission_classes = [IsAuthenticated]
    def dispatch(self, request, *args, **kwargs):
        return track_metrics_dispatch(self, request, *args, **kwargs)
    def get(self, request, contract_id): 
        try: 
            obj_id = ObjectId(contract_id)
        except InvalidId: 
            return Response({"error": "Invalid Contract ID"}, status=status.HTTP_400_BAD_REQUEST)
        
        contract = contracts_collection.find_one({"_id": obj_id})
        if not contract:
            return Response({"error": "Contract not found"}, status=status.HTTP_404_NOT_FOUND)
        
        contract['_id'] = str(contract['_id'])  # Serialize ObjectId
        return Response(contract, status=status.HTTP_200_OK)


class ContractAnalysisView(APIView):
    permission_classes = [IsAuthenticated]
    def dispatch(self, request, *args, **kwargs):
        return track_metrics_dispatch(self, request, *args, **kwargs)
    def post(self, request, contract_id=None):
        if contract_id:
            try:
                obj_id = ObjectId(contract_id)
            except InvalidId:
                return Response({"error": "Invalid Contract ID"}, status=status.HTTP_400_BAD_REQUEST)

            contract = contracts_collection.find_one({"_id": obj_id})
            if not contract:
                return Response({"error": "Contract not found"}, status=status.HTTP_404_NOT_FOUND)

            if 'text' not in contract:
                return Response({"error": "Contract does not contain analyzable text"}, status=status.HTTP_400_BAD_REQUEST)

            try:
                analysis_result = analyze_contract(contract['text'])
                update_fields = {
                    "analysis": analysis_result['analysis'],
                    "model_used": analysis_result['model_used'],
                    "analysis_date": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }
                contracts_collection.update_one({"_id": obj_id}, {"$set": update_fields})

                return Response({
                    "message": "Contract re-analyzed successfully",
                    "contract_id": contract_id,
                    "analysis": analysis_result['analysis'],
                    "model_used": analysis_result['model_used']
                }, status=status.HTTP_200_OK)

            except Exception as e:
                return Response({"error": f"Re-analysis failed: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        contract_text = request.data.get("text")

        if not contract_text:
            uploaded_file = request.FILES.get("file")
            if not uploaded_file:
                return Response(
                    {"error": "Missing 'text' field or uploaded 'file'"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

            if uploaded_file.name.endswith(".txt"):
                contract_text = uploaded_file.read().decode("utf-8")
            else:
                return Response(
                    {"error": "Only .txt files are supported for now"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

        contract_metadata = {
            'title': request.data.get('title', 'Untitled Contract'),
            'client': request.data.get('client', 'Unknown Client'),
            'signed': request.data.get('signed', False),
            'date': request.data.get('date', datetime.now().strftime('%Y-%m-%d'))
        }

        try:
            analysis_result = analyze_contract(contract_text)
            
            contract_data = {
                **contract_metadata,
                'text': contract_text,
                'analysis': analysis_result['analysis'],
                'model_used': analysis_result['model_used'],
                'analysis_date': datetime.now().isoformat(),
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            result = contracts_collection.insert_one(contract_data)
            
            return Response({
                "contract_id": str(result.inserted_id),
                "analysis": analysis_result['analysis'],
                "model_used": analysis_result['model_used'],
                "message": "Contract analyzed and saved successfully"
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {"error": f"Analysis failed: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class ContractAnalysisDetailView(APIView):
    permission_classes = [IsAuthenticated]
    def dispatch(self, request, *args, **kwargs):
        return track_metrics_dispatch(self, request, *args, **kwargs)
    def get(self, request, contract_id): 
        try: 
            obj_id = ObjectId(contract_id)
        except InvalidId: 
            return Response(
                {'error': 'Invalid contract ID'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        contract = contracts_collection.find_one({"_id": obj_id}, {"_id": 0})
        if not contract: 
            return Response(
                {'error': 'Contract not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        if 'analysis' not in contract: 
            return Response(
                {'error': 'No analysis found for this contract'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response({
            'analysis': contract['analysis'], 
            'model_used': contract.get('model_used', 'DeepSeek Reasoning Model (Live)'),
            'analysis_date': contract.get('analysis_date'),
            'contract_title': contract.get('title'),
            'contract_client': contract.get('client')
        }, status=status.HTTP_200_OK)


def analyze_contract(contract_text):
    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "deepseek-reasoner",  
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

    response = requests.post("https://api.deepseek.com/v1/chat/completions", json=payload, headers=headers)
    response.raise_for_status()
    result = response.json()
    model_reply = result["choices"][0]["message"]["content"]
    return {
        "analysis": model_reply,
        "model_used": "DeepSeek Reasoning Model (Live)"
    }

class ContractEvaluationView(APIView):
    permission_classes = [IsAuthenticated]
    def dispatch(self, request, *args, **kwargs):
        return track_metrics_dispatch(self, request, *args, **kwargs)
    def post(self, request): 
        contract_text = request.data.get('text')
        if not contract_text: 
            uploaded_file = request.FILES.get('file')
            if not uploaded_file: 
                return Response(
                    {'error': "Missing 'text' field or uploaded 'file'"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            if uploaded_file.name.endswith('.txt'): 
                contract_text = uploaded_file.read().decode('utf-8')
            else: 
                return Response(
                    {'error': 'Only .txt files are supported for now'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        try: 
            headers = {
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": "deepseek-reasoner", 
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
            response = requests.post("https://api.deepseek.com/v1/chat/completions", json=payload, headers=headers)
            response.raise_for_status()
            print(response.text)
            result = response.json()
            reply = result["choices"][0]["message"]["content"]
            approved = "not approved" not in reply.lower()
            return Response({
                "approved": approved, 
                "reasoning": reply.strip()
            }, status=status.HTTP_200_OK)
        except Exception as e: 
            return Response(
                {"error": f"ContractEvaluation failed: {str(e)}"}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )                

class HealthzView(APIView):
    permission_classes = [IsAuthenticated]
    def dispatch(self, request, *args, **kwargs):
        return track_metrics_dispatch(self, request, *args, **kwargs)
    def get(self, request):
        return Response({"status": "ok"}, status=status.HTTP_200_OK)

class ReadyzView(APIView):
    permission_classes = [IsAuthenticated]
    def dispatch(self, request, *args, **kwargs):
        return track_metrics_dispatch(self, request, *args, **kwargs)
    def get(self, request):
        try:
            db_stats = contracts_collection.database.command("ping")
            if db_stats.get("ok") == 1.0:
                return Response({"status": "ready"}, status=status.HTTP_200_OK)
            else:
                return Response({"status": "not ready"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as e:
            return Response({"status": "not ready", "error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class MetricsView(APIView):
    permission_classes = [IsAuthenticated]
    def dispatch(self, request, *args, **kwargs):
        return track_metrics_dispatch(self, request, *args, **kwargs)
    def get(self, request):
        avg_latency = cumulative_latency / request_count if request_count > 0 else 0.0
        return Response({
            "request_count": request_count,
            "average_latency": avg_latency
        }, status=status.HTTP_200_OK)                