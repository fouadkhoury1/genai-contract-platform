from rest_framework.views import APIView 
from rest_framework.response import Response 
from rest_framework import status 
from config.mongo import db 
from datetime import datetime
from bson import ObjectId 
from bson.errors import InvalidId
import os
import requests
import PyPDF2
import io
from rest_framework.permissions import IsAuthenticated
import time
from functools import wraps
from django.utils.decorators import method_decorator
from rest_framework.pagination import PageNumberPagination
from django.utils.deprecation import MiddlewareMixin
from .ai_service import AIService

ai_service = AIService()

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
contracts_collection = db["contracts"] 
logs_collection = db["logs"]
clients_collection = db["clients"]

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
        contracts = list(contracts_collection.find({}))
        # Convert ObjectId to string for JSON serialization
        for contract in contracts:
            contract['_id'] = str(contract['_id'])
        return Response(contracts)
    
    def post(self, request): 
        data = request.data.copy()  # Make a mutable copy
        contract_text = data.get('text')
        # If 'text' is missing, try to extract from uploaded file
        if not contract_text:
            uploaded_file = request.FILES.get('file')
            if not uploaded_file:
                required_fields = ['title', 'client', 'signed', 'text']
                missing_fields = [field for field in required_fields if field not in data]
                return Response(
                    {"error": f"Missing fields: {', '.join(missing_fields)}"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            if uploaded_file.name.endswith('.pdf'):
                try:
                    pdf_reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.read()))
                    contract_text = ""
                    for page in pdf_reader.pages:
                        contract_text += page.extract_text()
                    if not contract_text.strip():
                        return Response(
                            {"error": "Could not extract text from PDF. The file might be empty or corrupted."},
                            status=status.HTTP_400_BAD_REQUEST
                        )
                except Exception as e:
                    return Response(
                        {"error": f"Error reading PDF file: {str(e)}"},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            elif uploaded_file.name.endswith('.txt'):
                contract_text = uploaded_file.read().decode('utf-8')
            else:
                return Response(
                    {"error": "Only .pdf and .txt files are supported"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            data['text'] = contract_text
        # Convert signed field to boolean if it's a string
        if 'signed' in data and isinstance(data['signed'], str):
            data['signed'] = data['signed'].lower() == 'true'
        
        # Now proceed as before
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
            analysis_result = ai_service.analyze_contract(data['text'])
            data['analysis'] = analysis_result['analysis']
            data['model_used'] = analysis_result['model_used']
            data['analysis_date'] = datetime.now().isoformat()
            # Evaluate contract approval
            evaluation_result = ai_service.evaluate_contract(data['text'])
            data['approved'] = evaluation_result['approved']
            data['evaluation_reasoning'] = evaluation_result['reasoning']
        except Exception as e:
            return Response(
                {"error": f"Contract analysis or evaluation failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        # Remove the file object before saving to MongoDB (it can't be serialized)
        if 'file' in data:
            del data['file']
        
        # Ensure _id is not present (MongoDB will generate it)
        if '_id' in data:
            del data['_id']
            
        # Create a clean document structure to avoid any MongoDB issues
        contract_document = {
            'title': data['title'],
            'client': data['client'],
            'signed': data['signed'],
            'text': data['text'],
            'date': data['date'],
            'created_at': data['created_at'],
            'updated_at': data['updated_at'],
            'analysis': data['analysis'],
            'model_used': data['model_used'],
            'analysis_date': data['analysis_date'],
            'approved': data['approved'],
            'evaluation_reasoning': data['evaluation_reasoning']
        }
        
        result = contracts_collection.insert_one(contract_document)
        data['_id'] = str(result.inserted_id)
        return Response({
            'message': 'Contract Created and Analyzed!',
            'contract_id': str(result.inserted_id),
            'analysis': data['analysis'],
            'approved': data['approved'],
            'evaluation_reasoning': data['evaluation_reasoning']
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
        # Ensure approved and evaluation_reasoning are present in the response
        if 'approved' not in contract:
            contract['approved'] = None
        if 'evaluation_reasoning' not in contract:
            contract['evaluation_reasoning'] = None
        return Response(contract, status=status.HTTP_200_OK)

    def put(self, request, contract_id):
        try:
            obj_id = ObjectId(contract_id)
        except InvalidId:
            return Response({"error": "Invalid Contract ID"}, status=status.HTTP_400_BAD_REQUEST)
        data = request.data
        data['updated_at'] = datetime.now().isoformat()
        result = contracts_collection.update_one({"_id": obj_id}, {"$set": data})
        if result.matched_count == 0:
            return Response({"error": "Contract not found"}, status=status.HTTP_404_NOT_FOUND)
        # Return updated contract with approved/evaluation_reasoning if present
        contract = contracts_collection.find_one({"_id": obj_id})
        contract['_id'] = str(contract['_id'])
        if 'approved' not in contract:
            contract['approved'] = None
        if 'evaluation_reasoning' not in contract:
            contract['evaluation_reasoning'] = None
        return Response(contract, status=status.HTTP_200_OK)

    def patch(self, request, contract_id):
        try:
            obj_id = ObjectId(contract_id)
        except InvalidId:
            return Response({"error": "Invalid Contract ID"}, status=status.HTTP_400_BAD_REQUEST)
        data = request.data
        data['updated_at'] = datetime.now().isoformat()
        result = contracts_collection.update_one({"_id": obj_id}, {"$set": data})
        if result.matched_count == 0:
            return Response({"error": "Contract not found"}, status=status.HTTP_404_NOT_FOUND)
        # Return updated contract with approved/evaluation_reasoning if present
        contract = contracts_collection.find_one({"_id": obj_id})
        contract['_id'] = str(contract['_id'])
        if 'approved' not in contract:
            contract['approved'] = None
        if 'evaluation_reasoning' not in contract:
            contract['evaluation_reasoning'] = None
        return Response(contract, status=status.HTTP_200_OK)

    def delete(self, request, contract_id):
        try:
            obj_id = ObjectId(contract_id)
        except InvalidId:
            return Response({"error": "Invalid Contract ID"}, status=status.HTTP_400_BAD_REQUEST)
        result = contracts_collection.delete_one({"_id": obj_id})
        if result.deleted_count == 0:
            return Response({"error": "Contract not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response({"message": "Contract deleted successfully"}, status=status.HTTP_200_OK)


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
                analysis_result = ai_service.analyze_contract(contract['text'])
                # Evaluate contract approval
                evaluation_result = ai_service.evaluate_contract(contract['text'])
                update_fields = {
                    "analysis": analysis_result['analysis'],
                    "model_used": analysis_result['model_used'],
                    "analysis_date": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat(),
                    "approved": evaluation_result['approved'],
                    "evaluation_reasoning": evaluation_result['reasoning']
                }
                contracts_collection.update_one({"_id": obj_id}, {"$set": update_fields})

                return Response({
                    "message": "Contract re-analyzed successfully",
                    "contract_id": contract_id,
                    "analysis": analysis_result['analysis'],
                    "model_used": analysis_result['model_used'],
                    "approved": evaluation_result['approved'],
                    "evaluation_reasoning": evaluation_result['reasoning']
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

            if uploaded_file.name.endswith(".pdf"):
                # Read PDF and extract text
                try:
                    pdf_reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.read()))
                    contract_text = ""
                    for page in pdf_reader.pages:
                        contract_text += page.extract_text()
                    if not contract_text.strip():
                        return Response(
                            {"error": "Could not extract text from PDF. The file might be empty or corrupted."}, 
                            status=status.HTTP_400_BAD_REQUEST
                        )
                except Exception as e:
                    return Response(
                        {"error": f"Error reading PDF file: {str(e)}"}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
            elif uploaded_file.name.endswith(".txt"):
                contract_text = uploaded_file.read().decode("utf-8")
            else:
                return Response(
                    {"error": "Only .pdf and .txt files are supported"}, 
                    status=status.HTTP_400_BAD_REQUEST
                )

        contract_metadata = {
            'title': request.data.get('title', 'Untitled Contract'),
            'client': request.data.get('client', 'Unknown Client'),
            'signed': request.data.get('signed', False),
            'date': request.data.get('date', datetime.now().strftime('%Y-%m-%d'))
        }

        try:
            analysis_result = ai_service.analyze_contract(contract_text)
            
            contract_data = {
                **contract_metadata,
                'text': contract_text,
                'analysis': analysis_result['analysis'],
                'model_used': analysis_result['model_used'],
                'analysis_date': datetime.now().isoformat(),
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }

            # Evaluate contract approval
            evaluation_result = ai_service.evaluate_contract(contract_text)
            contract_data['approved'] = evaluation_result['approved']
            contract_data['evaluation_reasoning'] = evaluation_result['reasoning']

            result = contracts_collection.insert_one(contract_data)
            
            return Response({
                "contract_id": str(result.inserted_id),
                "analysis": analysis_result['analysis'],
                "model_used": analysis_result['model_used'],
                "approved": evaluation_result['approved'],
                "evaluation_reasoning": evaluation_result['reasoning'],
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
            if uploaded_file.name.endswith('.pdf'):
                # Read PDF and extract text
                try:
                    pdf_reader = PyPDF2.PdfReader(io.BytesIO(uploaded_file.read()))
                    contract_text = ""
                    for page in pdf_reader.pages:
                        contract_text += page.extract_text()
                    if not contract_text.strip():
                        return Response(
                            {"error": "Could not extract text from PDF. The file might be empty or corrupted."}, 
                            status=status.HTTP_400_BAD_REQUEST
                        )
                except Exception as e:
                    return Response(
                        {"error": f"Error reading PDF file: {str(e)}"}, 
                        status=status.HTTP_400_BAD_REQUEST
                    )
            elif uploaded_file.name.endswith('.txt'): 
                contract_text = uploaded_file.read().decode('utf-8')
            else: 
                return Response(
                    {'error': 'Only .pdf and .txt files are supported'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        try: 
            result = ai_service.evaluate_contract(contract_text)
            return Response({
                "approved": result["approved"], 
                "reasoning": result["reasoning"]
            }, status=status.HTTP_200_OK)
        except Exception as e: 
            return Response(
                {"error": f"Contract evaluation failed: {str(e)}"}, 
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

# Logging middleware
class RequestLogMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        user = str(request.user) if hasattr(request, 'user') and request.user.is_authenticated else None
        log_entry = {
            "user": user,
            "endpoint": request.path,
            "method": request.method,
            "date": datetime.now().isoformat(),
            "status": response.status_code
        }
        logs_collection.insert_one(log_entry)
        return response

class LogsPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class LogsView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request):
        user = request.query_params.get('user')
        endpoint = request.query_params.get('endpoint')
        date = request.query_params.get('date')
        status_code = request.query_params.get('status')
        query = {}
        if user:
            query['user'] = user
        if endpoint:
            query['endpoint'] = endpoint
        if date:
            query['date'] = {'$regex': f'^{date}'}
        if status_code:
            try:
                query['status'] = int(status_code)
            except ValueError:
                pass
        logs_cursor = logs_collection.find(query).sort('date', -1)
        logs_list = list(logs_cursor)
        for log in logs_list:
            if '_id' in log:
                log['_id'] = str(log['_id'])
        paginator = LogsPagination()
        page = paginator.paginate_queryset(logs_list, request)
        return paginator.get_paginated_response(page)

class ClientListCreateView(APIView):
    permission_classes = [IsAuthenticated]
    def dispatch(self, request, *args, **kwargs):
        return track_metrics_dispatch(self, request, *args, **kwargs)
    def post(self, request):
        data = request.data
        required_fields = ['name']
        missing_fields = [field for field in required_fields if field not in data]
        if missing_fields:
            return Response({"error": f"Missing fields: {', '.join(missing_fields)}"}, status=status.HTTP_400_BAD_REQUEST)
        # Ensure unique name
        if clients_collection.find_one({"name": data['name']}):
            return Response({"error": "Client name must be unique."}, status=status.HTTP_400_BAD_REQUEST)
        client_doc = {
            "name": data["name"],
            "email": data.get("email"),
            "company_id": data.get("company_id"),
            "created_at": datetime.now().isoformat()
        }
        result = clients_collection.insert_one(client_doc)
        client_doc["_id"] = str(result.inserted_id)
        return Response(client_doc, status=status.HTTP_201_CREATED)

class ClientContractsView(APIView):
    permission_classes = [IsAuthenticated]
    def dispatch(self, request, *args, **kwargs):
        return track_metrics_dispatch(self, request, *args, **kwargs)
    def get(self, request, client_id):
        # Find client by id
        try:
            obj_id = ObjectId(client_id)
        except InvalidId:
            return Response({"error": "Invalid Client ID"}, status=status.HTTP_400_BAD_REQUEST)
        client = clients_collection.find_one({"_id": obj_id})
        if not client:
            return Response({"error": "Client not found"}, status=status.HTTP_404_NOT_FOUND)
        # Find contracts for this client (by name)
        contracts = list(contracts_collection.find({"client": client["name"]}))
        for contract in contracts:
            contract["_id"] = str(contract["_id"])
        return Response(contracts, status=status.HTTP_200_OK)                