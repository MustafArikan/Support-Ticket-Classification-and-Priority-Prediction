import torch
import torch.nn as nn
from transformers import AutoModel, AutoTokenizer
import os

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
        pooled = self.dropout(outputs.last_hidden_state[:, 0])  # [CLS]
        logits = {t: self.heads[f"head_{t}"](pooled) for t in self.task_names}
        return logits

class BertTicketModel:
    def __init__(self, model_path: str):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.tokenizer = AutoTokenizer.from_pretrained("bert-base-multilingual-cased")
        self.model = MultiTaskTransformer("bert-base-multilingual-cased", num_classes_dict)
        
        # Load weights
        from safetensors.torch import load_file
        weights = load_file(os.path.join(model_path, "model.safetensors"))
        self.model.load_state_dict(weights, strict=False)
        self.model.to(self.device)
        self.model.eval()

    def predict(self, text):
        inputs = self.tokenizer(text, return_tensors="pt", truncation=True, max_length=256, padding=True)
        inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        with torch.no_grad():
            logits = self.model(**inputs)
        
        result = {}
        confidence_sum = 0
        for task in self.task_names:
            probs = torch.softmax(logits[task], dim=1)[0].cpu().numpy()
            pred_idx = probs.argmax()
            conf = probs[pred_idx]
            result[task] = LABELS[task][pred_idx]
            if task in ['category', 'priority']:
                confidence_sum += conf
                
        result['confidence'] = float(confidence_sum / 2.0)
        return result
