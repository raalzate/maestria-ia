# Guía Técnica: Fine-Tuning de T5 para Corrección Gramatical en Mac

Esta guía detalla el proceso para entrenar un modelo **T5 (Text-to-Text Transfer Transformer)** especializado en la **Corrección de Errores Gramaticales (GEC)** en inglés, optimizado para hardware **Apple Silicon (M1/M2/M3)** o Intel con soporte para **Metal Performance Shaders (MPS)**.

---

## 1. Requisitos del Sistema y Entorno

Para aprovechar la GPU de tu Mac, utilizaremos el backend `mps` de PyTorch.

### Instalación de Dependencias
Ejecuta los siguientes comandos en tu terminal para configurar un entorno virtual y las librerías necesarias:

```bash
# Crear y activar entorno virtual
python3 -m venv venv_gec
source venv_gec/bin/activate

# Instalar PyTorch con soporte MPS
pip install torch torchvision torchaudio

# Instalar librerías de Hugging Face y utilidades
pip install transformers datasets evaluate sacrebleu accelerate sentencepiece
```

---

## 2. Selección y Preparación del Dataset

Para la corrección gramatical, el dataset **`dim/grammarly_coedit`** es una excelente opción moderna, ya que incluye pares de oraciones erróneas y corregidas con etiquetas de tarea específicas.

### Estructura de Datos para T5
T5 es un modelo "texto-a-texto", por lo que el entrenamiento consiste en mapear una secuencia de entrada con un prefijo a una secuencia de salida corregida:
- **Entrada:** `grammar: I has a apple.`
- **Salida:** `I have an apple.`

---

## 3. Código de Fine-Tuning (Optimizado para Mac)

El siguiente script utiliza la clase `Trainer` de Hugging Face, que detecta automáticamente el dispositivo `mps` si está disponible.

```python
import torch
from transformers import T5Tokenizer, T5ForConditionalGeneration, TrainingArguments, Trainer
from datasets import load_dataset

# 1. Configuración del Dispositivo
device = "mps" if torch.backends.mps.is_available() else "cpu"
print(f"Usando dispositivo: {device}")

# 2. Cargar Modelo y Tokenizer
model_name = "t5-small" # Recomendado para empezar en Mac
tokenizer = T5Tokenizer.from_pretrained(model_name)
model = T5ForConditionalGeneration.from_pretrained(model_name).to(device)

# 3. Cargar y Preprocesar Dataset
dataset = load_dataset("dim/grammarly_coedit", split="train[:10000]") # Subconjunto para ejemplo
dataset = dataset.train_test_split(test_size=0.1)

def preprocess_function(examples):
    inputs = ["grammar: " + doc for doc in examples["src"]]
    model_inputs = tokenizer(inputs, max_length=128, truncation=True, padding="max_length")
    
    with tokenizer.as_target_tokenizer():
        labels = tokenizer(examples["tgt"], max_length=128, truncation=True, padding="max_length")

    model_inputs["labels"] = labels["input_ids"]
    return model_inputs

tokenized_dataset = dataset.map(preprocess_function, batched=True)

# 4. Argumentos de Entrenamiento
training_args = TrainingArguments(
    output_dir="./t5-gec-mac",
    evaluation_strategy="epoch",
    learning_rate=2e-5,
    per_device_train_batch_size=8, # Ajustar según memoria unificada
    per_device_eval_batch_size=8,
    weight_decay=0.01,
    save_total_limit=3,
    num_train_epochs=3,
    predict_with_generate=True,
    fp16=False, # MPS no soporta fp16 nativo igual que CUDA, usar bf16 si es M1/M2/M3
    use_mps_device=True, # Forzar uso de GPU de Mac
)

# 5. Entrenador
trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=tokenized_dataset["train"],
    eval_dataset=tokenized_dataset["test"],
    tokenizer=tokenizer,
)

# 6. Iniciar Entrenamiento
trainer.train()
```

---

## 4. Especialización en Estructura Gramatical

Para que el modelo no solo corrija, sino que "entienda" si una oración cumple la estructura, puedes implementar una lógica de **puntuación de confianza**:

1.  **Generación de Corrección:** Pasa la oración por el modelo.
2.  **Comparación:** Si la salida es idéntica a la entrada, el modelo considera que la estructura es correcta.
3.  **Probabilidad de Logits:** Puedes extraer la probabilidad de los tokens generados para medir qué tan "seguro" está el modelo de que la estructura original era errónea.

---

## 5. Consejos para Usuarios de Mac

| Aspecto | Recomendación |
| :--- | :--- |
| **Memoria Unificada** | Si tienes 8GB de RAM, usa `t5-small`. Con 16GB o más, puedes intentar `t5-base`. |
| **Monitoreo** | Usa el **Monitor de Actividad** (pestaña GPU) para verificar que el proceso `python` esté utilizando el procesador gráfico. |
| **Bf16** | En chips Apple Silicon, usar `bf16=True` en los `TrainingArguments` puede acelerar el entrenamiento y reducir el uso de memoria sin perder mucha precisión. |
| **LoRA (Low-Rank Adaptation)** | Si quieres entrenar modelos más grandes (`t5-large`), utiliza la librería `peft` para hacer fine-tuning solo de una pequeña fracción de los parámetros. |

---

## 6. Inferencia (Uso del Modelo)

Una vez entrenado, puedes usarlo así:

```python
def correct_grammar(text, model, tokenizer):
    input_text = "grammar: " + text
    inputs = tokenizer(input_text, return_tensors="pt").to("mps")
    outputs = model.generate(**inputs, max_length=128)
    return tokenizer.decode(outputs[0], skip_special_tokens=True)

print(correct_grammar("He go to store yesterday.", model, tokenizer))
# Salida esperada: "He went to the store yesterday."
```
