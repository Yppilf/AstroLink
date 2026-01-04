from astrolink.dynamic_email import send_dynamic_email
from django.contrib import messages
from authentication.models import User
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib.auth import login
from datetime import date

def password_reset_request(request):
    if request.method == "POST":
        email = request.POST.get('email', '').strip().lower()

        # Try to find user (case-insensitive)
        user = User.objects.filter(email__iexact=email).first()

        if user:
            # Generate password reset token and UID
            token = default_token_generator.make_token(user)
            uid = urlsafe_base64_encode(force_bytes(user.pk))

            reset_link = request.build_absolute_uri(f"/reset-password/{uid}/{token}/")

            TEMPLATE_ID = 4
            DYNAMIC_DATA = {
                'username': getattr(user, user.display_name(), "User"),
                'reset_link': reset_link,
                'year': date.today().year,
            }

            send_dynamic_email(
                recipients=user.email,
                template_id=TEMPLATE_ID,
                dynamic_data=DYNAMIC_DATA
            )

        # Always show this message, regardless of user existence
        messages.success(request, "If an account with that email exists, a reset link has been sent.")
        return redirect('astrolink:forum_home')

    return render(request, "authentication/password_reset_request.html", {
        "title": "Forgot Password?",
        "submit_text": "Send Reset Link",
        "cancel_url": reverse("authentication:login"),
        "error": None,
    })


def password_reset_confirm(request, uidb64, token):
    try:
        uid = urlsafe_base64_decode(uidb64).decode()
        user = User.objects.get(pk=uid)
    except (User.DoesNotExist, ValueError, TypeError):
        user = None

    if user and default_token_generator.check_token(user, token):
        if request.method == "POST":
            new_password = request.POST.get('new_password')
            confirm_password = request.POST.get('confirm_password')

            if new_password == confirm_password:
                user.set_password(new_password)
                user.save()

                # Auto login after password reset
                login(request, user)
                return redirect('astrolink:forum_home')
            else:
                return render(request, 'authentication/password_reset_confirm.html', {
                    'error': 'Passwords do not match.',
                    'uidb64': uidb64,
                    'token': token
                })

        return render(request, 'authentication/password_reset_confirm.html', {
            'uidb64': uidb64,
            'token': token
        })

    return render(request, 'authentication/password_reset_invalid.html')