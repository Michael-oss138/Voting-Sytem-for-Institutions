from django.shortcuts import render
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status   
from .models import User, Election
from .serializers import AdminRegisterSerializer, StudentSignUpsertializer, ElectionSerializer
from rest_framework.permissions import IsAuthenticated  
from rest_framework.decorators import permission_classes    
from rest_framework.permissions import IsAuthenticated, AllowAny
# Create your views here.

@api_view(['POST'])
@permission_classes([AllowAny])
def register_student(request):
    serializer = StudentSignUpsertializer(data=request.data)

    if serializer.is_valid():
        serializer.save()
        return Response(
            {"message": "Student Registered Successfully"},
            status=status.HTTP_201_CREATED
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def register_admin(request):
    if not request.user.is_superuser:
        return Response(
        {"error": "Only Superusers can create admins"},
        status=status.HTTP_403_FORBIDDEN
        )

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
        return Response({"error": "Access Denied"}, status=status.HTTP_403_FORBIDDEN)
    
    return Response({"message": f"welcome {request.user.user_name}, you are an admin"})
    
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_election(request):
    #print("USER:", request.user)
    #print("ROLE:", request.user.role)

    #return Response({"me""You reached here"}, status=403)

    if not request.user.is_staff:
        return Response(
            {"error": "Only admins can create elections"},
            status=status.HTTP_403_FORBIDDEN
        )
    serializer = ElectionSerializer(data=request.data)

    if serializer.is_valid():
        serializer.save(created_by=request.user)
        return Response(
            {"message": "Election Created Successfully"},
            status=status.HTTP_201_CREATED
        )
    return Response(serializer.errors, status=400)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_elections(request):
    elections = Election.objects.all()
    serializer = ElectionSerializer(elections, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def open_election(request, pk):
    election = Election.objects.get(id=pk)
    if not request.user.is_staff:
        return Response(
            {"error": "Admins only"},
            status=403
        )
    
    election.status = 'opened'
    election.is_manually_controlled = True
    election.save()

    return Response({"message": "Election opened successfully"})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def close_election(request, pk):
    election = Election.objects.get(id=pk)

    if not request.user.is_staff:
        return Response(
            {"error": "Admins only"},
            status=403
        )
    
    election.status = 'closed'
    election.is_manually_controlled = True
    election.save()

    return Response({"message": "Election closed successfully"})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reset_election(request, pk):
    election = Election.objects.get(id=pk)

    if not request.user.is_staff:
        return Response(
            {"error": "Admins only"},
            status=403
        )
    
    
    election.is_manually_controlled = False

    if hasattr(election, "update_status"):
        election.update_status()
    election.save()

    return Response({"message": "Election reset successfully"})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def apply_candidate(request, election_id):
    election = get_object_or_404(Election, id=election_id)

    data = request.data.copy()
    data['user'] = request.user.id
    data['eleciton'] = election.id

    candidate = Candidate.objects.create(
        user = request.user,
        election = election,
        manifesto = data.get('manifesto'),
        cgpa = data.get('cgpa'),
        department = data.get('department'),
        status = 'pending'
    )

    return Response({
        "message": "Application Submitted",
        "status": candidate.status
    }, status=201)