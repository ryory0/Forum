from django.shortcuts import render
from django.views import View
from .models import UserActivateTokens
from django.http import HttpResponse  
from .models import Thread, Comment, LikeForPost, User, LikeForComment, ViewHistory
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib import messages
from django.views.generic import TemplateView # テンプレートタグ
from .forms import AccountForm, CommentForm# ユーザーアカウントフォーム
from django.shortcuts import get_object_or_404
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect
from django.db.models import Sum

#ajax通信
from django.http.response import JsonResponse
# ログイン・ログアウト処理に利用
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse
from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.views import generic
from django.db.models import Q # 追加
from django.core.paginator import Paginator

#投稿削除
class DeleteView(LoginRequiredMixin, generic.edit.DeleteView):
    model = Thread
    success_url = reverse_lazy('app_folder:thread')

#投稿検索
class IndexView(generic.ListView):
    template_name = 'app_folder/thread_list.html'
    model = Thread
    paginate_by = 10
    def get_queryset(self):
        q_word = self.request.GET.get('query')
        # チェックボックスにチェックが入っている項目だけを検索対象とする
        selected_title = self.request.GET.get('title')
        selected_article = self.request.GET.get('article')
 
        if q_word:
            if selected_title and selected_article:
                object_list = Thread.objects.filter(
                    Q(title__icontains=q_word) | Q(content__icontains=q_word)).order_by("-pk")
            elif selected_title:
                object_list = Thread.objects.filter(Q(title__icontains=q_word)).order_by("-pk")
            else: # 投稿内容のみ、または両方ともチェックされていない場合は投稿内容のみを検索する
                object_list = Thread.objects.filter(Q(content__icontains=q_word)).order_by("-pk")
        else:
            object_list = Thread.objects.all().order_by("-pk")
        # Paginator
        paginator = Paginator(object_list, self.paginate_by)
        page      = self.request.GET.get('page')
        try:
            page_obj = paginator.page(page)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)
        # テンプレートに変数を渡す
        messages.add_message(self.request, messages.INFO, page_obj)
        return object_list

class CreateView(LoginRequiredMixin, generic.edit.CreateView):
    model = Thread
    fields = ['content', 'title', ]
 
    def form_valid(self, form):
        form.instance.author = self.request.user
        return super(CreateView, self).form_valid(form)
        
class BbsView(View):
    template_name = "app_folder/comment.html"
    model = Thread
    paginate_by = 30

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        thread = self.object
        comments = Comment.objects.filter(thread=thread).select_related('user')

        liked_comments = comments.filter(likeforcomment__user=self.request.user)
        context['liked_comment_pks'] = list(liked_comments.values_list('pk', flat=True))

        like_for_post_count = thread.likeforpost_set.count()
        context['like_for_post_count'] = like_for_post_count

        if thread.likeforpost_set.filter(user=self.request.user).exists():
            context['is_user_liked_for_post'] = True
        else:
            context['is_user_liked_for_post'] = False

        like_for_comment_count = comments.aggregate(Sum('likeforcomment__value'))['likeforcomment__value__sum'] or 0
        context['like_for_comment_count'] = like_for_comment_count

        if liked_comments.exists():
            context['is_user_liked_for_comment'] = True
        else:
            context['is_user_liked_for_comment'] = False

        return context
    
    def get(self, request, pk, *args, **kwargs):
        thread = Thread.objects.get(pk=pk)
        form = CommentForm()
        comments = Comment.objects.filter(thread=thread).select_related('user')
        # Paginator
        paginator = Paginator(comments, self.paginate_by)
        page = self.request.GET.get('page')
        try:
            page_obj = paginator.page(page)
        except PageNotAnInteger:
            page_obj = paginator.page(1)
        except EmptyPage:
            page_obj = paginator.page(paginator.num_pages)

        content = {
            "page_obj":page_obj,
            "thread":thread,
            "form":form,
        }
        
        if request.user.is_authenticated:
            liked_comments = comments.filter(likeforcomment__user=self.request.user)
            content['liked_comment_pks'] = list(liked_comments.values_list('pk', flat=True))

            like_for_post_count = thread.likeforpost_set.count()
            content['like_for_post_count'] = like_for_post_count

            if thread.likeforpost_set.filter(user=self.request.user).exists():
                content['is_user_liked_for_post'] = True
            else:
                content['is_user_liked_for_post'] = False

            like_for_comment_count = comments.filter(likeforcomment__user=self.request.user)
            content['liked_comment_pks'] = list(liked_comments.values_list('pk', flat=True))
            content['like_for_comment_count'] = like_for_comment_count

            if liked_comments.exists():
                content['is_user_liked_for_comment'] = True
            else:
                content['is_user_liked_for_comment'] = False
        
        return render(request,"app_folder/comment.html",content)

display_comments = BbsView.as_view()

@login_required
def create_comment(request):
    thread_id = request.POST['thread_id']
    #入力値をフォームに追加
    form = CommentForm(request.POST)
    #入力内容が正しければ
    if form.is_valid():
        #DBに登録する準備を行う
        comment = form.save(commit=False)
        #commentにログイン中ユーザー情報を追加
        comment.user = request.user
        comment.thread_id = thread_id
        #DBに登録
        comment.save()
        messages.success(request, "投稿が完了しました！")
    return redirect('app_folder:display_comments', pk = thread_id)

class DetailView(generic.DetailView):
    template_name = "app_folder/thread_detail.html"#必要ない
    model = Thread
    
    def get_context_data(self,**kwargs):
        context = super().get_context_data(**kwargs)
        like_for_post_count = self.object.likeforpost_set.count()
        # ポストに対するイイね数
        context['like_for_post_count'] = like_for_post_count
        if self.request.user.is_authenticated:
            # ログイン中のユーザーがイイねしているかどうか
            if self.object.likeforpost_set.filter(user=self.request.user).exists():
                context['is_user_liked_for_post'] = True
            else:
                context['is_user_liked_for_post'] = False

        return context
    
    def get(self, request, *args, **kwargs):
        # 閲覧履歴を記録する

        if self.request.user.is_authenticated:
            thread = self.get_object()
            ViewHistory.objects.create(user=self.request.user, thread=thread)
        return super().get(request, *args, **kwargs)
    
@login_required   
def like_for_post(request):
    post_pk = request.POST.get('post_pk')
    context = {
        'user': f'{request.user.last_name} {request.user.first_name}',
    }
    post = get_object_or_404(Thread, pk=post_pk)
    like = LikeForPost.objects.filter(target=post, user=request.user)

    if like.exists():
        like.delete()
        context['method'] = 'delete'
    else:
        like.create(target=post, user=request.user)
        context['method'] = 'create'

    context['like_for_post_count'] = post.likeforpost_set.count()

    return JsonResponse(context)

@login_required 
def like_for_comment(request):
    comment_pk = request.POST.get('comment_pk')
    context = { 
    }
    comment = get_object_or_404(Comment, pk=comment_pk)
    like = LikeForComment.objects.filter(target=comment, user=request.user)
    if like.exists():
        like.delete()
        context['method'] = 'delete'
    else:
        like.create(target=comment, user=request.user)
        context['method'] = 'create'

    context['like_for_comment_count'] = comment.likeforcomment_set.count()

    return JsonResponse(context)

class CreateView(LoginRequiredMixin, generic.edit.CreateView):
    model = Thread
    fields = ['content', 'title', ]
 
    def form_valid(self, form):
        form.instance.author = self.request.user
        return super(CreateView, self).form_valid(form)

#投稿更新
class UpdateView(LoginRequiredMixin, generic.edit.UpdateView):
    model = Thread
    fields = ['content', 'title', ]
 
    def dispatch(self, request, *args, **kwargs):
        obj = self.get_object()
 
        if obj.author != self.request.user:
            raise PermissionDenied('You do not have permission to edit.')
 
        return super(UpdateView, self).dispatch(request, *args, **kwargs)

#ログイン
def Login(request):
    # POST
    if request.method == 'POST':
        # フォーム入力のユーザーID・パスワード取得
        print(request.POST)
        username = request.POST.get('username')
        Pass = request.POST.get('password')
        # Djangoの認証機能
        user = authenticate(username=username, password=Pass)

        # ユーザー認証
        if user:
            #ユーザーアクティベート判定
            if user.is_active:
                # ログイン
                login(request,user)
                # ホームページ遷移
                return HttpResponseRedirect(reverse('app_folder:thread'))
            else:
                # アカウント利用不可
                return HttpResponse("アカウントが有効ではありません")
        # ユーザー認証失敗
        else:
            return HttpResponse("ログインIDまたはパスワードが間違っています")
    # GET
    else:
        return render(request, 'app_folder/login.html')

#ログアウト
@login_required
def Logout(request):
    logout(request)
    # ログイン画面遷移
    return HttpResponseRedirect(reverse('app_folder:thread'))

#ホーム
@login_required
def home(request):
    login_user_id = request.user.id
    page = request.GET.get('page', 1)
    your_thread = Thread.objects.filter(author_id=login_user_id).order_by("-pk")
    
    # Paginator
    paginator = Paginator(your_thread, 5)
    try:
        your_thread = paginator.page(page)
    except PageNotAnInteger:
        your_thread = paginator.page(1)
    except EmptyPage:
        your_thread = paginator.page(paginator.num_pages)
    
    result = User.objects.get(id=login_user_id)
    
    # 最近の閲覧履歴を取得
    recent_view_history = ViewHistory.objects.filter(user=request.user).order_by('-viewed_at')[:5]
    
    params = {
        "UserID": result.username,
        "page_obj": your_thread,
        "recent_view_history": recent_view_history,
    }
    
    return render(request, "app_folder/my_page.html", params)


#新規登録
class  AccountRegistration(TemplateView):
    def __init__(self):
        self.params = {
            "AccountCreate": False,
            "account_form": AccountForm(),
        }

    # Get処理
    def get(self, request):
        self.params["account_form"] = AccountForm()
        self.params["AccountCreate"] = False
        return render(request, "app_folder/register.html", context=self.params)

    # Post処理
    def post(self, request):
        self.params["account_form"] = AccountForm(data=request.POST)

        # フォーム入力の有効検証
        if self.params["account_form"].is_valid():

            # アカウント情報をDB保存
            account = self.params["account_form"].save()
            # パスワードをハッシュ化
            account.set_password(account.password)
            # ハッシュ化パスワード更新
            account.save()
            # アカウント作成情報更新
            self.params["AccountCreate"] = True
        else:
            # フォームが有効でない場合
            print(self.params["account_form"].errors)

        return render(request, "app_folder/register.html", context=self.params)

def activate_user(request, activate_token):
    print(f'Activating user with token: {activate_token}')
    try:
        activated_user = UserActivateTokens.objects.activate_user_by_token(
            activate_token)
        print(f'User found: {activated_user}')
    except UserActivateTokens.DoesNotExist:
        print('Invalid token')
        return HttpResponse('無効なトークンです')

    if activated_user.is_active:
        message = 'ユーザーのアクティベーションが完了しました'
    else:
        message = 'アクティベーションが失敗しています。管理者に問い合わせてください'

    return HttpResponse(message)
