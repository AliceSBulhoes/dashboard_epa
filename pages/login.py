import streamlit as st
from utils.auth import verify_credentials


def render_login_page():
    st.logo("https://grupoepa.net.br/wp-content/uploads/2025/04/e50d93c1-0cce-46d4-bb75-1985e4968e18__1_-removebg-preview.png")
    st.write("# Acesso Restrito")
    st.write("Entre com seu usuário e senha para acessar o dashboard.")

    with st.form("login_form", clear_on_submit=False, border=True):
        username = st.text_input("Usuário", key="login_username")
        password = st.text_input("Senha", type="password", key="login_password")
        submitted = st.form_submit_button("Entrar")

        if submitted:
            if verify_credentials(username, password):
                st.session_state["authenticated"] = True
                st.session_state["username"] = username
                st.success("Login realizado com sucesso. Redirecionando...")
                st.rerun()
            else:
                st.error("Credenciais inválidas. Tente novamente.")


def main():
    render_login_page()


if __name__ == "__main__":
    main()


