"""Provider transport never holds a database transaction across network IO."""
import base64
import hashlib
import hmac
import json
import os
import secrets
from decimal import Decimal
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen
from django.conf import settings
from .security import Problem, require

class Iyzico:
    def __init__(self):
        self.key = os.environ.get('STEP_IYZICO_API_KEY', '')
        self.secret = os.environ.get('STEP_IYZICO_SECRET_KEY', '')
        self.base = 'https://api.iyzipay.com' if settings.PAYMENT_PROVIDER == 'iyzico_live' else 'https://sandbox-api.iyzipay.com'
    def call(self, method, path, payload):
        require(bool(self.key and self.secret), 'provider_unconfigured', 'Ödeme sağlayıcısı anahtarları eksik.', 503)
        body = b'' if payload is None else json.dumps(payload,ensure_ascii=False,separators=(',',':')).encode()
        random = secrets.token_hex(16)
        signature = hmac.new(self.secret.encode(),random.encode()+path.split('?')[0].encode()+body,hashlib.sha256).hexdigest()
        authorization = base64.b64encode(f'apiKey:{self.key}&randomKey:{random}&signature:{signature}'.encode()).decode()
        request = Request(self.base+path,data=None if payload is None else body,method=method,headers={'Authorization':'IYZWSv2 '+authorization,'x-iyzi-rnd':random,'Content-Type':'application/json','Accept':'application/json'})
        try:
            with urlopen(request,timeout=30) as response:
                data = json.loads(response.read(2097152))
        except HTTPError:
            raise Problem('provider_http_error','Sağlayıcı isteği reddetti; operatör incelemesi gerekir.',502)
        except (URLError, TimeoutError, OSError, ValueError):
            raise Problem('provider_unknown','Sağlayıcı sonucu bilinmiyor; kör tekrar yerine uzlaştırma gerekir.',503)
        require(isinstance(data,dict), 'provider_invalid', 'Geçersiz sağlayıcı yanıtı.',502)
        if data.get('status') != 'success':
            # Never persist/return provider free-text messages containing PII.
            raise Problem('provider_rejected','Sağlayıcı işlemi onaylamadı: '+str(data.get('errorCode','unknown'))[:50],409)
        return data
    def payment_detail(self,payment_id,conversation):
        return self.call('POST','/payment/detail',{'locale':'tr',**({'paymentId':payment_id} if payment_id else {'paymentConversationId':conversation})})
    def reporting(self,payment_id):
        from urllib.parse import urlencode
        return self.call('GET','/v2/reporting/payment/details?'+urlencode({'paymentId':payment_id}),None)
    def initialize(self,payload):
        return self.call('POST','/payment/iyzipos/checkoutform/initialize/auth/ecom',payload)
    def retrieve(self,token,conversation):
        return self.call('POST','/payment/iyzipos/checkoutform/auth/ecom/detail',{'locale':'tr','conversationId':conversation,'token':token})
    def onboard(self,payload):
        return self.call('POST','/onboarding/submerchant',payload)
    def submerchant_retrieve(self,external_id):
        return self.call('POST','/onboarding/submerchant/detail',{'locale':'tr','subMerchantExternalId':external_id})
    def approve(self,item):
        return self.call('POST','/payment/iyzipos/item/approve',{'locale':'tr','paymentTransactionId':item})
    def seller_price(self,item,amount,submerchant):
        result=self.call('PUT','/payment/item',{'locale':'tr','paymentTransactionId':item,'subMerchantPrice':str(amount),'subMerchantKey':submerchant})
        require(str(result.get('paymentTransactionId'))==item and result.get('subMerchantKey')==submerchant and Decimal(str(result.get('subMerchantPrice','-1')))==amount,'provider_unknown','Hakediş yanıtı alıcı/kırılım/net tutara bağlanamadı.',502)
        return result
    def refund(self,item,amount,conversation,ip):
        result=self.call('POST','/payment/refund',{'locale':'tr','conversationId':conversation,'paymentTransactionId':item,'price':str(amount),'currency':'TRY','ip':ip})
        require(str(result.get('paymentTransactionId'))==item and str(result.get('conversationId'))==conversation and result.get('currency')=='TRY' and Decimal(str(result.get('price','-1')))==amount,'provider_unknown','İade sonucu hedef/tutar kanıtı eksik; uzlaştırma gerekir.',502)
        return result
    def payout_retrieve(self,reference):
        return self.call('POST','/v1/mass/payout/retrieve',{'locale':'tr','externalId':reference})

def phone_send(phone,code):
    username = os.environ.get('STEP_NETGSM_USER','')
    password = os.environ.get('STEP_NETGSM_PASSWORD','')
    header = os.environ.get('STEP_NETGSM_HEADER','')
    require(bool(username and password and header), 'otp_unconfigured', 'Telefon sağlayıcısı yapılandırılmadı.',503)
    from xml.etree.ElementTree import Element, SubElement, tostring
    root = Element('mainbody'); head = SubElement(root,'header')
    for key,value in [('usercode',username),('password',password),('type','1:n'),('msgheader',header)]: SubElement(head,key).text=value
    body = SubElement(root,'body'); SubElement(body,'msg').text='STEP doğrulama kodunuz: '+code; SubElement(body,'no').text=phone
    request = Request('https://api.netgsm.com.tr/sms/send/otp',data=tostring(root,encoding='utf-8'),headers={'Content-Type':'application/xml'})
    try:
        with urlopen(request,timeout=30) as response: result=response.read(2048).decode().strip()
    except (URLError,HTTPError,TimeoutError,OSError):
        raise Problem('otp_transport','Telefon sağlayıcısına gönderim doğrulanamadı.',503)
    require(result.startswith('00 '), 'otp_failed','Telefon kodu gönderilemedi.',502)

class PayoutGateway:
    """No fabricated checkout fields stand in for an actual bank result API."""
    def request(self,payout):
        from .models import Policy,MoneyEntry,Payment
        strategy=Policy.objects.get_or_create(pk=1)[0].values.get('capabilities',{}).get('withdrawal_strategy')
        sources=[]
        for entry in MoneyEntry.objects.filter(user=payout.owner,kind='earned',mode=payout.mode):
            sources.extend(str(p.pk) for p in Payment.objects.filter(target_id=entry.source,mode=payout.mode))
        return {'state':'unavailable','code':'on_demand_withdrawal_unproven','operation':'marketplace bank-settlement reconciliation','strategy':strategy,'source_payments':sources,'required_evidence':'Official transaction-bound bank result API and on-demand held-funds agreement; checkout approve/retrieve is not bank payment proof'}
    def reconcile(self,payout):
        # Public CF/reporting documents contain item approval/payout amounts, not a
        # destination-bound completed bank transfer. No paid result is inferred.
        raise Problem('bank_result_unavailable','Resmî işlem/IBAN bağlı banka sonuç API kanıtı yok; paid yazılamaz.',503)
