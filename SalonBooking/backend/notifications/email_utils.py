"""
Email notification system for SalonBooking.
Sends beautiful HTML emails for:
- Booking confirmation
- Booking cancellation
- Booking reminder (day before)
- Payment receipt
"""

from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags


def get_time_display(time_slot):
    """Convert hour integer to readable time range."""
    h = time_slot
    start = f"{h % 12 or 12}:00 {'AM' if h < 12 else 'PM'}"
    eh = h + 1
    end = f"{eh % 12 or 12}:00 {'AM' if eh < 12 else 'PM'}"
    return f"{start} — {end}"


def send_email(to_email, subject, html_content):
    """
    Core email sender. Uses Gmail SMTP configured in settings.
    Falls back gracefully if email not configured.
    """
    if not settings.EMAIL_HOST_USER:
        print(f"[Email] Not configured. Would send to {to_email}: {subject}")
        return False

    try:
        text_content = strip_tags(html_content)
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[to_email],
        )
        msg.attach_alternative(html_content, "text/html")
        msg.send()
        print(f"[Email] ✅ Sent to {to_email}: {subject}")
        return True
    except Exception as e:
        print(f"[Email] ❌ Failed to send to {to_email}: {e}")
        return False


def booking_confirmation_html(booking):
    """Generate booking confirmation HTML email."""
    time_display = get_time_display(booking.time_slot)
    payment_row = ""
    if hasattr(booking, 'payment') and booking.payment.status == 'paid':
        payment_row = f"""
        <tr>
            <td style="padding:8px 0;color:#9CA3AF;font-size:14px;">Transaction ID</td>
            <td style="padding:8px 0;color:#ffffff;font-size:14px;font-weight:600;text-align:right;">
                {booking.payment.razorpay_payment_id}
            </td>
        </tr>
        """

    return f"""
    <!DOCTYPE html>
    <html>
    <head><meta charset="UTF-8"><meta name="viewport" content="width=device-width,initial-scale=1"></head>
    <body style="margin:0;padding:0;background:#0f0f1a;font-family:'Segoe UI',Arial,sans-serif;">
        <div style="max-width:560px;margin:40px auto;padding:0 20px;">

            <!-- Header -->
            <div style="text-align:center;padding:32px 0 24px;">
                <div style="font-size:48px;margin-bottom:8px;">💈</div>
                <h1 style="color:#ffffff;font-size:24px;margin:0;font-weight:800;">
                    Salon<span style="color:#8B5CF6;">Book</span>
                </h1>
            </div>

            <!-- Success Banner -->
            <div style="background:linear-gradient(135deg,#065F46,#047857);border-radius:16px;padding:24px;text-align:center;margin-bottom:24px;">
                <div style="font-size:40px;margin-bottom:8px;">🎉</div>
                <h2 style="color:#ffffff;margin:0;font-size:22px;font-weight:800;">Booking Confirmed!</h2>
                <p style="color:#A7F3D0;margin:8px 0 0;font-size:14px;">
                    Your appointment is all set. See you soon!
                </p>
            </div>

            <!-- Booking Details Card -->
            <div style="background:#16213e;border:1px solid rgba(255,255,255,0.08);border-radius:16px;padding:24px;margin-bottom:24px;">
                <h3 style="color:#8B5CF6;font-size:13px;font-weight:700;letter-spacing:0.1em;text-transform:uppercase;margin:0 0 16px;">
                    Booking Details
                </h3>
                <table style="width:100%;border-collapse:collapse;">
                    <tr style="border-bottom:1px solid rgba(255,255,255,0.06);">
                        <td style="padding:10px 0;color:#9CA3AF;font-size:14px;">Booking ID</td>
                        <td style="padding:10px 0;color:#8B5CF6;font-size:14px;font-weight:700;text-align:right;font-family:monospace;">
                            {booking.booking_id}
                        </td>
                    </tr>
                    <tr style="border-bottom:1px solid rgba(255,255,255,0.06);">
                        <td style="padding:10px 0;color:#9CA3AF;font-size:14px;">Service</td>
                        <td style="padding:10px 0;color:#ffffff;font-size:14px;font-weight:600;text-align:right;">
                            {booking.service.name}
                        </td>
                    </tr>
                    <tr style="border-bottom:1px solid rgba(255,255,255,0.06);">
                        <td style="padding:10px 0;color:#9CA3AF;font-size:14px;">Date</td>
                        <td style="padding:10px 0;color:#ffffff;font-size:14px;font-weight:600;text-align:right;">
                            {booking.date.strftime('%A, %d %B %Y')}
                        </td>
                    </tr>
                    <tr style="border-bottom:1px solid rgba(255,255,255,0.06);">
                        <td style="padding:10px 0;color:#9CA3AF;font-size:14px;">Time</td>
                        <td style="padding:10px 0;color:#ffffff;font-size:14px;font-weight:600;text-align:right;">
                            {time_display}
                        </td>
                    </tr>
                    <tr style="border-bottom:1px solid rgba(255,255,255,0.06);">
                        <td style="padding:10px 0;color:#9CA3AF;font-size:14px;">Amount Paid</td>
                        <td style="padding:10px 0;color:#10B981;font-size:16px;font-weight:800;text-align:right;">
                            ₹{booking.service.price}
                        </td>
                    </tr>
                    {payment_row}
                </table>
            </div>

            <!-- Reminder Box -->
            <div style="background:rgba(139,92,246,0.1);border:1px solid rgba(139,92,246,0.3);border-radius:12px;padding:16px;margin-bottom:24px;">
                <p style="color:#C4B5FD;font-size:13px;margin:0;line-height:1.6;">
                    📍 <strong>Please arrive 5 minutes early</strong><br>
                    ❌ Cancel at least 2 hours before your slot to avoid charges<br>
                    📞 Questions? Reply to this email
                </p>
            </div>

            <!-- Footer -->
            <div style="text-align:center;padding:16px 0 40px;">
                <p style="color:#4B5563;font-size:12px;margin:0;">
                    Thank you for choosing SalonBook 💈<br>
                    This is an automated email — please do not reply directly.
                </p>
            </div>

        </div>
    </body>
    </html>
    """


def cancellation_html(booking):
    """Generate booking cancellation HTML email."""
    time_display = get_time_display(booking.time_slot)
    return f"""
    <!DOCTYPE html>
    <html>
    <body style="margin:0;padding:0;background:#0f0f1a;font-family:'Segoe UI',Arial,sans-serif;">
        <div style="max-width:560px;margin:40px auto;padding:0 20px;">

            <div style="text-align:center;padding:32px 0 24px;">
                <div style="font-size:48px;">💈</div>
                <h1 style="color:#ffffff;font-size:24px;margin:8px 0 0;font-weight:800;">
                    Salon<span style="color:#8B5CF6;">Book</span>
                </h1>
            </div>

            <div style="background:linear-gradient(135deg,#7F1D1D,#991B1B);border-radius:16px;padding:24px;text-align:center;margin-bottom:24px;">
                <div style="font-size:40px;margin-bottom:8px;">❌</div>
                <h2 style="color:#ffffff;margin:0;font-size:22px;font-weight:800;">Booking Cancelled</h2>
                <p style="color:#FECACA;margin:8px 0 0;font-size:14px;">
                    Your booking has been cancelled successfully.
                </p>
            </div>

            <div style="background:#16213e;border:1px solid rgba(255,255,255,0.08);border-radius:16px;padding:24px;margin-bottom:24px;">
                <table style="width:100%;border-collapse:collapse;">
                    <tr style="border-bottom:1px solid rgba(255,255,255,0.06);">
                        <td style="padding:10px 0;color:#9CA3AF;font-size:14px;">Booking ID</td>
                        <td style="padding:10px 0;color:#EF4444;font-size:14px;font-weight:700;text-align:right;font-family:monospace;">
                            {booking.booking_id}
                        </td>
                    </tr>
                    <tr style="border-bottom:1px solid rgba(255,255,255,0.06);">
                        <td style="padding:10px 0;color:#9CA3AF;font-size:14px;">Service</td>
                        <td style="padding:10px 0;color:#ffffff;font-size:14px;text-align:right;">{booking.service.name}</td>
                    </tr>
                    <tr>
                        <td style="padding:10px 0;color:#9CA3AF;font-size:14px;">Was scheduled</td>
                        <td style="padding:10px 0;color:#ffffff;font-size:14px;text-align:right;">
                            {booking.date.strftime('%d %B %Y')} · {time_display}
                        </td>
                    </tr>
                </table>
            </div>

            <div style="background:rgba(245,158,11,0.1);border:1px solid rgba(245,158,11,0.3);border-radius:12px;padding:16px;margin-bottom:24px;">
                <p style="color:#FCD34D;font-size:13px;margin:0;line-height:1.6;">
                    💰 If you paid online, your refund will be processed within <strong>5-7 business days</strong>.<br>
                    📅 Want to rebook? Visit our app anytime.
                </p>
            </div>

            <div style="text-align:center;padding:16px 0 40px;">
                <p style="color:#4B5563;font-size:12px;margin:0;">SalonBook 💈 — See you next time!</p>
            </div>
        </div>
    </body>
    </html>
    """


def reminder_html(booking):
    """Generate day-before reminder HTML email."""
    time_display = get_time_display(booking.time_slot)
    return f"""
    <!DOCTYPE html>
    <html>
    <body style="margin:0;padding:0;background:#0f0f1a;font-family:'Segoe UI',Arial,sans-serif;">
        <div style="max-width:560px;margin:40px auto;padding:0 20px;">

            <div style="text-align:center;padding:32px 0 24px;">
                <div style="font-size:48px;">💈</div>
                <h1 style="color:#ffffff;font-size:24px;margin:8px 0 0;font-weight:800;">
                    Salon<span style="color:#8B5CF6;">Book</span>
                </h1>
            </div>

            <div style="background:linear-gradient(135deg,#1E3A5F,#1E40AF);border-radius:16px;padding:24px;text-align:center;margin-bottom:24px;">
                <div style="font-size:40px;margin-bottom:8px;">⏰</div>
                <h2 style="color:#ffffff;margin:0;font-size:22px;font-weight:800;">Reminder: Tomorrow!</h2>
                <p style="color:#BFDBFE;margin:8px 0 0;font-size:14px;">
                    Your appointment is tomorrow. Don't forget!
                </p>
            </div>

            <div style="background:#16213e;border:1px solid rgba(255,255,255,0.08);border-radius:16px;padding:24px;margin-bottom:24px;">
                <table style="width:100%;border-collapse:collapse;">
                    <tr style="border-bottom:1px solid rgba(255,255,255,0.06);">
                        <td style="padding:10px 0;color:#9CA3AF;font-size:14px;">Service</td>
                        <td style="padding:10px 0;color:#ffffff;font-size:14px;font-weight:600;text-align:right;">{booking.service.name}</td>
                    </tr>
                    <tr style="border-bottom:1px solid rgba(255,255,255,0.06);">
                        <td style="padding:10px 0;color:#9CA3AF;font-size:14px;">Date</td>
                        <td style="padding:10px 0;color:#60A5FA;font-size:15px;font-weight:700;text-align:right;">
                            Tomorrow · {booking.date.strftime('%d %B')}
                        </td>
                    </tr>
                    <tr>
                        <td style="padding:10px 0;color:#9CA3AF;font-size:14px;">Time</td>
                        <td style="padding:10px 0;color:#ffffff;font-size:14px;font-weight:600;text-align:right;">{time_display}</td>
                    </tr>
                </table>
            </div>

            <div style="background:rgba(16,185,129,0.1);border:1px solid rgba(16,185,129,0.3);border-radius:12px;padding:16px;margin-bottom:24px;">
                <p style="color:#6EE7B7;font-size:13px;margin:0;line-height:1.8;">
                    ✅ Arrive 5 minutes early<br>
                    🚿 Come with clean, dry hair for hair services<br>
                    📵 Need to cancel? Do it at least 2 hours before
                </p>
            </div>

            <div style="text-align:center;padding:16px 0 40px;">
                <p style="color:#4B5563;font-size:12px;">SalonBook 💈 — Looking forward to seeing you!</p>
            </div>
        </div>
    </body>
    </html>
    """


# ── Public functions called from views ──────────────────

def send_booking_confirmation_email(booking):
    """Send confirmation email after successful payment."""
    if not booking.user.email:
        print(f"[Email] No email for user {booking.user.phone} — skipping")
        return False
    return send_email(
        to_email=booking.user.email,
        subject=f"✅ Booking Confirmed — {booking.booking_id} | SalonBook",
        html_content=booking_confirmation_html(booking),
    )


def send_cancellation_email(booking):
    """Send cancellation email."""
    if not booking.user.email:
        return False
    return send_email(
        to_email=booking.user.email,
        subject=f"❌ Booking Cancelled — {booking.booking_id} | SalonBook",
        html_content=cancellation_html(booking),
    )


def send_reminder_email(booking):
    """Send day-before reminder email."""
    if not booking.user.email:
        return False
    return send_email(
        to_email=booking.user.email,
        subject=f"⏰ Reminder: Your appointment is tomorrow! | SalonBook",
        html_content=reminder_html(booking),
    )