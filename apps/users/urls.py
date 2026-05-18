from django.urls import path
from . import views

urlpatterns = [
    path('login/',              views.LoginView.as_view(),              name='login'),
    path('logout/',             views.LogoutView.as_view(),             name='logout'),
    path('signup/',             views.SignupView.as_view(),             name='signup'),
    path('refresh/', views.TokenRefreshCookieView.as_view(), name='token_refresh'),
    # path('logout/', views.LogoutView.as_view(), name='logout'),
    # path('me/', views.UserProfileView.as_view(), name='me'),
    # path('verify-email/', views.VerifyEmailView.as_view(), name='verify_email'),
    # path('password-reset/', views.PasswordResetView.as_view(), name='password_reset'),
    # path('password-reset/confirm/<uidb64>/<token>/', views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    # path('password-change/', views.PasswordChangeView.as_view(), name='password_change'),
    # path('password-change/done/', views.PasswordChangeDoneView.as_view(), name='password_change_done'),
    # path('deactivate-account/', views.DeactivateAccountView.as_view(), name='deactivate_account'),
    # path('delete-account/', views.DeleteAccountView.as_view(), name='delete_account'),
]