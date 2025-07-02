from rest_framework.views import APIView 
from rest_framework.response import Response 
from rest_framework import status 
from config.mongo import db 
from datetime import datetime
from bson import ObjectId 
from bson.errors import InvalidId


contracts_collection = db["contracts"] 

class ContractListCreateView(APIView):
    def get(self, request): 
        contracts = list(contracts_collection.find({}, {'_id': 0}))
        return Response(contracts)
    
    def post(self, request): 
        data = request.data 
        
        required_fields = ['title', 'client', 'signed']
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
        
        contracts_collection.insert_one(data)
        return Response({'message': 'Contract Created!'}, status=status.HTTP_201_CREATED)

class ContractDetailView(APIView): 
    def get(self, request, contract_id): 
        try: 
            obj_id = ObjectId(contract_id)
        except InvalidId: 
            return Response ({"error: Invalid Contract ID"}, status=status.HTTP_400_BAD_REQUEST)
        
        contract = contracts_collection.find_one({"_id": obj_id}, {"_id": 0})
        if not contract:
            return Response(contract, status=status.HTTP_200_OK)
        return Response(contract, status=status.HTTP_200_OK)