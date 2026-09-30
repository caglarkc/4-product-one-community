import uuid
from decimal import Decimal
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import Q
from django.utils import timezone

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra):
        user = self.model(email=self.normalize_email(email).casefold(), **extra)
        user.set_password(password)
        user.save(using=self._db)
        return user
    def create_superuser(self, email, password=None, **extra):
        extra.update(is_staff=True, is_superuser=True)
        return self.create_user(email, password, **extra)

class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    username = None
    email = models.EmailField(unique=True)
    display_name = models.CharField(max_length=120)
    roles = models.JSONField(default=list)
    profile = models.JSONField(default=dict)
    preferences = models.JSONField(default=dict)
    submerchant_key = models.CharField(max_length=160, blank=True)
    bank_name = models.CharField(max_length=160, blank=True)
    iban_masked = models.CharField(max_length=40, blank=True)
    bank_digest = models.CharField(max_length=64, blank=True)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['display_name']
    objects = UserManager()

class Record(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    class Meta:
        abstract = True

class Policy(models.Model):
    id = models.PositiveSmallIntegerField(primary_key=True, default=1, editable=False)
    values = models.JSONField(default=dict)

class University(Record):
    name = models.CharField(max_length=200)
    domains = models.JSONField(default=list)

class Category(Record):
    name = models.CharField(max_length=100, unique=True)

class Eligibility(Record):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='eligibility')
    student_email = models.EmailField(blank=True)
    birth_date = models.DateField(null=True)
    education_level = models.CharField(max_length=30, blank=True)
    status = models.CharField(max_length=30, default='unverified')
    verified_until = models.DateTimeField(null=True)

class EmployerVerification(Record):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='employer_verification')
    kind = models.CharField(max_length=20, default='individual')
    details = models.JSONField(default=dict)
    phone_verified_at = models.DateTimeField(null=True)
    verified_phone = models.CharField(max_length=30, blank=True)
    status = models.CharField(max_length=20, default='pending')
    identity_reference = models.CharField(max_length=300, blank=True)
    company_reference = models.CharField(max_length=300, blank=True)
    authorized_reference = models.CharField(max_length=300, blank=True)

class Challenge(Record):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    purpose = models.CharField(max_length=30)
    digest = models.CharField(max_length=64, unique=True)
    target = models.CharField(max_length=254, blank=True)
    data = models.JSONField(default=dict)
    expires_at = models.DateTimeField()
    attempts = models.PositiveSmallIntegerField(default=0)
    used_at = models.DateTimeField(null=True)

class DeviceCredential(Record):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    digest = models.CharField(max_length=64, unique=True)
    expires_at = models.DateTimeField()
    revoked_at = models.DateTimeField(null=True)
    password_digest = models.CharField(max_length=64)

class RateWindow(models.Model):
    key = models.CharField(max_length=64, primary_key=True)
    count = models.PositiveIntegerField(default=0)
    starts_at = models.DateTimeField(default=timezone.now)

class Idempotency(Record):
    scope = models.CharField(max_length=180)
    key = models.UUIDField()
    digest = models.CharField(max_length=64)
    response = models.JSONField(null=True)
    status = models.PositiveSmallIntegerField(default=200)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['scope','key'], name='step_idem_scope_key')]

class Team(Record):
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    leader = models.ForeignKey(User, on_delete=models.PROTECT)

class Membership(Record):
    team = models.ForeignKey(Team, on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    status = models.CharField(max_length=20, default='invited')
    class Meta:
        constraints = [models.UniqueConstraint(fields=['team','user'], name='step_team_user')]

class Wallet(Record):
    user = models.OneToOneField(User, on_delete=models.PROTECT, null=True)
    team = models.OneToOneField(Team, on_delete=models.PROTECT, null=True)
    balance = models.BigIntegerField(default=0)
    mode = models.CharField(max_length=20)
    class Meta:
        constraints = [models.CheckConstraint(condition=(Q(user__isnull=False,team__isnull=True)|Q(user__isnull=True,team__isnull=False)), name='step_wallet_owner'), models.CheckConstraint(condition=Q(balance__gte=0), name='step_wallet_nonnegative')]

class CreditEntry(Record):
    wallet = models.ForeignKey(Wallet, on_delete=models.PROTECT, related_name='entries')
    amount = models.BigIntegerField()
    reason = models.CharField(max_length=100)
    event_key = models.CharField(max_length=250, unique=True)
    source = models.UUIDField(null=True)
    balance_after = models.BigIntegerField()

class Job(Record):
    owner = models.ForeignKey(User, on_delete=models.PROTECT)
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(Category,on_delete=models.PROTECT)
    skills = models.JSONField(default=list)
    work_type = models.CharField(max_length=10)
    budget = models.DecimalField(max_digits=16, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))])
    expected_duration = models.CharField(max_length=120)
    deadline = models.DateTimeField(null=True)
    status = models.CharField(max_length=20, default='draft')
    boosted_until = models.DateTimeField(null=True)

class Conversation(Record):
    users = models.ManyToManyField(User)
    contract = models.ForeignKey('Contract', on_delete=models.PROTECT, null=True, related_name='conversations')

class Application(Record):
    job = models.ForeignKey(Job, on_delete=models.PROTECT, related_name='applications')
    student = models.ForeignKey(User, on_delete=models.PROTECT)
    team = models.ForeignKey(Team, on_delete=models.PROTECT, null=True)
    cover_letter = models.TextField()
    price = models.DecimalField(max_digits=16, decimal_places=2)
    duration = models.CharField(max_length=120)
    sample_url = models.URLField(blank=True)
    status = models.CharField(max_length=20, default='submitted')
    conversation = models.OneToOneField(Conversation, on_delete=models.PROTECT)
    boosted_until = models.DateTimeField(null=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['job','student'], condition=Q(team__isnull=True), name='step_application_student'), models.UniqueConstraint(fields=['job','team'], condition=Q(team__isnull=False), name='step_application_team')]

class Invitation(Record):
    job = models.ForeignKey(Job, on_delete=models.PROTECT)
    student = models.ForeignKey(User, on_delete=models.PROTECT, null=True)
    team = models.ForeignKey(Team, on_delete=models.PROTECT, null=True)
    conversation = models.OneToOneField(Conversation, on_delete=models.PROTECT)
    status = models.CharField(max_length=20, default='pending')
    class Meta:
        constraints = [models.CheckConstraint(condition=(Q(student__isnull=False,team__isnull=True)|Q(student__isnull=True,team__isnull=False)),name='step_invitation_target')]

class Contract(Record):
    application = models.OneToOneField(Application, on_delete=models.PROTECT)
    employer = models.ForeignKey(User, on_delete=models.PROTECT, related_name='employer_contracts')
    freelancer = models.ForeignKey(User, on_delete=models.PROTECT, related_name='freelancer_contracts')
    team = models.ForeignKey(Team, on_delete=models.PROTECT, null=True)
    payee = models.ForeignKey(User, on_delete=models.PROTECT, related_name='payee_contracts')
    status = models.CharField(max_length=20, default='pending')
    scope = models.TextField()
    work_type = models.CharField(max_length=10)
    rate = models.DecimalField(max_digits=16, decimal_places=2)
    weekly_limit = models.DecimalField(max_digits=7, decimal_places=2, null=True)
    expected_duration = models.CharField(max_length=120)
    revision_terms = models.TextField()
    tracker_required = models.BooleanField(default=True)
    accepted_by = models.JSONField(default=list)
    version = models.PositiveIntegerField(default=1)

class ContractWorker(Record):
    contract = models.ForeignKey(Contract, on_delete=models.PROTECT, related_name='workers')
    user = models.ForeignKey(User, on_delete=models.PROTECT)
    hourly_rate = models.DecimalField(max_digits=16, decimal_places=2)
    active = models.BooleanField(default=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['contract','user'],name='step_contract_worker')]

class ContractChange(Record):
    contract = models.ForeignKey(Contract, on_delete=models.PROTECT)
    proposer = models.ForeignKey(User, on_delete=models.PROTECT)
    terms = models.JSONField(default=dict)
    accepted_by = models.JSONField(default=list)
    base_version = models.PositiveIntegerField()
    status = models.CharField(max_length=20, default='pending')

class LeaderChange(Record):
    team = models.ForeignKey(Team, on_delete=models.PROTECT)
    baseline_leader = models.ForeignKey(User, on_delete=models.PROTECT, related_name='baseline_leader_changes')
    new_leader = models.ForeignKey(User, on_delete=models.PROTECT, related_name='leader_changes')
    payee = models.ForeignKey(User, on_delete=models.PROTECT, related_name='payee_changes')
    contracts = models.ManyToManyField(Contract)
    reason = models.TextField()
    accepted_by = models.JSONField(default=list)
    admin_approved = models.BooleanField(default=False)
    status = models.CharField(max_length=20, default='pending')

class Milestone(Record):
    contract = models.ForeignKey(Contract, on_delete=models.PROTECT, related_name='milestones')
    title = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=16, decimal_places=2)
    status = models.CharField(max_length=20, default='unfunded')
    submission = models.JSONField(null=True)
    submitted_at = models.DateTimeField(null=True)
    review_due_at = models.DateTimeField(null=True)
    revision = models.PositiveIntegerField(default=0)

class Week(Record):
    contract = models.ForeignKey(Contract, on_delete=models.PROTECT, related_name='weeks')
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    status = models.CharField(max_length=20, default='unfunded')
    limit_hours = models.DecimalField(max_digits=7, decimal_places=2)
    reserved_amount = models.DecimalField(max_digits=16, decimal_places=2)
    worked_seconds = models.PositiveIntegerField(default=0)
    gross = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    net = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    review_due_at = models.DateTimeField(null=True)
    remainder_choice = models.CharField(max_length=20, default='refund')
    rate_snapshot = models.JSONField(default=dict)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['contract','starts_at'],name='step_contract_week')]

class MoneyAccount(Record):
    user = models.OneToOneField(User, on_delete=models.PROTECT)
    available = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    reserved = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    mode = models.CharField(max_length=30)
    class Meta:
        constraints = [models.CheckConstraint(condition=Q(available__gte=0,reserved__gte=0),name='step_money_nonnegative')]

class MoneyEntry(Record):
    user = models.ForeignKey(User, on_delete=models.PROTECT, null=True)
    kind = models.CharField(max_length=40)
    amount = models.DecimalField(max_digits=16, decimal_places=2)
    event_key = models.CharField(max_length=250, unique=True)
    source = models.UUIDField()
    mode = models.CharField(max_length=30)
    details = models.JSONField(default=dict)

class CreditPurchase(Record):
    owner = models.ForeignKey(User, on_delete=models.PROTECT)
    wallet = models.ForeignKey(Wallet, on_delete=models.PROTECT)
    credits = models.PositiveIntegerField()
    amount = models.DecimalField(max_digits=16, decimal_places=2)
    status = models.CharField(max_length=20, default='pending')

class Payment(Record):
    owner = models.ForeignKey(User, on_delete=models.PROTECT)
    target_type = models.CharField(max_length=30)
    target_id = models.UUIDField()
    amount = models.DecimalField(max_digits=16, decimal_places=2)
    mode = models.CharField(max_length=30)
    status = models.CharField(max_length=20, default='created')
    checkout_url = models.URLField(blank=True)
    checkout_expires_at = models.DateTimeField(null=True)
    provider_token = models.TextField(blank=True)
    provider_token_digest = models.CharField(max_length=64,blank=True)
    provider_reference = models.CharField(max_length=100, blank=True)
    provider_item = models.CharField(max_length=100, blank=True)
    total_funding = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    funded_at = models.DateTimeField(null=True)
    released_amount = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    refunded_amount = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    settlement_status = models.CharField(max_length=20, default='held')
    error_code = models.CharField(max_length=100, blank=True)
    attempt = models.PositiveIntegerField(default=1)
    conversation_id = models.UUIDField(default=uuid.uuid4)
    retry_allowed = models.BooleanField(default=False)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['target_type','target_id','mode'],name='step_payment_target')]

class PaymentAttempt(Record):
    payment = models.ForeignKey(Payment,on_delete=models.PROTECT,related_name='previous_attempts')
    number = models.PositiveIntegerField()
    conversation_id = models.UUIDField(unique=True)
    provider_token = models.TextField(blank=True)
    provider_token_digest = models.CharField(max_length=64,blank=True)
    status = models.CharField(max_length=20)
    error_code = models.CharField(max_length=100,blank=True)
    proof = models.JSONField(default=dict)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['payment','number'],name='step_attempt_number')]

class ProviderOperation(Record):
    payment = models.ForeignKey(Payment, on_delete=models.PROTECT, null=True)
    kind = models.CharField(max_length=40)
    event_key = models.CharField(max_length=200, unique=True)
    payload = models.JSONField(default=dict)
    state = models.CharField(max_length=20, default='pending')
    attempts = models.PositiveIntegerField(default=0)
    result = models.JSONField(default=dict)
    lease_until = models.DateTimeField(null=True)

class ProviderEvent(Record):
    digest = models.CharField(max_length=64, unique=True)
    reference = models.CharField(max_length=100)
    mode = models.CharField(max_length=30)
    payment = models.ForeignKey(Payment, on_delete=models.PROTECT, null=True)

class Payout(Record):
    owner = models.ForeignKey(User, on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=16, decimal_places=2)
    mode = models.CharField(max_length=30)
    account_name = models.CharField(max_length=160)
    iban_masked = models.CharField(max_length=40)
    status = models.CharField(max_length=20, default='requested')
    provider_reference = models.CharField(max_length=100, blank=True)
    paid_at = models.DateTimeField(null=True)
    failure_reason = models.CharField(max_length=200, blank=True)
    bank_ciphertext = models.TextField(blank=True)
    bank_digest = models.CharField(max_length=64, blank=True)

class Promotion(Record):
    target_type = models.CharField(max_length=20)
    target_id = models.UUIDField()
    wallet = models.ForeignKey(Wallet, on_delete=models.PROTECT)
    credits = models.PositiveIntegerField()
    ends_at = models.DateTimeField()
    refunded = models.BooleanField(default=False)

class Report(Record):
    reporter = models.ForeignKey(User, on_delete=models.PROTECT)
    job = models.ForeignKey(Job, on_delete=models.PROTECT)
    reason = models.TextField()
    status = models.CharField(max_length=20, default='pending')

class RefundRequest(Record):
    owner = models.ForeignKey(User, on_delete=models.PROTECT)
    purchase = models.ForeignKey(CreditPurchase, on_delete=models.PROTECT)
    reason = models.TextField()
    status = models.CharField(max_length=20, default='pending')

class Dispute(Record):
    contract = models.ForeignKey(Contract, on_delete=models.PROTECT)
    opener = models.ForeignKey(User, on_delete=models.PROTECT)
    target_type = models.CharField(max_length=20)
    target_id = models.UUIDField()
    reason = models.TextField()
    status = models.CharField(max_length=20, default='open')
    resolved_at = models.DateTimeField(null=True)

class InvestigationGrant(Record):
    operator = models.ForeignKey(User, on_delete=models.PROTECT)
    contract = models.ForeignKey(Contract, on_delete=models.PROTECT)
    case_type = models.CharField(max_length=20)
    case_id = models.UUIDField()
    reason = models.TextField()
    expires_at = models.DateTimeField()

class Asset(Record):
    owner = models.ForeignKey(User, on_delete=models.PROTECT)
    contract = models.ForeignKey(Contract, on_delete=models.PROTECT, null=True)
    conversation = models.ForeignKey(Conversation, on_delete=models.PROTECT, null=True)
    job = models.ForeignKey(Job, on_delete=models.PROTECT, null=True)
    storage_key = models.CharField(max_length=120)
    filename = models.CharField(max_length=180)
    mime = models.CharField(max_length=100)
    size = models.PositiveIntegerField()
    digest = models.CharField(max_length=64)
    state = models.CharField(max_length=20, default='private')
    captured_at = models.DateTimeField(null=True)
    publish_at = models.DateTimeField(null=True)
    publication_ready_at = models.DateTimeField(null=True)
    purged_at = models.DateTimeField(null=True)

class PrivacyRequest(Record):
    asset = models.OneToOneField(Asset, on_delete=models.PROTECT)
    reason = models.TextField()
    status = models.CharField(max_length=20, default='pending')
    decision = models.CharField(max_length=20, blank=True)
    resolved_at = models.DateTimeField(null=True)

class WorkSession(Record):
    owner = models.ForeignKey(User, on_delete=models.PROTECT)
    contract = models.ForeignKey(Contract, on_delete=models.PROTECT)
    client_id = models.UUIDField()
    memo = models.TextField(blank=True)
    ends_at = models.DateTimeField()
    stopped_at = models.DateTimeField(null=True)
    reserved_seconds = models.PositiveIntegerField(default=0)
    used_seconds = models.PositiveIntegerField(default=0)
    monitor_id = models.CharField(max_length=120, blank=True)
    funding = models.JSONField(default=dict)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['owner','client_id'],name='step_session_client')]

class TimeBlock(Record):
    owner = models.ForeignKey(User, on_delete=models.PROTECT)
    session = models.ForeignKey(WorkSession, on_delete=models.PROTECT)
    client_id = models.UUIDField()
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    seconds = models.PositiveIntegerField()
    key_count = models.PositiveIntegerField(default=0)
    mouse_count = models.PositiveIntegerField(default=0)
    active_app = models.CharField(max_length=160, blank=True)
    screenshot = models.OneToOneField(Asset, on_delete=models.PROTECT, null=True)
    digest = models.CharField(max_length=64)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['owner','client_id'],name='step_block_client')]

class ManualTime(Record):
    owner = models.ForeignKey(User, on_delete=models.PROTECT)
    contract = models.ForeignKey(Contract, on_delete=models.PROTECT)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    memo = models.TextField()
    status = models.CharField(max_length=20, default='pending')

class Message(Record):
    conversation = models.ForeignKey(Conversation, on_delete=models.PROTECT, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.PROTECT)
    text = models.TextField(blank=True)
    attachments = models.ManyToManyField(Asset)

class Rating(Record):
    contract = models.ForeignKey(Contract, on_delete=models.PROTECT, related_name='ratings')
    author = models.ForeignKey(User, on_delete=models.PROTECT)
    party = models.CharField(max_length=20)
    score = models.PositiveSmallIntegerField()
    comment = models.TextField(blank=True)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['contract','party'],name='step_contract_rating'), models.CheckConstraint(condition=Q(score__gte=1,score__lte=5),name='step_rating_score')]

class Notification(Record):
    recipient = models.ForeignKey(User, on_delete=models.PROTECT)
    kind = models.CharField(max_length=50)
    text = models.CharField(max_length=300)
    resource_id = models.UUIDField(null=True)
    read_at = models.DateTimeField(null=True)

class Outbox(Record):
    event_key = models.CharField(max_length=200, unique=True)
    recipient = models.ForeignKey(User, on_delete=models.PROTECT)
    subject = models.CharField(max_length=200)
    destination = models.EmailField(blank=True)
    body = models.TextField()
    state = models.CharField(max_length=20, default='pending')
    attempts = models.PositiveIntegerField(default=0)
    next_at = models.DateTimeField(default=timezone.now)
    lease_until = models.DateTimeField(null=True)

class AuditEvent(Record):
    actor = models.ForeignKey(User, on_delete=models.PROTECT, null=True)
    resource = models.CharField(max_length=80)
    resource_id = models.UUIDField(null=True)
    reason = models.TextField()
    outcome = models.CharField(max_length=80)

class Rollover(Record):
    contract = models.ForeignKey(Contract, on_delete=models.PROTECT)
    source_payment = models.OneToOneField(Payment, on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=16, decimal_places=2)
    mode = models.CharField(max_length=30)
    applied_week = models.ForeignKey(Week, on_delete=models.PROTECT, null=True)
    used_amount = models.DecimalField(max_digits=16, decimal_places=2, default=0)
    refunded_amount = models.DecimalField(max_digits=16, decimal_places=2, default=0)

class EnvironmentState(models.Model):
    id = models.PositiveSmallIntegerField(primary_key=True,default=1,editable=False)
    mode = models.CharField(max_length=20)
    provider = models.CharField(max_length=30)

class RolloverAllocation(Record):
    rollover = models.ForeignKey(Rollover, on_delete=models.PROTECT)
    week = models.ForeignKey(Week, on_delete=models.PROTECT)
    returned = models.BooleanField(default=False)
    amount = models.DecimalField(max_digits=16, decimal_places=2)
    class Meta:
        constraints = [models.UniqueConstraint(fields=['rollover','week'],name='step_rollover_week')]

class BankSettlement(Record):
    payment = models.OneToOneField(Payment,on_delete=models.PROTECT)
    payout = models.ForeignKey(Payout,on_delete=models.PROTECT)
    reference = models.CharField(max_length=200,unique=True)
    amount = models.DecimalField(max_digits=16,decimal_places=2)
    bank_digest = models.CharField(max_length=64)
