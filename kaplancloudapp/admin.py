from django.contrib import admin

from .models import LanguageProfile, Termbase, TBEntry, TBEntryUpdate, TranslationMemory, TMEntry, TMEntryUpdate, Project, ProjectFile, Client, Segment, SegmentUpdate

# Register your models here.


class LanguageProfileAdmin(admin.ModelAdmin):
    def get_changeform_initial_data(self, request):
        get_data = super(LanguageProfileAdmin, self).get_changeform_initial_data(request)
        get_data['created_by'] = request.user.pk
        return get_data

admin.site.register(LanguageProfile, LanguageProfileAdmin)

admin.site.register(Termbase)

admin.site.register(TBEntry)

admin.site.register(TBEntryUpdate)

admin.site.register(TranslationMemory)

admin.site.register(TMEntry)

admin.site.register(TMEntryUpdate)

admin.site.register(Project)

admin.site.register(ProjectFile)

# admin.site.register(Client)

admin.site.register(Segment)

admin.site.register(SegmentUpdate)
