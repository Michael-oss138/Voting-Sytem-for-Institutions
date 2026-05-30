from django.shortcuts import render, get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from .models import User, Election, Post, Candidate, Vote
from .serializers import AdminRegisterSerializer, StudentSignUpsertializer, ElectionSerializer
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from django.db.models import Count


#  JWT CUSTOM TOKEN 

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        token['username'] = user.username
        token['role']     = user.role
        return token

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


#  REGISTRATION 

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


#  ADMIN DASHBOARD 

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_dashboard(request):
    if request.user.role != 'admin':
        return Response({"error": "Access Denied"}, status=status.HTTP_403_FORBIDDEN)
    return Response({"message": f"Welcome {request.user.username}, you are an admin"})


#  ELECTIONS 

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_election(request):
    if not request.user.is_staff:
        return Response(
            {"error": "Only admins can create elections"},
            status=status.HTTP_403_FORBIDDEN
        )

    # Extract posts from request
    posts = request.data.get('posts', [])
    if not posts:
        return Response(
            {"error": "At least one post is required"},
            status=400
        )

    serializer = ElectionSerializer(data=request.data)
    if serializer.is_valid():
        election = serializer.save(created_by=request.user)

        # Create all posts for this election
        for post_title in posts:
            Post.objects.create(
                election=election,
                title=post_title
            )

        return Response(
            {"message": "Election created successfully"},
            status=status.HTTP_201_CREATED
        )
    return Response(serializer.errors, status=400)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_elections(request):
    elections = Election.objects.all()

    for election in elections:
        if not election.is_manually_controlled:
            election.update_status()

    serializer = ElectionSerializer(elections, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_posts(request, election_id):
    election = get_object_or_404(Election, id=election_id)
    posts = Post.objects.filter(election=election)
    data = [
        {
            "id":          p.id,
            "title":       p.title,
            "description": p.description,
            "candidate_count": Candidate.objects.filter(post=p, status='approved').count()
        }
        for p in posts
    ]
    return Response(data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def open_election(request, pk):
    if not request.user.is_staff:
        return Response({"error": "Admins only"}, status=403)
    election = get_object_or_404(Election, id=pk)
    if election.created_by != request.user:
        return Response({"error": "You can only manage elections you created"}, status=403)
    election.status = 'opened'
    election.is_manually_controlled = True
    election.save()
    return Response({"message": "Election opened successfully"})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def close_election(request, pk):
    if not request.user.is_staff:
        return Response({"error": "Admins only"}, status=403)
    election = get_object_or_404(Election, id=pk)
    if election.created_by != request.user:
        return Response({"error": "You can only manage elections you created"}, status=403)
    election.status = 'closed'
    election.is_manually_controlled = True
    election.save()
    return Response({"message": "Election closed successfully"})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reset_election(request, pk):
    if not request.user.is_staff:
        return Response({"error": "Admins only"}, status=403)
    election = get_object_or_404(Election, id=pk)
    if election.created_by != request.user:
        return Response({"error": "You can only manage elections you created"}, status=403)
    election.status = 'draft'
    election.is_manually_controlled = False
    election.save()
    return Response({"message": "Election reset to draft successfully"})


#  CANDIDATES 

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def apply_candidate(request, election_id, post_id):
    election = get_object_or_404(Election, id=election_id)
    post     = get_object_or_404(Post, id=post_id, election=election)

    # Check if already applied for any post
    if Candidate.objects.filter(user=request.user).exists():
        return Response({"error": "You have already applied as a candidate in an election"}, status=400)

    cgpa       = float(request.data.get('cgpa', 0))
    department = request.data.get('department')
    manifesto  = request.data.get('manifesto')

    status_value = 'approved' if cgpa >= 3.0 else 'rejected'

    candidate = Candidate.objects.create(
        user=request.user,
        election=election,
        post=post,
        manifesto=manifesto,
        cgpa=cgpa,
        department=department,
        status=status_value
    )

    return Response({
        "message": "Application submitted",
        "status":  candidate.status
    }, status=201)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_candidates(request, election_id, post_id):
    election   = get_object_or_404(Election, id=election_id)
    post       = get_object_or_404(Post, id=post_id, election=election)
    candidates = Candidate.objects.filter(election=election, post=post, status='approved')

    data = [
        {
            "id":         c.id,
            "username":   c.user.username,
            "manifesto":  c.manifesto,
            "cgpa":       c.cgpa,
            "department": c.department,
            "status":     c.status,
            "post":       post.title,
        }
        for c in candidates
    ]
    return Response(data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def approve_candidate(request, candidate_id):
    if request.user.role != 'admin':
        return Response({"error": "Admin Only"}, status=403)
    candidate = get_object_or_404(Candidate, id=candidate_id)
    candidate.status = "approved"
    candidate.save()
    return Response({"message": "Candidate Approved"})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reject_candidate(request, candidate_id):
    if request.user.role != 'admin':
        return Response({"error": "Admin only"}, status=403)
    candidate = get_object_or_404(Candidate, id=candidate_id)
    candidate.status = "rejected"
    candidate.save()
    return Response({"message": "Candidate Rejected"})


#  VOTING 

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def cast_vote(request, election_id, post_id, candidate_id):
    election  = get_object_or_404(Election, id=election_id)
    post      = get_object_or_404(Post, id=post_id, election=election)
    candidate = get_object_or_404(Candidate, id=candidate_id, post=post, election=election)

    if election.status != 'opened':
        return Response({"error": "Election is not open"}, status=400)

    if candidate.status != 'approved':
        return Response({"error": "Candidate is not approved"}, status=400)

    # One vote per post per election
    if Vote.objects.filter(voter=request.user, election=election, post=post).exists():
        return Response({"error": "You have already voted for this post"}, status=400)

    Vote.objects.create(
        voter=request.user,
        election=election,
        post=post,
        candidate=candidate
    )
    return Response({"message": "Vote cast successfully"}, status=201)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_vote_status(request, election_id):
    election = get_object_or_404(Election, id=election_id)
    posts    = Post.objects.filter(election=election)

    voted_posts = []
    for post in posts:
        has_voted = Vote.objects.filter(
            voter=request.user,
            election=election,
            post=post
        ).exists()
        voted_posts.append({
            "post_id":   post.id,
            "post_title": post.title,
            "has_voted": has_voted
        })

    return Response({"posts": voted_posts})


#  RESULTS 

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def election_results(request, election_id):
    election = get_object_or_404(Election, id=election_id)
    posts    = Post.objects.filter(election=election)

    all_results = []

    for post in posts:
        candidates = Candidate.objects.filter(election=election, post=post, status='approved')

        post_results = []
        for candidate in candidates:
            vote_count = Vote.objects.filter(
                election=election,
                post=post,
                candidate=candidate
            ).count()
            post_results.append({
                "candidate_id":   candidate.id,
                "candidate_name": candidate.user.username,
                "department":     candidate.department,
                "votes":          vote_count
            })

        post_results.sort(key=lambda x: x['votes'], reverse=True)
        winner = post_results[0] if post_results else None

        all_results.append({
            "post_id":    post.id,
            "post_title": post.title,
            "winner":     winner,
            "candidates": post_results
        })

    return Response({
        "election": election.title,
        "results":  all_results
    })


#  TEMPLATE VIEWS 

def login_page(request):
    return render(request, 'login.html')

def register_page(request):
    return render(request, 'register.html')

def dashboard_page(request):
    return render(request, 'dashboard.html')

def elections_page(request):
    return render(request, 'elections.html')

def election_detail_page(request, pk):
    return render(request, 'election_detail.html')

def results_page(request, pk):
    return render(request, 'results.html')

def post_detail_page(request, pk, post_pk):
    return render(request, 'post_detail.html')

def create_election_page(request):
    return render(request, 'create_election.html')