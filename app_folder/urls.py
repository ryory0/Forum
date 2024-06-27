from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

app_name = 'app_folder'
urlpatterns = [
    path('thread_list', views.IndexView.as_view(), name='thread'),
    path('display_comments/<int:pk>/', views.display_comments, name='display_comments'),
    path('resister', views.AccountRegistration.as_view(), name='register'),
    path("my_page", views.home, name="my_page"),
    path('accounts/login/',views.Login,name='Login'),
    path("logout",views.Logout,name="Logout"),
    path('<int:pk>', views.DetailView.as_view(), name='detail'),
    path('create/', views.CreateView.as_view(), name='create'),
    path('<int:pk>/update/', views.UpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', views.DeleteView.as_view(), name='delete'),
    path('like_for_post/', views.like_for_post, name='like_for_post'),
    path('like_for_comment/', views.like_for_comment, name='like_for_comment'),
    path("create_comment/", views.create_comment, name="create_comment"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
