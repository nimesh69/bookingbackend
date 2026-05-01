from django.contrib import admin
from unfold.admin import ModelAdmin as UnfoldModelAdmin
from unfold.admin import TabularInline
from .models import Match, MatchParticipant


class MatchParticipantInline(TabularInline):
    model = MatchParticipant
    extra = 1
    fields = ('user', 'status', 'team')


@admin.register(Match)
class MatchAdmin(UnfoldModelAdmin):
    list_display = ('sport', 'created_by', 'match_date', 'start_time', 'status', 'slots_needed', 'created_at')
    list_filter = ('status', 'sport', 'skill_level', 'match_date')
    list_per_page = 25
    search_fields = ('sport', 'created_by__email', 'location_text', 'id')
    readonly_fields = ('id', 'created_at', 'updated_at')
    inlines = (MatchParticipantInline,)
    
    fieldsets = (
        ('Match Info', {
            'fields': ('id', 'created_by', 'sport', 'turf')
        }),
        ('Schedule', {
            'fields': ('match_date', 'start_time', 'format')
        }),
        ('Details', {
            'fields': ('location_text', 'skill_level', 'slots_needed', 'status')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(MatchParticipant)
class MatchParticipantAdmin(UnfoldModelAdmin):
    list_display = ('match', 'user', 'status', 'team', 'created_at')
    list_filter = ('status', 'team', 'match__sport', 'created_at')
    list_per_page = 50
    search_fields = ('match__id', 'user__email')
    readonly_fields = ('id', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Participant Info', {
            'fields': ('id', 'match', 'user')
        }),
        ('Status', {
            'fields': ('status', 'team')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
