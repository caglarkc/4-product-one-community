import os
from datetime import timedelta
from decimal import ROUND_HALF_UP
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from .common import *
from .providers import Iyzico
from .serialization import dto


def capability(name):
    if settings.STEP_MODE=='live':require(policy().get('capabilities',{}).get(name) is True,'provider_capability','Sağlayıcı '+name+' kabiliyeti teyit edilmedi.',503)

def mode_ready():
    require(settings.PAYMENT_PROVIDER in ['simulator','iyzico_sandbox','iyzico_live'],'provider_invalid','Sağlayıcı seçimi geçersiz.',503)
    if settings.PAYMENT_PROVIDER!='simulator':encrypted_text('provider-key-preflight')
    if settings.PAYMENT_PROVIDER=='simulator':require(settings.DEBUG and settings.STEP_MODE=='test','simulator_forbidden','Simulator yalnız yerel test modunda kullanılabilir.')
    else:require(os.environ.get('STEP_IYZICO_API_KEY') and os.environ.get('STEP_IYZICO_SECRET_KEY'),'provider_unconfigured','Sağlayıcı anahtarları eksik.',503)
    if settings.STEP_MODE=='live':
        require(settings.PAYMENT_PROVIDER=='iyzico_live','provider_mode','Canlı sağlayıcı zorunlu.',503);capability('merchant_kyc');capability('underwriting')
        from .accounts import readiness
        require(not readiness(),'live_not_ready','Canlı operasyon gereksinimleri tamamlanmadı.',503)

def entries(user,kind,amount,event,source,mode):
    return MoneyEntry.objects.get_or_create(event_key=event,defaults={'user':user,'kind':kind,'amount':amount,'source':source,'mode':mode})[0]

def target_of(payment,lock=False):
    return object_get({'milestone':Milestone,'week':Week,'credit_purchase':CreditPurchase}[payment.target_type],payment.target_id,lock)

def target_payment(target):
    kind='milestone' if isinstance(target,Milestone) else 'week'
    return Payment.objects.select_for_update().filter(target_type=kind,target_id=target.pk,status='funded',mode=settings.PAYMENT_PROVIDER).first()

@transaction.atomic
def credit_purchase(request):
    count=request.data.get('credits');require(isinstance(count,int) and count>0,'credit_count','Pozitif tam kredi sayısı gerekir.',400)
    team=object_get(Team,request.data['team']) if request.data.get('team') else None;wallet=wallet_for(request.user,team,True);price=money(setting_value('credit_price'))
    return dto(CreditPurchase.objects.create(owner=request.user,wallet=wallet,credits=count,amount=(price*count).quantize(CENT)))


def payment_start(request):
    mode_ready();data=request.data;keys=[key for key in ['milestone','week','credit_purchase'] if data.get(key)];require(len(keys)==1,'payment_target','Tek ödeme hedefi gerekir.',400);kind=keys[0]
    buyer=data.get('buyer',{})
    if settings.PAYMENT_PROVIDER!='simulator':
        fields(buyer,['first_name','last_name','phone','address','city','identity_number'])
        require(os.environ.get('STEP_API_URL','').startswith('https://'),'callback_unconfigured','HTTPS sağlayıcı callback adresi gerekir.',503)
    with transaction.atomic():
        target=object_get({'milestone':Milestone,'week':Week,'credit_purchase':CreditPurchase}[kind],data[kind],True)
        if kind=='credit_purchase':require(target.owner_id==request.user.pk and target.status=='pending');amount=target.amount;payee=None
        else:
            require(target.contract.employer_id==request.user.pk and target.contract.status=='active' and target.status=='unfunded','funding_state','Aktif ve fonlanmamış hedef gerekir.',409);amount=target.amount if kind=='milestone' else target.reserved_amount;payee=target.contract.payee
        existing=Payment.objects.filter(target_type=kind,target_id=target.pk,mode=settings.PAYMENT_PROVIDER).first()
        if existing:return dto(existing)
        if kind=='week' and settings.STEP_MODE=='live':capability('partial_release');capability('unused_refund');capability('rollover')
        total=amount
        if kind=='week':
            Contract.objects.select_for_update().get(pk=target.contract_id)
            for rollover in Rollover.objects.select_for_update().filter(contract=target.contract,mode=settings.PAYMENT_PROVIDER).order_by('created_at'):
                available=rollover.amount-rollover.used_amount-rollover.refunded_amount
                if available<=0 or amount<=0:continue
                if settings.PAYMENT_PROVIDER!='simulator':capability('rollover_allocation')
                taken=min(available,amount);RolloverAllocation.objects.create(rollover=rollover,week=target,amount=taken);rollover.used_amount+=taken;rollover.save();amount-=taken
        if payee and settings.PAYMENT_PROVIDER!='simulator':require(bool(payee.submerchant_key),'seller_unconfigured','Alıcı sağlayıcı kaydı eksik.',409)
        payment=Payment.objects.create(owner=request.user,target_type=kind,target_id=target.pk,amount=amount,total_funding=total,mode=settings.PAYMENT_PROVIDER,status='pending')
    return initialize_payment(request,payment,target,payee)

def initialize_payment(request,payment,target,payee):
    data=request.data;kind=payment.target_type;amount=payment.amount
    if payment.mode=='simulator':
        payment.checkout_url=settings.WEB_URL.rstrip('/')+'/money?payment='+str(payment.pk);payment.save();return dto(payment)
    buyer=data.get('buyer',{})
    try:
        fields(buyer,['first_name','last_name','phone','address','city','identity_number'])
        require(not payee or bool(payee.submerchant_key),'seller_unconfigured','Ödeme alıcısı sağlayıcı kaydını tamamlamalı.',409)
        callback=os.environ.get('STEP_API_URL','').rstrip('/')+'/api/v1/payment-webhooks/iyzico/'
        require(callback.startswith('https://'),'callback_unconfigured','HTTPS sağlayıcı callback adresi gerekir.',503)
        item={'id':str(target.pk),'name':'STEP '+kind,'category1':'Student services','itemType':'VIRTUAL','price':str(amount)}
        if payee:item.update(subMerchantKey=payee.submerchant_key,subMerchantPrice=str((amount*Decimal('0.90')).quantize(CENT,rounding=ROUND_HALF_UP)))
        address={'contactName':buyer['first_name']+' '+buyer['last_name'],'city':buyer['city'],'country':'Turkey','address':buyer['address']}
        result=Iyzico().initialize({'locale':'tr','conversationId':str(payment.conversation_id),'price':str(amount),'paidPrice':str(amount),'currency':'TRY','basketId':str(payment.conversation_id),'paymentGroup':'PRODUCT','callbackUrl':callback,'buyer':{'id':str(request.user.pk),'name':buyer['first_name'],'surname':buyer['last_name'],'gsmNumber':buyer['phone'],'email':request.user.email,'identityNumber':buyer['identity_number'],'registrationAddress':buyer['address'],'ip':request.META.get('REMOTE_ADDR',''),'city':buyer['city'],'country':'Turkey'},'shippingAddress':address,'billingAddress':address,'basketItems':[item]})
        require(result.get('token') and result.get('paymentPageUrl'),'provider_invalid','Hosted checkout kimliği eksik.',502)
        payment.provider_token=encrypted_text(result['token']);payment.provider_token_digest=__import__('hashlib').sha256(result['token'].encode()).hexdigest();payment.checkout_url=safe_url(result['paymentPageUrl']);payment.checkout_expires_at=timezone.now()+timedelta(seconds=int(result.get('tokenExpireTime',1800)));payment.save()
    except Problem as exc:
        payment.status='failed' if exc.detail['code']=='provider_rejected' else 'unknown';payment.retry_allowed=payment.status=='failed' and not payment.provider_token;payment.error_code=exc.detail['code'];payment.save()
        if payment.status=='failed':raise
    return dto(payment)


def reconcile(request,id,simulated=None):
    payment=object_get(Payment,id);require(payment.owner_id==request.user.pk or (request.user.is_staff and (request.user.is_superuser or request.user.has_perm('core.change_payment'))))
    if payment.status in ['funded','refunded']:return dto(payment)
    if simulated:
        require(payment.mode=='simulator' and settings.DEBUG and settings.STEP_MODE=='test','simulator_forbidden','Simülasyon kapalı.')
        require(simulated in ['success','failure'],'outcome_invalid','Geçerli sonuç gerekir.',400)
        result={'paymentStatus':'SUCCESS' if simulated=='success' else 'FAILURE','status':'success','conversationId':str(payment.conversation_id),'currency':'TRY','paidPrice':str(payment.amount),'paymentId':'simulator:'+str(payment.pk),'basketId':str(payment.conversation_id),'fraudStatus':1,'itemTransactions':[{'paymentTransactionId':'simulator:'+str(payment.pk),'itemId':str(payment.target_id),'price':str(payment.amount)}]}
    else:
        require(payment.mode!='simulator','reconciliation_unavailable','Fixture yalnız açık simulate işlemiyle sonuçlandırılır.',409)
        result=Iyzico().retrieve(decrypted_text(payment.provider_token),str(payment.conversation_id)) if payment.provider_token else Iyzico().payment_detail(None,str(payment.conversation_id))
    verified=result.get('status')=='success' and result.get('paymentStatus')=='SUCCESS' and str(result.get('conversationId'))==str(payment.conversation_id) and str(result.get('basketId'))==str(payment.conversation_id) and result.get('currency')=='TRY' and Decimal(str(result.get('paidPrice','0')))==payment.amount and result.get('fraudStatus')==1
    items=result.get('itemTransactions',[]);item=next((i for i in items if str(i.get('itemId'))==str(payment.target_id)),None)
    require(not verified or bool(item and item.get('paymentTransactionId')),'provider_binding','Sağlayıcı işlem hedefi uyuşmuyor.',409)
    with transaction.atomic():
        expected_conversation=payment.conversation_id;payment=object_get(Payment,id,True);require(payment.conversation_id==expected_conversation,'attempt_changed','Deneme değişti; eski sonuç yeni denemeye uygulanamaz.',409)
        if payment.status=='funded':return dto(payment)
        if not verified:
            failure=result.get('status')=='success' and result.get('paymentStatus')=='FAILURE' and str(result.get('conversationId'))==str(payment.conversation_id)
            payment.status='failed' if failure else 'unknown';payment.retry_allowed=failure;payment.error_code='provider_not_settled';payment.save();return dto(payment)
        target=target_of(payment,True)
        if isinstance(target,CreditPurchase):
            require(target.status=='pending','purchase_state','Satın alma durumu uyuşmuyor.',409);credit_change(target.wallet,target.credits,'purchase','purchase:'+str(target.pk),target.pk);target.status='funded'
        else:
            require(target.status=='unfunded' and target.contract.status=='active','target_changed','Ödeme hedefi değişmiş; operatör uzlaştırması gerekir.',409);target.status='funded'
        target.save();payment.status='funded';payment.retry_allowed=False;payment.funded_at=timezone.now();payment.provider_reference=str(result['paymentId']);payment.provider_item=str(item['paymentTransactionId']);payment.save()
        entries(payment.owner,'funding',-payment.amount,'fund-debit:'+str(payment.pk),payment.pk,payment.mode);entries(None,'held_funds',payment.amount,'fund-credit:'+str(payment.pk),payment.pk,payment.mode)
        notify(payment.owner,'payment.funded','Ön fonlama doğrulandı.',payment)
    return dto(payment)

def retry_payment(request,id):
    mode_ready();payment=object_get(Payment,id);require(payment.owner_id==request.user.pk)
    require(payment.status=='failed' and payment.retry_allowed and payment.funded_at is None and not payment.provider_reference and payment.released_amount==0 and payment.refunded_amount==0,'retry_unsafe','Yalnız kesin başarısız ve hiç fonlanmamış deneme yeniden açılır.',409)
    if payment.mode!='simulator':
        fields(request.data.get('buyer',{}),['first_name','last_name','phone','address','city','identity_number'])
    proof={'kind':'initialize_rejected','error_code':payment.error_code}
    if payment.provider_token and payment.mode!='simulator':
        result=Iyzico().retrieve(decrypted_text(payment.provider_token),str(payment.conversation_id))
        require(result.get('status')=='success' and result.get('paymentStatus')=='FAILURE' and str(result.get('conversationId'))==str(payment.conversation_id),'retry_unproven','Sağlayıcı terminal başarısız sonuç kanıtını vermedi.',409)
        proof={'kind':'retrieve_failure','conversation_id':str(payment.conversation_id),'payment_status':'FAILURE'}
    elif payment.mode=='simulator':proof={'kind':'local_fixture_failure'}
    else:require(payment.error_code=='provider_rejected','retry_unproven','Gönderilmeyen veya belirsiz sonuç yeniden açılamaz.',409)
    expected=payment.conversation_id
    with transaction.atomic():
        payment=object_get(Payment,id,True);require(payment.conversation_id==expected and payment.status=='failed' and payment.retry_allowed,'attempt_changed','Ödeme denemesi değişti.',409)
        target=target_of(payment,True)
        require((isinstance(target,CreditPurchase) and target.status=='pending') or (not isinstance(target,CreditPurchase) and target.status=='unfunded' and target.contract.status=='active'),'target_changed','Fonlama hedefi artık yeniden denenemez.',409)
        PaymentAttempt.objects.create(payment=payment,number=payment.attempt,conversation_id=payment.conversation_id,provider_token=payment.provider_token,provider_token_digest=payment.provider_token_digest,status=payment.status,error_code=payment.error_code,proof=proof)
        payment.attempt+=1;payment.conversation_id=uuid.uuid4();payment.provider_token='';payment.provider_token_digest='';payment.checkout_url='';payment.checkout_expires_at=None;payment.error_code='';payment.retry_allowed=False;payment.status='pending';payment.save();audit(request.user,payment,'Sağlayıcı terminal başarısız denemeden kontrollü tekrar','checkout.retry')
        payee=None if isinstance(target,CreditPurchase) else target.contract.payee
    return initialize_payment(request,payment,target,payee)

@transaction.atomic
def release_target(target,dispute_resolution=False):
    target=object_get(target.__class__,target.pk,True);c=object_get(Contract,target.contract_id,True)
    if target.status=='released':return dto(target)
    allowed=['submitted','review']+(['disputed'] if dispute_resolution else [])
    require(target.status in allowed,'release_state','Ödeme serbest bırakılamaz.',409)
    require(dispute_resolution or not Dispute.objects.filter(target_id=target.pk,status='open').exists(),'payment_disputed','İtiraz ödeme serbest bırakmasını engelliyor.',409)
    payment=target_payment(target);require(payment is not None,'payment_unfunded','Doğrulanmış ön fon bulunamadı.',409)
    gross=target.amount if isinstance(target,Milestone) else target.gross;net=(gross*Decimal('0.90')).quantize(CENT,rounding=ROUND_HALF_UP);unused=(payment.total_funding or payment.amount)-gross
    if unused>0:capability('partial_release');capability('unused_refund')
    if isinstance(target,Week) and target.remainder_choice=='rollover' and unused>0:capability('rollover')
    operation,_=ProviderOperation.objects.get_or_create(event_key='release:'+str(target.pk),defaults={'payment':payment,'kind':'release','payload':{'gross':str(gross),'net':str(net),'unused':str(unused),'target_type':payment.target_type,'target_id':str(target.pk),'rollover':isinstance(target,Week) and target.remainder_choice=='rollover','payee':str(c.payee_id),'submerchant_key':c.payee.submerchant_key}})
    target.status='release_pending';target.review_due_at=None;target.save()
    if payment.mode=='simulator':finish_operation(operation,{})
    return dto(target.__class__.objects.get(pk=target.pk))

@transaction.atomic
def queue_refund(target):
    payment=target_payment(target);require(payment is not None,'payment_unfunded','İade için fonlama bulunamadı.',409)
    operation,_=ProviderOperation.objects.get_or_create(event_key='refund:'+str(target.pk),defaults={'payment':payment,'kind':'refund','payload':{'amount':str((payment.total_funding or payment.amount)-payment.refunded_amount),'target_type':payment.target_type,'target_id':str(target.pk)}})
    target.status='refund_pending';target.review_due_at=None;target.save()
    if payment.mode=='simulator':finish_operation(operation,{})

def run_operation(id):
    with transaction.atomic():
        op=object_get(ProviderOperation,id,True)
        if op.state not in ['pending']:return
        op.state='processing';op.attempts+=1;op.lease_until=timezone.now()+timedelta(minutes=2);op.save()
    try:
        payment=op.payment;gate=Iyzico();result={}
        if op.kind=='release':
            # Live capability must cover held seller allocation and unused-fund handling.
            unused=Decimal(op.payload['unused'])
            if unused>0 and not op.payload.get('rollover') and not op.result.get('unused_refund_confirmed'):
                result['refund']=gate.refund(payment.provider_item,unused,str(op.pk),os.environ.get('STEP_SERVER_PUBLIC_IP',''))
                with transaction.atomic():ProviderOperation.objects.filter(pk=op.pk).update(result={'unused_refund_confirmed':True})
            gate.seller_price(payment.provider_item,Decimal(op.payload['net']),op.payload['submerchant_key'])
            with transaction.atomic():ProviderOperation.objects.filter(pk=op.pk).update(result={**ProviderOperation.objects.get(pk=op.pk).result,'allocation_confirmed':True,'allocation_payee':op.payload['payee']})
            result['approval']=gate.approve(payment.provider_item)
            require(str(result['approval'].get('paymentTransactionId'))==payment.provider_item,'provider_unknown','Onay yanıtı ödeme kırılımına bağlanamadı.',502)
            with transaction.atomic():ProviderOperation.objects.filter(pk=op.pk).update(result={**ProviderOperation.objects.get(pk=op.pk).result,'approval_confirmed':True,'net':op.payload['net']})
        elif op.kind in ['refund','rollover_refund']:
            result['refund']=gate.refund(payment.provider_item,Decimal(op.payload['amount']),str(op.pk),os.environ.get('STEP_SERVER_PUBLIC_IP',''))
            with transaction.atomic():ProviderOperation.objects.filter(pk=op.pk).update(result={'refund_confirmed':True,'amount':op.payload['amount'],'provider_item':payment.provider_item})
        else:raise Problem('operation_invalid','Desteklenmeyen sağlayıcı işlemi.',409)
        finish_operation(op,result)
    except Problem as exc:
        with transaction.atomic():
            op=object_get(ProviderOperation,id,True);op.state='failed' if exc.detail['code']=='provider_rejected' else 'unknown';op.result={'error_code':exc.detail['code'],**op.result};op.save()
            if op.payment_id:Payment.objects.filter(pk=op.payment_id).update(error_code=exc.detail['code'])
        # Unknown/failed mutations are not blindly retried by tick.

def operation_dto(op):
    return {'id':op.pk,'kind':op.kind,'state':op.state,'payment':op.payment_id,'attempts':op.attempts,'error_code':op.result.get('error_code'),'missing_operation':op.result.get('missing_operation') or op.result.get('required_evidence')}

def reconcile_operation(request,id):
    require(request.user.is_staff and (request.user.is_superuser or request.user.has_perm('core.change_provideroperation')),'operator_permission','Sağlayıcı uzlaştırma yetkisi gerekir.');fields(request.data,['reason']);op=object_get(ProviderOperation,id)
    if op.kind=='onboarding':
        from .accounts import reconcile_onboarding
        return reconcile_onboarding(request,op)
    require(op.payment_id is not None and op.kind in ['release','refund','rollover_refund'],'operation_scope','Banka operasyonu kendi çekim ekranında uzlaştırılır.',409)
    if op.state=='confirmed':return operation_dto(op)
    p=op.payment
    if p.mode=='simulator':require(settings.DEBUG and settings.STEP_MODE=='test','simulator_forbidden','Fixture kapalı.');finish_operation(op,{});return operation_dto(ProviderOperation.objects.get(pk=op.pk))
    require(bool(p.provider_reference),'payment_proof_missing','Sağlayıcı payment kimliği olmadan operasyon sonuçlanamaz.',409)
    report=Iyzico().reporting(p.provider_reference)
    records=report.get('payments',[]);record=next((r for r in records if str(r.get('paymentId'))==p.provider_reference and str(r.get('paymentConversationId'))==str(p.conversation_id) and r.get('currency')=='TRY'),None)
    require(record is not None,'report_binding','Rapor kayıtlı payment/deneme/para birimine bağlanamadı.',409)
    item=next((i for i in record.get('itemTransactions',[]) if str(i.get('paymentTransactionId'))==p.provider_item),None);require(item is not None,'report_binding','Rapor kayıtlı kırılıma bağlanamadı.',409)
    confirmed=op.kind=='release' and op.result.get('allocation_confirmed') and op.result.get('allocation_payee')==op.payload.get('payee') and item.get('transactionStatus')==2 and Decimal(str(item.get('subMerchantPrice','-1')))==Decimal(op.payload['net']) and (Decimal(op.payload['unused'])==0 or op.payload.get('rollover') or op.result.get('unused_refund_confirmed'))
    if op.kind in ['refund','rollover_refund']:confirmed=bool(op.result.get('refund_confirmed') and op.result.get('provider_item')==p.provider_item and Decimal(op.result['amount'])==Decimal(op.payload['amount']))
    with transaction.atomic():
        current=object_get(ProviderOperation,id,True)
        if current.state=='confirmed':return operation_dto(current)
        audit(request.user,current,request.data['reason'],'provider.reconcile')
        if confirmed:finish_operation(current,{'report_verified':True})
        else:
            matches=[{'refund_transaction':r.get('refundTxId'),'conversation':r.get('refundConversationId'),'amount':r.get('refundPrice'),'currency':r.get('currencyCode'),'status':r.get('refundStatus')} for r in item.get('refunds',[]) if str(r.get('refundConversationId'))==str(current.pk)]
            current.state='unknown';current.result={**current.result,'report_seen':True,'item_status':item.get('transactionStatus'),'matching_refunds':matches,'missing_operation':'Terminal bound refund-status evidence or remaining marketplace approval; no blind retry'};current.save()
        return operation_dto(ProviderOperation.objects.get(pk=current.pk))

def admin_reconcile_payment(request,id):
    require(request.user.is_staff and (request.user.is_superuser or request.user.has_perm('core.change_payment')),'operator_permission','Ödeme uzlaştırma yetkisi gerekir.');fields(request.data,['reason']);row=object_get(Payment,id)
    result=reconcile(request,id)
    with transaction.atomic():audit(request.user,row,request.data['reason'],'checkout.reconcile')
    return result

@transaction.atomic
def finish_operation(operation,result):
    op=object_get(ProviderOperation,operation.pk,True)
    if op.state=='confirmed':return
    p=object_get(Payment,op.payment_id,True);target=target_of(p,True)
    if op.kind=='rollover_refund':
        rollover=object_get(Rollover,op.payload['rollover'],True);amount=Decimal(op.payload['amount']);require(rollover.amount-rollover.used_amount-rollover.refunded_amount>=amount,'rollover_changed','Aktarma fonu durumu değişmiş.',409)
        entries(p.owner,'rollover_refund',amount,'rollover-refund-credit:'+str(op.pk),rollover.pk,p.mode);entries(None,'held_refund',-amount,'rollover-refund-debit:'+str(op.pk),rollover.pk,p.mode);rollover.refunded_amount+=amount;rollover.save();p.refunded_amount+=amount
    elif op.kind=='release':
        require(target.status=='release_pending','release_changed','Hakediş durumu değişmiş.',409);c=object_get(Contract,target.contract_id,True);payee=object_get(User,op.payload['payee']);gross=Decimal(op.payload['gross']);net=Decimal(op.payload['net']);fee=gross-net;unused=Decimal(op.payload['unused'])
        account,_=MoneyAccount.objects.get_or_create(user=payee,defaults={'mode':p.mode});account=MoneyAccount.objects.select_for_update().get(pk=account.pk);require(account.mode==p.mode,'mode_mismatch','Test kazancı canlıya taşınamaz.',409)
        if not MoneyEntry.objects.filter(event_key='earned:'+str(target.pk)).exists():
            account.available+=net;account.save();entries(payee,'earned',net,'earned:'+str(target.pk),target.pk,p.mode);entries(None,'commission',fee,'fee:'+str(target.pk),target.pk,p.mode);entries(None,'held_release',-gross,'release-debit:'+str(target.pk),target.pk,p.mode)
            if unused>0:
                if op.payload.get('rollover'):Rollover.objects.get_or_create(source_payment=p,defaults={'contract':c,'amount':unused,'mode':p.mode})
                else:entries(p.owner,'refund',unused,'unused-refund:'+str(target.pk),target.pk,p.mode);entries(None,'held_refund',-unused,'unused-debit:'+str(target.pk),target.pk,p.mode);p.refunded_amount+=unused
        p.released_amount=gross;p.settlement_status='pending' if p.mode!='simulator' else 'unavailable';target.status='released';target.save();notify(payee,'payment.released','Hakediş serbest bırakıldı; banka aktarımı ayrı izlenir.',target)
    elif op.kind=='refund':
        amount=Decimal(op.payload['amount']);entries(p.owner,'refund',amount,'refund-credit:'+str(op.pk),target.pk,p.mode);entries(None,'held_refund',-amount,'refund-debit:'+str(op.pk),target.pk,p.mode);p.refunded_amount+=amount;p.status='refunded';target.status='refunded';target.save()
    p.save();op.state='confirmed';op.result={**op.result,'confirmed':True};op.lease_until=None;op.save()

@transaction.atomic
def payouts(request):
    u=request.user;data=request.data
    if request.method=='GET':return page(request,Payout.objects.filter(owner=u).order_by('-created_at'),dto)
    fields(data,['amount','iban','account_name']);amount=money(data['amount']);minimum=money(setting_value('withdraw_minimum'));require(amount>=minimum,'withdraw_minimum','Çekim alt limiti karşılanmalı.',400)
    setting_value('withdraw_schedule');mode_ready();capability('withdrawal');capability('bank_reconciliation')
    require(u.bank_name and str(data['account_name']).casefold()==u.bank_name.casefold() and u.bank_digest==bank_digest(data['iban']),'bank_identity','Kendi adınıza sağlayıcıda doğrulanmış banka hesabı gerekir.',409)
    account=MoneyAccount.objects.select_for_update().filter(user=u,mode=settings.PAYMENT_PROVIDER).first();require(account is not None and account.available>=amount,'insufficient_earnings','Yeterli çekilebilir kazanç yok.',409)
    account.available-=amount;account.reserved+=amount;account.save();row=Payout.objects.create(owner=u,amount=amount,mode=settings.PAYMENT_PROVIDER,account_name=u.bank_name,iban_masked=u.iban_masked,bank_ciphertext=encrypted_text(str(data['iban'])),bank_digest=u.bank_digest);ProviderOperation.objects.create(kind='withdrawal',event_key='withdrawal:'+str(row.pk),state='blocked' if row.mode!='simulator' else 'fixture',payload={'payout':str(row.pk),'amount':str(amount),'bank_digest':u.bank_digest});return dto(row)


def money_dto(user):
    account=MoneyAccount.objects.filter(user=user,mode=settings.PAYMENT_PROVIDER).first()
    pending=Decimal('0')
    for c in Contract.objects.filter(payee=user):
        for m in c.milestones.filter(status__in=['funded','in_progress','submitted','revision','disputed','release_pending']):pending+=m.amount*Decimal('0.90')
        for w in c.weeks.filter(status__in=['review','disputed','release_pending']):pending+=w.net
    return {'currency':'TRY','mode':settings.PAYMENT_PROVIDER,'available':account.available if account else '0.00','reserved':account.reserved if account else '0.00','pending':pending.quantize(CENT),'entries':[{'id':e.pk,'delta':e.amount,'kind':e.kind,'created_at':e.created_at} for e in MoneyEntry.objects.filter(user=user,mode=settings.PAYMENT_PROVIDER).order_by('-created_at')[:100]],'payouts':[dto(p) for p in Payout.objects.filter(owner=user).order_by('-created_at')[:100]]}

@transaction.atomic
def cancel_rollover(contract):
    # Return allocations for unfunded future weeks, then refund unused held rollover.
    for allocation in RolloverAllocation.objects.select_for_update().filter(week__contract=contract,week__status='unfunded',returned=False):
        rollover=object_get(Rollover,allocation.rollover_id,True);rollover.used_amount-=allocation.amount;rollover.save();allocation.returned=True;allocation.save()
    for rollover in Rollover.objects.select_for_update().filter(contract=contract):
        available=rollover.amount-rollover.used_amount-rollover.refunded_amount
        if available<=0:continue
        operation,_=ProviderOperation.objects.get_or_create(event_key='rollover-cancel:'+str(rollover.pk),defaults={'payment':rollover.source_payment,'kind':'rollover_refund','payload':{'rollover':str(rollover.pk),'amount':str(available)}})
        if rollover.mode=='simulator':finish_operation(operation,{})
