from django.dispatch import receiver
from django.contrib.auth.signals import user_logged_in
from django.core.mail import send_mail
from django.utils import timezone
from allauth.account.signals import user_signed_up

def send_welcome_email(user):
    if not user.email:
        return
    subject = "Welcome to Expenza - Smart Financial Tracker!"
    message = (
        f"Hello {user.first_name or user.username},\n\n"
        f"Welcome to Expenza! We are excited to have you on board.\n\n"
        f"With Expenza, you can:\n"
        f"• Track your daily expenses and income streams effortlessly\n"
        f"• Filter transactions by Today, This Week, This Month, or This Year\n"
        f"• View interactive charts and category breakdowns\n"
        f"• Download PDF reports anytime and receive automated monthly email summaries\n\n"
        f"Happy Tracking!\n"
        f"The Expenza Team\n"
    )
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=None,
            recipient_list=[user.email],
            fail_silently=True
        )
    except Exception as e:
        print(f"Error sending welcome email to {user.email}: {e}")

def send_login_email(user):
    if not user.email:
        return
    login_time = timezone.now().strftime('%B %d, %Y at %I:%M %p UTC')
    subject = "Login Alert - Expenza Account Access"
    message = (
        f"Hello {user.first_name or user.username},\n\n"
        f"This is a quick security confirmation that your Expenza account was accessed on {login_time}.\n\n"
        f"If this was you, no action is required!\n"
        f"If you did not log in, please change your password immediately.\n\n"
        f"Best regards,\n"
        f"The Expenza Team\n"
    )
    try:
        send_mail(
            subject=subject,
            message=message,
            from_email=None,
            recipient_list=[user.email],
            fail_silently=True
        )
    except Exception as e:
        print(f"Error sending login email to {user.email}: {e}")

@receiver(user_signed_up)
def handle_social_signup(sender, request, user, **kwargs):
    send_welcome_email(user)

@receiver(user_logged_in)
def handle_user_login(sender, request, user, **kwargs):
    send_login_email(user)
