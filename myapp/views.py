from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status   
from .models import User
from .serializers import AdminRegisterSerializer, StudentSignUpsertializer
from rest_framework.permissions import IsAuthenticated  
from rest_framework.decorators import permission_classes    
# Create your views here.

@api_view(['POST'])
@permission_classes([AllowAny])
def register_admin(request):
    serializer = AdminRegisterSerializer(data=request.data)

    if serializer.is_valid():
        serializer.save()
        return Response(
            {"message": "Admin registered successfully."},
            status=status.HTTP_201_CREATED
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_dashboard(request):
    if request.user.role != 'admin':
        return Response({"message": "This is a protected view accessible only to authenticated users."}, status=403)
    
    return Response({"message": "Welcome to the admin dashboard!"})