from django.db import models
from django.contrib.auth.models import User


def user_directory_path(instance, filename):
    """
    User directory path to be created
    """
    # file will be uploaded to MEDIA_ROOT / user_<id>/<filename>
    return f'user_{instance.upload_by}/{filename}'


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    user_type = models.CharField(max_length=20)

    def __str__(self):
        """self.user.username"""
        return str(self.user.username)
    

class Notes(models.Model):
    subject_name = models.CharField(max_length=20)
    class_standard = models.IntegerField()
    topic = models.CharField(max_length=50)
    description = models.TextField()
    upload_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField()
    links = models.URLField(null=True)

    def __str__(self):
        return self.topic
    


class ParentGuidance(models.Model):
    issue_name = models.CharField(max_length=50)
    issue_description = models.TextField()

    def __str__(self):
        return self.issue_name
