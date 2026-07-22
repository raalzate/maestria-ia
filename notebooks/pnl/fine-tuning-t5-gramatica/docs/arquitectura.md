# Arquitectura de la PoC

## Pipeline de extremo a extremo

```
┌─────────────────────────────────────────────────────────────────────────┐
│                       Hugging Face Hub                                  │
│   ┌──────────────────┐         ┌────────────────────────┐               │
│   │ grammarly/coedit │         │  google-t5/t5-small    │               │
│   │   (dataset)      │         │  (modelo + tokenizer)  │               │
│   └────────┬─────────┘         └───────────┬────────────┘               │
└────────────┼─────────────────────────────────┼──────────────────────────┘
             │                                 │
             ▼                                 ▼
   ┌──────────────────┐                ┌──────────────────┐
   │   notebook 03    │                │   notebook 02    │
   │      EDA         │                │  Setup + MPS     │
   └────────┬─────────┘                └─────────┬────────┘
            │                                    │
            └─────────────┬──────────────────────┘
                          ▼
                 ┌──────────────────┐
                 │   notebook 04    │
                 │  Tokenización    │   →  artifacts/tokenized_dataset/
                 │  + Collator      │
                 └────────┬─────────┘
                          │
                          ▼
                 ┌──────────────────┐
                 │   notebook 05    │
                 │  Seq2SeqTrainer  │   →  artifacts/t5-gec-mac/
                 │   (MPS, bf16)    │      (checkpoints + tokenizer)
                 └────────┬─────────┘
                          │
            ┌─────────────┴─────────────┐
            ▼                           ▼
   ┌──────────────────┐        ┌──────────────────┐
   │   notebook 06    │        │   notebook 07    │
   │  SacreBLEU/GLEU  │        │ Inferencia +     │
   │  + EM            │        │ score confianza  │
   └────────┬─────────┘        └────────┬─────────┘
            │                           │
            ▼                           ▼
   artifacts/eval_metrics.json   artifacts/inference_samples.json

                     [OPCIONAL]
                          │
                          ▼
                 ┌──────────────────┐
                 │   notebook 08    │
                 │   LoRA / PEFT    │   →  artifacts/t5-base-lora/
                 │   (t5-base)      │
                 └──────────────────┘
```

## Flujo de datos detallado

### Entrada cruda
```
{"src": "I has a apple.", "tgt": "I have an apple.", "task": "gec"}
```

### Tras preprocesamiento (notebook 04)
```
{
  "input_ids":      [tokens de "grammar: I has a apple."],
  "attention_mask": [1,1,1,...],
  "labels":         [tokens de "I have an apple."]
}
```

### Loss (durante training)
```
cross_entropy(decoder_logits, labels)   # T5 shifts labels internamente
```

### Inferencia (notebook 07)
```
"grammar: He go to store yesterday."
        │
        ▼ encoder
[hidden_states]
        │
        ▼ decoder (auto-regresivo, beam=4)
"He went to the store yesterday."
        │
        ▼ logits → log-probs → confianza
{"output": "...", "confidence": 0.92}
```

## Componentes runtime

| Capa | Componente | Versión | Rol |
|---|---|---|---|
| Hardware | Apple Silicon GPU (MPS) | M1/M2/M3 | Compute |
| Framework | PyTorch | ≥2.2 | Tensor ops |
| Modelo | T5ForConditionalGeneration | transformers ≥4.41 | Encoder-decoder |
| Tokenizer | T5TokenizerFast | sentencepiece | Subword |
| Datos | Datasets | ≥2.19 | Streaming + cache local |
| Trainer | Seq2SeqTrainer | transformers | Loop + checkpointing |
| Métricas | SacreBLEU / GLEU | evaluate ≥0.4 | Evaluación |
| PEFT | LoRA | peft ≥0.11 | Fine-tune eficiente (notebook 08) |

## Persistencia

Todos los artefactos se escriben en `./artifacts/` (gitignored). Cada notebook lee de la carpeta del anterior; ninguno parte desde cero excepto el 02-04.

## Inversión de control para escalar

Cada notebook expone un bloque `# === CONFIG ===` al inicio con parámetros (model_name, batch_size, num_samples, num_epochs). Cambiar valores ahí escala la PoC sin tocar el resto del código.
