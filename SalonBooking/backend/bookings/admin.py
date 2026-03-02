from django.contrib import admin
from .models import SlotConfig, Booking


@admin.register(SlotConfig)
class SlotConfigAdmin(admin.ModelAdmin):
    list_display = ('date', 'is_open', 'opening_hour', 'closing_hour', 'max_bookings_per_slot')
    list_filter = ('is_open',)
    list_editable = ('is_open', 'opening_hour', 'closing_hour', 'max_bookings_per_slot')


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ('booking_id', 'user', 'service', 'date', 'time_slot', 'status', 'created_at')
    list_filter = ('status', 'date', 'service')
    search_fields = ('booking_id', 'user__phone', 'user__name')
    list_editable = ('status',)
    readonly_fields = ('booking_id', 'created_at')