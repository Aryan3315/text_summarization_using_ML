
import torch
from rouge_score import rouge_scorer
from tqdm import tqdm

from src.config import Config
from src.model import Seq2SeqSummarizer
from src.dataset import get_dataloader, get_tokenizer
from src.inference import greedy_decode


def evaluate_rouge(num_samples: int = 500):
    cfg    = Config()
    device = torch.device(cfg.DEVICE if torch.cuda.is_available() else "cpu")

    tokenizer = get_tokenizer()
    loader    = get_dataloader("test", tokenizer, shuffle=False)

    model = Seq2SeqSummarizer(cfg).to(device)
    ckpt  = torch.load(
        f"{cfg.MODEL_DIR}/best_model.pt",
        map_location=device,
        weights_only=True,
    )
    model.load_state_dict(ckpt["model_state"])
    model.eval()

    scorer  = rouge_scorer.RougeScorer(["rouge1", "rouge2", "rougeL"], use_stemmer=True)
    scores  = {"rouge1": [], "rouge2": [], "rougeL": []}
    count   = 0

    for batch in tqdm(loader, desc="Evaluating"):
        src_ids  = batch["src_ids"].to(device)
        src_mask = batch["src_mask"].to(device)
        tgt_ids  = batch["tgt_ids"]

        for i in range(src_ids.size(0)):
            if count >= num_samples:
                break

            pred_ids = greedy_decode(
                model,
                src_ids[i].unsqueeze(0),
                src_mask[i].unsqueeze(0),
                tokenizer,
                device,
                cfg,
            )
            pred_text = tokenizer.decode(pred_ids, skip_special_tokens=True)
            ref_text  = tokenizer.decode(tgt_ids[i].tolist(), skip_special_tokens=True)

            result = scorer.score(ref_text, pred_text)
            for key in scores:
                scores[key].append(result[key].fmeasure)

            count += 1

        if count >= num_samples:
            break

    print("\n=== ROUGE Scores ===")
    for key, vals in scores.items():
        print(f"  {key}: {sum(vals)/len(vals):.4f}")
