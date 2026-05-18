class AuthController:
    def __init__(self, user_service):
        self.user_service = user_service

    def autenticar(self, username, senha):
        return self.user_service.autenticar(username, senha)

    def listar_usuarios(self):
        return self.user_service.listar_todos()
