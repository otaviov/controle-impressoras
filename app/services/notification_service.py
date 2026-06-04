from __future__ import annotations

import json
import logging
import smtplib
import ssl
from dataclasses import dataclass, field
from datetime import datetime
from email.mime.text import MIMEText
from pathlib import Path
from threading import Thread
from typing import Any

log = logging.getLogger(__name__)

NOTIFICACAO_CONFIG_PATH = Path(__file__).resolve().parent.parent.parent / "notification_config.json"


@dataclass
class NotificacaoConfig:
    desktop_ativado: bool = True
    email_ativado: bool = False
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_usuario: str = ""
    smtp_senha: str = ""
    email_remetente: str = ""
    email_destinatario: str = ""

    @classmethod
    def carregar(cls) -> "NotificacaoConfig":
        if NOTIFICACAO_CONFIG_PATH.exists():
            try:
                dados = json.loads(NOTIFICACAO_CONFIG_PATH.read_text("utf-8"))
                return cls(**dados)
            except Exception as e:
                log.warning("Erro ao carregar config de notificação: %s", e)
        return cls()

    def salvar(self) -> None:
        dados = {
            "desktop_ativado": self.desktop_ativado,
            "email_ativado": self.email_ativado,
            "smtp_host": self.smtp_host,
            "smtp_port": self.smtp_port,
            "smtp_usuario": self.smtp_usuario,
            "smtp_senha": self.smtp_senha,
            "email_remetente": self.email_remetente,
            "email_destinatario": self.email_destinatario,
        }
        NOTIFICACAO_CONFIG_PATH.write_text(json.dumps(dados, indent=2, ensure_ascii=False), "utf-8")

    def testar_email(self) -> tuple[bool, str]:
        if not all([self.smtp_host, self.smtp_usuario, self.smtp_senha, self.email_remetente, self.email_destinatario]):
            return False, "Preencha todos os campos de e-mail."
        try:
            contexto = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.ehlo()
                server.starttls(context=contexto)
                server.ehlo()
                server.login(self.smtp_usuario, self.smtp_senha)
                msg = MIMEText("Teste de notificação do Controle de Impressoras.\n\nSe voc\u00ea recebeu esta mensagem, a configuração de e-mail está funcionando.")
                msg["Subject"] = "Teste de Notificação - Controle de Impressoras"
                msg["From"] = self.email_remetente
                msg["To"] = self.email_destinatario
                server.sendmail(self.email_remetente, [self.email_destinatario], msg.as_string())
            return True, "E-mail de teste enviado com sucesso!"
        except smtplib.SMTPAuthenticationError:
            return False, "Falha de autenticação SMTP. Verifique usuário/senha."
        except smtplib.SMTPException as e:
            return False, f"Erro SMTP: {e}"
        except Exception as e:
            return False, f"Erro: {e}"


class NotificadorService:
    def __init__(self, tray_icon: Any = None) -> None:
        self._config: NotificacaoConfig = NotificacaoConfig.carregar()
        self._tray_icon: Any = tray_icon

    @property
    def config(self) -> NotificacaoConfig:
        return self._config

    def recarregar_config(self) -> None:
        self._config = NotificacaoConfig.carregar()

    def salvar_config(self) -> None:
        self._config.salvar()

    def notificar_alerta(self, alerta: Any) -> None:
        if not alerta:
            return

        if self._config.desktop_ativado:
            self._notificar_desktop(alerta)

        if self._config.email_ativado:
            Thread(target=self._notificar_email, args=(alerta,), daemon=True).start()

    def _notificar_desktop(self, alerta: Any) -> None:
        if not self._tray_icon or not self._tray_icon.isVisible():
            return
        try:
            titulo = f"\u26a0 Alerta: {alerta.titulo or 'Sem título'}"
            if hasattr(alerta, "printer") and alerta.printer:
                msg = f"Impressora: {alerta.printer.patrimonio} - {alerta.printer.modelo}"
            else:
                msg = alerta.descricao or ""
            self._tray_icon.showMessage(titulo, msg, msecs=8000)
        except Exception as e:
            log.warning("Erro ao notificar desktop: %s", e)

    def _notificar_email(self, alerta: Any) -> None:
        cfg = self._config
        if not all([cfg.smtp_host, cfg.smtp_usuario, cfg.smtp_senha, cfg.email_remetente, cfg.email_destinatario]):
            return
        try:
            printer_info = ""
            if hasattr(alerta, "printer") and alerta.printer:
                printer_info = f"Impressora: {alerta.printer.patrimonio} - {alerta.printer.modelo} ({alerta.printer.marca})"
            corpo = f"""
Alerta Crítico - Controle de Impressoras

Título: {alerta.titulo}
Tipo: {alerta.tipo}
Descrição: {alerta.descricao or "N/A"}
Data: {alerta.data_alerta or datetime.now()}
{printer_info}

Este é um alerta automático do sistema Controle de Impressoras Pro.
"""
            msg = MIMEText(corpo.strip())
            msg["Subject"] = f"\u26a0 Alerta: {alerta.titulo}"
            msg["From"] = cfg.email_remetente
            msg["To"] = cfg.email_destinatario

            contexto = ssl.create_default_context()
            with smtplib.SMTP(cfg.smtp_host, cfg.smtp_port) as server:
                server.ehlo()
                server.starttls(context=contexto)
                server.ehlo()
                server.login(cfg.smtp_usuario, cfg.smtp_senha)
                server.sendmail(cfg.email_remetente, [cfg.email_destinatario], msg.as_string())
            log.info("E-mail de notificação enviado para %s", cfg.email_destinatario)
        except Exception as e:
            log.warning("Erro ao enviar e-mail de notificação: %s", e)
