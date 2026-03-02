"""
WhatsApp Cloud API integration for booking notifications.
"""

import requests
from django.conf import settings


def send_whatsapp_message(phone, message):
    """Send a text message via WhatsApp Cloud API."""
    token = settings.WHATSAPP_TOKEN
    phone_id = settings.WHATSAPP_PHONE_ID

    if not token or not phone_id:
        print(f"[WhatsApp] Not configured. Message for {phone}: {message}")
        return False

    # Add country code if not present
    if not phone.startswith('+'):
        phone = f"+91{phone}"

    url = f"https://graph.facebook.com/v17.0/{phone_id}/messages"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": phone,
        "type": "text",
        "text": {"body": message}
    }

    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            print(f"[WhatsApp] Sent to {phone} ✅")
            return True
        else:
            print(f"[WhatsApp] Failed: {response.text}")
            return False
    except Exception as e:
        print(f"[WhatsApp] Error: {e}")
        return False


def send_booking_confirmation(booking):
    """Send booking confirmation via WhatsApp."""
    h = booking.time_slot
    start = f"{h % 12 or 12}:00 {'AM' if h < 12 else 'PM'}"
    eh = h + 1
    end = f"{eh % 12 or 12}:00 {'AM' if eh < 12 else 'PM'}"

    payment_info = ""
    if hasattr(booking, 'payment'):
        payment_info = f"\n💰 Amount: ₹{booking.payment.amount}\n🧾 Transaction: {booking.payment.razorpay_payment_id}"

    message = (
        f"✅ *Booking Confirmed!*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🎫 Booking ID: *{booking.booking_id}*\n"
        f"💇 Service: *{booking.service.name}*\n"
        f"📅 Date: *{booking.date.strftime('%d %B %Y')}*\n"
        f"🕐 Time: *{start} — {end}*"
        f"{payment_info}\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🙏 Thank you for choosing our salon!\n"
        f"📍 Please arrive 5 mins early.\n"
        f"❌ Cancel at least 2 hours before your slot."
    )

    send_whatsapp_message(booking.user.phone, message)


def send_cancellation_message(booking):
    """Send cancellation notification via WhatsApp."""
    message = (
        f"❌ *Booking Cancelled*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"🎫 Booking ID: *{booking.booking_id}*\n"
        f"💇 Service: *{booking.service.name}*\n"
        f"📅 Date: *{booking.date.strftime('%d %B %Y')}*\n"
        f"━━━━━━━━━━━━━━━━━━\n"
        f"Your booking has been cancelled.\n"
        f"Refund will be processed within 5-7 days."
    )

    send_whatsapp_message(booking.user.phone, message)