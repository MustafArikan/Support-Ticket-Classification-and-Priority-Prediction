import torch
from src.api.bert_inference import BertTicketModel, LABELS


def test_predict_decodes_all_model_heads_without_checkpoint():
    model = BertTicketModel.__new__(BertTicketModel)
    model.device = torch.device("cpu")
    model.tokenizer = lambda *args, **kwargs: {"input_ids": torch.tensor([[1]])}

    class Backbone:
        task_names = list(LABELS)

        def __call__(self, **kwargs):
            return {
                name: torch.zeros(1, len(labels)) for name, labels in LABELS.items()
            }

    model.model = Backbone()
    result = model.predict("Please help with my account")
    for name, labels in LABELS.items():
        assert result[name] == labels[0]
    assert 0 <= result["confidence"] <= 1
