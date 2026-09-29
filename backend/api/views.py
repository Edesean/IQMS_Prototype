# backend/api/views.py

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.core.mail import send_mail
from django.conf import settings
from django.db.models import Avg
from django.utils import timezone
from datetime import timedelta


from .models import User, Branch, Customer, ServiceCategory, QueueTicket, Notification, AuditLog
from .serializers import (
    UserSerializer, BranchSerializer, ServiceCategorySerializer,
    QueueTicketSerializer, JoinQueueSerializer, PushSubscriptionSerializer
)
from prediction.predictor import predict_wait_time
from .push_utils import send_push_to_customer


# ---------- Email helper ----------
def send_email(to_email, subject, message):
    """Send an email notification. Fails silently so queue operations are never blocked."""
    if not to_email:
        print("[EMAIL] Skipped - no email address")
        return
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[to_email],
            fail_silently=False,
        )
        print(f"[EMAIL SENT] to {to_email} | {subject}")
    except Exception as e:
        print(f"[EMAIL ERROR] {to_email} | {e}")


def _ordinal(n):
    if 10 <= n % 100 <= 20:
        suffix = "th"
    else:
        suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def notify_approaching_customers(branch):
    """
    Notify customers who are 2nd or 3rd in line.
    Sends in-app notification record + email (if customer has email).
    """
    services = ServiceCategory.objects.filter(branch=branch, is_active=True)

    for service in services:
        active = QueueTicket.objects.filter(
            branch=branch,
            service_category=service,
            status__in=['waiting', 'called'],
        ).order_by('joined_at')

        for idx, ticket in enumerate(active):
            position = idx + 1
            if position not in (2, 3):
                continue
            if ticket.status != 'waiting':
                continue

            ordinal = _ordinal(position)
            marker = f"You are now {ordinal} in line"

            already_sent = Notification.objects.filter(
                queue_ticket=ticket,
                type='update',
                message__startswith=marker,
            ).exists()
            if already_sent:
                continue

            message = (
                f"{marker} at {branch.name} for {service.name}. "
                f"Please start heading to the branch — your turn is approaching."
            )

            Notification.objects.create(
                queue_ticket=ticket,
                customer=ticket.customer,
                type='update',
                channel='both',
                recipient=ticket.customer.phone_number,
                message=message,
            )

            send_push_to_customer(
                ticket.customer,
                f"IQMS: {_ordinal(position)} in line",
                message,
                ticket.ticket_number,
            )

            # Send email to customer (if they provided one)
            if ticket.customer.email:
                send_email(
                    to_email=ticket.customer.email,
                    subject=f"IQMS: {marker} - {ticket.ticket_number}",
                    message=(
                        f"Dear Customer,\n\n"
                        f"Your queue status has been updated.\n\n"
                        f"Ticket Number: {ticket.ticket_number}\n"
                        f"Branch: {branch.name}\n"
                        f"Service: {service.name}\n"
                        f"Current Position: {position} of the queue\n\n"
                        f"{message}\n\n"
                        f"Please start making your way to the branch.\n\n"
                        f"Thank you,\n"
                        f"IQMS - Intelligent Queue Management System"
                    ),
                )


# ---------- Authentication ----------
class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')

        if not email or not password:
            return Response({'error': 'Email and password are required'},
                            status=status.HTTP_400_BAD_REQUEST)

        user = authenticate(email=email, password=password)
        if not user:
            return Response({'error': 'Invalid credentials'},
                            status=status.HTTP_401_UNAUTHORIZED)

        # --- Record this login in the audit trail ---
        AuditLog.objects.create(
            user=user,
            branch=user.branch,
            action='login',
            details={'role': user.role},
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', '')[:200]
        )

        if not user.is_active:
            return Response({'error': 'Account is deactivated'},
                            status=status.HTTP_403_FORBIDDEN)

        refresh = RefreshToken.for_user(user)
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': UserSerializer(user).data
        })


# ---------- Public listing endpoints ----------
class BranchListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        branches = Branch.objects.all()
        return Response(BranchSerializer(branches, many=True).data)


class ServiceCategoryListView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        branch_id = request.query_params.get('branch')
        if branch_id:
            services = ServiceCategory.objects.filter(branch_id=branch_id)
        else:
            services = ServiceCategory.objects.all()
        return Response(ServiceCategorySerializer(services, many=True).data)


# ---------- Join queue ----------
class JoinQueueView(APIView):
    """
    Customer joins a queue. Business rules:

    Mon-Fri, open hours     → normal join (live queue)
    Mon-Fri, before open    → pre-booked for TODAY
    Mon-Fri, after close    → pre-booked for NEXT BUSINESS DAY
                                (Fri evening → Monday)
    Saturday / Sunday       → pre-booked for MONDAY
    """
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = JoinQueueSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        branch_id = data['branch_id']
        service_category_id = data['service_category_id']
        phone_number = data['phone_number']
        email = data.get('email') or None
        first_name = data.get('first_name', '')
        last_name = data.get('last_name', '')

        try:
            branch = Branch.objects.get(id=branch_id)
        except Branch.DoesNotExist:
            return Response({'error': 'Branch not found'}, status=status.HTTP_404_NOT_FOUND)

        try:
            service_category = ServiceCategory.objects.get(id=service_category_id, branch=branch)
        except ServiceCategory.DoesNotExist:
            return Response(
                {'error': 'This service is not available at the selected branch. Please choose a different service.'},
                status=status.HTTP_404_NOT_FOUND
            )

        if not service_category.is_active:
            return Response(
                {'error': f'"{service_category.name}" is currently unavailable at {branch.name}. '
                        f'Please choose a different service or try again later.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        customer, _ = Customer.objects.get_or_create(
            phone_number=phone_number,
            defaults={'email': email, 'first_name': first_name, 'last_name': last_name}
        )
        if email and customer.email != email:
            customer.email = email
            customer.save()

        # ---------- Business hours & business day logic ----------
        now_local = timezone.localtime(timezone.now())
        current_hour = now_local.hour
        current_weekday = now_local.weekday()   # Mon=0 ... Sun=6

        # Use the branch's actual opening/closing hours
        open_hour = branch.opening_time.hour
        close_hour = branch.closing_time.hour

        is_weekend = current_weekday >= 5   # Sat=5, Sun=6
        is_working_hours = (not is_weekend) and (open_hour <= current_hour < close_hour)

        if is_working_hours:
            mode = 'open'
            target_phrase = None
        elif is_weekend:
            mode = 'weekend'
            target_phrase = 'Monday'
        else:
            # Weekday, outside open hours
            if current_hour < open_hour:
                mode = 'before_open'
                target_phrase = 'today'
            else:
                mode = 'after_close'
                # Friday evening → next business day is Monday
                if current_weekday == 4:  # Friday
                    target_phrase = 'Monday'
                else:
                    next_day = now_local + timedelta(days=1)
                    target_phrase = next_day.strftime('%A')  # Tuesday/Wednesday/Thursday

        # ---------- Sequential position (all modes) ----------
        queue_position = QueueTicket.objects.filter(
            branch=branch,
            service_category=service_category,
            status__in=['waiting', 'called']
        ).count() + 1

        # ---------- Ticket number ----------
        last_ticket = QueueTicket.objects.filter(
            branch=branch,
            service_category=service_category,
        ).order_by('-created_at').first()

        if last_ticket:
            try:
                num = int(last_ticket.ticket_number.split('-')[-1]) + 1
            except (IndexError, ValueError):
                num = 1
        else:
            num = 1

        prefix = f"{branch.code}-{service_category.name[:1].upper()}"
        ticket_number = f"{prefix}-{num:04d}"

        # ---------- Predicted wait ----------
        if mode == 'open':
            predicted_wait = predict_wait_time(service_category, queue_position)
        else:
            predicted_wait = 0

        # ---------- Create ticket ----------
        ticket = QueueTicket.objects.create(
            ticket_number=ticket_number,
            branch=branch,
            service_category=service_category,
            customer=customer,
            queue_position=queue_position,
            estimated_wait_time=predicted_wait,
            status='waiting'
        )

        # ---------- Messages / email / push ----------
        if mode == 'open':
            minutes = predicted_wait // 60
            confirm_msg = (f"Welcome to {branch.name}! Your ticket is {ticket_number}. "
                        f"Wait time: {minutes} minutes. Position: {queue_position}.")
            email_subject = f"IQMS: Queue Confirmation - {ticket_number}"
            email_body = (
                f"Dear Customer,\n\n"
                f"You have successfully joined the queue.\n\n"
                f"Ticket Number: {ticket_number}\n"
                f"Branch: {branch.name}\n"
                f"Service: {service_category.name}\n"
                f"Estimated Wait Time: {minutes} minutes\n"
                f"Position in Queue: {queue_position}\n\n"
                f"Thank you,\nIQMS"
            )
            push_title = f"IQMS: Joined queue - {ticket_number}"
            response_message = None

        elif mode == 'before_open':
            # Weekday before opening — pre-booked for TODAY
            confirm_msg = (f"Pre-booking confirmed at {branch.name}. "
                        f"You are customer #{queue_position} for TODAY ({now_local.strftime('%A')}). "
                        f"Please come by 8:30 AM today.")
            email_subject = f"IQMS: Pre-Booking Confirmed (Today) - {ticket_number}"
            email_body = (
                f"Dear Customer,\n\n"
                f"We open at {branch.opening_time.strftime('%H:%M')} today ({now_local.strftime('%A')}).\n\n"
                f"You have been pre-booked as customer #{queue_position} for TODAY.\n\n"
                f"Ticket Number: {ticket_number}\n"
                f"Branch: {branch.name}\n"
                f"Service: {service_category.name}\n\n"
                f"Please come by 8:30 AM today.\n\n"
                f"Thank you,\nIQMS"
            )
            push_title = "IQMS: Pre-Booking Confirmed (Today)"
            response_message = (
                f"We are not yet open (business hours: {branch.opening_time.strftime('%H:%M')} - "
                f"{branch.closing_time.strftime('%H:%M')}, Mon-Fri). "
                f"You have been pre-booked as customer #{queue_position} for TODAY. "
                f"Kindly come by 8:30 AM today."
            )

        elif mode == 'after_close':
            # Weekday after closing — pre-booked for the next business day
            comes_on = "tomorrow" if target_phrase != 'Monday' else "Monday"
            confirm_msg = (f"Pre-booking confirmed at {branch.name}. "
                        f"You are customer #{queue_position} for {target_phrase}. "
                        f"Please come by 8:30 AM {comes_on}.")
            email_subject = f"IQMS: Pre-Booking Confirmed ({target_phrase}) - {ticket_number}"
            email_body = (
                f"Dear Customer,\n\n"
                f"Our branches are currently closed "
                f"(business hours: {branch.opening_time.strftime('%H:%M')} - {branch.closing_time.strftime('%H:%M')}, Mon-Fri).\n\n"
                f"You have been pre-booked as customer #{queue_position} for {target_phrase}.\n\n"
                f"Ticket Number: {ticket_number}\n"
                f"Branch: {branch.name}\n"
                f"Service: {service_category.name}\n\n"
                f"Please come by 8:30 AM {comes_on}.\n\n"
                f"Thank you,\nIQMS"
            )
            push_title = f"IQMS: Pre-Booking Confirmed ({target_phrase})"
            response_message = (
                f"We are currently closed (business hours: {branch.opening_time.strftime('%H:%M')} - "
                f"{branch.closing_time.strftime('%H:%M')}, Mon-Fri). "
                f"You have been pre-booked as customer #{queue_position} for {target_phrase}. "
                f"Kindly come by 8:30 AM {comes_on}."
            )

        else:  # weekend
            confirm_msg = (f"Pre-booking confirmed at {branch.name}. "
                        f"You are customer #{queue_position} for Monday. "
                        f"Please come by 8:30 AM Monday.")
            email_subject = f"IQMS: Pre-Booking Confirmed (Monday) - {ticket_number}"
            email_body = (
                f"Dear Customer,\n\n"
                f"Our branches are closed on weekends.\n"
                f"We are open Monday to Friday, "
                f"{branch.opening_time.strftime('%H:%M')} - {branch.closing_time.strftime('%H:%M')}.\n\n"
                f"You have been pre-booked as customer #{queue_position} for MONDAY.\n\n"
                f"Ticket Number: {ticket_number}\n"
                f"Branch: {branch.name}\n"
                f"Service: {service_category.name}\n\n"
                f"Please come by 8:30 AM on Monday.\n\n"
                f"Thank you,\nIQMS"
            )
            push_title = "IQMS: Pre-Booking Confirmed (Monday)"
            response_message = (
                f"Our branches are closed on weekends. "
                f"You have been pre-booked as customer #{queue_position} for MONDAY. "
                f"Kindly come by 8:30 AM on Monday."
            )

        Notification.objects.create(
            queue_ticket=ticket,
            customer=customer,
            type='confirmation',
            channel='both',
            recipient=phone_number,
            message=confirm_msg,
        )

        if customer.email:
            send_email(customer.email, email_subject, email_body)

        send_push_to_customer(customer, push_title, confirm_msg, ticket_number)

        return Response({
            'ticket_number': ticket_number,
            'queue_position': queue_position,
            'estimated_wait_time': predicted_wait,
            'status': 'waiting',
            'is_prebooking': mode != 'open',
            'message': response_message,
        }, status=status.HTTP_201_CREATED)

# ---------- Teller: call next customer ----------


class CallNextView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        if not user.branch:
            return Response({'error': 'User has no branch assigned'},
                            status=status.HTTP_400_BAD_REQUEST)

        filters = {'branch': user.branch, 'status': 'waiting'}
        assigned_services = list(user.service_categories.values_list('id', flat=True))
        if assigned_services:
            filters['service_category_id__in'] = assigned_services

        next_ticket = QueueTicket.objects.filter(**filters).order_by('created_at').first()

        if not next_ticket:
            return Response({'message': 'No customers waiting'},
                            status=status.HTTP_404_NOT_FOUND)

        next_ticket.status = 'called'
        next_ticket.called_at = timezone.now()
        next_ticket.teller = user
        next_ticket.save()

        call_msg = (f"Your turn is now! Please proceed to the counter for "
                    f"{next_ticket.service_category.name}. Ticket: {next_ticket.ticket_number}.")

        Notification.objects.create(
            queue_ticket=next_ticket,
            customer=next_ticket.customer,
            type='call_alert',
            channel='both',
            recipient=next_ticket.customer.phone_number,
            message=call_msg,
        )

        if next_ticket.customer.email:
            send_email(
                to_email=next_ticket.customer.email,
                subject=f"IQMS: Your turn now - {next_ticket.ticket_number}",
                message=(
                    f"Dear Customer,\n\n"
                    f"IT IS YOUR TURN NOW!\n\n"
                    f"Please proceed to the counter for {next_ticket.service_category.name}.\n\n"
                    f"Ticket Number: {next_ticket.ticket_number}\n"
                    f"Branch: {next_ticket.branch.name}\n\n"
                    f"Thank you,\nIQMS"
                ),
            )

        send_push_to_customer(
            next_ticket.customer,
            "IQMS: It's your turn!",
            call_msg,
            next_ticket.ticket_number,
        )

        notify_approaching_customers(user.branch)

        return Response({
            'id': str(next_ticket.id),
            'ticket_number': next_ticket.ticket_number,
            'customer_name': (f"{next_ticket.customer.first_name} "
                              f"{next_ticket.customer.last_name}").strip() or 'Customer',
            'service_category': next_ticket.service_category.name,
            'service_name': next_ticket.service_category.name,
            'status': next_ticket.status,
            'joined_at': next_ticket.joined_at,
        })


class StartServiceView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        ticket_id = request.data.get('ticket_id')
        if not ticket_id:
            return Response({'error': 'Ticket ID is required'},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            ticket = QueueTicket.objects.get(id=ticket_id, teller=request.user)
        except QueueTicket.DoesNotExist:
            return Response({'error': 'Ticket not found or not assigned to you'},
                            status=status.HTTP_404_NOT_FOUND)

        if ticket.status != 'called':
            return Response({'error': 'Ticket must be in "called" status'},
                            status=status.HTTP_400_BAD_REQUEST)

        ticket.status = 'serving'
        ticket.served_at = timezone.now()
        ticket.save()

        return Response({
            'id': str(ticket.id),
            'ticket_number': ticket.ticket_number,
            'status': ticket.status,
        })


class CompleteServiceView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        ticket_id = request.data.get('ticket_id')
        if not ticket_id:
            return Response({'error': 'Ticket ID is required'},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            ticket = QueueTicket.objects.get(id=ticket_id, teller=request.user)
        except QueueTicket.DoesNotExist:
            return Response({'error': 'Ticket not found or not assigned to you'},
                            status=status.HTTP_404_NOT_FOUND)

        if ticket.status != 'serving':
            return Response({'error': 'Ticket must be in "serving" status'},
                            status=status.HTTP_400_BAD_REQUEST)

        ticket.status = 'completed'
        ticket.completed_at = timezone.now()

        if ticket.joined_at and ticket.served_at:
            ticket.actual_wait_time = int((ticket.served_at - ticket.joined_at).total_seconds())
        if ticket.served_at and ticket.completed_at:
            ticket.service_duration = int((ticket.completed_at - ticket.served_at).total_seconds())

        ticket.save()

        notify_approaching_customers(ticket.branch)

        return Response({
            'id': str(ticket.id),
            'ticket_number': ticket.ticket_number,
            'status': ticket.status,
            'actual_wait_time': ticket.actual_wait_time,
            'service_duration': ticket.service_duration,
        })


class QueueStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if not user.branch:
            return Response({'error': 'User has no branch assigned'},
                            status=status.HTTP_400_BAD_REQUEST)

        base_filters = {'branch': user.branch}
        assigned_services = list(user.service_categories.values_list('id', flat=True))
        if assigned_services:
            base_filters['service_category_id__in'] = assigned_services

        waiting_count = QueueTicket.objects.filter(
            status='waiting', **base_filters
        ).count()

        current_ticket = QueueTicket.objects.filter(
            teller=user,
            status__in=['called', 'serving']
        ).first()

        return Response({
            'waiting_count': waiting_count,
            'current_ticket': QueueTicketSerializer(current_ticket).data if current_ticket else None,
        })


class AnalyticsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        if not user.branch:
            return Response({'error': 'User has no branch assigned'},
                            status=status.HTTP_400_BAD_REQUEST)

        date_range = request.query_params.get('range', 'today')
        now = timezone.now()
        if date_range == 'today':
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
        elif date_range == 'week':
            start_date = now - timedelta(days=7)
        elif date_range == 'month':
            start_date = now - timedelta(days=30)
        else:
            start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)

        tickets = QueueTicket.objects.filter(branch=user.branch, created_at__gte=start_date)
        completed_tickets = tickets.filter(status='completed')
        cancelled_tickets = tickets.filter(status='cancelled')

        total = tickets.count()
        avg_wait = completed_tickets.aggregate(Avg('actual_wait_time'))['actual_wait_time__avg'] or 0
        avg_service = completed_tickets.aggregate(Avg('service_duration'))['service_duration__avg'] or 0

        stats = {
            'total_tickets': total,
            'completed_count': completed_tickets.count(),
            'cancelled_count': cancelled_tickets.count(),
            'average_wait_time': round(avg_wait, 2),
            'average_service_time': round(avg_service, 2),
            'abandonment_rate': round((cancelled_tickets.count() / total * 100), 2) if total > 0 else 0,
        }
        return Response({'stats': stats})


class CheckStatusView(APIView):
    permission_classes = [AllowAny]

    def _notifications_for(self, ticket):
        notifs = Notification.objects.filter(
            queue_ticket=ticket
        ).order_by('-created_at').values('type', 'message', 'created_at')
        return list(notifs)

    def post(self, request):
        ticket_number = str(request.data.get('ticket_number', '')).strip().upper()
        phone_number = str(request.data.get('phone_number', '')).strip()

        if not ticket_number or not phone_number:
            return Response({'error': 'Ticket number and phone number are required'},
                            status=status.HTTP_400_BAD_REQUEST)

        ticket = QueueTicket.objects.select_related(
            'service_category', 'customer', 'branch'
        ).filter(
            ticket_number=ticket_number,
            customer__phone_number=phone_number
        ).order_by('-created_at').first()

        if not ticket:
            return Response({'error': 'No ticket found with those details'},
                            status=status.HTTP_404_NOT_FOUND)

        notifs = self._notifications_for(ticket)

        if ticket.status in ['completed', 'cancelled']:
            return Response({
                'ticket_number': ticket.ticket_number,
                'status': ticket.status,
                'queue_position': 0,
                'estimated_wait_time': 0,
                'service_category': ticket.service_category.name,
                'branch': ticket.branch.name,
                'joined_at': ticket.joined_at,
                'message': 'This ticket is no longer active.',
                'notifications': notifs,
            })

        if ticket.status == 'serving':
            return Response({
                'ticket_number': ticket.ticket_number,
                'status': 'serving',
                'queue_position': 0,
                'estimated_wait_time': 0,
                'service_category': ticket.service_category.name,
                'branch': ticket.branch.name,
                'joined_at': ticket.joined_at,
                'message': 'You are currently being served.',
                'notifications': notifs,
            })

        if ticket.status == 'called':
            return Response({
                'ticket_number': ticket.ticket_number,
                'status': 'called',
                'queue_position': 0,
                'estimated_wait_time': 0,
                'service_category': ticket.service_category.name,
                'branch': ticket.branch.name,
                'joined_at': ticket.joined_at,
                'message': 'It is your turn! Please proceed to the counter.',
                'notifications': notifs,
            })

        current_position = QueueTicket.objects.filter(
            branch=ticket.branch,
            service_category=ticket.service_category,
            status__in=['waiting', 'called'],
            joined_at__lt=ticket.joined_at,
        ).count() + 1

        predicted_wait = predict_wait_time(ticket.service_category, current_position)

        ticket.queue_position = current_position
        ticket.estimated_wait_time = predicted_wait
        ticket.save(update_fields=['queue_position', 'estimated_wait_time', 'updated_at'])

        return Response({
            'ticket_number': ticket.ticket_number,
            'status': 'waiting',
            'queue_position': current_position,
            'estimated_wait_time': predicted_wait,
            'service_category': ticket.service_category.name,
            'branch': ticket.branch.name,
            'joined_at': ticket.joined_at,
            'message': 'You are still in the queue.',
            'notifications': notifs,
        })


class SubscribePushView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        from .models import PushSubscription

        serializer = PushSubscriptionSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        try:
            customer = Customer.objects.get(phone_number=data['phone_number'])
        except Customer.DoesNotExist:
            return Response({'error': 'Customer not found'}, status=status.HTTP_404_NOT_FOUND)

        sub, created = PushSubscription.objects.update_or_create(
            endpoint=data['endpoint'],
            defaults={
                'customer': customer,
                'p256dh': data['p256dh'],
                'auth': data['auth'],
            }
        )
        return Response({'status': 'ok', 'created': created})


class CancelTicketView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        ticket_number = str(request.data.get('ticket_number', '')).strip().upper()
        phone_number = str(request.data.get('phone_number', '')).strip()

        if not ticket_number or not phone_number:
            return Response({'error': 'Ticket number and phone number are required'},
                            status=status.HTTP_400_BAD_REQUEST)

        ticket = QueueTicket.objects.filter(
            ticket_number=ticket_number,
            customer__phone_number=phone_number
        ).order_by('-created_at').first()

        if not ticket:
            return Response({'error': 'No ticket found with those details'},
                            status=status.HTTP_404_NOT_FOUND)

        if ticket.status in ['completed', 'cancelled']:
            return Response({'error': f'This ticket is already {ticket.status}'},
                            status=status.HTTP_400_BAD_REQUEST)

        if ticket.status in ['called', 'serving']:
            return Response({'error': 'Cannot cancel - your ticket is being served.'},
                            status=status.HTTP_400_BAD_REQUEST)

        ticket.status = 'cancelled'
        ticket.cancellation_reason = 'Cancelled by customer'
        ticket.save()

        cancel_msg = f"Your ticket {ticket.ticket_number} has been cancelled."

        Notification.objects.create(
            queue_ticket=ticket,
            customer=ticket.customer,
            type='update',
            channel='both',
            recipient=ticket.customer.phone_number,
            message=cancel_msg,
        )

        send_push_to_customer(ticket.customer, "IQMS: Ticket Cancelled",
                              cancel_msg, ticket.ticket_number)

        notify_approaching_customers(ticket.branch)

        return Response({
            'status': 'cancelled',
            'ticket_number': ticket.ticket_number,
            'message': 'Your ticket has been cancelled successfully.'
        })


class NoShowView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        ticket_id = request.data.get('ticket_id')
        if not ticket_id:
            return Response({'error': 'Ticket ID is required'},
                            status=status.HTTP_400_BAD_REQUEST)

        try:
            ticket = QueueTicket.objects.get(id=ticket_id, teller=request.user)
        except QueueTicket.DoesNotExist:
            return Response({'error': 'Ticket not found or not assigned to you'},
                            status=status.HTTP_404_NOT_FOUND)

        if ticket.status != 'called':
            return Response({'error': 'Only tickets in "called" status can be marked no-show'},
                            status=status.HTTP_400_BAD_REQUEST)

        ticket.status = 'cancelled'
        ticket.cancellation_reason = 'Customer did not respond (no-show)'
        ticket.completed_at = timezone.now()
        ticket.save()

        no_show_msg = (f"Your ticket {ticket.ticket_number} was cancelled because you did not "
                       f"respond when called. Please rejoin the queue if you still need service.")

        Notification.objects.create(
            queue_ticket=ticket,
            customer=ticket.customer,
            type='update',
            channel='both',
            recipient=ticket.customer.phone_number,
            message=no_show_msg,
        )

        send_push_to_customer(ticket.customer, "IQMS: Ticket Cancelled (No-Show)",
                              no_show_msg, ticket.ticket_number)

        notify_approaching_customers(ticket.branch)

        return Response({
            'status': 'cancelled',
            'ticket_number': ticket.ticket_number,
            'message': 'Customer marked as no-show.'
        })