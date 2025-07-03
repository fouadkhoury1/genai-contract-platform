from rest_framework.views import APIView 
from rest_framework.response import Response 
from rest_framework import status 
from config.mongo import db 
from datetime import datetime
from bson import ObjectId 
from bson.errors import InvalidId
import os
import requests

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")
contracts_collection = db["contracts"] 


class ContractListCreateView(APIView):
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
    def post(self, request):      
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


# Shared helper function
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