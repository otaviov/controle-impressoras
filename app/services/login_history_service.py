from datetime import datetime

from app.models import LoginHistory


class LoginHistoryService:
    def __init__(self, session):
        self.session = session

    def registrar_login(self, user_id, ip_address=""):
        sessao = LoginHistory(user_id=user_id, ip_address=ip_address)
        self.session.add(sessao)
        self.session.commit()
        return sessao

    def registrar_logout(self, user_id):
        sessao = self.session.query(LoginHistory).filter(
            LoginHistory.user_id == user_id,
            LoginHistory.logout_at.is_(None)
        ).order_by(LoginHistory.login_at.desc()).first()
        if sessao:
            sessao.logout_at = datetime.utcnow()
            self.session.commit()
        return sessao

    def listar_por_usuario(self, user_id, limite=50):
        return self.session.query(LoginHistory).filter(
            LoginHistory.user_id == user_id
        ).order_by(LoginHistory.login_at.desc()).limit(limite).all()

    def listar_todos(self, limite=100):
        return self.session.query(LoginHistory).order_by(
            LoginHistory.login_at.desc()
        ).limit(limite).all()

    def ultimo_login(self, user_id):
        return self.session.query(LoginHistory).filter(
            LoginHistory.user_id == user_id
        ).order_by(LoginHistory.login_at.desc()).first()

    def tempo_medio_sessao(self, user_id):
        from sqlalchemy import func
        result = self.session.query(
            func.avg(LoginHistory.logout_at - LoginHistory.login_at)
        ).filter(
            LoginHistory.user_id == user_id,
            LoginHistory.logout_at.isnot(None)
        ).scalar()
        return result
