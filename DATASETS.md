# 📊 RapidCare AI — Training Datasets

Curated datasets for training, fine-tuning, and evaluating all AI components of RapidCare AI.

---

## 🚑 Triage & Emergency Decision-Making

### 1. MIMIC-IV-Ext Triage Instruction Corpus (MIETIC)
| Property | Value |
|----------|-------|
| **Size** | 9,629 structured triage cases |
| **Labels** | Emergency Severity Index (ESI) levels 1–5 |
| **Use Case** | Fine-tuning NLP triage classifier (`nlp_service.py`) |
| **Source** | [PhysioNet](https://physionet.org) (requires credentialing) |
| **Format** | Structured clinical text + ESI label |

**Integration Plan:**
```python
# Fine-tune distilbert on MIETIC instead of keyword matching
# Maps ESI levels to our severity scale:
# ESI 1 (Critical)   → severity_score 90-100
# ESI 2 (Emergent)   → severity_score 70-89
# ESI 3 (Urgent)     → severity_score 45-69
# ESI 4 (Semi-urgent)→ severity_score 20-44
# ESI 5 (Non-urgent) → severity_score 0-19
```

---

### 2. ER-REASON
| Property | Value |
|----------|-------|
| **Size** | 25,174 clinical notes from 3,437 ER patients |
| **Use Case** | LLM reasoning across full ER workflow; evaluate NLP pipeline |
| **Source** | [PhysioNet](https://physionet.org) (requires credentialing) |
| **Format** | Clinical notes + structured reasoning labels |

**Integration Plan:**
```python
# Use as test set for nlp_service.py accuracy evaluation
# Benchmark our keyword matching vs distilbert classification
# Target: >80% accuracy on ESI label prediction
```

---

### 3. Trauma THOMPSON Dataset
| Property | Value |
|----------|-------|
| **Size** | 3,717 egocentric video clips |
| **Annotations** | Action recognition, anticipation, Medical VQA |
| **Use Case** | Train Vision AI to recognize trauma procedures |
| **Source** | [AAAI Publication](https://aaai.org) |
| **Format** | Egocentric video + frame-level annotations |

**Integration Plan:**
```python
# Fine-tune YOLOv8 or ViT on video frames for:
# - Bleeding detection
# - CPR recognition  
# - Fracture assessment
# - Wound severity classification

# In vision_service.py:
model = YOLO("yolov8n.pt")  # Base model
# → Fine-tune on THOMPSON frames
# → model.train(data="thompson_dataset.yaml", epochs=50)
```

---

### 4. EgoEMS Dataset
| Property | Value |
|----------|-------|
| **Size** | 20+ hours of egocentric video, 233 scenarios, 62 participants |
| **Participants** | EMS professionals + general public |
| **Use Case** | Realistic responder-patient interaction modeling |
| **Source** | [Harvard Dataverse](https://dataverse.harvard.edu) |
| **Format** | Egocentric video + scenario metadata |

**Integration Plan:**
```python
# Use for training the ambulance/responder simulation
# Model realistic response times and protocols
# Fine-tune speech recognition on EMS radio communication patterns
```

---

## 💊 First-Aid & Medical Knowledge

### 5. MedRescue (ericrisco/medrescue)
| Property | Value |
|----------|-------|
| **Size** | 86,667 medical Q&A pairs |
| **Sources** | 11 specialized medical datasets + 14 WHO/ICRC PDFs |
| **Use Case** | Replacing TF-IDF RAG with fine-tuned LLM (`firstaid_service.py`) |
| **Source** | [Hugging Face](https://huggingface.co/datasets/ericrisco/medrescue) |
| **Format** | instruction/input/output JSON pairs |

**Integration Plan:**
```python
# UPGRADE PATH: Replace TF-IDF RAG with fine-tuned Medical Gemma
# from transformers import AutoModelForCausalLM, AutoTokenizer

# Load fine-tuned model
model = AutoModelForCausalLM.from_pretrained("ericrisco/medical-gemma-3n")
tokenizer = AutoTokenizer.from_pretrained("ericrisco/medical-gemma-3n")

def get_first_aid_llm(emergency_type: str, context: str) -> str:
    prompt = f"""Emergency: {emergency_type}
Context: {context}
Provide step-by-step first aid instructions:"""
    inputs = tokenizer(prompt, return_tensors="pt")
    output = model.generate(**inputs, max_new_tokens=300)
    return tokenizer.decode(output[0])
```

---

### 6. FirstAidQA
| Property | Value |
|----------|-------|
| **Size** | 5,500 high-quality Q&A pairs |
| **Source Book** | "Vital First Aid Book (2019)" |
| **Use Case** | Instruction-tuning smaller models for first-aid |
| **Source** | [Hugging Face](https://huggingface.co/datasets) |
| **Format** | question/answer pairs |

**Integration Plan:**
```python
# Augment current knowledge_base/first_aid_protocols.json
# Add 5,500+ Q&A pairs to the TF-IDF corpus
# Improves RAG retrieval accuracy significantly

# Load and index
from datasets import load_dataset
dataset = load_dataset("firstaidqa")
for item in dataset["train"]:
    corpus.append(f"{item['question']} {item['answer']}")
vectorizer.fit_transform(corpus)
```

---

## 📈 Survival & Outcome Prediction

### 7. Clinical and Survival Information Dataset
| Property | Value |
|----------|-------|
| **Content** | Clinical variables, treatment data, survival endpoints |
| **Domain** | Breast cancer (transferable survival patterns) |
| **Use Case** | Multi-task learning for prognosis / survival estimation |
| **Source** | [IEEE DataPort](https://ieee-dataport.org) |
| **Format** | CSV with clinical features + binary survival label |

**Integration Plan:**
```python
# Train the SurvivalPredictor neural network on real survival data
# Transfer learned features to emergency survival prediction

class SurvivalPredictor(nn.Module):
    def __init__(self, input_features=50):
        super().__init__()
        self.fc1 = nn.Linear(input_features, 128)
        self.fc2 = nn.Linear(128, 64)
        self.fc3 = nn.Linear(64, 32)
        self.fc4 = nn.Linear(32, 1)
        self.dropout = nn.Dropout(0.2)

    def forward(self, x):
        x = F.relu(self.fc1(x)); x = self.dropout(x)
        x = F.relu(self.fc2(x)); x = self.dropout(x)
        x = F.relu(self.fc3(x))
        return torch.sigmoid(self.fc4(x))  # 0-1 survival prob

# Input features: age, HR, BP, O2, GCS, bleeding, injuries, time_to_treatment...
```

---

### 8. Cancer Type & Survival Prediction (GAN-Augmented)
| Property | Value |
|----------|-------|
| **Content** | Transcriptomic + survival data for 10 cancer types |
| **Augmented** | GANs used to generate synthetic training samples |
| **Use Case** | Improve prediction models with data augmentation techniques |
| **Source** | [Zenodo](https://zenodo.org) |

---

### 9. Echocardiogram Dataset for Survival Analysis
| Property | Value |
|----------|-------|
| **Size** | 100,000 synthetic samples (derived from UCI Echocardiogram) |
| **Task** | Predicting 1-year survival post-heart attack |
| **Use Case** | Cardiac arrest survival prediction in `severity_service.py` |
| **Source** | [Mendeley Data](https://data.mendeley.com) |
| **Format** | Tabular features + binary 1-year survival label |

**Integration Plan:**
```python
# Specialized cardiac survival model
# More accurate than general sigmoid formula for cardiac cases

cardiac_model = SurvivalPredictor(input_features=12)
# Train on echocardiogram dataset
# Input: fractional_shortening, epss, lvdd, wall_motion_score, age, ...
# Output: 1-year survival probability

# Use in severity_service.py when emergency_type == "cardiac_arrest"
if emergency_type == "cardiac_arrest":
    survival = cardiac_model.predict(cardiac_features)
```

---

## 🗺️ Upgrade Roadmap

```
Current (Demo Mode)           →    Upgraded (Full Mode + Real Data)
──────────────────────────────────────────────────────────────────
Keyword NLP classifier        →    MIETIC fine-tuned distilbert
TF-IDF RAG (8 protocols)      →    MedRescue 86K Q&A + FirstAidQA 5.5K
Rule-based severity scoring   →    MIETIC ESI-calibrated scoring
Sigmoid survival formula      →    Echocardiogram neural network
Mock YOLO detections          →    THOMPSON/EgoEMS fine-tuned YOLOv8
Mock Whisper STT              →    Whisper-small (local, no API needed)
```

---

## 📥 How to Access Datasets

| Dataset | Access |
|---------|--------|
| MIEMIC, ER-REASON | Register at [PhysioNet](https://physionet.org) — free credentialing |
| THOMPSON, EgoEMS | Contact authors via AAAI / [Harvard Dataverse](https://dataverse.harvard.edu) |
| MedRescue | `pip install datasets` → `load_dataset("ericrisco/medrescue")` |
| FirstAidQA | `pip install datasets` → `load_dataset("firstaidqa")` |
| Echocardiogram | [Mendeley Data](https://data.mendeley.com) — free download |

---

> 💡 **Note:** These datasets significantly improve the system when switching to `AI_MODE=full`. The current demo mode is fully functional without any of these datasets.
