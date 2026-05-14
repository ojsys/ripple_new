from django.shortcuts import render, redirect
from django.contrib import messages
from django.utils import timezone
from .models import IncubatorAcceleratorPage, IncubatorApplication
from .forms import IncubatorApplicationForm


WEEKS = [
    (1,  "The Founder Mindset"),
    (2,  "Problem Discovery"),
    (3,  "Market Research & Sizing"),
    (4,  "Customer Segmentation & Personas"),
    (5,  "Solution Design & MVP Thinking"),
    (6,  "Business Model Design"),
    (7,  "Brand Identity & Positioning"),
    (8,  "Go-to-Market Strategy"),
    (9,  "Product Development Basics"),
    (10, "Finance for Founders"),
    (11, "Pitching & Storytelling"),
    (12, "Demo Day & What's Next"),
]

def incubator_page(request):
    """Display the Incubator/Accelerator program page."""
    try:
        page = IncubatorAcceleratorPage.objects.first()
    except IncubatorAcceleratorPage.DoesNotExist:
        page = None

    context = {
        'page': page,
        'weeks': WEEKS,
    }
    return render(request, 'incubator/incubator_accelerator_page.html', context)


def apply(request):
    """Handle incubator application form."""
    # Check if applications are open
    try:
        page = IncubatorAcceleratorPage.objects.first()
        if page and not page.is_accepting_applications:
            messages.warning(request, 'Applications are currently closed. Please check back later.')
            return redirect('incubator:incubator_page')

        if page and page.application_deadline and page.application_deadline < timezone.now():
            messages.warning(request, 'The application deadline has passed.')
            return redirect('incubator:incubator_page')
    except IncubatorAcceleratorPage.DoesNotExist:
        pass

    if request.method == 'POST':
        form = IncubatorApplicationForm(request.POST, request.FILES)
        if form.is_valid():
            application = form.save()
            messages.success(
                request,
                f'Thank you, {application.applicant_name}! Your application for "{application.project}" has been submitted successfully.'
            )
            return redirect('incubator:thank_you')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = IncubatorApplicationForm()

    context = {
        'form': form,
        'page': IncubatorAcceleratorPage.objects.first(),
    }
    return render(request, 'incubator/incubator_application_form.html', context)


def thank_you(request):
    """Display thank you page after successful application."""
    return render(request, 'incubator/thank_you.html')
