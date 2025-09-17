import streamlit as st

# Credenciais pré-definidas
PREDEFINED_CREDENTIALS = {
    "username": "admin",
    "password": "admin123",
}


def verify_credentials(username: str, password: str) -> bool:
    return (
        username == PREDEFINED_CREDENTIALS["username"]
        and password == PREDEFINED_CREDENTIALS["password"]
    )


def require_authentication() -> bool:
    """Retorna True se autenticado, caso contrário False."""
    return bool(st.session_state.get("authenticated", False))


