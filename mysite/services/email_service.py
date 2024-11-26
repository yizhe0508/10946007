# services/email_service.py
from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.contrib.sites.shortcuts import get_current_site
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.auth.tokens import default_token_generator

class EmailService:
    @staticmethod
    def send_activation_email(request, user):
        current_site = get_current_site(request)
        activation_days = getattr(settings, 'ACCOUNT_ACTIVATION_DAYS', 7)
        
        context = {
            'user': user,
            'domain': current_site.domain,
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': default_token_generator.make_token(user),
            'activation_days': activation_days,
        }
        
        return EmailService._send_email(
            subject='請啟用您的【虛擬寶物交換網】帳號',
            template_prefix='activation_email',
            context=context,
            to_email=user.email
        )

    @staticmethod
    def send_password_reset_email(request, user):
        current_site = get_current_site(request)
        reset_days = getattr(settings, 'PASSWORD_RESET_TIMEOUT_DAYS', 1)
        
        context = {
            'user': user,
            'domain': current_site.domain,
            'uid': urlsafe_base64_encode(force_bytes(user.pk)),
            'token': default_token_generator.make_token(user),
            'reset_days': reset_days,
        }
        
        return EmailService._send_email(
            subject='【虛擬寶物交換網】請重設您的密碼',
            template_prefix='reset_password_email',
            context=context,
            to_email=user.email
        )

    @staticmethod
    def _send_email(subject, template_prefix, context, to_email):
        message_html = render_to_string(f'{template_prefix}.html', context)
        message_plain = render_to_string(f'{template_prefix}.txt', context)
        
        email_message = EmailMultiAlternatives(
            subject=subject,
            body=message_plain,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[to_email]
        )
        email_message.attach_alternative(message_html, "text/html")
        return email_message.send(fail_silently=False)