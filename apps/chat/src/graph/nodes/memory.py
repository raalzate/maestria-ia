from typing import List, Optional, Set, Dict, Any
import logging
import json
import re
from pydantic import BaseModel, ValidationError

# Asumimos que estas importaciones existen en tu proyecto
from src.graph.state import AgentState
from src.graph.llm import Llama3Wrapper
from src.services.progress_service import ProgressService

logger = logging.getLogger(__name__)

# --- CONFIGURACIÓN Y CONSTANTES ---

INVALID_VALUES = {
    'NONE', 'N/A', 'UNKNOWN', 'NOT PROVIDED', 'NOT PROVIDED YET',
    'NO', 'EMPTY', 'NULL', 'UNDEFINED', '[]', '', 'ANONYMOUS',
    'USER', 'STUDENT', 'CLIENT', 'THE USER', 'THE STUDENT', 'UNKNOWN USER',
    'NOT MENTIONED', 'TBD',
    'EMMA', 'AI', 'TUTOR', 'TEACHER', 'ASSISTANT'
}

# --- MODELOS DE DATOS (PYDANTIC) ---
# Definimos qué esperamos recibir del LLM para facilitar la validación

class ExtractedProfile(BaseModel):
    name: Optional[str] = None
    interests: List[str] = []
    goals: List[str] = []
    vocabulary: List[str] = []
    facts: List[str] = []

# --- UTILIDADES ---

def _clean_value(value: Any) -> Optional[str]:
    """Limpia y valida un string individual."""
    if not isinstance(value, str) or not value:
        return None
    
    cleaned = value.strip().strip('"').strip("'").strip().rstrip('.')
    
    if not cleaned or cleaned.upper() in INVALID_VALUES:
        return None
    return cleaned

def _parse_llm_json(response: str) -> Dict[str, Any]:
    """Intenta extraer y parsear JSON de una respuesta de texto del LLM."""
    try:
        # Intento 1: JSON directo
        if response.strip().startswith("{"):
            return json.loads(response)
        
        # Intento 2: Buscar bloque JSON con Regex
        json_match = re.search(r"\{[\s\S]*\}", response)
        if json_match:
            return json.loads(json_match.group(0))
            
    except json.JSONDecodeError:
        logger.warning(f"Memory: JSON decoding failed. Raw response: {response[:100]}...")
    
    return {}

def _merge_unique_items(current_list: List[str], new_items: List[str]) -> List[str]:
    """
    Combina dos listas de strings ignorando duplicados (case-insensitive).
    Retorna la lista combinada (current + nuevos) solo si hubo cambios.
    """
    if not new_items:
        return current_list

    current_lower = {item.lower() for item in current_list}
    to_add = []

    for item in new_items:
        clean = _clean_value(item)
        if clean and clean.lower() not in current_lower:
            to_add.append(clean)
            current_lower.add(clean.lower()) # Evitar duplicados dentro de la misma lista nueva
    
    if to_add:
        return current_list + to_add
    return current_list # Si no hay nada nuevo, retornamos la lista original

# --- LÓGICA DEL PROMPT ---

def _build_extraction_prompt(last_message: str, current_info: Dict[str, Any]) -> str:
    interests_str = ", ".join(current_info.get('student_interests', [])) or "None"
    goals_str = ", ".join(current_info.get('student_goals', [])) or "None"
    
    return (
        "### SYSTEM ###\n"
        "You are a Data Extraction Assistant.\n"
        "CONTEXT: 'Emma' is the AI Tutor. The USER is the student.\n"
        "GOAL: Extract explicit details about the STUDENT from the conversation.\n\n"
        f"--- CURRENT INFO ---\n"
        f"NAME: {current_info.get('student_name')}\n"
        f"INTERESTS: {interests_str}\n"
        f"GOALS: {goals_str}\n"
        "--------------------\n\n"
        "### RULES ###\n"
        "1. Output ONLY valid JSON.\n"
        "2. IDENTITY RULE: NEVER extract 'Emma', 'AI', or 'Tutor' as the name.\n"
        "3. If name is unknown/unchanged, omit the field.\n"
        "4. Only extract NEW information not listed in CURRENT INFO.\n"
        "5. VOCABULARY RULE: Favor extracting full, meaningful phrases (2+ words) instead of single short words. Ensure all items have at least 3 characters.\n\n"
        "### OUTPUT FORMAT (JSON) ###\n"
        '{"name": "...", "interests": ["..."], "goals": ["..."], "vocabulary": ["..."], "facts": ["..."]}\n\n'
        "### USER INPUT ###\n"
        f"\"{last_message}\""
    )

# --- NODO PRINCIPAL ---

def memory_node(state: AgentState):
    """
    Nodo de Memoria: Analiza el último mensaje, extrae metadatos y actualiza el progreso.
    """
    logger.debug("--- Memory Node Start ---")
    
    # 1. Validación de estado inicial
    current_mode = state.get('current_mode', 'chat')
    messages = state.get('messages', [])
    last_message = messages[-1].content
    
    # 2. Inicialización de Servicios
    try:
        llm = Llama3Wrapper()
        ps = ProgressService()

        data_info = ps.load_progress()
        
        current_context = {
            'student_name': data_info.get('student_name', ''),
            'student_interests': data_info.get('student_interests') or [],
            'student_goals': data_info.get('student_goals') or [],
            'user_memory': data_info.get('user_memory') or []
        }

        if current_mode != 'chat':
            return current_context

        # 3. Llamada al LLM y Parsing
        prompt = _build_extraction_prompt(last_message, current_context)
        llm_response = llm.invoke(prompt)
        raw_data = _parse_llm_json(str(llm_response))
        
        if not raw_data:
            return {}

        # Validar estructura con Pydantic (ignora campos extraños automáticamente)
        try:
            extracted = ExtractedProfile(**raw_data)
        except ValidationError as e:
            logger.warning(f"Memory: Validation error in LLM response: {e}")
            return {}

        # 4. Cálculo de diferencias (Updates)
        updates = {}
        has_changes = False

        # A. Nombre
        new_name = _clean_value(extracted.name)
        if new_name and new_name != current_context['student_name']:
            updates['student_name'] = new_name
            has_changes = True
            logger.info(f"Memory: Name updated to {new_name}")

        # B. Intereses y Metas (Usando la función helper DRY)
        new_interests = _merge_unique_items(current_context['student_interests'], extracted.interests)
        if len(new_interests) > len(current_context['student_interests']):
            updates['student_interests'] = new_interests
            has_changes = True
            logger.info(f"Memory: Interests updated")

        new_goals = _merge_unique_items(current_context['student_goals'], extracted.goals)
        if len(new_goals) > len(current_context['student_goals']):
            updates['student_goals'] = new_goals
            has_changes = True
            logger.info(f"Memory: Goals updated")

        # C. Memoria episódica (Facts / Vocab)
        new_memory_items = []
        for cat_list, label in [(extracted.vocabulary, 'Vocabulary'), (extracted.facts, 'Facts')]:
            for item in cat_list:
                clean = _clean_value(item)
                if clean:
                    # Aplicar filtro de longitud mínima de 3 caracteres para Vocabulario
                    if label == 'Vocabulary' and len(clean) < 3:
                        logger.debug(f"Memory: Skipping short vocabulary item: '{clean}'")
                        continue
                    new_memory_items.append(f"{label}: {clean}")
        
        if new_memory_items:
            # Merge verifying uniqueness
            full_memory = _merge_unique_items(current_context['user_memory'], new_memory_items)
            
            if len(full_memory) > len(current_context['user_memory']):
                updates['user_memory'] = full_memory
                has_changes = True
                added_count = len(full_memory) - len(current_context['user_memory'])
                logger.info(f"Memory: Added {added_count} unique items to memory stream")

        # 5. Persistencia
        if has_changes:
            try:
                # Actualizamos el objeto en memoria del servicio
                ps.current_progress.update(updates)
                ps.save_progress()
                logger.info("Memory: Changes persisted to disk.")
            except Exception as e:
                logger.error(f"Memory: Failed to save progress: {e}")
                # Aún así retornamos updates para que el state del grafo se actualice en esta ejecución
        
        return updates

    except Exception as e:
        logger.error(f"Critical error in memory_node: {e}", exc_info=True)
        return {}