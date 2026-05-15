from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from .models import LMSCourse, LMSModule, LMSLesson, LMSEnrollment, LMSLessonProgress, LMSDeliverableSubmission
from apps.incubator.models import IncubatorApplication


def _can_access_lms(user):
    if not user.is_authenticated or user.user_type != 'founder':
        return False
    # Provisioned students have an LMSEnrollment; fall back to checking an application exists
    if LMSEnrollment.objects.filter(user=user, is_active=True).exists():
        return True
    return IncubatorApplication.objects.filter(applicant_email=user.email).exists()


def _lms_access_denied(request):
    """Redirect unauthenticated users to login; authenticated users to the LMS home with a message."""
    if not request.user.is_authenticated:
        return redirect(f"{reverse('accounts:login')}?next={request.path}")
    messages.warning(
        request,
        "Your account doesn't have access to the LaunchPadi program yet. "
        "If you've applied and been approved, contact us at info@startupripple.com."
    )
    return redirect('lms:lms_home')


def lms_home(request):
    course = LMSCourse.objects.filter(is_active=True).first()
    modules = course.modules.filter(is_published=True) if course else []
    enrollment = None
    if request.user.is_authenticated and course:
        enrollment = LMSEnrollment.objects.filter(user=request.user, course=course).first()
    return render(request, 'lms/home.html', {
        'course': course,
        'modules': modules,
        'enrollment': enrollment,
    })


@login_required
def lms_enroll(request):
    if not _can_access_lms(request.user):
        messages.error(request, "You need to have applied to the LaunchPadi program to access the LMS. Apply first to unlock this content.")
        return _lms_access_denied(request)
    course = LMSCourse.objects.filter(is_active=True).first()
    if not course:
        messages.error(request, "No active course is available at the moment.")
        return redirect('lms:lms_home')
    enrollment, created = LMSEnrollment.objects.get_or_create(user=request.user, course=course)
    if created:
        messages.success(request, "You're enrolled! Start with Week 1 below.")
    return redirect('lms:lms_dashboard')


@login_required
def lms_dashboard(request):
    if not _can_access_lms(request.user):
        messages.error(request, "You need to have applied to LaunchPadi to access this program.")
        return _lms_access_denied(request)
    course = LMSCourse.objects.filter(is_active=True).first()
    if not course:
        return redirect('lms:lms_home')
    enrollment, _ = LMSEnrollment.objects.get_or_create(user=request.user, course=course)
    all_modules = list(course.modules.filter(is_published=True))
    module_data = []
    completed_ids = enrollment.completed_lesson_ids()
    found_current = False
    for module in all_modules:
        lessons = module.lessons.filter(is_published=True)
        total = lessons.count()
        done = sum(1 for l in lessons if l.id in completed_ids)
        percent = int((done / total * 100)) if total else 0
        is_unlocked = enrollment.is_module_unlocked(module, all_modules)
        is_current = is_unlocked and percent < 100 and not found_current
        if is_current:
            found_current = True
        has_deliverable = hasattr(module, 'deliverable')
        submission = None
        if has_deliverable:
            submission = LMSDeliverableSubmission.objects.filter(
                enrollment=enrollment, deliverable=module.deliverable
            ).first()
        module_data.append({
            'module': module,
            'lessons': lessons,
            'total': total,
            'done': done,
            'percent': percent,
            'submission': submission,
            'is_unlocked': is_unlocked,
            'is_current': is_current,
        })
    return render(request, 'lms/dashboard.html', {
        'course': course,
        'enrollment': enrollment,
        'module_data': module_data,
        'overall_percent': enrollment.total_progress_percent(),
    })


@login_required
def module_detail(request, pk):
    if not _can_access_lms(request.user):
        messages.error(request, "You need to have applied to LaunchPadi to access this program.")
        return _lms_access_denied(request)
    module = get_object_or_404(LMSModule, pk=pk, is_published=True)
    course = module.course
    enrollment, _ = LMSEnrollment.objects.get_or_create(user=request.user, course=course)
    all_modules = list(course.modules.filter(is_published=True))
    if not enrollment.is_module_unlocked(module, all_modules):
        prev_idx = next((i for i, m in enumerate(all_modules) if m.pk == module.pk), 1) - 1
        prev_module = all_modules[prev_idx] if prev_idx >= 0 else None
        if prev_module:
            messages.warning(request, f"Complete Week {prev_module.week_number} first to unlock this module.")
        return redirect('lms:lms_dashboard')
    lessons = module.lessons.filter(is_published=True)
    completed_ids = enrollment.completed_lesson_ids()
    exercises = module.exercises.all()
    deliverable = getattr(module, 'deliverable', None)
    submission = None
    if deliverable:
        submission = LMSDeliverableSubmission.objects.filter(
            enrollment=enrollment, deliverable=deliverable
        ).first()
    return render(request, 'lms/module_detail.html', {
        'module': module,
        'lessons': lessons,
        'completed_ids': completed_ids,
        'exercises': exercises,
        'deliverable': deliverable,
        'submission': submission,
        'enrollment': enrollment,
    })


@login_required
def lesson_detail(request, pk):
    if not _can_access_lms(request.user):
        messages.error(request, "You need to have applied to LaunchPadi to access this program.")
        return _lms_access_denied(request)
    lesson = get_object_or_404(LMSLesson, pk=pk, is_published=True)
    module = lesson.module
    course = module.course
    enrollment, _ = LMSEnrollment.objects.get_or_create(user=request.user, course=course)
    all_modules = list(course.modules.filter(is_published=True))
    if not enrollment.is_module_unlocked(module, all_modules):
        messages.warning(request, "Complete the previous module first to unlock this content.")
        return redirect('lms:lms_dashboard')

    if request.method == 'POST':
        LMSLessonProgress.objects.get_or_create(enrollment=enrollment, lesson=lesson)
        lessons = list(module.lessons.filter(is_published=True).order_by('order'))
        idx = next((i for i, l in enumerate(lessons) if l.pk == lesson.pk), None)
        if idx is not None and idx + 1 < len(lessons):
            return redirect('lms:lesson_detail', pk=lessons[idx + 1].pk)
        return redirect('lms:module_detail', pk=module.pk)

    completed_ids = enrollment.completed_lesson_ids()
    lessons = list(module.lessons.filter(is_published=True).order_by('order'))
    idx = next((i for i, l in enumerate(lessons) if l.pk == lesson.pk), None)
    prev_lesson = lessons[idx - 1] if idx and idx > 0 else None
    next_lesson = lessons[idx + 1] if idx is not None and idx + 1 < len(lessons) else None

    return render(request, 'lms/lesson_detail.html', {
        'lesson': lesson,
        'module': module,
        'enrollment': enrollment,
        'is_completed': lesson.pk in completed_ids,
        'prev_lesson': prev_lesson,
        'next_lesson': next_lesson,
    })


@login_required
def submit_deliverable(request, pk):
    if request.method != 'POST':
        return redirect('lms:lms_dashboard')
    from .models import LMSDeliverable
    deliverable = get_object_or_404(LMSDeliverable, pk=pk)
    course = deliverable.module.course
    enrollment, _ = LMSEnrollment.objects.get_or_create(user=request.user, course=course)
    submission, created = LMSDeliverableSubmission.objects.get_or_create(
        enrollment=enrollment, deliverable=deliverable,
        defaults={
            'submission_text': request.POST.get('submission_text', ''),
            'file_upload': request.FILES.get('file_upload'),
        }
    )
    if not created:
        submission.submission_text = request.POST.get('submission_text', '')
        if request.FILES.get('file_upload'):
            submission.file_upload = request.FILES.get('file_upload')
        submission.status = 'submitted'
        submission.save()
        messages.success(request, "Deliverable updated successfully.")
    else:
        messages.success(request, "Deliverable submitted! Your mentor will review it shortly.")
    return redirect('lms:module_detail', pk=deliverable.module.pk)
