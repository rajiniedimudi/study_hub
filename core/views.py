from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
import smtplib
from email.mime.text import MIMEText
from django.contrib.sites.shortcuts import get_current_site
from django.utils.encoding import force_bytes
from django.template.loader import render_to_string
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout, views
from django.contrib.auth.models import User
from django.utils import timezone
from django.views import View
from django.views.generic import TemplateView
from .models import Profile, Notes, ParentGuidance
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib import messages
import json
import requests
from django.conf import settings

class HomeView(TemplateView):
    template_name = 'home.html'


class SignupView(View):
    template_name = 'signup.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)
    
    def post(self, request, *args, **kwargs):
        name = self.request.POST.get('name')
        user_type = self.request.POST.get('user_type')
        email = self.request.POST.get('email')
        password = self.request.POST.get('password')
        
        try:
            # saving student user
            user = User.objects.create(first_name=name, username=email, email=email)
            user.set_password(password)
            user.save()
            student = Profile.objects.create(user=user,user_type=user_type)
            student.save()

            # authenticate student user
            auth_user = authenticate(request, username=email, password=password)
            if auth_user:
                login(request, auth_user)
                return redirect('home')
        except:
            messages.info(self.request, 'User already exists ')
            logout(self.request)
            return redirect('home')
           

class SigninView(View):
    template_name = 'signin.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)
    
    def post(self, request, *args, **kwargs):
        email = self.request.POST.get('email')
        password = self.request.POST.get('password')
        user = User.objects.filter(username=email)
        if user.exists():
            if Profile.objects.filter(user=user.last()).exists():
                auth_user = authenticate(username=email, password=password)
                if auth_user:
                    login(self.request, auth_user)
                    messages.info(request, "User Logged In ")
                    return redirect('home')
                else:
                    logout(self.request)
                    messages.info(request, "User and Password not matched !!")
            else:
                messages.info(request, "User is a Teacher !!")
        else:
            messages.info(request, "User not Exists !!")

        return HttpResponseRedirect(self.request.path_info)
    

class ProfileUpdateView(LoginRequiredMixin, View):
    template_name = 'user_profile.html'
    login_url = '/sign_in/'

    def get(self, request, *args, **kwargs):
        user_id = self.kwargs['pk']
        user = User.objects.filter(id=user_id)
        match_user = str(user.last().username) == str(self.request.user)
        if match_user:
            context = {'user': user.last(), 'first_name': user.last().first_name}
            if user.exists():
                user_type = Profile.objects.get(user=user.last()).user_type
                context.update({'user_type': user_type})  
            return render(request, self.template_name, context=context)
        else:
            return redirect('home')
        

    def post(self, request, *args, **kwargs):
        post_data = self.request.POST
        user_id = post_data.get('user')
        name = post_data.get('name')
        password = post_data.get('password')
        user = User.objects.filter(username=user_id)
        get_user = user.last()
        auth_user_pwd = authenticate(username=user_id, password=password)
        if user.exists() and auth_user_pwd:
            get_user.first_name = name
            get_user.save()
            messages.success(request, "PROFILE UPDATED")
        else:
            messages.warning(request, "USER NOT MATCHED !!")

        return HttpResponseRedirect(self.request.path_info)
    

class MyPasswordResetView(View):
    template_name = "reset_password.html"

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)

    def post(self, request, *args, **kwargs):
        post_data = self.request.POST
        associated_users = User.objects.filter(username=post_data['email'])
        current_site = get_current_site(self.request)
        if associated_users.exists():
            user = associated_users.last()
            subject = "Password Reset Requested"
            email_template_name = "reset_password_email.txt"
            c = {
                "email": user.email,
                'domain': current_site.domain,
                'site_name': 'Study HUB',
                "uid": urlsafe_base64_encode(force_bytes(user.pk)),
                "user": user,
                'token': default_token_generator.make_token(user),
                'protocol': 'http',
            }
            email = render_to_string(email_template_name, c)
            try:
                mail_info = MIMEText(email)
                mail_info['Subject'] = subject
                mail_info['From'] = settings.DEFAULT_FROM_EMAIL
                mail_info['To'] = user.email
                smtp_server = settings.EMAIL_HOST
                smtp_port = settings.EMAIL_PORT
                with smtplib.SMTP(smtp_server, smtp_port) as server:
                    server.starttls()
                    server.login(settings.DEFAULT_FROM_EMAIL, settings.EMAIL_HOST_PASSWORD)
                    server.send_message(mail_info)
                messages.info(self.request, f'Reset Password Mail Sent to {user.username}')
                return redirect('home')
            except:
                return HttpResponse('Invalid header found.')
        else: 
            messages.info(self.request, 'User not exists !!')

        return HttpResponseRedirect(self.request.path_info)


class PasswordResetConfirmView(View):
    template_name='password_reset_form.html'

    def get(self, request, *args, **kwargs):
        return render(self.request, self.template_name)
    
    def post(self, request, *args, **kwargs):
        post_data = self.request.POST
        if 'new_password' in post_data and 'confirm_password' in post_data:
            password_new = post_data.get('new_password')
            password_confirm = post_data.get('confirm_password')
            if password_new == password_confirm:
                try:
                    # Decode UID to get the user ID
                    uid = urlsafe_base64_decode(kwargs['uidb64']).decode()
                    # Retrieve user by user ID
                    user = User.objects.get(pk=uid)
                except:
                    user = None
                if user:
                    user.set_password(password_confirm)
                    user.save()
                    messages.info(self.request, 'Sucessfully password saved')
                    return redirect('home') 
            else:
                    messages.info(self.request, 'Password not matched !!') 
                    
        else:
            messages.info(self.request, 'Please enter new and confirm password !!') 

        return HttpResponseRedirect(self.request.path_info) 
    

class ChangePasswordView(View):
    template_name='change_password.html'

    def get(self, request, *args, **kwargs):
        user_id = self.request.user
        user = get_object_or_404(User, username=user_id)
        context = {'user': user}
        return render(self.request, self.template_name, context)
    
    def post(self, request, *args, **kwargs):
        post_data = self.request.POST
        if 'new_password' in post_data and 'confirm_password' in post_data:
            password_new = post_data.get('new_password')
            password_confirm = post_data.get('confirm_password')
            if password_new == password_confirm:
                try:
                    # Retrieve user by user ID
                    user = User.objects.get(pk=kwargs['id'])
                except:
                    user = None
                if user:
                    user.set_password(password_confirm)
                    user.save()
                    messages.info(self.request, 'Sucessfully password saved')
                    return redirect('home') 
            else:
                    messages.info(self.request, 'Password not matched !!') 
                    
        else:
            messages.info(self.request, 'Please enter new and confirm password !!') 

        return HttpResponseRedirect(self.request.path_info)
    

class SubjectView(LoginRequiredMixin, TemplateView):
    template_name = 'subjects.html'
    login_url = '/sign_in/'


class AllNotesView(LoginRequiredMixin, View):
    template_name = 'notes.html'
    login_url = '/sign_in/'

    def get(self, request, *args, **kwargs):
        kwargs_data = self.kwargs
        get_data = self.request.GET
        user_id = self.request.user
        user = User.objects.filter(username=user_id)
        context = {}
        if user.exists():
            user_profile = Profile.objects.filter(user=user.last())
            context.update({'usertype': user_profile.last().user_type})
        if 'sub_class' in kwargs_data and self.kwargs['sub_class'] != '':
            subject_class = self.kwargs['sub_class']
            split_url = subject_class.split('_')
            subject = split_url[0]
            class_no = split_url[-1]
            notes = Notes.objects.filter(subject_name=subject, class_standard=class_no).order_by('-created_at')
            context.update({'subject_class': subject_class, 'notes': notes})
         # <QueryDict: {'subject': ['physics'], 'class_standard': ['8']}>
        elif 'subject' in get_data and 'class_standard' in get_data:
            context.update({'search_results': True})
            if get_data['class_standard'] == '' and get_data['subject'] != '':
                notes = Notes.objects.filter(subject_name=get_data['subject']).order_by('-created_at')
                context.update({'notes': notes})
            elif get_data['subject'] == '' and get_data['class_standard'] != '':
                class_no = int(get_data['class_standard'])
                notes = Notes.objects.filter(class_standard=class_no).order_by('-created_at')
                context.update({'notes': notes})
            elif get_data['subject'] != '' and get_data['class_standard'] != '':
                class_no = int(get_data['class_standard'])
                notes = Notes.objects.filter(class_standard=class_no,
                                             subject_name=get_data['subject']).order_by('-created_at')
                context.update({'notes': notes})
            else:
                notes = Notes.objects.all().order_by('-created_at')
                context.update({'notes': notes})

        else:
            notes = Notes.objects.all().order_by('-created_at')
            context.update({'notes': notes})
        return render(self.request, self.template_name, context)
    
    def post(self, request, *args, **kwargs):

        post_data = self.request.POST
        user_id = post_data.get('user')
        subject = post_data.get('subject')
        class_standard = post_data.get('class_standard')
        topic = post_data.get('topic')
        details = post_data.get('details')
        links = post_data.get('links')

        user = User.objects.filter(username=user_id)
        timezone.activate('Asia/Kolkata')
        current_datetime = timezone.localtime(timezone.now())

        # Save notes
        notes = Notes.objects.create(upload_by=user.last(), subject_name=subject, class_standard=class_standard,
                            topic=topic, description=details, created_at=current_datetime, links=links)
        notes.save()

        messages.info(self.request, ' Note Added ')

        return HttpResponseRedirect(self.request.path_info)
    
    
class NoteView(LoginRequiredMixin, View):
    template_name = "view_note.html"
    login_url = '/sign_in/'

    def get(self, request, *args, **kwargs):
        subject_id = self.kwargs['id']
        context = {'subject_id': subject_id}
        notes = get_object_or_404(Notes, id=subject_id)
        user_profile = Profile.objects.filter(user=notes.upload_by)
        if user_profile.exists() and user_profile.last().user == self.request.user:
            context.update({'usertype': user_profile.last().user_type})
        links = str(notes.links)
        # make youtube link as embed
        if 'watch?v=' in links:
            links = links.split("watch?v=")[-1]
        elif '?feature=shared' in links:
            removed_text = links.replace("?feature=shared",'')
            links = removed_text.split('/')[-1]
        context.update({'links': links})
        # filter all doc of notes
        subjects = ['Computer', 'Physics', 'Chemistry', 'Mathematics', 'Biology']
        classes = [6, 7, 8, 9, 10, 11, 12]
        context.update({'note': notes, 'subjects': subjects, 'classes': classes})
        
        return render(self.request, self.template_name, context) 
    
    def post(self, request, *args, **kwargs):

        post_data = self.request.POST
        note_id = post_data.get('id')
        user_id = post_data.get('user')
        subject = post_data.get('subject')
        class_standard = post_data.get('class_standard')
        topic = post_data.get('topic')
        details = post_data.get('details')
        links = post_data.get('links')
        user = User.objects.filter(username=user_id)
        # get local current date time
        timezone.activate('Asia/Kolkata')
        current_datetime = timezone.localtime(timezone.now())
        # save notes
        note_instance = get_object_or_404(Notes, id=note_id)
        note_instance.subject_name = subject
        note_instance.class_standard = class_standard
        note_instance.topic = topic
        note_instance.description = details
        note_instance.created_at = current_datetime
        note_instance.links = links
        note_instance.save()
       
        messages.info(self.request, ' Note Added ')

        return HttpResponseRedirect(self.request.path_info)


class DeleteNoteView(LoginRequiredMixin, View):
    login_url = '/sign_in/'

    def post(self, request, *args, **kwargs):
        note_id = self.kwargs['id']
        note_instance = get_object_or_404(Notes, id=note_id)
        note_instance.delete()
        messages.info(self.request, 'Note Deleted ')
        return redirect('notes')
    

def chatgpt(topic):
    api_key = settings.API_KEY  # GPT 3
    # Send prompt GPT 3
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}"
    }
    payload = {
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "system", "content": "As I am Student, You are a good helpfull assistant to explain."},
            {"role": "user", "content": str(topic)}
            ]
    }
    response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
    response_json = response.json()
    # print(response_json)
    try:
        response_content = response_json['choices'][0]['message']['content']
        # print(response_content, 'response_content')
    except Exception as e:
        print('Exception ERROR ====> ', e)
        
    return response_json
        

class chatAiView(LoginRequiredMixin, View):
    login_url = '/sign_in/'
    template_name = 'chatai.html'

    def get(self, request, *args, **kwargs):
        return render(self.request, self.template_name)
    
    def post(self, request, *args, **kwargs):
        topic = self.request.POST.get('topic')
        data = chatgpt(topic)
        return JsonResponse(data)
    

class ParentalGuidanceView(LoginRequiredMixin, View):
    template_name = "parentalguide.html"
    login_url = '/sign_in/'

    def get(self, request, *args, **kwargs):
        print(self.request.GET)
        get_data = self.request.GET
        context = {}
        if 'choice' in get_data:
            choice = get_data['choice']
            get_choice = ParentGuidance.objects.filter(issue_name=choice)
            content = get_choice.last().issue_description
            context.update({'content': content})
        return render(self.request, self.template_name, context)
    
    def post(self, request, *args, **kwargs):
        post_data = self.request.POST
        print(post_data, 'post data')
        if 'content' in post_data:
            content = self.request.POST.get('content')
            data = chatgpt(content)
            return JsonResponse(data)
        else:
            messages.info(self.request, "You didn't select the below choices..")
        
        return HttpResponseRedirect(self.request.path_info)
