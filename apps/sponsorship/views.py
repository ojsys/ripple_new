from django.shortcuts import render, redirect
from django.contrib import messages
from .models import SponsorshipPage, SponsorshipTier
from .forms import SponsorshipInquiryForm


def sponsorship_page(request):
    page = SponsorshipPage.load()
    tiers = SponsorshipTier.objects.filter(is_active=True)
    form = SponsorshipInquiryForm()
    return render(request, 'sponsorship/sponsorship_page.html', {
        'page': page,
        'tiers': tiers,
        'form': form,
    })


def submit_inquiry(request):
    if request.method != 'POST':
        return redirect('sponsorship:sponsorship_page')
    form = SponsorshipInquiryForm(request.POST)
    if form.is_valid():
        form.save()
        return redirect('sponsorship:thank_you')
    page = SponsorshipPage.load()
    tiers = SponsorshipTier.objects.filter(is_active=True)
    messages.error(request, "Please correct the errors below.")
    return render(request, 'sponsorship/sponsorship_page.html', {
        'page': page,
        'tiers': tiers,
        'form': form,
    })


def thank_you(request):
    return render(request, 'sponsorship/thank_you.html')
