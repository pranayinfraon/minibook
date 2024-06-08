from django.urls import path
from .views import SignupView, LoginView, UserSearchView, SendFriendRequestView, HandleFriendRequestView, FriendsListView, PendingFriendRequestsView

urlpatterns = [
    path('signup/', SignupView.as_view(), name='signup'),
    path('login/', LoginView.as_view(), name='login'),
    path('search/', UserSearchView.as_view(), name='user_search'),
    path('friend-request/send/', SendFriendRequestView.as_view(), name='send_friend_request'),
    path('friend-request/handle/', HandleFriendRequestView.as_view(), name='handle_friend_request'),
    path('friends/', FriendsListView.as_view(), name='friends_list'),
    path('friend-requests/pending/', PendingFriendRequestsView.as_view(), name='pending_friend_requests'),
]


'''
headers = {'Authorization': 'Bearer ea4ae8083a56b0174933bff156a4fbe6a2a7981d'}
response = requests.get('http://localhost:9000/api/login/', headers=headers)

if response.status_code == 200:
    print(response.content)
else:
    print(response.status_code)

'''