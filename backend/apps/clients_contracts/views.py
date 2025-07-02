from rest_framework.views import APIView 
from rest_framework.response import Response 
from rest_framework import status 
from config.mongo import db 

contracts_collection = db["contracts"] 

class ContractListCreateView(APIView):
    def get(self, request): 
        contracts = list(contracts_collection.find({}, {'_id': 0}))
        return Response(contracts)
    
    def post(self, request): 
        data = request.data 
        contracts_collection.insert_one(data)
        return Response({'message: Contract Created!'}, status=status.HTTP_201_CREATED)
    