from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import *
@admin.register(User)
class StepUserAdmin(UserAdmin):
    ordering=['email'];list_display=['email','display_name','is_staff','is_active'];search_fields=['email','display_name']
    fieldsets=((None,{'fields':('email','password')}),('Profile',{'fields':('display_name','roles','profile','preferences')}),('Permissions',{'fields':('is_active','is_staff','is_superuser','groups','user_permissions')}))
    add_fieldsets=((None,{'classes':('wide',),'fields':('email','display_name','password1','password2')}),)
@admin.register(Policy,University,Category,InvestigationGrant)
class ConfigurationAdmin(admin.ModelAdmin):
    def has_change_permission(self,request,obj=None):return request.user.is_superuser
class LedgerAdmin(admin.ModelAdmin):
    def has_add_permission(self,request):return False
    def has_delete_permission(self,request,obj=None):return False
    def has_change_permission(self,request,obj=None):return False
for model in [CreditEntry,MoneyEntry,AuditEvent,ProviderOperation,Payment,PaymentAttempt,Payout]:admin.site.register(model,LedgerAdmin)
