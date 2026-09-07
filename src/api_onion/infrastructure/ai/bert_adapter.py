import torch
import torch.nn as nn
from transformers import AutoModel, AutoTokenizer
import os
import logging
from src.api_onion.core.domain.ports import ModelInterface

logger = logging.getLogger(__name__)

LABELS = {
    'type': ['Change', 'Incident', 'Problem', 'Request'], 
    'queue': ['Billing and Payments', 'Customer Service', 'General Inquiry', 'Human Resources', 'IT Support', 'Product Support', 'Returns and Exchanges', 'Sales and Pre-Sales', 'Service Outages and Maintenance', 'Technical Support'], 
    'category': ['Account Management', 'Billing', 'General Inquiry', 'Refund', 'Technical Issue'], 
    'priority': ['critical', 'high', 'low', 'medium']
}
num_classes_dict = {col: len(classes) for col, classes in LABELS.items()}

class MultiTaskTransformer(nn.Module):
    def __init__(self, model_name, num_classes_dict, dropout=0.2):
        super().__init__()
        self.backbone = AutoModel.from_pretrained(model_name)
        hidden = self.backbone.config.hidden_size
        self.dropout = nn.Dropout(dropout)
        self.task_names = list(num_classes_dict.keys())
        self.heads = nn.ModuleDict({f"head_{t}": nn.Linear(hidden, n) for t, n in num_classes_dict.items()})

    def forward(self, input_ids=None, attention_mask=None, **kwargs):
        outputs = self.backbone(input_ids=input_ids, attention_mask=attention_mask)
        pooled = self.dropout(outputs.last_hidden_state[:, 0])
        logits = {t: self.heads[f"head_{t}"](pooled) for t in self.task_names}
        return logits

class BertModelAdapter(ModelInterface):
    def __init__(self):
        self.model_path = os.path.join(os.path.dirname(__file__), "../../../../models/bert_multitask_checkpoints/checkpoint-20048")
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        try:
            self.tokenizer = AutoTokenizer.from_pretrained("bert-base-multilingual-cased")
            self.model = MultiTaskTransformer("bert-base-multilingual-cased", num_classes_dict)
            
            from safetensors.torch import load_file
            weights = load_file(os.path.join(self.model_path, "model.safetensors"))
            self.model.load_state_dict(weights, strict=False)
            self.model.to(self.device)
            self.model.eval()
            self.is_loaded = True
            logger.info("BERT Model loaded successfully via Adapter.")
        except Exception as e:
            logger.error(f"Failed to load BERT model: {e}")
            self.is_loaded = False

    def predict(self, text: str):
        if not self.is_loaded:
            raise Exception("Model is not loaded.")
        
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=256, padding=True)
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        with torch.no_grad():
            logits = self.model(**inputs)
        
        result = {}
        confidence_sum = 0
        for task in self.model.task_names:
            probs = torch.softmax(logits[task], dim=1)[0].cpu().numpy()
            pred_idx = probs.argmax()
            result[task] = LABELS[task][pred_idx]
            if task in ['category', 'priority']:
                confidence_sum += probs[pred_idx]
        
        avg_confidence = float(confidence_sum / 2)
        
        # Determine if we should use SHAP or LIME (e.g., based on length or randomly, or compute both and combine)
        # We will compute both to provide a comprehensive explanation, or choose one for speed.
        # Let's implement SHAP using shap.Explainer and LIME using LimeTextExplainer properly.
        
        explain_words = {}
        
        try:
            # --- SHAP Explanation ---
            import shap
            import numpy as np
            
            # SHAP requires a pipeline or a model that outputs probability arrays directly
            def shap_predictor(texts):
                inps = self.tokenizer(texts.tolist() if isinstance(texts, np.ndarray) else texts, 
                                      return_tensors="pt", truncation=True, max_length=256, padding=True)
                inps = {k: v.to(self.device) for k, v in inps.items()}
                with torch.no_grad():
                    outs = self.model(**inps)
                # Let's explain the 'category' prediction
                return torch.softmax(outs['category'], dim=1).cpu().numpy()

            # For SHAP text explainer, we need a masker
            masker = shap.maskers.Text(self.tokenizer)
            shap_explainer = shap.Explainer(shap_predictor, masker, output_names=LABELS['category'])
            
            # Compute SHAP values
            shap_values = shap_explainer([text])
            
            # Extract top words from SHAP
            # shap_values.values shape: (1, num_tokens, num_classes)
            # We want the explanation for the predicted class
            pred_class_idx = LABELS['category'].index(result['category'])
            
            # Get token strings and their corresponding SHAP values for the predicted class
            tokens = shap_values.data[0]
            values_for_pred = shap_values.values[0, :, pred_class_idx]
            
            # Store in explain_words
            shap_word_scores = {}
            for token, val in zip(tokens, values_for_pred):
                # Clean up subword tokens (e.g., ## or whitespace markers depending on tokenizer)
                clean_token = token.replace('##', '').strip()
                if len(clean_token) > 2 and abs(val) > 0.01:
                    # Accumulate scores for subwords forming a word
                    if clean_token in shap_word_scores:
                        shap_word_scores[clean_token] += abs(val)
                    else:
                        shap_word_scores[clean_token] = abs(val)
                        
            # Keep top 3 from SHAP
            sorted_shap = sorted(shap_word_scores.items(), key=lambda x: x[1], reverse=True)[:3]
            for word, score in sorted_shap:
                explain_words[f"{word} (SHAP)"] = round(float(score), 3)
                
            # --- LIME Explanation ---
            from lime.lime_text import LimeTextExplainer
            lime_explainer = LimeTextExplainer(class_names=LABELS['category'])
            
            def lime_predictor(texts):
                inps = self.tokenizer(texts, return_tensors="pt", truncation=True, max_length=256, padding=True)
                inps = {k: v.to(self.device) for k, v in inps.items()}
                with torch.no_grad():
                    outs = self.model(**inps)
                return torch.softmax(outs['category'], dim=1).cpu().numpy()
                
            # Use a proper number of samples for LIME to be accurate
            exp = lime_explainer.explain_instance(text, lime_predictor, num_features=3, num_samples=500)
            
            for word, score in exp.as_list():
                if len(word) > 2:
                    # Avoid duplicates with SHAP if they found the same word
                    clean_word = word.lower()
                    if not any(clean_word in k.lower() for k in explain_words.keys()):
                        explain_words[f"{word} (LIME)"] = round(abs(score), 3)

        except Exception as e:
            logger.error(f"Explainability error (SHAP/LIME): {e}")
            # If both fail completely, return empty dict rather than fake words
            pass
        
        result['confidence'] = avg_confidence
        result['explainability'] = explain_words
        
        # --- BUSINESS METRICS LOGGING ---
        try:
            from src.api_onion.infrastructure.monitoring.metrics import TICKET_PROCESSED_COUNT, AI_CONFIDENCE_SCORE
            TICKET_PROCESSED_COUNT.labels(category=result.get('category', 'unknown'), priority=result.get('priority', 'unknown')).inc()
            AI_CONFIDENCE_SCORE.observe(avg_confidence)
        except Exception as e:
            logger.error(f"Failed to record prometheus metrics: {e}")
            
        return result