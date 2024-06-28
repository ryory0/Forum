from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.core.mail import send_mail
from django.contrib.auth.base_user import BaseUserManager
from django.urls import reverse
from django.conf import settings
import uuid
import datetime
from django.core.mail import send_mail

#メール送信
from django.conf import settings
from django.core.mail import send_mail
from django.db.models.signals import post_save
from datetime import datetime, timedelta
from django.dispatch import receiver
class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, username, email, password, **extra_fields):
        """
        Create and save a user with the given username, email, and password.
        """
        if not username:
            raise ValueError('The given username must be set')
        email = self.normalize_email(email)
        username = self.model.normalize_username(username)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(username, email, password, **extra_fields)

    def create_superuser(self, username, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(username, email, password, **extra_fields)

class User(AbstractBaseUser, PermissionsMixin):
    """
    An abstract base class implementing a fully featured User model with
    admin-compliant permissions.
    Username and password are required. Other fields are optional.
    """
    username_validator = UnicodeUsernameValidator()

    username = models.CharField(
        _('username'),
        max_length=150,
        unique=True,
        help_text=_('Required. 150 characters or fewer. Letters, digits and @/./+/-/_ only.'),
        validators=[username_validator],
        error_messages={
            'unique': _("A user with that username already exists."),
        },
    )
    last_name = models.CharField(_('last_name'), max_length=100)
    first_name = models.CharField(_('first_name'), max_length=100)
    email = models.EmailField(_('email address'), blank=True)
    
    is_staff = models.BooleanField(
        _('staff status'),
        default=False,
        help_text=_('Designates whether the user can log into this admin site.'),
    )
    is_active = models.BooleanField(
        _('active'),
        default=False,
        help_text=_(
            'Designates whether this user should be treated as active. '
            'Unselect this instead of deleting accounts.'
        ),
    )
    date_joined = models.DateTimeField(_('date joined'), default=timezone.now)

    objects = UserManager()

    EMAIL_FIELD = 'email'
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    class Meta:
        verbose_name = _('user')
        verbose_name_plural = _('users')

    def clean(self):
        super().clean()
        self.email = self.__class__.objects.normalize_email(self.email)

    def get_full_name(self):
        """
        Return the first_name plus the last_name, with a space in between.
        """
        full_name = '%s %s' % (self.first_name, self.last_name)
        return full_name.strip()

    def get_short_name(self):
        """Return the short name for the user."""
        return self.first_name

#有効期限付きアクティベーション用トークン保持テーブルを実装
class UserActivateTokensManager(models.Manager):

    def activate_user_by_token(self, activate_token):
        user_activate_token = self.filter(
            activate_token=activate_token,
            expired_at__gte=datetime.now() # __gte = greater than equal
        ).first()
        if hasattr(user_activate_token, 'user'):
            user = user_activate_token.user
            user.is_active = True
            user.save()
            return user

class UserActivateTokens(models.Model):

    token_id = models.UUIDField(default=uuid.uuid4, primary_key=True, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    activate_token = models.UUIDField(default=uuid.uuid4)
    expired_at = models.DateTimeField()

    objects = UserActivateTokensManager()

#ユーザー生成時にトークンを発行しメール送信をする処理の実装    
@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def publish_activate_token(sender, instance, created, **kwargs):
    if created and not instance.is_active:
        user_activate_token = UserActivateTokens.objects.create(
            user=instance,
            expired_at=datetime.now()+timedelta(days=settings.ACTIVATION_EXPIRED_DAYS),
        )
        subject = 'Please Activate Your Account'
        message = f'以下のURLにアクセスしていただきますと登録が完了となります。 \n https://forum-appry-be3dcf92c9d9.herokuapp.com/users/{user_activate_token.activate_token}/activation/'
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [
            instance.email,
        ]
        send_mail(subject, message, from_email, recipient_list)
    elif created and instance.is_active:
        subject = 'Activated! Your Account!'
        message = 'ユーザーが使用できるようになりました'
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [
            instance.email,
        ]
        send_mail(subject, message, from_email, recipient_list)

#投稿
class Thread(models.Model):
    title = models.CharField(max_length = 200)
    content = models.TextField(max_length=1000)
    view_counts = models.IntegerField(default=0)
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    thread_likes = models.ManyToManyField(
        User,
        through='LikeForPost',
        related_name='thread_likes',
        blank=True,
    )
    def __str__(self):
        return self.content
    
    def thread_like_count(self):
        return self.thread_likes.count()
 
    def get_absolute_url(self):
        return reverse('app_folder:detail', kwargs={'pk': self.pk})
    
class Comment(models.Model):
    comment = models.TextField(blank=False, null=False)
    user    = models.ForeignKey(User, on_delete=models.CASCADE)
    thread  = models.ForeignKey(Thread, on_delete=models.CASCADE)
    created_datetime = models.DateTimeField(auto_now_add=True)
    updated_datetime = models.DateTimeField(auto_now=True)
    comment_likes = models.ManyToManyField(
        User,
        through='LikeForComment',
        related_name='comment_likes',
        blank=True,
    )
    def comment_like_count(self):
        return self.comment_likes.count()
    
    def __str__(self):
        return self.comment

class LikeForPost(models.Model):
    """投稿に対するいいね"""
    target = models.ForeignKey(Thread, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(default=timezone.now)

class LikeForComment(models.Model):
    """コメントに対するいいね"""
    target = models.ForeignKey(Comment, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    timestamp = models.DateTimeField(default=timezone.now)

class ViewHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    thread = models.ForeignKey(Thread, on_delete=models.CASCADE)
    viewed_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} viewed {self.thread.title} at {self.viewed_at}"
