from django import forms

class CellImageForm(forms.Form):
    uploaded_image = forms.ImageField(
        widget=forms.ClearableFileInput(attrs={
            'class': 'form-control upload-input',
            'accept': '.jpg,.jpeg,.png,.tif,.tiff',
        })
    )