from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    register_admin, register_student, admin_dashboard,
    create_election, list_elections, open_election, close_election, reset_election,
    apply_candidate, list_candidates, approve_candidate, reject_candidate,
    cast_vote, check_vote_status, election_results,
    login_page, register_page, dashboard_page,
    elections_page, election_detail_page, results_page,
    post_detail_page, list_posts,create_election_page,
    CustomTokenObtainPairView,apply_page,nominate_candidate, submit_manifesto, get_my_candidacy
)

urlpatterns = [

    # Template Pages 
    path('', login_page, name='login-page'),
    path('register/', register_page, name='register-page'),
    path('dashboard/', dashboard_page, name='dashboard-page'),
    path('elections-page/create/', create_election_page, name='create-election-page'),
    path('elections-page/', elections_page, name='elections-page'),
    path('elections-page/<int:pk>/', election_detail_page, name='election-detail-page'),
    path('elections-page/<int:pk>/posts/<int:post_pk>/', post_detail_page, name='post-detail-page'),
    path('elections-page/<int:pk>/results/', results_page, name='results-page'),

    #  Auth 
    path('login/', CustomTokenObtainPairView.as_view(), name='login'),
    path('refresh/', TokenRefreshView.as_view(), name='refresh'),

    #  Registration 
    path('admin/register/', register_admin),
    path('student/register/', register_student),

    #  Admin 
    path('admin/dashboard/', admin_dashboard),

    #  Elections 
    path('elections/create/', create_election),
    path('elections/', list_elections),
    path('elections/<int:pk>/open/', open_election),
    path('elections/<int:pk>/close/', close_election),
    path('elections/<int:pk>/reset/', reset_election),

    #  Posts & Candidates 
    path('elections/<int:election_id>/posts/', list_posts),
    path('elections/<int:election_id>/posts/<int:post_id>/candidates/', list_candidates),
    path('elections/<int:election_id>/posts/<int:post_id>/apply/', apply_candidate),
    path('candidates/<int:candidate_id>/approve/', approve_candidate),
    path('candidates/<int:candidate_id>/reject/', reject_candidate),

    #  Voting 
    path('elections/<int:election_id>/posts/<int:post_id>/vote/<int:candidate_id>/', cast_vote),
    path('elections/<int:election_id>/vote-status/', check_vote_status),

    #  Results 
    path('elections/<int:election_id>/results/', election_results),

    path('elections-page/<int:pk>/posts/<int:post_pk>/apply/', apply_page, name='apply-page'),

    # Nomination
    path('candidates/<int:candidate_id>/nominate/', nominate_candidate),

    # Manifesto submission
    path('elections/<int:election_id>/posts/<int:post_id>/submit-manifesto/', submit_manifesto),

    # Student checks own candidacy status
    path('elections/<int:election_id>/posts/<int:post_id>/my-candidacy/', get_my_candidacy)
]