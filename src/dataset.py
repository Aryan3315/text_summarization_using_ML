
import torch
from torch.utils.data import Dataset, DataLoader
from transformers import AutoTokenizer
from datasets import load_dataset
from src.config import Config


def get_tokenizer():
  
    tokenizer = AutoTokenizer.from_pretrained(Config.TOKENIZER_MODEL)
    return tokenizer


class SummarizationDataset(Dataset):
   
    def __init__(self, split: str, tokenizer):
        assert split in ("train", "validation", "test")
        raw = load_dataset(
            Config.DATASET_NAME,
            Config.DATASET_VERSION,
            split=split,
            trust_remote_code=True,
        )
        self.tokenizer = tokenizer
        self.data = raw

    def __len__(self):
        return len(self.data)

    def __getitem__(self, idx):
        item = self.data[idx]
        article = item["article"]
        summary = item["highlights"]

        src = self.tokenizer(
            article,
            max_length=Config.MAX_ARTICLE_LEN,
            truncation=True,
            padding="max_length",
            return_tensors="pt",
        )
        tgt = self.tokenizer(
            summary,
            max_length=Config.MAX_SUMMARY_LEN,
            truncation=True,
            padding="max_length",
            return_tensors="pt",
        )

        return {
            "src_ids":      src["input_ids"].squeeze(0),       # (src_len,)
            "src_mask":     src["attention_mask"].squeeze(0),  # (src_len,)
            "tgt_ids":      tgt["input_ids"].squeeze(0),       # (tgt_len,)
            "tgt_mask":     tgt["attention_mask"].squeeze(0),  # (tgt_len,)
        }


def get_dataloader(split: str, tokenizer, shuffle: bool = True) -> DataLoader:
    dataset = SummarizationDataset(split, tokenizer)
    return DataLoader(
        dataset,
        batch_size=Config.BATCH_SIZE,
        shuffle=shuffle,
        num_workers=4,
        pin_memory=True,
    )
