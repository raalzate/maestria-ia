# Decisiones Técnicas (ADRs)

Este documento registra las decisiones tomadas para la PoC, sus alternativas y trade-offs. Cada ADR es independiente.

---

## ADR-01: Modelo base — `t5-small`

**Contexto.** GEC es una tarea seq2seq donde la entrada (oración con error) y la salida (oración corregida) son strings. Necesitamos un modelo encoder-decoder pre-entrenado en un objetivo compatible.

**Decisión.** Usar `t5-small` (60M params) como modelo base.

**Alternativas evaluadas.**

| Modelo | Params | Pros | Contras |
|---|---|---|---|
| `t5-small` | 60M | Cabe en 8 GB RAM unificada, tiempos de fine-tuning < 1h en M1 | Capacidad limitada |
| `t5-base` | 220M | Mejor calidad, sigue corriendo en MPS | Requiere ≥16 GB y bf16 |
| `t5-large` | 770M | Calidad SOTA en GEC | Requiere LoRA en MPS |
| `flan-t5-base` | 250M | Pre-entrenado con instrucciones | Estilo de prompt distinto, mayor footprint |
| `bart-base` | 140M | Encoder-decoder fuerte para denoising | Tokenizer no incluye prefijos de tarea T5 |

**Por qué T5 sobre BART/decoder-only.** T5 fue pre-entrenado con span-corruption — el modelo aprende a regenerar texto enmascarado. GEC es funcionalmente "regenerar la versión sin errores" → fit natural. Los modelos decoder-only (LLaMA, GPT) requieren prompt engineering extenso y son más caros.

**Consecuencia.** El notebook 08 muestra cómo escalar a `t5-base` con LoRA si se requiere mejor calidad sin costo en VRAM.

---

## ADR-02: Dataset — `grammarly/coedit`

**Contexto.** Necesitamos pares (src, tgt) etiquetados para GEC en inglés.

**Decisión.** Usar `grammarly/coedit` desde Hugging Face Hub.

**Alternativas.**

- **JFLEG** — pequeño (~1500 ejemplos), bueno para evaluación, insuficiente para fine-tuning.
- **W&I+LOCNESS (BEA-2019)** — gold standard, requiere descarga manual + licencia.
- **C4_200M synthetic** — masivo pero ruidoso, requiere filtrado pesado.
- **CoEdIT (`grammarly/coedit`)** — 82k ejemplos, ya etiquetados con tarea (`gec`, `paraphrase`, `simplify`...), formato (`src`, `tgt`) directo.

**Trade-off.** CoEdIT mezcla varias tareas; filtramos por `task == "gec"` para enfocarnos en gramática estricta.

---

## ADR-03: Backend de cómputo — MPS

**Contexto.** Mac Apple Silicon (M1/M2/M3) tiene GPU con memoria unificada. PyTorch expone esta GPU vía el backend `mps`.

**Decisión.** Detectar `torch.backends.mps.is_available()` y usar `mps` cuando disponible, fallback a CPU.

**Caveats documentados.**

1. **fp16 no soportado** en `mps` con la misma estabilidad que CUDA. Usar `bf16=True` en M1/M2/M3 (soportado nativamente).
2. **Operadores faltantes** — algunas ops caen a CPU automáticamente; setear `PYTORCH_ENABLE_MPS_FALLBACK=1`.
3. **No DDP** — entrenamiento multi-GPU no aplica; un solo dispositivo MPS.

---

## ADR-04: Trainer — `Seq2SeqTrainer` (no `Trainer`)

**Contexto.** La guía fuente sugiere `Trainer` con `predict_with_generate=True`.

**Decisión.** Usar `Seq2SeqTrainer` + `Seq2SeqTrainingArguments`.

**Razón.** El argumento `predict_with_generate` y los métodos asociados (`generation_max_length`, `generation_num_beams`) **solo existen** en la subclase Seq2Seq. Con `Trainer` plano, las métricas se calcularían sobre logits crudos en vez de texto generado, lo que arruina las métricas tipo BLEU.

**Otras correcciones de la guía.**

| Guía dice | PoC usa | Razón |
|---|---|---|
| `use_mps_device=True` | omitir | deprecado desde `transformers>=4.34`, MPS auto-detectado |
| `evaluation_strategy="epoch"` | `eval_strategy="epoch"` | renombrado en `transformers>=4.41` |
| `tokenizer.as_target_tokenizer()` | `text_target=...` directo | API más limpia, equivalente |

---

## ADR-05: DataCollator — `DataCollatorForSeq2Seq` (no padding fijo)

**Contexto.** La guía hace `padding="max_length"` en preprocesamiento → todos los batches tienen longitud 128 incluso si la oración tiene 6 tokens. Desperdicia compute.

**Decisión.** Tokenizar **sin padding** y delegar a `DataCollatorForSeq2Seq` que paddea **dinámicamente al máximo del batch**.

**Beneficio medido.** En CoEdIT la longitud media de src es ~25 tokens. Padding dinámico reduce ~70% del compute por batch.

---

## ADR-06: Métricas — SacreBLEU + GLEU + Exact-Match

**Contexto.** BLEU sobre-penaliza cambios pequeños (típicos de GEC).

**Decisión.** Reportar tres métricas complementarias.

| Métrica | Captura | Limitación |
|---|---|---|
| **SacreBLEU** | Calidad general n-grama | Penaliza correcciones cortas |
| **GLEU** (Google-BLEU para GEC) | Específica para GEC, premia ediciones mínimas correctas | Menos estandarizada |
| **Exact-Match** | % oraciones idénticas a referencia | Binaria, dura |

Lo ideal para producción sería **ERRANT** (alinea ediciones), pero requiere parser de inglés y queda fuera del scope de la PoC.

---

## ADR-07: Score de confianza por logits

**Contexto.** El modelo siempre genera "algo". Necesitamos saber **qué tan seguro** está.

**Decisión.** Usar `model.generate(..., output_scores=True, return_dict_in_generate=True)` y promediar log-probs de los tokens generados.

**Heurísticas adicionales.**

- Si `output == input` → confianza alta de que la oración era correcta.
- Si log-prob promedio < umbral (ej: -1.5) → marcar para revisión humana.

---

## ADR-08: PEFT/LoRA — opcional, notebook 08

**Contexto.** Para `t5-base`/`t5-large`, fine-tuning completo en MPS es lento.

**Decisión.** Documentar la ruta LoRA con `peft` como notebook independiente.

**Trade-off.** LoRA entrena ~0.5% de los parámetros con ~95% de la calidad del full fine-tune. Reduce tiempo de epoch ~3x y permite cargar `t5-base` cómodamente en 16 GB.

---

## ADR-09: Subset de 10k ejemplos para PoC

**Contexto.** CoEdIT tiene 82k pares. Fine-tuning completo en M1 con `t5-small` toma ~6h.

**Decisión.** PoC usa `train[:10000]` con `train_test_split(test_size=0.1)` → ~9k train, ~1k eval. Tiempo total ~30min en M1 Pro.

**Consecuencia.** Calidad sub-óptima vs full dataset. Documentado en notebook 06; el notebook está parametrizado para escalar a full corriendo una sola celda.
