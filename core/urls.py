from django.urls import path, include
from .views import *
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static


urlpatterns = [
    path('', HomeView.as_view(), name='home'),
    path('sign_up/', SignupView.as_view(), name='sign-up'),
    path('sign_in/', SigninView.as_view(), name='sign-in'),
    path('logout',auth_views.LogoutView.as_view(), name='logout'),
    path('profile_update/<int:pk>/',ProfileUpdateView.as_view(), name='profile-update'),
    path('subjects/',SubjectView.as_view(), name='subjects'),
    path('notes/',AllNotesView.as_view(), name='notes'),
    path('notes_list/<str:sub_class>/',AllNotesView.as_view(), name='notes-list'),
    path('view_note/<int:id>/',NoteView.as_view(), name='view-note'),
    path('update_note/<str:id>/',AllNotesView.as_view(), name='update-note'),
    path('delete_note/<str:id>/',DeleteNoteView.as_view(), name='delete-note'),
    path('ai_notes/', chatAiView.as_view(), name="ai-notes"),
    path('parental_guide/', ParentalGuidanceView.as_view(), name="parental-guide"),
    path('reset_password/',
         MyPasswordResetView.as_view(),
         name='reset_password'),
    path('reset/<uidb64>/<token>', PasswordResetConfirmView.as_view(
         template_name="password_reset_form.html"),
         name='password_reset_confirm'),
    path('change_password/<str:id>/', ChangePasswordView.as_view(), name='change_password'),
]