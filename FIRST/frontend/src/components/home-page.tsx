'use client';
import {EmailReminder} from './account-status';
import {useSession, SessionPending} from './session-provider';
import {ActionLink, PageHeading, Surface} from './ui';

export function HomePage() {
  const {status, user} = useSession();
  if(status !== 'ready') return <SessionPending/>;
  return <div className="home-dashboard">
    <PageHeading eyebrow="FIRST / BİRLİKTE ÜRET" title={user ? `Merhaba, ${user.full_name || user.username}.` : 'Birlikte üretmeye ilk adım.'}
      description={user ? 'Projelerinize devam edin, yeni bir paylaşım hazırlayın veya hesabınızı yönetin.' : 'GitHub projelerinizi toplulukla paylaşın. FIRST hesabınızla çalışmalarınızı bir araya getirin.'}/>
    {user ? <>
      {!user.email_verified && <EmailReminder/>}
      <div className="dashboard-grid">
        <Surface className="dashboard-card"><h2>Projelerim</h2><p>Paylaştığınız projeleri görüntüleyin ve bilgilerini güncelleyin.</p><ActionLink href="/projelerim">Projelerime git</ActionLink></Surface>
        <Surface className="dashboard-card"><h2>Yeni bir paylaşım</h2><p>GitHub repolarınızdan birini seçin ve topluluğa tanıtın.</p><ActionLink href="/projelerim/yeni" variant="secondary">Proje paylaş</ActionLink></Surface>
        <Surface className="dashboard-card"><h2>Hesabım</h2><p>Profilinizi, bağlı hesaplarınızı ve güvenlik ayarlarınızı yönetin.</p><ActionLink href="/hesap" variant="quiet">Hesabıma git</ActionLink></Surface>
      </div>
    </> : <Surface className="welcome-panel"><h2>Çalışmalarınıza bir yer açın.</h2><p>Hesabınızı oluşturun, GitHub bağlantınızı tamamlayın ve ilk projenizi paylaşın.</p><div className="action-row"><ActionLink href="/kayit">Hesap oluştur</ActionLink><ActionLink href="/giris" variant="secondary">Giriş yap</ActionLink></div></Surface>}
  </div>;
}
