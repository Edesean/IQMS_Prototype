# backend/api/serializers.py

from rest_framework import serializers
from .models import User, Branch, Customer, ServiceCategory, QueueTicket, Notification, Feedback, AuditLog


class UserSerializer(serializers.ModelSerializer):
    service_category_names = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ['id', 'full_name', 'email', 'phone_number', 'role', 'branch',
                'service_categories', 'service_category_names', 'is_active']
        read_only_fields = ['id']

    def get_service_category_names(self, obj):
        return list(obj.service_categories.values_list('name', flat=True))


class BranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = '__all__'


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = '__all__'


class ServiceCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ServiceCategory
        fields = '__all__'


class QueueTicketSerializer(serializers.ModelSerializer):
    customer_name = serializers.SerializerMethodField()
    service_name = serializers.SerializerMethodField()

    class Meta:
        model = QueueTicket
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_customer_name(self, obj):
        return f"{obj.customer.first_name} {obj.customer.last_name}".strip() or obj.customer.phone_number

    def get_service_name(self, obj):
        return obj.service_category.name


class JoinQueueSerializer(serializers.Serializer):
    branch_id = serializers.UUIDField()
    service_category_id = serializers.UUIDField()
    phone_number = serializers.CharField(max_length=20)
    email = serializers.EmailField(required=False, allow_blank=True)
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'


class FeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = Feedback
        fields = '__all__'


class AuditLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditLog
        fields = '__all__'



class PushSubscriptionSerializer(serializers.Serializer):
    phone_number = serializers.CharField()
    endpoint = serializers.CharField()
    p256dh = serializers.CharField()
    auth = serializers.CharField()