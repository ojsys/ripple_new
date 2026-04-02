from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Sum
from decimal import Decimal

from apps.projects.models import Project
from .models import FounderWithdrawalRequest
from .forms import FounderWithdrawalForm


@login_required
def founder_withdrawal_request(request, project_id):
    """Founder requests withdrawal of investment funds for a specific project."""
    if request.user.user_type != 'founder':
        messages.error(request, 'Only founders can request withdrawals.')
        return redirect('accounts:dashboard')

    project = get_object_or_404(
        Project,
        id=project_id,
        creator=request.user,
        listing_type='venture',
        status='approved',
    )

    available = FounderWithdrawalRequest.get_available_amount(project)

    pending_withdrawals = FounderWithdrawalRequest.objects.filter(
        project=project,
        status__in=['pending', 'approved', 'processing']
    )

    if request.method == 'POST':
        form = FounderWithdrawalForm(request.POST, project=project)
        if form.is_valid():
            withdrawal = form.save(commit=False)
            withdrawal.project = project
            withdrawal.founder = request.user
            withdrawal.save()
            messages.success(
                request,
                f'Withdrawal request for ${withdrawal.amount_usd:,.2f} submitted successfully! '
                f'You will receive ₦{withdrawal.amount_ngn:,.2f} once approved and processed.'
            )
            return redirect('funding:founder_withdrawal_detail', reference=withdrawal.reference)
    else:
        form = FounderWithdrawalForm(project=project)

    context = {
        'project': project,
        'form': form,
        'available': available,
        'pending_withdrawals': pending_withdrawals,
        'ngn_rate': FounderWithdrawalRequest.NGN_RATE,
        'direct_investment': project.total_investment_raised,
        'srt_tokens': project.srt_amount_raised,
        'srt_usd': project.srt_raised_usd,
        'total_investment': project.total_investment_raised + project.srt_raised_usd,
    }
    return render(request, 'funding/founder_withdrawal_form.html', context)


@login_required
def founder_withdrawal_detail(request, reference):
    """View a specific withdrawal request."""
    withdrawal = get_object_or_404(
        FounderWithdrawalRequest,
        reference=reference,
        founder=request.user,
    )
    return render(request, 'funding/founder_withdrawal_detail.html', {'withdrawal': withdrawal})


@login_required
def founder_withdrawals(request):
    """List all withdrawal requests for the current founder."""
    if request.user.user_type != 'founder':
        messages.error(request, 'Only founders can view withdrawals.')
        return redirect('accounts:dashboard')

    status_filter = request.GET.get('status', '')
    withdrawals = FounderWithdrawalRequest.objects.filter(founder=request.user)

    if status_filter:
        withdrawals = withdrawals.filter(status=status_filter)

    stats = {
        'total_withdrawn_usd': FounderWithdrawalRequest.objects.filter(
            founder=request.user, status='completed'
        ).aggregate(total=Sum('amount_usd'))['total'] or Decimal('0'),
        'pending_count': FounderWithdrawalRequest.objects.filter(
            founder=request.user, status='pending'
        ).count(),
        'completed_count': FounderWithdrawalRequest.objects.filter(
            founder=request.user, status='completed'
        ).count(),
    }

    # Ventures the founder can withdraw from, with totals precomputed
    raw_ventures = Project.objects.filter(
        creator=request.user,
        listing_type='venture',
        status='approved',
    ).order_by('title')
    venture_projects = [
        {
            'project': p,
            'total': p.total_investment_raised + p.srt_raised_usd,
            'available': FounderWithdrawalRequest.get_available_amount(p),
        }
        for p in raw_ventures
    ]

    paginator = Paginator(withdrawals, 15)
    page = request.GET.get('page', 1)
    withdrawals = paginator.get_page(page)

    context = {
        'withdrawals': withdrawals,
        'stats': stats,
        'current_status': status_filter,
        'venture_projects': venture_projects,
    }
    return render(request, 'funding/founder_withdrawals.html', context)


@login_required
def cancel_founder_withdrawal(request, reference):
    """Cancel a pending withdrawal request."""
    withdrawal = get_object_or_404(
        FounderWithdrawalRequest,
        reference=reference,
        founder=request.user,
        status='pending',
    )
    if withdrawal.cancel():
        messages.success(request, 'Withdrawal request cancelled.')
    else:
        messages.error(request, 'Unable to cancel this request.')
    return redirect('funding:founder_withdrawals')
