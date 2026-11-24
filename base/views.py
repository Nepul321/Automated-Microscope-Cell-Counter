from django.shortcuts import render
from .forms import CellImageForm
from .models import CellImage

def HomeView(request, *args, **kwargs):
    template = "base/home.html"
    form = CellImageForm(request.POST or None, request.FILES or None)
    cell_image = None

    if request.method == "POST":
        if not request.user.is_authenticated:
            form.add_error(None, "Please sign in before uploading an image.")
        elif form.is_valid():
            try:
                cell_image = CellImage.objects.create(
                    user=request.user,
                    uploaded_image=form.cleaned_data["uploaded_image"],
                )
            except ValueError as error:
                form.add_error("uploaded_image", str(error))

    context = {
        "form": form,
        "cell_image": cell_image,
    }
    return render(request, template, context)