"""PySide6 Widgets desktop. Private previews are decoded only in GUI memory."""
import socket
import sys

from PySide6.QtCore import Qt
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import (QApplication, QCheckBox, QComboBox, QDialog, QDialogButtonBox,
                             QFormLayout, QHBoxLayout, QInputDialog, QLabel, QLineEdit,
                             QListWidget, QListWidgetItem, QMainWindow, QMessageBox,
                             QPushButton, QScrollArea, QStackedWidget, QTextEdit,
                             QVBoxLayout, QWidget)

from .engine import Engine


class PreviewDialog(QDialog):
    def __init__(self, parent, ident, png):
        super().__init__(parent)
        self.ident = ident
        self.setWindowTitle("STEP — kişisel ekran önizlemesi")
        self.resize(1000, 760)
        layout = QVBoxLayout(self)
        notice = QLabel("Bu görüntü size özeldir. Güvenli olduğuna karar vermeden yayın işlemi seçmeyin.")
        notice.setWordWrap(True)
        layout.addWidget(notice)
        self.picture = QLabel()
        self.picture.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.picture.setAccessibleName("Seçtiğiniz ekranın kişisel önizlemesi")
        image = QPixmap()
        if not image.loadFromData(png, "PNG"):
            raise ValueError("Görüntü PNG olarak okunamadı.")
        self.image = image
        self.picture.setPixmap(image.scaled(940, 590, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setWidget(self.picture)
        layout.addWidget(scroll, 1)
        self.state = QLabel()
        self.state.setWordWrap(True)
        layout.addWidget(self.state)
        controls = QHBoxLayout()
        self.privacy_button = QPushButton("Kişisel bilgi talebi")
        self.ready_button = QPushButton("İncelemeyi tamamla")
        self.publish_button = QPushButton("Güvenli, şimdi yayımla")
        controls.addWidget(self.privacy_button)
        controls.addStretch()
        controls.addWidget(self.ready_button)
        controls.addWidget(self.publish_button)
        layout.addLayout(controls)
        close = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        close.rejected.connect(self.reject)
        layout.addWidget(close)
        self.privacy_button.clicked.connect(lambda: parent.request_privacy(ident))
        self.ready_button.clicked.connect(lambda: parent.request_publication(ident, "review-ready"))
        self.publish_button.clicked.connect(lambda: parent.request_publication(ident, "publish"))

    def update_record(self, record):
        self.privacy_button.setEnabled(record.get("can_privacy", False))
        self.ready_button.setEnabled(record.get("can_publish", False))
        self.publish_button.setEnabled(record.get("can_publish", False))
        text = "Durum: " + record["state"]
        if record.get("privacy_pending"):
            text += " · Kişisel bilgi talebi şifreli kuyrukta; işverene yayın açılmaz."
        if record.get("error"):
            text += " · " + record["error"]["message"]
        self.state.setText(text)


class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("STEP Tracker")
        self.resize(1060, 810)
        self.engine = Engine()
        self.record_map = {}
        self.preview_dialogs = {}
        self.latest = {}
        self.closing = False
        self.allowed_close = False
        self.pages = QStackedWidget()
        self.setCentralWidget(self.pages)
        self._login_page()
        self._work_page()
        self.engine.changed.connect(self.update_state)
        self.engine.authenticated.connect(self.on_authenticated)
        self.engine.monitor_list.connect(self.on_monitors)
        self.engine.preview.connect(self.on_preview)
        self.engine.error.connect(self.show_error)
        self.engine.closed.connect(self.finish_close)
        for label in self.findChildren(QLabel):
            label.setTextFormat(Qt.TextFormat.PlainText)
        self.engine.start()
        # STEP keeps its own modest Widgets layout; no FIRST CSS/assets are imported.
        self.setStyleSheet("""
            QWidget { font-size: 14px; }
            QMainWindow, QDialog { background: #f3f6f6; }
            QLabel#heading { font-size: 25px; font-weight: 600; color: #123b3b; }
            QPushButton { padding: 9px 13px; border: 1px solid #647b7b; border-radius: 4px; background: white; }
            QPushButton:focus, QLineEdit:focus, QComboBox:focus { border: 2px solid #006c67; }
            QPushButton:disabled { color: #647b7b; background: #e5ecec; }
            QLineEdit, QTextEdit, QComboBox, QListWidget { padding: 6px; background: white; }
            QLabel#error { color: #8c2020; }
        """)

    def _login_page(self):
        page = QWidget()
        box = QVBoxLayout(page)
        box.setContentsMargins(90, 70, 90, 70)
        title = QLabel("STEP Tracker")
        title.setObjectName("heading")
        box.addWidget(title)
        explanation = QLabel("Windows, macOS ve Linux X11 için seçili ekran ve etkinlik sayacı.\n"
                             "Klavye içeriği, pencere başlığı, kamera veya video kaydedilmez.")
        explanation.setWordWrap(True)
        box.addWidget(explanation)
        form = QFormLayout()
        self.url = QLineEdit()
        self.url.setPlaceholderText("https://step-backend.example")
        self.email = QLineEdit()
        self.email.setPlaceholderText("E-posta")
        self.password = QLineEdit()
        self.password.setEchoMode(QLineEdit.EchoMode.Password)
        self.device = QLineEdit(socket.gethostname()[:100])
        self.local = QCheckBox("Açık localhost geliştirmesi: yalnız yerel HTTP'ye izin ver")
        form.addRow("Backend HTTPS adresi", self.url)
        form.addRow("E-posta", self.email)
        form.addRow("Şifre", self.password)
        form.addRow("Cihaz adı", self.device)
        box.addLayout(form)
        box.addWidget(self.local)
        controls = QHBoxLayout()
        self.login_button = QPushButton("Cihaz girişi yap")
        self.cached_button = QPushButton("Bu hesabın kayıtlı cihazını aç")
        controls.addWidget(self.login_button)
        controls.addWidget(self.cached_button)
        box.addLayout(controls)
        self.login_error = QLabel()
        self.login_error.setObjectName("error")
        self.login_error.setWordWrap(True)
        self.login_error.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        box.addWidget(self.login_error)
        help_text = QLabel("Token ve şifreli kuyruk anahtarı işletim sistemi anahtarlığında tutulur.\n"
                           "Güvenli anahtarlık ve gerçek OS izinleri olmadan takip başlamaz. "
                           "Kayıtlı cihaz çevrimdışı açılabilir; yeni çalışma yetkisi sunucudan alınır.")
        help_text.setWordWrap(True)
        box.addWidget(help_text)
        box.addStretch()
        self.pages.addWidget(page)
        self.login_button.clicked.connect(lambda: self.login(False))
        self.cached_button.clicked.connect(lambda: self.login(True))
        self.password.returnPressed.connect(lambda: self.login(False))

    def _work_page(self):
        page = QWidget()
        box = QVBoxLayout(page)
        box.setContentsMargins(26, 22, 26, 22)
        header = QHBoxLayout()
        title = QLabel("STEP · çalışma takibi")
        title.setObjectName("heading")
        header.addWidget(title)
        header.addStretch()
        self.account_label = QLabel()
        header.addWidget(self.account_label)
        self.reauth_button = QPushButton("Cihaz girişini yenile")
        header.addWidget(self.reauth_button)
        box.addLayout(header)
        form = QFormLayout()
        self.contract_picker = QComboBox()
        self.contract_picker.setAccessibleName("Çalışma sözleşmesi")
        self.monitor_picker = QComboBox()
        self.monitor_picker.setAccessibleName("Kaydedilecek tek fiziksel ekran")
        self.memo = QTextEdit()
        self.memo.setPlaceholderText("Bu bölümde yapacağınız işi kısaca açıklayın")
        self.memo.setMaximumHeight(82)
        form.addRow("Sözleşme", self.contract_picker)
        form.addRow("Seçili ekran", self.monitor_picker)
        form.addRow("Çalışma açıklaması", self.memo)
        box.addLayout(form)
        self.contract_info = QLabel()
        self.contract_info.setWordWrap(True)
        box.addWidget(self.contract_info)
        setup = QHBoxLayout()
        self.refresh_button = QPushButton("Sözleşme / fonu yenile")
        self.monitor_button = QPushButton("Ekranları yenile")
        self.permission_button = QPushButton("OS izinlerini kontrol et / iste")
        setup.addWidget(self.refresh_button)
        setup.addWidget(self.monitor_button)
        setup.addWidget(self.permission_button)
        setup.addStretch()
        box.addLayout(setup)
        controls = QHBoxLayout()
        self.start_button = QPushButton("Başlat / elle devam et")
        self.pause_button = QPushButton("Duraklat")
        self.stop_button = QPushButton("Çalışmayı durdur")
        self.sync_button = QPushButton("Kuyruğu senkronize et")
        for button in (self.start_button, self.pause_button, self.stop_button, self.sync_button):
            controls.addWidget(button)
        box.addLayout(controls)
        self.mode_label = QLabel("Hazır")
        self.mode_label.setWordWrap(True)
        self.time_label = QLabel()
        self.funding_label = QLabel()
        self.funding_label.setWordWrap(True)
        self.sync_label = QLabel()
        self.sync_label.setWordWrap(True)
        self.error_label = QLabel()
        self.error_label.setObjectName("error")
        self.error_label.setWordWrap(True)
        self.error_label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        for label in (self.mode_label, self.time_label, self.funding_label, self.sync_label, self.error_label):
            box.addWidget(label)
        section = QLabel("Kişisel görüntü önizlemeleri")
        section.setObjectName("heading")
        box.addWidget(section)
        self.images = QListWidget()
        self.images.setAccessibleName("Kişisel ekran görüntüleri ve gönderim durumları")
        box.addWidget(self.images, 1)
        image_controls = QHBoxLayout()
        self.preview_button = QPushButton("Seçili görüntüyü incele")
        self.privacy_button = QPushButton("Kişisel bilgi talebi")
        self.ready_button = QPushButton("İncelemeyi tamamla")
        self.publish_button = QPushButton("Güvenli, şimdi yayımla")
        for button in (self.preview_button, self.privacy_button, self.ready_button, self.publish_button):
            image_controls.addWidget(button)
        box.addLayout(image_controls)
        policy = QLabel("Görüntüler otomatik yüklenince yalnız kişisel önizlemeye gider. "
                        "Kişisel bilgi talebi süreyi/ücreti düşürmez. Silme işlemi bulunmaz. "
                        "Hareketsizlikte son etkinlikten sonrası ücretli süreye eklenmez. Yeni etkinlik, ACK ve fon kontrolünden sonra otomatik devam ettirir; kullanıcı durdurması veya hata sonrası elle devam gerekir.")
        policy.setWordWrap(True)
        box.addWidget(policy)
        self.pages.addWidget(page)
        self.start_button.clicked.connect(self.start_capture)
        self.pause_button.clicked.connect(lambda: self.engine.send("pause"))
        self.stop_button.clicked.connect(lambda: self.engine.send("stop"))
        self.sync_button.clicked.connect(lambda: self.engine.send("sync"))
        self.refresh_button.clicked.connect(lambda: self.engine.send("refresh"))
        self.monitor_button.clicked.connect(lambda: self.engine.send("monitors"))
        self.permission_button.clicked.connect(lambda: self.engine.send("permissions"))
        self.reauth_button.clicked.connect(self.reauthenticate)
        self.contract_picker.currentIndexChanged.connect(self.update_contract_info)
        self.images.currentItemChanged.connect(self.update_image_buttons)
        self.images.itemDoubleClicked.connect(lambda _: self.open_selected_preview())
        self.preview_button.clicked.connect(self.open_selected_preview)
        self.privacy_button.clicked.connect(lambda: self.request_privacy(self.selected_image()))
        self.ready_button.clicked.connect(lambda: self.request_publication(self.selected_image(), "review-ready"))
        self.publish_button.clicked.connect(lambda: self.request_publication(self.selected_image(), "publish"))

    def login(self, cached):
        self.login_error.clear()
        self.login_button.setEnabled(False)
        self.cached_button.setEnabled(False)
        self.engine.send("login", url=self.url.text(), email=self.email.text(), password=self.password.text(),
                         device_name=self.device.text(), development=self.local.isChecked(), cached=cached)
        self.password.clear()

    def on_authenticated(self, value):
        self.account_label.setText(value["user"].get("display_name") or value["user"].get("email", ""))
        previous = self.contract_picker.currentData()
        previous_id = previous.get("id") if previous else None
        self.contract_picker.blockSignals(True)
        self.contract_picker.clear()
        for contract in value["contracts"]:
            label = contract.get("scope", "").replace("\n", " ")[:90] or contract["id"][:8]
            self.contract_picker.addItem(label + (" · hazır" if contract.get("tracker_ready") else " · bekliyor"), contract)
            if contract["id"] == previous_id:
                self.contract_picker.setCurrentIndex(self.contract_picker.count() - 1)
        self.contract_picker.blockSignals(False)
        self.update_contract_info()
        self.pages.setCurrentIndex(1)
        self.login_button.setEnabled(True)
        self.cached_button.setEnabled(True)

    def on_monitors(self, rows):
        old = self.monitor_picker.currentData()
        self.monitor_picker.clear()
        for monitor in rows:
            self.monitor_picker.addItem(monitor.label, monitor.id)
            if monitor.id == old:
                self.monitor_picker.setCurrentIndex(self.monitor_picker.count() - 1)

    def update_contract_info(self):
        contract = self.contract_picker.currentData()
        if not contract:
            self.contract_info.setText("Takip için sözleşme bulunamadı. STEP web uygulamasından sözleşme ve ön fon oluşturun.")
            return
        if contract.get("tracker_ready"):
            text = "Sözleşme takip için hazır. Yeni kayıt başlarken sunucu bu cihaza ayrı fon/süre yetkisi ayırır."
            if contract.get("remaining_seconds") is not None:
                text += f" Ortak bütçe görünümü: {contract['remaining_seconds']} saniye; bu cihazın çevrimdışı yetkisi değildir."
        else:
            reasons = {"unfunded": "Ön fon eksik", "limit_exhausted": "Ortak haftalık limit dolmuş",
                       "payment_not_ready": "Ödeme hazırlığı tamamlanmamış", "inactive": "Sözleşme aktif değil"}
            code = contract.get("blocked_reason", "")
            text = reasons.get(code, "Sözleşme fon/limit veya erişim nedeniyle hazır değil") + (" [" + code + "]" if code else "")
        self.contract_info.setText(text)

    def start_capture(self):
        contract = self.contract_picker.currentData()
        monitor = self.monitor_picker.currentData()
        if not contract or not monitor:
            self.show_error("Sözleşme ve fiziksel ekran seçin. Wayland yerine Linux X11/Xorg oturumu gerekir.")
            return
        self.error_label.clear()
        self.engine.send("start", contract_id=contract["id"], memo=self.memo.toPlainText(), monitor_id=monitor)

    def reauthenticate(self):
        password, accepted = QInputDialog.getText(self, "Cihaz girişini yenile", "Aynı hesabın şifresi", QLineEdit.EchoMode.Password)
        if accepted and password:
            self.engine.send("reauthenticate", password=password)

    def update_state(self, state):
        self.latest = state
        environment = {"test": "Test sunucusu", "live": "Canlı sunucu"}.get(state.get("server_mode"), "Sunucu modu yetki alınınca doğrulanır")
        self.mode_label.setText(environment + " · " + state["mode"])
        self.time_label.setText(f"Bu bölüm: {state['elapsed']} sn · bu cihazın yetkisinde kalan: " + (f"{state['remaining']} sn" if state["remaining"] is not None else "kayıt açık değil"))
        funding = state.get("funding")
        self.funding_label.setText("Ayrılmış fon: " + str(funding.get("reserved_amount", "")) + " " + funding.get("currency", "") + " · Yetki sonu: " + state["authorized_until"] if funding else "Çevrimdışı kayıt yalnız önceden bu cihaza ayrılmış sunucu yetkisi içinde sürer. Yeni yetki çevrimiçi alınır.")
        self.sync_label.setText(f"Bekleyen şifreli işlem: {state['pending']} · {state['sync']}")
        busy = state["recording"] or state["starting"]
        watching = state.get("idle_waiting", False)
        editing_locked = busy or watching
        self.start_button.setEnabled(not busy and state["pending"] == 0 and not self.closing)
        self.pause_button.setEnabled((busy or watching) and not self.closing)
        self.stop_button.setEnabled((busy or watching or state["pending"] > 0) and not self.closing)
        self.contract_picker.setEnabled(not editing_locked and not self.closing)
        self.monitor_picker.setEnabled(not editing_locked and not self.closing)
        self.memo.setEnabled(not editing_locked and not self.closing)
        self.monitor_button.setEnabled(not editing_locked and not self.closing)
        self.permission_button.setEnabled(not editing_locked and not self.closing)
        self.reauth_button.setEnabled(not editing_locked and not self.closing)
        old_id = self.selected_image()
        self.record_map = {r["id"]: r for r in state["screenshots"]}
        self.images.blockSignals(True)
        self.images.clear()
        for record in state["screenshots"]:
            label = (record.get("at") or "") + f" · {record['seconds']} sn · {record['state']}"
            if record.get("privacy_pending"):
                label += " · kişisel bilgi talebi bekliyor"
            if record.get("error"):
                label += " · gönderim bekliyor"
            item = QListWidgetItem(label)
            item.setData(Qt.ItemDataRole.UserRole, record["id"])
            self.images.addItem(item)
            if record["id"] == old_id:
                self.images.setCurrentItem(item)
        self.images.blockSignals(False)
        self.update_image_buttons()
        for ident, dialog in list(self.preview_dialogs.items()):
            if ident in self.record_map:
                dialog.update_record(self.record_map[ident])

    def selected_image(self):
        item = self.images.currentItem()
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def update_image_buttons(self, *_):
        record = self.record_map.get(self.selected_image(), {})
        self.preview_button.setEnabled(bool(record) and not self.closing)
        self.privacy_button.setEnabled(record.get("can_privacy", False) and not self.closing)
        self.ready_button.setEnabled(record.get("can_publish", False) and not self.closing)
        self.publish_button.setEnabled(record.get("can_publish", False) and not self.closing)

    def open_selected_preview(self):
        ident = self.selected_image()
        if ident:
            self.engine.send("preview", ident=ident)

    def on_preview(self, value):
        ident = value["ident"]
        if ident in self.preview_dialogs and self.preview_dialogs[ident].isVisible():
            self.preview_dialogs[ident].raise_()
            return
        try:
            dialog = PreviewDialog(self, ident, value["png"])
        except ValueError as exc:
            self.show_error(str(exc))
            return
        dialog.update_record(self.record_map.get(ident, {"state": "Bekliyor"}))
        self.preview_dialogs[ident] = dialog
        dialog.finished.connect(lambda _: self.preview_dialogs.pop(ident, None))
        dialog.show()

    def request_privacy(self, ident):
        if not ident or not self.record_map.get(ident, {}).get("can_privacy"):
            return
        reason, accepted = QInputDialog.getMultiLineText(self, "Kişisel bilgi talebi", "Hangi kişisel bilginin incelenmesini istiyorsunuz?\nTalep görüntüyü işveren kanallarından engeller; süre/ücret otomatik düşmez.")
        if accepted and reason.strip():
            self.engine.send("privacy", ident=ident, reason=reason)

    def request_publication(self, ident, operation):
        if not ident or not self.record_map.get(ident, {}).get("can_publish"):
            return
        if operation == "publish":
            text = "Görüntüyü inceledim; kişisel bilgi talebim yok ve bu görüntünün işverene şimdi açılmasını onaylıyorum."
        else:
            seconds = self.latest.get("preview_seconds")
            text = "Görüntüyü inceledim; kişisel bilgi talebim yok. "
            text += f"Sunucu bu açık seçimden sonra {seconds} saniyelik önizleme süresini başlatır." if seconds is not None else "Sunucuda önizleme süresi ayarlanmamış; otomatik yayın başlamaz."
        if QMessageBox.question(self, "Açık yayın onayı", text, QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No) == QMessageBox.StandardButton.Yes:
            self.engine.send("publication", ident=ident, operation=operation)

    def show_error(self, text):
        self.login_error.setText(text)
        self.error_label.setText(text)
        self.login_button.setEnabled(True)
        self.cached_button.setEnabled(True)

    def closeEvent(self, event):
        if self.allowed_close:
            event.accept()
            return
        event.ignore()
        if self.closing:
            return
        self.closing = True
        self.mode_label.setText("Takip kapatılıyor; son bölüm şifreli olarak korunuyor")
        self.login_button.setEnabled(False)
        self.cached_button.setEnabled(False)
        self.pages.setEnabled(False)
        for dialog in list(self.preview_dialogs.values()):
            dialog.close()
        self.engine.send("quit")

    def finish_close(self):
        self.engine.wait()
        self.allowed_close = True
        self.close()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("STEP Tracker")
    app.setOrganizationName("STEP")
    window = Window()
    window.show()
    return app.exec()
