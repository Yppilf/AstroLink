from django import forms

class RichTextWidget(forms.Textarea):
    template_name = "widgets/richtext.html"