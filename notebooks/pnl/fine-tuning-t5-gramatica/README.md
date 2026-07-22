# PoC — Fine-Tuning de T5 para Corrección Gramatical (GEC) en Apple Silicon

PoC didáctica en notebooks que implementa el fine-tuning de **T5** sobre el dataset **`grammarly/coedit`** para la tarea de **Grammatical Error Correction (GEC)** en inglés, optimizado para **Apple Silicon (MPS)**.

Basado en `Guía Técnica_ Fine-Tuning de T5 para Corrección Gramatical en Mac.md`.

---

## Estructura

```
fine-tunning/
├── Guía Técnica_ ...md       # guía fuente
├── README.md                 # este archivo (índice + cómo correr)
├── requirements.txt          # dependencias pinneadas mínimas
├── docs/
│   ├── decisiones_tecnicas.md   # ADRs: por qué T5, MPS, Seq2SeqTrainer, bf16, LoRA
│   └── arquitectura.md          # diagrama de pipeline + flujo de datos
└── notebooks/
    ├── 01_teoria_t5_gec.ipynb           # Marco teórico (T5, GEC, transfer learning)
    ├── 02_setup_entorno_mac.ipynb       # Verificación MPS + instalación
    ├── 03_dataset_eda.ipynb             # Carga + EDA del coedit
    ├── 04_preprocesamiento.ipynb        # Tokenización + DataCollator
    ├── 05_finetuning.ipynb              # Entrenamiento con Seq2SeqTrainer
    ├── 06_evaluacion.ipynb              # SacreBLEU + GLEU + exact-match
    ├── 07_inferencia_confianza.ipynb    # Generación + score de confianza por logits
    └── 08_lora_peft.ipynb               # PEFT/LoRA para t5-base/large
```

---

## Orden de ejecución sugerido

1. **01** — leer teoría antes de tocar código.
2. **02** — verificar `torch.backends.mps.is_available() == True`. Si no, abortar o caer a CPU.
3. **03 → 04** — explorar dataset y construir tokenized splits.
4. **05** — fine-tuning real (entrena `t5-small` en subset de 10k para PoC).
5. **06** — métricas cuantitativas + ejemplos cualitativos.
6. **07** — inferencia con score de confianza derivado de logits.
7. **08** — opcional, ruta avanzada con LoRA para `t5-base`.

Cada notebook es **independiente**: encabezado de teoría + código ejecutable + observaciones. Pueden correrse de forma aislada si los artefactos de checkpoints existen.

---

## Cómo correr

```bash
cd /Users/raul.alzate/Documents/maestria/maestria/pnl/fine-tunning

python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

python -m ipykernel install --user --name venv-gec --display-name "Python (venv-gec)"
jupyter lab
```

Selecciona el kernel **Python (venv-gec)** en cada notebook.

---

## Entregables de la PoC

- Notebook 05 deja artefactos en `./artifacts/t5-gec-mac/` (checkpoints + tokenizer).
- Notebook 06 emite `./artifacts/eval_metrics.json` con SacreBLEU, GLEU y exact-match.
- Notebook 07 emite ejemplos `./artifacts/inference_samples.json` con confianza.

---

## Correcciones a la guía original

La guía técnica fuente contiene tres detalles que la PoC corrige (documentados en `docs/decisiones_tecnicas.md`):

| Guía dice | PoC usa | Razón |
|---|---|---|
| `Trainer` + `predict_with_generate=True` | `Seq2SeqTrainer` + `Seq2SeqTrainingArguments` | `predict_with_generate` solo existe en la versión Seq2Seq |
| `use_mps_device=True` | omitido (auto-detectado) | deprecado desde `transformers>=4.34` |
| `evaluation_strategy` | `eval_strategy` | renombrado en `transformers>=4.41` |

---

## Audiencia

PoC para maestría en PNL. Asume familiaridad con Python, PyTorch básico y conceptos de NLP (tokens, attention). Toda decisión arquitectónica está justificada en el cuerpo de los notebooks.
