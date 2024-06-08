from django.shortcuts import render
from rest_framework_simplejwt.tokens import RefreshToken
import logging
from rest_framework import generics, status, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from django.db.models import Count
from datetime import timedelta
from django.contrib.auth import get_user_model
from .models import FriendRequest, Friendship, User
from .serializers import SignupSerializer, UserSerializer, FriendRequestSerializer, FriendshipSerializer
from django.db.models import Q
from rest_framework.pagination import PageNumberPagination
from rest_framework.decorators import api_view
from rest_framework.permissions import IsAuthenticated
from users.models import User
# User = get_user_model()
logger = logging.getLogger(__name__)

class SignupView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = SignupSerializer
    permission_classes = [permissions.AllowAny]

class LoginView(APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request, *args, **kwargs):
        email = request.data.get('email')
        password = request.data.get('password')
        user = User.objects.filter(email__iexact=email).first()
        if user and user.check_password(password):
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            })

        return Response({'error': 'Invalid credentials'}, status=status.HTTP_400_BAD_REQUEST)

class UserSearchView(generics.ListAPIView):
    serializer_class = UserSerializer
    pagination_class = PageNumberPagination

    def get_queryset(self):
        logger.info('UserSearchView called')
        query = self.request.query_params.get('query', '')
        logger.info(f'Query: {query}')
        if '@' in query:
            return User.objects.filter(email__iexact=query)
        return User.objects.filter(Q(name__iexact=query))
    
class SendFriendRequestView(APIView):
    def post(self, request, *args, **kwargs):
        last_minute = timezone.now() - timedelta(minutes=1)
        num_requests = FriendRequest.objects.filter(from_user=request.user, created_at__gte=last_minute).count()
        if num_requests >= 3:
            return Response({'error': 'Exceeded the limit of 3 friend requests per minute'}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        to_user_id = request.data.get('to_user_id')
        to_user = User.objects.get(id=to_user_id)
        if FriendRequest.objects.filter(from_user=request.user, to_user=to_user).exists():
            return Response({'error': 'Friend request already sent'}, status=status.HTTP_400_BAD_REQUEST)
        
        friend_request = FriendRequest(from_user=request.user, to_user=to_user)
        friend_request.save()
        return Response({'success': 'Friend request sent'}, status=status.HTTP_201_CREATED)

class HandleFriendRequestView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def post(self, request, *args, **kwargs):
        request_id = request.data.get('request_id')
        if not request_id:
            return Response({'error': 'Request ID is required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            friend_request = FriendRequest.objects.get(id=request_id)
        except FriendRequest.DoesNotExist:
            return Response({'error': 'Friend request not found'}, status=status.HTTP_404_NOT_FOUND)
        action = request.data.get('action')
        
        if action == 'accept':
            friend_request.status = 'accepted'
            
        elif action == 'reject':
            friend_request.status = 'rejected'
        else:
            return Response({'error': 'Invalid action'}, status=status.HTTP_400_BAD_REQUEST)

        friend_request.save()
        serializer = FriendRequestSerializer(friend_request)
        return Response(serializer.data, status=status.HTTP_200_OK)

class FriendsListView(generics.ListAPIView):
    serializer_class = UserSerializer

    def get_queryset(self):
        user = self.request.user
        friendships = Friendship.objects.filter(Q(user1=user) | Q(user2=user))
        friend_ids = [f.user1.id if f.user1 != user else f.user2.id for f in friendships]
        return User.objects.filter(id__in=friend_ids)

class PendingFriendRequestsView(generics.ListAPIView):
    serializer_class = FriendRequestSerializer

    def get_queryset(self):
        return FriendRequest.objects.filter(to_user=self.request.user, status='pending')


# def limit_requests_per_minute(num_requests=3, timeout=60):
#     def decorator(view_func):
#         @wraps(view_func)
#         def wrapped_view(request, *args, **kwargs):
#             cache_key = f'request_count_{request.user.id}'
#             request_count = cache.get(cache_key, 0)

#             if request_count >= num_requests:
#                 return Response({'error': 'Too many requests. Please try again later.'}, status=status.HTTP_429_TOO_MANY_REQUESTS)

#             cache.set(cache_key, request_count + 1, timeout)
#             response = view_func(request, *args, **kwargs)
#             return response

#         return wrapped_view
#     return decorator