# LoRA Fine-Tuning & Colab Training Guide

This guide details the complete PEFT/LoRA fine-tuning workflow for adapting `Qwen2.5-1.5B-Instruct` into a specialized Back-Office AI Business Analyst.

---

## 1. Pipeline Architecture

```
                                  [Synthetic Dataset Builder]
                                               │
                                               ▼
                              training/data/train.jsonl (196 samples)
                              training/data/validation.jsonl (24 samples)
                              training/data/test.jsonl (25 samples)
                                               │
               ┌───────────────────────────────┴──────────────────────────────┐
               ▼                                                              ▼
    [Local CPU / Dry-Run Mode]                                   [Google Colab Free T4 GPU]
    python training/train_lora.py --dry-run                       python training/colab_train.py
               │                                                              │
               └───────────────────────────────┬──────────────────────────────┘
                                               ▼
                                 [LoRA Adapter Package]
                             models/adapters/business-analyst-v1/
                                 - adapter_config.json
                                 - adapter_model.bin / safetensors
                                 - README.md
                                               │
                                               ▼
                                 [Benchmark Evaluation]
                             python training/evaluate_model.py
                                               │
                                               ▼
                                 [Model Registry Update]
                               models/model_registry.json
```

---

## 2. Step 1: Check System Hardware

Before training, check whether your machine can train locally or if Colab is recommended:

```powershell
backend\.venv\Scripts\python.exe training/check_training_hardware.py
```

- **GPU VRAM >= 8 GB**: Local full training supported.
- **GPU VRAM 4–8 GB**: 4-bit QLoRA supported.
- **No NVIDIA GPU / RAM < 16 GB**: Use Google Colab T4 (free) or run `--dry-run`.

---

## 3. Step 2: Generate Synthetic Datasets

Generate 240+ multi-domain synthetic training examples covering HR, Sales, Inventory, and graceful metric refusals:

```powershell
backend\.venv\Scripts\python.exe training/business_analyst_dataset_builder.py
```

Generated files:
- `training/data/train.jsonl`
- `training/data/validation.jsonl`
- `training/data/test.jsonl`

---

## 4. Step 3: Train with Google Colab (Free T4 GPU)

For high-speed training (10–15 minutes on a free GPU):

1. Go to [Google Colab](https://colab.research.google.com/).
2. In Colab menu: **Runtime &rarr; Change runtime type &rarr; Hardware accelerator: T4 GPU**.
3. Upload `training/colab_train.py` and `training/data/train.jsonl`.
4. Run the training command:
   ```bash
   !python colab_train.py
   ```
5. Download the exported `business_analyst_lora.zip` and extract its contents into:
   ```
   models/adapters/business-analyst-v1/
   ```

### Local Dry-Run / Test Mode
If you wish to verify the training configuration locally without invoking heavy GPU training:
```powershell
backend\.venv\Scripts\python.exe training/train_lora.py --dry-run
```

---

## 5. Step 4: Run Evaluation Benchmarks

Evaluate direct metric accuracy, dimension rankings, missing metric refusals, and injection safety:

```powershell
backend\.venv\Scripts\python.exe training/evaluate_model.py
```

**Target Benchmarks**:
- Direct Metric Accuracy: `100.0%`
- Dimension Lookup Correctness: `100.0%`
- Missing Metric Refusal Rate: `100.0%`
- Prompt Injection Neutralization: `100.0%`
- Numerical Grounding Enforcement: `100.0%`

---

## 6. Step 5: Verify Model Registry

Inspect `models/model_registry.json` to confirm adapter status and metadata:

```json
{
  "active_model_id": "qwen2.5-1.5b-instruct-ba-v1",
  "adapters": [
    {
      "adapter_id": "business-analyst-v1",
      "status": "active",
      "lora_r": 8,
      "lora_alpha": 16,
      "target_modules": ["q_proj", "k_proj", "v_proj", "o_proj"]
    }
  ]
}
```

The active adapter and evaluation stats will appear automatically in the frontend under **AI Model & LoRA** (`/ai-management`).
