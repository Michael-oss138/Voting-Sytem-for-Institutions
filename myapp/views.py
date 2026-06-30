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
from .ai import analyse_manifesto


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
    if Election.objects.filter(created_by=request.user).exists():
        return Response(
            {"error": "You have already created an election. You cannot create more than one."},
            status=400
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
    # Re-fetch after status updates
    elections = Election.objects.all()
    serializer = ElectionSerializer(elections, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_posts(request, election_id):
    election = get_object_or_404(Election, id=election_id)
    if not election.is_manually_controlled:
        election.update_status()
        election.refresh_from_db()
    posts = Post.objects.filter(election=election)
    data = [
        {
            "id":              p.id,
            "title":           p.title,
            "description":     p.description,
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

    # Check if permanently disqualified
    existing = Candidate.objects.filter(user=request.user).first()
    if existing:
        if existing.application_attempts >= 2:
            return Response({"error": "You have been permanently disqualified from all elections."}, status=400)
        if existing.status in ['pending', 'nominated', 'approved']:
            return Response({"error": "You already have an active application in an election."}, status=400)
        # If rejected and attempts < 2, delete old record and let them reapply
        if existing.status == 'rejected':
            existing.delete()

    cgpa = float(request.data.get('cgpa', 0))

    # CGPA check — don't save if fails
    if cgpa < 3.0:
        return Response({
            "error": "Your CGPA does not meet the minimum requirement of 3.0.",
            "status": "rejected"
        }, status=400)

    department      = request.data.get('department')
    date_of_birth   = request.data.get('date_of_birth')
    profile_picture = request.FILES.get('profile_picture')
    full_name       = request.data.get('full_name')

    candidate = Candidate.objects.create(
        user=request.user,
        election=election,
        post=post,
        full_name=full_name,
        cgpa=cgpa,
        department=department,
        date_of_birth=date_of_birth,
        profile_picture=profile_picture,
        status='pending',
    )

    return Response({
        "message": "Application submitted. Awaiting admin review.",
        "status":  candidate.status
    }, status=201)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def nominate_candidate(request, candidate_id):
    if not request.user.is_staff:
        return Response({"error": "Admins only"}, status=403)
    candidate = get_object_or_404(Candidate, id=candidate_id)

    # Only the admin who created the election can nominate
    if candidate.election.created_by != request.user:
        return Response({"error": "You can only nominate candidates in your own election."}, status=403)

    if candidate.status != 'pending':
        return Response({"error": "Candidate must be in pending state to nominate."}, status=400)

    candidate.status = 'nominated'
    candidate.save()
    return Response({"message": "Candidate nominated successfully"})

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def submit_manifesto(request, election_id, post_id):
    election  = get_object_or_404(Election, id=election_id)
    post      = get_object_or_404(Post, id=post_id, election=election)
    candidate = get_object_or_404(Candidate, user=request.user, election=election, post=post)

    if candidate.status != 'nominated':
        return Response({"error": "You are not nominated for this post."}, status=400)

    if candidate.application_attempts >= 2:
        candidate.status = 'disqualified'
        candidate.save()
        return Response({"error": "You have been permanently disqualified."}, status=400)

    manifesto = request.data.get('manifesto')
    if not manifesto:
        return Response({"error": "Manifesto is required."}, status=400)

    ai_result = analyse_manifesto(manifesto)

    # Increment attempts
    candidate.application_attempts += 1

    if ai_result['ai_score'] == 'Weak':
        candidate.save()  # save attempt count only
        attempts_left = 2 - candidate.application_attempts
        if attempts_left <= 0:
            candidate.status = 'disqualified'
            candidate.save()
            return Response({
                "error": "Your manifesto is too weak. You have been permanently disqualified.",
                "ai_score": ai_result['ai_score'],
                "ai_theme": ai_result['ai_theme'],
            }, status=400)
        return Response({
            "error": f"Your manifesto is too weak. You have {attempts_left} attempt(s) left.",
            "ai_score": ai_result['ai_score'],
            "ai_theme": ai_result['ai_theme'],
            "attempts_left": attempts_left,
        }, status=400)

    # Good manifesto — save everything and set to pending for admin review
    candidate.manifesto     = manifesto
    candidate.ai_theme      = ai_result['ai_theme']
    candidate.ai_score      = ai_result['ai_score']
    candidate.ai_confidence = ai_result['ai_confidence']
    candidate.status        = 'pending'
    candidate.save()

    return Response({
        "message": "Manifesto submitted successfully. Awaiting admin approval.",
        "ai_score": ai_result['ai_score'],
        "ai_theme": ai_result['ai_theme'],
    }, status=200)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def pending_nominations_count(request):
    if not request.user.is_staff:
        return Response({"error": "Admins only"}, status=403)

    # Count pending candidates in elections created by this admin
    count = Candidate.objects.filter(
        election__created_by=request.user,
        status='pending'
    ).count()

    # Get the list with election and post info for quick navigation
    pending = Candidate.objects.filter(
        election__created_by=request.user,
        status='pending'
    ).select_related('election', 'post', 'user')

    data = [
        {
            "candidate_id": c.id,
            "full_name":    c.full_name,
            "election_id":  c.election.id,
            "election":     c.election.title,
            "post_id":      c.post.id,
            "post":         c.post.title,
        }
        for c in pending
    ]

    return Response({"count": count, "pending": data})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_candidates(request, election_id, post_id):
    election = get_object_or_404(Election, id=election_id)
    post     = get_object_or_404(Post, id=post_id, election=election)

    if request.user.is_staff:
        # Admin sees all candidates
        candidates = Candidate.objects.filter(election=election, post=post)
    else:
        # Students only see approved candidates
        candidates = Candidate.objects.filter(election=election, post=post, status='approved')

    data = [
        {
            "id":                   c.id,
            "full_name":            c.full_name,
            "manifesto":            c.manifesto,
            "cgpa":                 c.cgpa,
            "department":           c.department,
            "date_of_birth":        str(c.date_of_birth) if c.date_of_birth else None,
            "status":               c.status,
            "application_attempts": c.application_attempts,
            "post":                 post.title,
            "ai_theme":             c.ai_theme,
            "ai_score":             c.ai_score,
            "ai_confidence":        c.ai_confidence,
            "profile_picture":      request.build_absolute_uri(c.profile_picture.url) if c.profile_picture else None,
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
    if candidate.status != 'pending':
        return Response({"error": "Candidate must be in pending state to approve."}, status=400)
    candidate.status = 'approved'
    candidate.save()
    return Response({"message": "Candidate Approved"})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def reject_candidate(request, candidate_id):
    if request.user.role != 'admin':
        return Response({"error": "Admin only"}, status=403)
    candidate = get_object_or_404(Candidate, id=candidate_id)
    if candidate.status not in ['pending', 'nominated']:
        return Response({"error": "Candidate cannot be rejected at this stage."}, status=400)
    candidate.status = 'rejected'
    candidate.save()
    return Response({
        "message": "Candidate rejected.",
        "attempts_used": candidate.application_attempts,
        "can_reapply": candidate.application_attempts < 2
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_my_candidacy(request, election_id, post_id):
    election  = get_object_or_404(Election, id=election_id)
    post      = get_object_or_404(Post, id=post_id, election=election)
    candidate = Candidate.objects.filter(user=request.user, election=election, post=post).first()

    if not candidate:
        return Response({"candidacy": None})

    return Response({
        "candidacy": {
            "status":               candidate.status,
            "application_attempts": candidate.application_attempts,
            "manifesto":            candidate.manifesto,
            "ai_score":             candidate.ai_score,
            "ai_theme":             candidate.ai_theme,
        }
    })

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

    # Check if user has voted in ANY OTHER election already
    other_election_vote = Vote.objects.filter(voter=request.user).exclude(election=election).exists()
    if other_election_vote:
        return Response({"error": "You can only vote in one election."}, status=400)

    # One vote per post within this election
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
    if not election.is_manually_controlled:
        election.update_status()
        election.refresh_from_db()
    posts = Post.objects.filter(election=election)

    all_results = []
    for post in posts:
        candidates = Candidate.objects.filter(election=election, post=post, status='approved')
        post_results = []
        for candidate in candidates:
            vote_count = Vote.objects.filter(
                election=election, post=post, candidate=candidate
            ).count()
            post_results.append({
                "candidate_id":   candidate.id,
                "candidate_name": candidate.full_name or candidate.user.username,
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
        "status":   election.status,
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

def apply_page(request, pk, post_pk):
    return render(request, 'apply.html')