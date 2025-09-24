import ast
import asyncio
import json
import uuid
import httpx
import streamlit as st
from typing import Optional

st.set_page_config(
    page_title="Esmé - Asistente ENAHO/GEIH",
    page_icon="🤖",
    layout="wide"
)

if "messages" not in st.session_state:
    st.session_state.messages = []

if "thread_id" not in st.session_state:
    st.session_state.thread_id = f"esma-chat-{str(uuid.uuid4())}"

if "is_processing" not in st.session_state:
    st.session_state.is_processing = False

if "debug_mode" not in st.session_state:
    st.session_state.debug_mode = False

BASE_URL = "https://esma-agent-514700908055.us-east1.run.app"
CONNECTION_TIMEOUT = 300.0

with st.sidebar:

    st.title("Esmé 🤖")
    st.markdown(
        "<h5><i>Tu asistente virtual para la ENAHO y la GEIH</i></h5>", 
        unsafe_allow_html=True
    )
    st.caption("Powered by ESMA SQL Agent")
    
    st.divider()
    st.markdown(
        """
        <h5>📋 Instrucciones</h5>
        <p style="font-size: 14px;">Pregunta sobre las bases de datos ENAHO (Perú) o GEIH (Colombia)</p>
        <p style="font-size: 14px;">Puedes solicitar análisis, estadísticas y consultas SQL</p>
        <p style="font-size: 14px;">Esmé puede cometer errores. Intenta ser preciso y claro en tus preguntas.</p>
        """,
        unsafe_allow_html=True
    )
    
    if st.button("🔄 Nueva Conversación", use_container_width=True):
        st.session_state.messages = []
        st.session_state.thread_id = f"esma-chat-{str(uuid.uuid4())}"
        st.rerun()
    
    st.divider()
    con1, con2 = st.columns(2)
    with con1:
        st.markdown("<h5>Estado de Conexión:</h5>", unsafe_allow_html=True)
    with con2:
        if st.session_state.is_processing:
            st.info("🔄 Procesando...")
        else:
            st.success("✅ Listo")

    id1, id2 = st.columns(2)
    with id1:
        st.markdown("<h5>ID de conversación:</h5>", unsafe_allow_html=True)
    with id2:
        st.code(st.session_state.thread_id[-8:], language=None)

    # st.divider()
    # st.session_state.debug_mode = st.checkbox("🐛 Modo Debug", value=st.session_state.debug_mode)


for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])


def parse_sse_content(content_str: str, debug: bool = False) -> Optional[str]:
    """
    Parse SSE content handling repr() format from the API with mixed quotes
    """
    if debug:
        st.sidebar.code(f"Raw SSE: {content_str[:100]}", language=None)
    
    try:
        # The API sends malformed JSON with mixed quotes: {"type": "content", "content": 'actual content'}
        # We need to fix this to be valid JSON
        
        # Method 1: Try to fix mixed quotes
        if '"content": \'' in content_str or '"content":\'' in content_str:
            # Handle both with and without space after colon
            if '"content": \'' in content_str:
                start_marker = '"content": \''
            else:
                start_marker = '"content":\''
            
            start_idx = content_str.index(start_marker) + len(start_marker)
            
            # The content might be incomplete (truncated) or complete
            # Look for the ending pattern '} or just take everything if incomplete
            if content_str.endswith('\'}'):
                end_idx = len(content_str) - 2  # Before '}
            elif '\'}\n' in content_str:
                end_idx = content_str.index('\'}\n')
            elif '\'}' in content_str:
                end_idx = content_str.index('\'}')
            else:
                # Content is truncated, take everything after the marker
                end_idx = len(content_str)
            
            # Extract the actual content
            actual_content = content_str[start_idx:end_idx]
            
            # Unescape characters from repr()
            actual_content = actual_content.replace("\\n", "\n")
            actual_content = actual_content.replace("\\t", "\t")
            actual_content = actual_content.replace("\\'", "'")
            actual_content = actual_content.replace("\\\\", "\\")
            
            if debug:
                st.sidebar.success(f"Extracted: {actual_content[:50]}...")
            
            return actual_content if actual_content else None
        
        # Method 2: Try standard JSON parsing (in case the API is fixed)
        try:
            content_data = json.loads(content_str)
            chunk = content_data.get("content", "")
            
            if debug:
                st.sidebar.info("Standard JSON parsing succeeded")
            
            return chunk if chunk else None
        except json.JSONDecodeError:
            pass
        
        # Method 3: Try to extract any text between quotes
        import re
        # Look for content between any quotes after "content":
        pattern = r'"content":\s*["\']([^"\']*)["\']'
        match = re.search(pattern, content_str)
        if match:
            content = match.group(1)
            # Unescape
            content = content.replace("\\n", "\n")
            content = content.replace("\\t", "\t")
            content = content.replace("\\'", "'")
            content = content.replace("\\\\", "\\")
            
            if debug:
                st.sidebar.info(f"Regex extraction: {content[:50]}...")
            
            return content
        
        if debug:
            st.sidebar.warning("No parsing method succeeded")
        
        return None
        
    except Exception as e:
        if debug:
            st.sidebar.error(f"Parse error: {e}")
        return None


async def get_api_response_streaming(message: str, thread_id: str, placeholder, debug_mode: bool = False):
    """
    Get streaming response from API and display it in real-time
    """
    url = f"{BASE_URL}/chat/stream"
    payload = {
        "message": message,
        "thread_id": thread_id
    }
    
    full_response = ""
    
    try:
        async with httpx.AsyncClient(timeout=CONNECTION_TIMEOUT) as client:
            try:
                async with client.stream("POST", url, json=payload) as response:
                    if response.status_code != 200:
                        error_msg = f"❌ Error: El servidor respondió con código {response.status_code}"
                        placeholder.error(error_msg)
                        return error_msg
                    
                    line_count = 0
                    chunk_count = 0
                    all_lines = []  # Store all lines for debugging
                    
                    # Process streaming response
                    async for line in response.aiter_lines():
                        line_count += 1
                        all_lines.append(line)
                        
                        if debug_mode:
                            # Show ALL lines, not just first 5
                            if line_count <= 10:
                                # Show the line with special character visualization
                                display_line = repr(line) if line else "[EMPTY LINE]"
                                st.sidebar.text(f"Line {line_count}: {display_line[:100]}")
                        
                        # Try different SSE formats
                        # Standard SSE format: "data: ..."
                        if line.startswith("data: "):
                            content_str = line[len("data: "):].strip()
                            
                            if debug_mode and line_count <= 3:
                                st.sidebar.code(f"Data content: {content_str[:100]}", language=None)
                            
                            # Skip empty data or special SSE signals
                            if not content_str or content_str == "[DONE]":
                                continue
                            
                            chunk = parse_sse_content(content_str, debug=debug_mode and chunk_count < 3)
                            
                            if chunk:
                                chunk_count += 1
                                full_response += chunk
                                # Update the placeholder with accumulated response
                                placeholder.markdown(full_response + "▌")
                        
                        # Also try parsing lines directly as JSON (some APIs don't use SSE format)
                        elif line.strip() and not line.startswith(":"):  # Skip comments and empty lines
                            try:
                                # Try to parse the line directly as JSON
                                data = json.loads(line)
                                if isinstance(data, dict):
                                    # Look for content in various possible fields
                                    content = data.get("content") or data.get("text") or data.get("message") or data.get("response")
                                    if content:
                                        chunk_count += 1
                                        full_response += str(content)
                                        placeholder.markdown(full_response + "▌")
                                        
                                        if debug_mode:
                                            st.sidebar.success(f"Found content in JSON: {content[:50]}")
                            except json.JSONDecodeError:
                                # Not JSON, might be plain text
                                if line.strip() and len(line.strip()) > 1:
                                    if debug_mode:
                                        st.sidebar.warning(f"Non-JSON line: {line[:50]}")
                                    # You could potentially add plain text handling here
                                    pass
                    
                    if debug_mode:
                        st.sidebar.info(f"Total lines: {line_count}, Chunks: {chunk_count}")
                        if line_count > 0 and chunk_count == 0:
                            st.sidebar.error("⚠️ Lines received but no chunks processed!")
                            st.sidebar.text("First few lines received:")
                            for i, line in enumerate(all_lines[:5]):
                                st.sidebar.code(f"{i+1}: {repr(line[:200])}", language=None)
                    
                    # Remove cursor and show final response
                    if full_response:
                        placeholder.markdown(full_response)
                    else:
                        error_msg = "⚠️ No se recibió respuesta del servidor"
                        if debug_mode:
                            error_msg += f"\n\nDebug: {line_count} líneas recibidas, {chunk_count} chunks procesados"
                        placeholder.warning(error_msg)
                        return error_msg
                        
            except httpx.TimeoutException:
                error_msg = "⏱️ Tiempo de espera agotado. Por favor, intenta de nuevo."
                placeholder.error(error_msg)
                return error_msg
                
            except httpx.ConnectError:
                error_msg = "🔌 No se pudo conectar con el servidor. Verifica tu conexión a internet."
                placeholder.error(error_msg)
                return error_msg
                
    except Exception as e:
        error_msg = f"❌ Error inesperado: {str(e)}"
        if debug_mode:
            error_msg += f"\n\nDetalles: {type(e).__name__}"
        placeholder.error(error_msg)
        return error_msg
    
    return full_response


if question := st.chat_input(
    "Pregúntame sobre la ENAHO o la GEIH...", 
    disabled=st.session_state.is_processing
):
    with st.chat_message("user"):
        st.markdown(question)
    
    st.session_state.messages.append(
        {"role": "user", "content": question}
    )
    
    with st.chat_message("assistant"):
        response_placeholder = st.empty()        
        st.session_state.is_processing = True
        
        response = asyncio.run(
            get_api_response_streaming(
                question, 
                st.session_state.thread_id,
                response_placeholder,
                st.session_state.debug_mode
            )
        )
        
        st.session_state.is_processing = False
    
    st.session_state.messages.append(
        {"role": "assistant", "content": response}
    )
    
    if not st.session_state.debug_mode:
        st.rerun()

