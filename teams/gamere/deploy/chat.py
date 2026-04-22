"""
Página 2: Chatbot turístico con RAG real.
Flujo: pregunta → detect_intent() → SPARQL al KG → contexto → LLM → respuesta
"""
import streamlit as st
from openai import OpenAI
from utils.sparql_queries import load_graph
from utils.rag_engine import build_context, detect_intent
import os
import re

# ── Credenciales (Databricks tiene prioridad, si no OpenAI) ──────────────────
DATABRICKS_TOKEN = os.getenv("DATABRICKS_TOKEN", "")
OPENAI_KEY       = os.getenv("OPENAI_API_KEY", "")

if DATABRICKS_TOKEN:
    _api_key      = DATABRICKS_TOKEN
    _base_url     = "https://7474650449734546.ai-gateway.cloud.databricks.com/mlflow/v1"
    _model        = "databricks-meta-llama-3-3-70b-instruct"
else:
    _api_key      = OPENAI_KEY
    _base_url     = None
    _model        = "gpt-4o-mini"

SYSTEM_PROMPT = """
Eres un asistente turístico experto en el patrimonio natural y cultural de Galicia (España)
y el norte de Portugal. Respondes SIEMPRE en el mismo idioma del usuario (galego, castellano o inglés).

REGLAS:
1. Usa SOLO los datos del bloque [Datos do KG] para responder preguntas concretas.
2. Si el contexto tiene números, cítalos exactamente. No estimes ni redondees.
3. Si el contexto no cubre la pregunta, dilo claramente y no inventes.
4. NUNCA inventes nombres de lugares, coordenadas ni datos ausentes del contexto.
5. Sé conciso (máx 200 palabras). Usa listas cuando hay varios elementos.
6. No muestres bloques técnicos (JSON, SPARQL) al usuario.
"""


st.markdown("### Asistente de IA para consultas")
st.markdown( "Pregunta sobre praias, castelos, fervenzas, mosteiros, miradores...")
st.markdown("Este é un LLM limitado que interpreta o prompt e completa consultas predefinidas en función da intención detectada. "
    "Se a pregunta é moi xenérica ou non se pode responder cos datos dispoñibles, o modelo indicará que non ten información en lugar de inventar respostas."
)

# ── Sidebar ───────────────────────────────────────────────────────────────
with st.sidebar:
    if not DATABRICKS_TOKEN and not OPENAI_KEY:
        st.error("Non se atoparon credenciais.")
    else:
        key_to_use      = _api_key
        base_url_to_use = _base_url
        model_to_use    = _model

# ── Cliente LLM ───────────────────────────────────────────────────────────
client_kwargs = {"api_key": key_to_use}
if base_url_to_use:
    client_kwargs["base_url"] = base_url_to_use
client = OpenAI(**client_kwargs)
graph  = load_graph()

# ── Historial ─────────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

_, col_clear = st.columns([5, 1])
with col_clear:
    if st.button("Limpar", help="Limpar conversación"):
        st.session_state.messages = []
        st.rerun()

if not st.session_state.messages:
    st.markdown("""
    <div class="chat-msg-bot">
    Exemplos de preguntas:<br>
    • <i>¿Cantas praias hai en Pontevedra?</i><br>
    • <i>Mosteiros cerca de Santiago de Compostela</i><br>
    • <i>Praias con bandera azul en A Coruña</i><br>
    • <i>¿Qué hai en Portugal no KG?</i><br>
    • <i>Resúmeme o Knowledge Graph</i>
    </div>
    """, unsafe_allow_html=True)

for msg in st.session_state.messages:
    css = "chat-msg-user" if msg["role"] == "user" else "chat-msg-bot"
    st.markdown(f'<div class="{css}">{msg["content"]}</div>', unsafe_allow_html=True)

# ── Input ─────────────────────────────────────────────────────────────────
user_input = st.chat_input("Escribe a túa pregunta...")
if not user_input:
    st.stop()

st.session_state.messages.append({"role": "user", "content": user_input})

# Paso 1: intent
with st.spinner("🔍 Analizando pregunta..."):
    intent = detect_intent(client, model_to_use, user_input)

# Paso 2: SPARQL → contexto
with st.spinner("📊 Consultando o Knowledge Graph..."):
    context, query_used = build_context(graph, intent)

# Paso 3: LLM → respuesta
with st.spinner("✍️ Xerando resposta..."):
    messages_api = [{"role": "system", "content": SYSTEM_PROMPT}]
    for m in st.session_state.messages[-6:]:
        messages_api.append({"role": m["role"], "content": m["content"]})
    if context:
        messages_api[-1] = {
            "role": "user",
            "content": f"{user_input}\n\n[Datos do KG]:\n{context}",
        }
    try:
        response = client.chat.completions.create(
            model=model_to_use,
            messages=messages_api,
            temperature=0.4,
            max_tokens=500,
        )
        raw = response.choices[0].message.content
        if isinstance(raw, list):
            answer = " ".join(
                b.text if hasattr(b, "text") else b.get("text", "")
                for b in raw
                if not (isinstance(b, dict) and b.get("type") == "reasoning")
            ).strip()
        else:
            answer = re.sub(r"<think>.*?</think>", "", str(raw), flags=re.DOTALL).strip()
            answer = re.sub(r"\{'type': 'reasoning'.*?\}", "", answer, flags=re.DOTALL).strip()
    except Exception as e:
        answer = f"Erro ao contactar co modelo: {e}"

st.session_state.messages.append({"role": "assistant", "content": answer})

st.rerun()