from django.conf import settings
from django.db import models
from apps.base_models import TimeStampedModel
from apps.settings.choices import LEAD_CONSOLIDATION




class Organization(TimeStampedModel):

	owner  = models.ForeignKey(settings.AUTH_USER_MODEL,on_delete=models.CASCADE)
	# lead_consolidation - leadga operatorni qaysi usulda biriktirishni bildiradi.
	lead_consolidation = models.CharField(max_length=20,choices=LEAD_CONSOLIDATION.choices,default=LEAD_CONSOLIDATION.MANUAL)
	organization_phone = models.CharField(max_length=255,null=True,blank=True)
	name = models.CharField(max_length=255)
	description = models.TextField(blank=True)
	logo = models.ImageField(upload_to="organization/logos/", null=True, blank=True)
	latitude = models.DecimalField(max_digits=9,decimal_places=6)
	longtitude = models.DecimalField(max_digits=9,decimal_places=6)
	address = models.CharField(max_length=1024, blank=True)
	sms_identifier = models.CharField(max_length=128, blank=True, help_text="Short name used when sending SMS from this branch")
	bank_accounts = models.JSONField(blank=True, null=True, help_text="Optional bank account details JSON")
	cash_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
	terminal_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)


	def __str__(self):
		return self.name


class Branch(TimeStampedModel):

	organization = models.ForeignKey(Organization, related_name="branches", on_delete=models.CASCADE)
	name = models.CharField(max_length=255)
	phone = models.CharField(max_length=50, blank=True)
	address = models.CharField(max_length=1024, blank=True)
	latitude = models.DecimalField(max_digits=9,decimal_places=6)
	longtitude = models.DecimalField(max_digits=9,decimal_places=6)
	sms_identifier = models.CharField(max_length=128, blank=True, help_text="Short name used when sending SMS from this branch")
	is_active = models.BooleanField(default=True)
	manager = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="managed_branches")
	bank_accounts = models.JSONField(blank=True, null=True, help_text="Optional bank account details JSON")
	cash_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)
	terminal_balance = models.DecimalField(max_digits=12, decimal_places=2, default=0)


	class Meta:
		verbose_name = "Branch"
		verbose_name_plural = "Branches"

	def __str__(self):
		return f"{self.name} ({'Active' if self.is_active else 'Inactive'})"

# Bu model haqida maslahatlashib chiqish kerak. Fieldlari bo'yicha
class ReceiptSettings(TimeStampedModel):

	LOGO_POSITION_TOP = "top"
	LOGO_POSITION_BOTTOM = "bottom"
	LOGO_POSITION_CHOICES = [
		(LOGO_POSITION_TOP, "Top"),
		(LOGO_POSITION_BOTTOM, "Bottom"),
	]

	branch = models.OneToOneField(Branch, related_name="receipt_settings", on_delete=models.CASCADE, null=True, blank=True)
	organization = models.ForeignKey(Organization, related_name="receipt_settings", on_delete=models.CASCADE, null=True, blank=True)

	# Content
	top_text = models.TextField(blank=True, help_text="Text shown in the top part of receipt (address/phone)")
	footer_text = models.TextField(blank=True, help_text="Footer / thank you / social links")
	logo = models.ImageField(upload_to="receipts/logos/", null=True, blank=True)

	# Visual toggles
	show_logo = models.BooleanField(default=True)
	show_top_section = models.BooleanField(default=True)
	show_address = models.BooleanField(default=True)
	show_phone = models.BooleanField(default=True)
	show_print_time = models.BooleanField(default=True)
	show_payment_id = models.BooleanField(default=True)
	show_student_info = models.BooleanField(default=True)
	show_group_info = models.BooleanField(default=True)
	show_payment_form = models.BooleanField(default=True)
	show_payment_date = models.BooleanField(default=True)
	show_cashier = models.BooleanField(default=True)
	show_amount = models.BooleanField(default=True)
	show_footer = models.BooleanField(default=True)
	show_qr_code = models.BooleanField(default=True)
	show_teacher_name = models.BooleanField(default=False)
	show_course_price = models.BooleanField(default=False)

	logo_position = models.CharField(max_length=10, choices=LOGO_POSITION_CHOICES, default=LOGO_POSITION_TOP)

	class Meta:
		verbose_name = "Receipt Settings"
		verbose_name_plural = "Receipt Settings"

	def __str__(self):
		target = self.branch.name if self.branch else (self.organization.name if self.organization else "Global")
		return f"Receipt settings — {target}"


class PaymentMethod(TimeStampedModel):

	name = models.CharField(max_length=100)
	code = models.SlugField(max_length=50, unique=True)
	is_active = models.BooleanField(default=False)


	def __str__(self):
		return self.name


class Weekend(TimeStampedModel):

	branch = models.ForeignKey(Branch, related_name="weekends", on_delete=models.CASCADE, null=True, blank=True)
	date = models.DateField()
	reason = models.TextField(blank=True)
	created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)


	class Meta:
		unique_together = ("branch", "date")

	def __str__(self):
		return f"{self.date} — {self.branch.name if self.branch else 'Global'}"


# class FeatureToggle(models.Model):
# 	key = models.SlugField(max_length=100, unique=True)
# 	name = models.CharField(max_length=255)
# 	description = models.TextField(blank=True)
# 	enabled = models.BooleanField(default=False)
# 	branch = models.ForeignKey(Branch, null=True, blank=True, on_delete=models.CASCADE, related_name="feature_toggles")
# 	updated_at = models.DateTimeField(auto_now=True)

# 	def __str__(self):
# 		scope = self.branch.name if self.branch else "Global"
# 		return f"{self.key} ({scope}) — {'On' if self.enabled else 'Off'}"


# class IntegrationSetting(models.Model):
# 	PROVIDER_AMO = "amocrm"
# 	PROVIDER_FACEID = "faceid"
# 	PROVIDER_SMS = "sms"
# 	PROVIDER_CHOICES = [
# 		(PROVIDER_AMO, "AmoCRM"),
# 		(PROVIDER_FACEID, "FaceID"),
# 		(PROVIDER_SMS, "SMS Provider"),
# 	]

# 	provider = models.CharField(max_length=50, choices=PROVIDER_CHOICES)
# 	branch = models.ForeignKey(Branch, null=True, blank=True, on_delete=models.CASCADE, related_name="integrations")
# 	name = models.CharField(max_length=255, blank=True)
# 	config = models.JSONField(blank=True, null=True, help_text="Provider-specific configuration (keys, ids, urls)")
# 	is_active = models.BooleanField(default=False)
# 	last_tested = models.DateTimeField(null=True, blank=True)
# 	last_test_status = models.CharField(max_length=255, blank=True)

# 	created_at = models.DateTimeField(auto_now_add=True)
# 	updated_at = models.DateTimeField(auto_now=True)

# 	def test_connection(self):
# 		self.last_tested = timezone.now()
# 		# Placeholder: integration-specific test logic should be implemented in service layer
# 		self.last_test_status = "not_implemented"
# 		self.save(update_fields=["last_tested", "last_test_status"])

# 	def __str__(self):
# 		scope = self.branch.name if self.branch else "Global"
# 		return f"{self.get_provider_display()} — {scope}"
