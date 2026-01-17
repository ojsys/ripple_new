from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from .models import (
    AboutPage, TeamMember, SiteSettings, HeroSlider,
    Testimonial, Contact, Announcement
)
from .forms import ContactForm


def about_page(request):
    """Display the About page with team members."""
    try:
        about = AboutPage.objects.first()
    except AboutPage.DoesNotExist:
        about = None

    team_members = TeamMember.objects.filter(is_active=True, is_visible=True).order_by('order')
    testimonials = Testimonial.objects.filter(is_active=True)[:6]

    context = {
        'about': about,
        'team_members': team_members,
        'testimonials': testimonials,
    }
    return render(request, 'cms/about_page.html', context)


def contact_page(request):
    """Display and handle contact form."""
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'Thank you for your message! We will get back to you soon.')
            return redirect('cms:contact')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ContactForm()

    context = {
        'form': form,
    }
    return render(request, 'cms/contact.html', context)


@require_POST
def contact_ajax(request):
    """Handle contact form submission via AJAX."""
    form = ContactForm(request.POST)
    if form.is_valid():
        form.save()
        return JsonResponse({
            'success': True,
            'message': 'Thank you for your message! We will get back to you soon.'
        })
    else:
        return JsonResponse({
            'success': False,
            'errors': form.errors
        }, status=400)


def testimonials_page(request):
    """Display all testimonials."""
    testimonials = Testimonial.objects.filter(is_active=True)

    context = {
        'testimonials': testimonials,
    }
    return render(request, 'cms/testimonials.html', context)


def team_page(request):
    """Display all team members."""
    team_members = TeamMember.objects.filter(is_active=True, is_visible=True).order_by('order')

    context = {
        'team_members': team_members,
    }
    return render(request, 'cms/team.html', context)
