import streamlit as st
import re
from src.chat.rag_pipeline import build_rag_chain
from src.db.database import init_db, get_db, get_cliente_por_identificacion, create_cliente
from sqlalchemy.orm import Session
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from pathlib import Path
import logging

# Configuración de logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Inicializar base de datos
init_db()

# Cargar prompt de registro
def load_registration_prompt() -> PromptTemplate:
    prompt_file = Path("src/prompts/v1_asistente_retail.txt")
    if not prompt_file.exists():
        raise FileNotFoundError(f"Prompt no encontrado: {prompt_file}")
    template = prompt_file.read_text(encoding="utf-8")
    return PromptTemplate(
        input_variables=["input"],
        template=template + "\n\n**Input del cliente:** {input}\n**Respuesta:**"
    )

# Validaciones
def validate_identificacion_frequent(identificacion: str, db: Session) -> tuple[bool, str]:
    """Valida identificación para clientes frecuentes."""
    if not re.match(r"^\d{4,11}$", identificacion):
        return False, "La identificación debe tener entre 4 y 11 dígitos numéricos."
    if not get_cliente_por_identificacion(db, identificacion):
        return False, "No encontramos esa identificación. Verifica el número o regístrate como nuevo."
    return True, ""

def validate_identificacion_new(identificacion: str, db: Session) -> tuple[bool, str]:
    """Valida identificación para clientes nuevos."""
    if not re.match(r"^\d{4,11}$", identificacion):
        return False, "La identificación debe tener entre 4 y 11 dígitos numéricos."
    if get_cliente_por_identificacion(db, identificacion):
        return False, "Esta identificación ya está registrada. Usa otra o inicia como cliente frecuente."
    return True, ""

def validate_nombre(nombre: str) -> tuple[bool, str]:
    if not re.match(r"^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]{1,100}$", nombre):
        return False, "El nombre debe tener entre 1 y 100 letras, sin números ni caracteres especiales (excepto tildes y ñ)."
    return True, ""

def validate_telefono(telefono: str) -> tuple[bool, str]:
    if not re.match(r"^[63]\d{9}$", telefono):
        return False, "El teléfono debe tener 10 dígitos y empezar con 6 o 3."
    return True, ""

def validate_email(email: str) -> tuple[bool, str]:
    if not re.match(r"^[^@]+@[^@]+\.[^@]+$", email):
        return False, "El correo debe contener '@' y un dominio válido."
    return True, ""

# Inicializar estado de sesión
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "user_state" not in st.session_state:
    st.session_state.user_state = "initial"
if "user_data" not in st.session_state:
    st.session_state.user_data = {}
if "session_id" not in st.session_state:
    st.session_state.session_id = "user_session"
if "rag_chain" not in st.session_state:
    st.session_state.rag_chain = build_rag_chain()
if "llm" not in st.session_state:
    st.session_state.llm = ChatOpenAI(model="gpt-4o", temperature=0)
if "registration_prompt" not in st.session_state:
    st.session_state.registration_prompt = load_registration_prompt()

# Interfaz de Streamlit
st.title("Asistente Virtual del Supermercado 🛒")
st.write("¡Bienvenido! Soy tu asistente virtual. ¿En qué puedo ayudarte hoy?")

# Mostrar historial de chat
for message in st.session_state.chat_history:
    if message["role"] == "user":
        with st.chat_message("user"):
            st.write(message["content"])
    else:
        with st.chat_message("assistant"):
            st.write(message["content"])

# Input del usuario
user_input = st.chat_input("Escribe tu mensaje aquí...")

if user_input:
    st.session_state.chat_history.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    db = next(get_db())
    response = ""

    # Flujo de registro
    if st.session_state.user_state == "initial":
        if "frecuente" in user_input.lower():
            st.session_state.user_state = "frequent_id"
            response = "¡Bienvenido de nuevo! Por favor, ingresa tu número de identificación."
        elif "nuevo" in user_input.lower():
            st.session_state.user_state = "new_id"
            response = "¡Hola! Bienvenido al Supermercado 😊. Para empezar, por favor ingresa tu número de identificación (solo números, entre 4 y 11 dígitos)."
        else:
            response = "Hola, ¿eres un cliente frecuente o es tu primera vez con nosotros? Por favor, dime si eres 'frecuente' o 'nuevo'."

    elif st.session_state.user_state == "frequent_id":
        is_valid, error = validate_identificacion_frequent(user_input, db)
        if is_valid:
            cliente = get_cliente_por_identificacion(db, user_input)
            st.session_state.user_data["identificacion"] = user_input
            st.session_state.user_state = "qa"
            response = f"¡Bienvenido de nuevo, {cliente.nombre}! ¿En qué puedo ayudarte hoy?"
        else:
            response = error + " Intenta de nuevo."

    elif st.session_state.user_state == "new_id":
        is_valid, error = validate_identificacion_new(user_input, db)
        if is_valid:
            st.session_state.user_data["identificacion"] = user_input
            st.session_state.user_state = "new_name"
            response = "Gracias por tu identificación. Ahora, por favor ingresa tu nombre completo (solo letras, sin números ni caracteres especiales)."
        else:
            response = error + " Intenta de nuevo."

    elif st.session_state.user_state == "new_name":
        is_valid, error = validate_nombre(user_input)
        if is_valid:
            st.session_state.user_data["nombre"] = user_input
            st.session_state.user_state = "new_phone"
            response = "Gracias por tu nombre. Ahora, por favor ingresa tu número de teléfono (10 dígitos, empezando con 6 o 3)."
        else:
            response = error + " Intenta de nuevo."

    elif st.session_state.user_state == "new_phone":
        is_valid, error = validate_telefono(user_input)
        if is_valid:
            st.session_state.user_data["telefono"] = user_input
            st.session_state.user_state = "new_email"
            response = "Gracias por tu teléfono. Por último, por favor ingresa tu correo electrónico (debe incluir '@' y un dominio)."
        else:
            response = error + " Intenta de nuevo."

    elif st.session_state.user_state == "new_email":
        is_valid, error = validate_email(user_input)
        if is_valid:
            st.session_state.user_data["email"] = user_input
            # Registrar cliente
            create_cliente(
                db=db,
                identificacion=st.session_state.user_data["identificacion"],
                nombre=st.session_state.user_data["nombre"],
                telefono=st.session_state.user_data["telefono"],
                email=st.session_state.user_data["email"]
            )
            st.session_state.user_state = "qa"
            response = "¡Muchas gracias! 🎉 Tus datos han sido registrados con éxito. ¿En qué puedo ayudarte ahora?"
        else:
            response = error + " Intenta de nuevo."

    # Flujo de preguntas frecuentes
    elif st.session_state.user_state == "qa":
        # Usar el pipeline RAG
        try:
            out = st.session_state.rag_chain.invoke(
                {"question": user_input},
                config={"configurable": {"session_id": st.session_state.session_id}}
            )
            response = out["answer"]
        except Exception as e:
            logger.error(f"Error en RAG chain: {e}")
            response = "Lo siento, hubo un problema al procesar tu pregunta. Por favor, intenta de nuevo."

    # Mostrar respuesta
    st.session_state.chat_history.append({"role": "assistant", "content": response})
    with st.chat_message("assistant"):
        st.write(response)

    db.close()