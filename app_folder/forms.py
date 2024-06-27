from django import forms
from .models import User
from .models import Comment


# フォームクラス作成
class AccountForm(forms.ModelForm):
    # パスワード入力：非表示対応
    password = forms.CharField(widget=forms.PasswordInput(attrs={'placeholder': 'password'}),label="パスワード")

    class Meta():
        # ユーザー認証
        model = User
        # フィールド指定
        fields = ('username','email','password',)
        # フィールド名指定
        #labels = {'username':"ユーザーID",'email':"メール"}
        widgets = {
            'username'   : forms.TextInput(attrs={'placeholder': 'username'}),
            'email': forms.TextInput(attrs={'placeholder': 'email'}),
            'password'   : forms.PasswordInput(attrs={'placeholder': 'password'}),
        }

class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ("comment",)