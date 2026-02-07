#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Dashboard ERP Protheus 2.0 - Autenticação
Autor: Fernando Vernier - https://www.linkedin.com/in/fernando-v-10758522/
"""

from flask import g, request, Response
from functools import wraps
from config import UsersConfig
import hashlib
import secrets


class Auth:
    """Classe para gerenciamento de autenticação"""
    
    @staticmethod
    def verificar_credenciais(usuario, senha):
        """Verifica se as credenciais são válidas"""
        usuarios = UsersConfig.get_users()
        
        if usuario not in usuarios:
            return False
        
        # Verifica senha
        senha_esperada = usuarios[usuario]["senha"]
        return senha == senha_esperada
    
    @staticmethod
    def obter_dados_usuario(usuario):
        """Retorna dados completos do usuário"""
        usuarios = UsersConfig.get_users()
        if usuario in usuarios:
            return usuarios[usuario]
        return None
    
    @staticmethod
    def obter_permissoes(tipo_permissao):
        """Retorna permissões de um tipo de usuário"""
        permissoes = UsersConfig.get_permissions()
        return permissoes.get(tipo_permissao, {})
    
    @staticmethod
    def usuario_pode(permissao):
        """Verifica se o usuário atual tem uma permissão específica"""
        if not hasattr(g, 'permissoes'):
            return False
        return g.permissoes.get(permissao, False)


def autenticar():
    """Solicita autenticação básica"""
    return Response(
        'Autenticação necessária.\n'
        'Por favor, forneça suas credenciais para acessar o Dashboard ERP Protheus.\n',
        401,
        {'WWW-Authenticate': 'Basic realm="Dashboard ERP Protheus 2.0"'}
    )


def requer_autenticacao(f):
    """Decorator para exigir autenticação"""
    @wraps(f)
    def decorated(*args, **kwargs):
        auth = request.authorization
        
        if not auth:
            return autenticar()
        
        if not Auth.verificar_credenciais(auth.username, auth.password):
            return autenticar()
        
        # Armazena dados do usuário no contexto
        dados_usuario = Auth.obter_dados_usuario(auth.username)
        g.usuario = auth.username
        g.nome_completo = dados_usuario.get('nome_completo', auth.username)
        g.email = dados_usuario.get('email', '')
        g.tipo_permissao = dados_usuario.get('permissoes', 'visualizacao')
        g.permissoes = Auth.obter_permissoes(g.tipo_permissao)
        
        return f(*args, **kwargs)
    
    return decorated


def requer_permissao(permissao):
    """Decorator para exigir uma permissão específica"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not Auth.usuario_pode(permissao):
                return Response(
                    f'Acesso negado. Você não tem permissão para: {permissao}\n',
                    403
                )
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def gerar_token_sessao():
    """Gera um token único para sessão"""
    return secrets.token_urlsafe(32)


def hash_senha(senha):
    """Gera hash SHA256 de uma senha"""
    return hashlib.sha256(senha.encode()).hexdigest()
