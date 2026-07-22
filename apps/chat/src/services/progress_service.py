import json
import os
from src.config import CURRICULUM

class ProgressService:
    def __init__(self, user_id="default_user"):
        self.user_id = user_id
        self.file_path = f"data/user_progress/user_progress_{user_id}.json"
        self.curriculum = CURRICULUM
        self.levels = list(self.curriculum.keys())
        self.current_progress = self.load_progress()

    def _get_topic_name(self, topic_item):
        if isinstance(topic_item, dict):
            return topic_item.get("topic", "")
        return str(topic_item)

    def load_progress(self):
        # 1. Intentar cargar el archivo si existe
        if os.path.exists(self.file_path):
            try:
                with open(self.file_path, 'r') as f:
                    data = json.load(f)
                    
                    # VALIDATION: Check if progress matches current curriculum
                    c_level = data.get("current_level")
                    c_topic = data.get("current_topic")
                    
                    if c_level in self.curriculum:
                        level_topics = self.curriculum[c_level]
                        # Check if topic exists in this level (comparing names)
                        topic_names = [self._get_topic_name(t) for t in level_topics]
                        
                        if c_topic in topic_names or c_topic == "CURRICULUM_COMPLETED":
                            return data
                            
                    print(f"⚠️ Progress mismatch or stale data for {self.user_id}. Resetting to default.")
            except json.JSONDecodeError:
                pass
        
        # 2. Definir datos por defecto
        first_level = self.levels[0]
        first_topic_item = self.curriculum[first_level][0]
        default_data = {
            "current_level": first_level,
            "current_topic": self._get_topic_name(first_topic_item),
            "completed_topics": []
        }

        # 3. CREAR LA CARPETA Y EL ARCHIVO
        try:
            # Extrae la ruta de la carpeta (ej: 'memory') de 'memory/archivo.json'
            directory = os.path.dirname(self.file_path)
            
            # Si la ruta tiene carpetas, las crea (exist_ok=True evita error si ya existen)
            if directory:
                os.makedirs(directory, exist_ok=True)

            # Ahora es seguro crear el archivo
            with open(self.file_path, 'w') as f:
                json.dump(default_data, f, indent=4)
                
        except OSError as e:
            print(f"Error crítico al guardar progreso: {e}")

        return default_data

    def save_progress(self):
        with open(self.file_path, 'w') as f:
            json.dump(self.current_progress, f, indent=4)

    def get_current_state(self):
        progress_info = self.current_progress.copy()
        progress_info['level_progress'] = self.get_level_progress()
        progress_info['total_progress'] = self.get_total_progress()
        return progress_info
    
    def get_level_progress(self):
        """Calculate progress percentage for the current level."""
        current_level = self.current_progress["current_level"]
        completed_topics = self.current_progress["completed_topics"]
        
        # Get all topics for current level
        level_topics = self.curriculum.get(current_level, [])
        if not level_topics:
            return {"percentage": 0, "completed": 0, "total": 0}
        
        # Count completed topics in this level
        level_topic_names = [self._get_topic_name(t) for t in level_topics]
        completed_in_level = sum(1 for topic in completed_topics if topic in level_topic_names)
        total_in_level = len(level_topics)
        percentage = int((completed_in_level / total_in_level) * 100) if total_in_level > 0 else 0
        
        return {
            "percentage": percentage,
            "completed": completed_in_level,
            "total": total_in_level
        }
    
    def get_total_progress(self):
        """Calculate overall curriculum progress."""
        completed_topics = self.current_progress["completed_topics"]
        total_topics = sum(len(topics) for topics in self.curriculum.values())
        
        if total_topics == 0:
            return {"percentage": 0, "completed": 0, "total": 0}
        
        percentage = int((len(completed_topics) / total_topics) * 100)
        
        return {
            "percentage": percentage,
            "completed": len(completed_topics),
            "total": total_topics
        }

    def complete_current_topic(self):
        current_level = self.current_progress["current_level"]
        current_topic = self.current_progress["current_topic"]
        
        if current_topic not in self.current_progress["completed_topics"]:
            self.current_progress["completed_topics"].append(current_topic)
        
        # Determine next topic
        level_topics = self.curriculum[current_level]
        level_topic_names = [self._get_topic_name(t) for t in level_topics]
        
        try:
            current_index = level_topic_names.index(current_topic)
            if current_index + 1 < len(level_topics):
                # Next topic in same level
                next_topic_item = level_topics[current_index + 1]
                self.current_progress["current_topic"] = self._get_topic_name(next_topic_item)
            else:
                # Move to next level
                current_level_index = self.levels.index(current_level)
                if current_level_index + 1 < len(self.levels):
                    next_level = self.levels[current_level_index + 1]
                    self.current_progress["current_level"] = next_level
                    next_level_first_item = self.curriculum[next_level][0]
                    self.current_progress["current_topic"] = self._get_topic_name(next_level_first_item)
                else:
                    # Curriculum completed
                    self.current_progress["current_topic"] = "CURRICULUM_COMPLETED"
        except ValueError:
            # Fallback if topic not found (shouldn't happen)
            pass
            
        self.save_progress()
        return self.current_progress

    def add_saved_phrase(self, text: str):
        """Adds a phrase to the saved list if it doesn't exist."""
        if "saved_phrases" not in self.current_progress:
            self.current_progress["saved_phrases"] = []
        
        text = text.strip()
        if text and text not in self.current_progress["saved_phrases"]:
            self.current_progress["saved_phrases"].append(text)
            self.save_progress()
            return True
        return False
        
    def get_saved_phrases(self):
        """Returns the list of saved phrases."""
        return self.current_progress.get("saved_phrases", [])

    def reset_progress(self):
        """Resets the progress to default and deletes the file."""
        if os.path.exists(self.file_path):
            os.remove(self.file_path)
        self.current_progress = self.load_progress()
        return self.current_progress
