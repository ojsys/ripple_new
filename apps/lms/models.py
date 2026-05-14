from django.db import models
from ckeditor.fields import RichTextField
from django.conf import settings


class LMSCourse(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    description = RichTextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Course'
        verbose_name_plural = 'Courses'

    def __str__(self):
        return self.title


class LMSModule(models.Model):
    course = models.ForeignKey(LMSCourse, on_delete=models.CASCADE, related_name='modules')
    title = models.CharField(max_length=200)
    week_number = models.PositiveIntegerField()
    overview = RichTextField()
    learning_objectives = RichTextField(help_text="List the key things founders will learn")
    is_published = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order', 'week_number']
        verbose_name = 'Module'
        verbose_name_plural = 'Modules'

    def __str__(self):
        return f"Week {self.week_number}: {self.title}"


class LMSLesson(models.Model):
    module = models.ForeignKey(LMSModule, on_delete=models.CASCADE, related_name='lessons')
    title = models.CharField(max_length=200)
    content = RichTextField()
    estimated_minutes = models.PositiveIntegerField(default=10, help_text="Estimated reading time in minutes")
    order = models.PositiveIntegerField(default=0)
    is_published = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']
        verbose_name = 'Lesson'
        verbose_name_plural = 'Lessons'

    def __str__(self):
        return f"{self.module.title} — {self.title}"


class LMSExercise(models.Model):
    module = models.ForeignKey(LMSModule, on_delete=models.CASCADE, related_name='exercises')
    title = models.CharField(max_length=200)
    instructions = RichTextField()
    tips = RichTextField(blank=True, help_text="Optional tips and hints")
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']
        verbose_name = 'Exercise'
        verbose_name_plural = 'Exercises'

    def __str__(self):
        return f"{self.module.title} — {self.title}"


class LMSDeliverable(models.Model):
    module = models.OneToOneField(LMSModule, on_delete=models.CASCADE, related_name='deliverable')
    title = models.CharField(max_length=200)
    description = RichTextField(help_text="What the founder needs to produce")
    format_guidance = models.CharField(max_length=200, help_text="e.g. '1-page PDF or Google Doc'")
    example_link = models.URLField(blank=True, help_text="Optional link to an example")

    class Meta:
        verbose_name = 'Deliverable'
        verbose_name_plural = 'Deliverables'

    def __str__(self):
        return f"{self.module.title} — {self.title}"


class LMSEnrollment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='lms_enrollments')
    course = models.ForeignKey(LMSCourse, on_delete=models.CASCADE, related_name='enrollments')
    enrolled_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ('user', 'course')
        verbose_name = 'Enrollment'
        verbose_name_plural = 'Enrollments'

    def __str__(self):
        return f"{self.user.email} — {self.course.title}"

    def completed_lesson_ids(self):
        return set(self.lesson_progress.values_list('lesson_id', flat=True))

    def module_progress_percent(self, module):
        total = module.lessons.filter(is_published=True).count()
        if total == 0:
            return 0
        done = self.lesson_progress.filter(lesson__module=module).count()
        return int((done / total) * 100)

    def total_progress_percent(self):
        total = LMSLesson.objects.filter(module__course=self.course, is_published=True).count()
        if total == 0:
            return 0
        done = self.lesson_progress.count()
        return int((done / total) * 100)


class LMSLessonProgress(models.Model):
    enrollment = models.ForeignKey(LMSEnrollment, on_delete=models.CASCADE, related_name='lesson_progress')
    lesson = models.ForeignKey(LMSLesson, on_delete=models.CASCADE, related_name='completions')
    completed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('enrollment', 'lesson')
        verbose_name = 'Lesson Progress'
        verbose_name_plural = 'Lesson Progress'

    def __str__(self):
        return f"{self.enrollment.user.email} completed {self.lesson.title}"


class LMSDeliverableSubmission(models.Model):
    STATUS_CHOICES = [
        ('submitted', 'Submitted'),
        ('reviewed', 'Reviewed'),
        ('approved', 'Approved'),
    ]
    enrollment = models.ForeignKey(LMSEnrollment, on_delete=models.CASCADE, related_name='submissions')
    deliverable = models.ForeignKey(LMSDeliverable, on_delete=models.CASCADE, related_name='submissions')
    submission_text = models.TextField(blank=True, help_text="Written submission or notes")
    file_upload = models.FileField(upload_to='lms/deliverables/', blank=True, null=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    feedback = models.TextField(blank=True, help_text="Mentor/admin feedback")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='submitted')

    class Meta:
        ordering = ['-submitted_at']
        verbose_name = 'Deliverable Submission'
        verbose_name_plural = 'Deliverable Submissions'

    def __str__(self):
        return f"{self.enrollment.user.email} — {self.deliverable.title}"
