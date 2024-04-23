from django import forms
from .models import Post, Comment, User


class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        # fields = '__all__'
        exclude = ('author', 'is_published')
        widgets = {
            'pub_date': forms.DateTimeInput(
                format='%Y-%m-%dT%H:%M',
                attrs={'type': 'datetime-local'}
            )
        }


class CommentForm(forms.ModelForm):

    class Meta:
        model = Comment
        fields = ('text',)


class UserForm(forms.ModelForm):

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'username', 'email')
