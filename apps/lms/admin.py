from django.contrib import admin
from django.utils.html import format_html
from .models import (
    LMSCourse, LMSModule, LMSLesson, LMSExercise, LMSDeliverable,
    LMSEnrollment, LMSLessonProgress, LMSDeliverableSubmission
)


class LMSLessonInline(admin.TabularInline):
    model = LMSLesson
    extra = 1
    fields = ['order', 'title', 'estimated_minutes', 'is_published']


class LMSExerciseInline(admin.TabularInline):
    model = LMSExercise
    extra = 1
    fields = ['order', 'title']


class LMSDeliverableInline(admin.StackedInline):
    model = LMSDeliverable
    extra = 0
    max_num = 1
    fields = ['title', 'description', 'format_guidance', 'example_link']


class LMSModuleInline(admin.TabularInline):
    model = LMSModule
    extra = 0
    fields = ['order', 'week_number', 'title', 'is_published']
    show_change_link = True


@admin.register(LMSCourse)
class LMSCourseAdmin(admin.ModelAdmin):
    list_display = ['title', 'is_active', 'created_at']
    list_editable = ['is_active']
    inlines = [LMSModuleInline]
    prepopulated_fields = {'slug': ('title',)}


@admin.register(LMSModule)
class LMSModuleAdmin(admin.ModelAdmin):
    list_display = ['week_number', 'title', 'course', 'lesson_count', 'is_published', 'order']
    list_filter = ['course', 'is_published']
    list_editable = ['is_published', 'order']
    ordering = ['course', 'order', 'week_number']
    inlines = [LMSLessonInline, LMSExerciseInline, LMSDeliverableInline]
    fieldsets = (
        ('Module Info', {
            'fields': ('course', 'week_number', 'title', 'cover_image', 'order', 'is_published'),
        }),
        ('Content', {
            'fields': ('overview', 'learning_objectives'),
        }),
    )

    def lesson_count(self, obj):
        return obj.lessons.count()
    lesson_count.short_description = 'Lessons'


@admin.register(LMSLesson)
class LMSLessonAdmin(admin.ModelAdmin):
    list_display = ['title', 'module', 'estimated_minutes', 'order', 'is_published']
    list_filter = ['module__course', 'is_published']
    list_editable = ['order', 'is_published']
    search_fields = ['title']
    ordering = ['module__order', 'order']
    fieldsets = (
        ('Lesson Info', {
            'fields': ('module', 'title', 'estimated_minutes', 'order', 'is_published'),
        }),
        ('Content', {
            'fields': ('content',),
        }),
    )


@admin.register(LMSEnrollment)
class LMSEnrollmentAdmin(admin.ModelAdmin):
    list_display = ['user', 'course', 'enrolled_at', 'progress_col', 'is_active']
    list_filter = ['course', 'is_active']
    search_fields = ['user__email', 'user__first_name', 'user__last_name']
    readonly_fields = ['enrolled_at']

    def progress_col(self, obj):
        pct = obj.total_progress_percent()
        color = '#26af59' if pct == 100 else '#2563eb' if pct > 0 else '#d1d5db'
        return format_html(
            '<div style="width:100px;background:#f3f4f6;border-radius:4px;overflow:hidden;">'
            '<div style="width:{}%;background:{};height:8px;border-radius:4px;"></div></div>'
            '<small style="color:#6b7280;">{}</small>',
            pct, color, f"{pct}%"
        )
    progress_col.short_description = 'Progress'


@admin.register(LMSDeliverableSubmission)
class LMSDeliverableSubmissionAdmin(admin.ModelAdmin):
    list_display = ['enrollment', 'deliverable', 'status_badge', 'submitted_at']
    list_filter = ['status', 'deliverable__module__course']
    search_fields = ['enrollment__user__email']
    readonly_fields = ['submitted_at']
    actions = ['mark_reviewed', 'mark_approved']
    fieldsets = (
        ('Submission', {
            'fields': ('enrollment', 'deliverable', 'submission_text', 'file_upload', 'submitted_at'),
        }),
        ('Review', {
            'fields': ('status', 'feedback'),
        }),
    )

    def status_badge(self, obj):
        colors = {'submitted': '#2563eb', 'reviewed': '#d97706', 'approved': '#16a34a'}
        color = colors.get(obj.status, '#6b7280')
        return format_html(
            '<span style="background:{};color:#fff;padding:2px 10px;border-radius:12px;font-size:0.75rem;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'

    @admin.action(description='Mark selected as Reviewed')
    def mark_reviewed(self, request, queryset):
        queryset.update(status='reviewed')

    @admin.action(description='Mark selected as Approved')
    def mark_approved(self, request, queryset):
        queryset.update(status='approved')
