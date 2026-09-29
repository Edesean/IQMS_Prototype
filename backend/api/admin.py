# backend/api/admin.py

from django.contrib import admin
from .models import User, Branch, Customer, ServiceCategory, QueueTicket, Notification, Feedback, AuditLog


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'role', 'branch', 'is_active')
    list_filter = ('role', 'is_active', 'branch')
    search_fields = ('full_name', 'email', 'phone_number')
    filter_horizontal = ('service_categories',)

@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ('name', 'city', 'state', 'code', 'contact_phone')
    search_fields = ('name', 'code', 'city')


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'phone_number', 'email')
    search_fields = ('first_name', 'last_name', 'phone_number')


@admin.register(ServiceCategory)
class ServiceCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'branch', 'average_service_time', 'is_active')
    list_filter = ('is_active', 'branch')
    search_fields = ('name',)


class CancellationTypeFilter(admin.SimpleListFilter):
    title = 'cancellation type'
    parameter_name = 'cancel_type'

    def lookups(self, request, model_admin):
        return (
            ('no_show', 'No Show'),
            ('customer', 'Cancelled by Customer'),
            ('other', 'Other'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'no_show':
            return queryset.filter(status='cancelled', cancellation_reason__icontains='no-show')
        if self.value() == 'customer':
            return queryset.filter(status='cancelled', cancellation_reason__icontains='customer')
        if self.value() == 'other':
            return queryset.filter(status='cancelled').exclude(
                cancellation_reason__icontains='no-show'
            ).exclude(cancellation_reason__icontains='customer')
        return queryset


@admin.register(QueueTicket)
class QueueTicketAdmin(admin.ModelAdmin):
    list_display = (
        'ticket_number',
        'branch',
        'service_category',
        'customer',
        'display_status',      # ← custom coloured status column
        'queue_position',
        'joined_at',
    )
    list_filter = ('status', CancellationTypeFilter, 'branch', 'service_category')
    search_fields = ('ticket_number', 'customer__phone_number', 'customer__first_name', 'customer__last_name')
    readonly_fields = ('id', 'created_at', 'updated_at')

    def display_status(self, obj):
        if obj.status == 'cancelled':
            reason = (obj.cancellation_reason or '').lower()
            if 'no-show' in reason or 'did not respond' in reason:
                return '🚫 No Show'
            elif 'customer' in reason:
                return '❌ Cancelled by Customer'
            else:
                return '❌ Cancelled'
        elif obj.status == 'completed':
            return '✅ Completed'
        elif obj.status == 'serving':
            return '🟢 Serving'
        elif obj.status == 'called':
            return '📣 Called'
        elif obj.status == 'waiting':
            return '⏳ Waiting'
        return obj.status

    display_status.short_description = 'Status'


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('type', 'recipient', 'status', 'queue_ticket', 'created_at')
    list_filter = ('type', 'status')
    search_fields = ('recipient',)


@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('queue_ticket', 'rating', 'created_at')
    list_filter = ('rating',)


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('action', 'user', 'branch', 'created_at')
    list_filter = ('action', 'branch')