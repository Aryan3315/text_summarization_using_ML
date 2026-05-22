
import os
import json
import torch
import torch.nn as nn
from torch.optim import Adam
from torch.optim.lr_scheduler import ReduceLROnPlateau
from tqdm import tqdm

from src.config import Config
from src.model import Seq2SeqSummarizer
from src.dataset import get_dataloader, get_tokenizer


def train_epoch(model, loader, optimizer, criterion, device, teacher_forcing):
    model.train()
    total_loss = 0.0

    for batch in tqdm(loader, desc="Training", leave=False):
        src_ids  = batch["src_ids"].to(device)
        src_mask = batch["src_mask"].to(device)
        tgt_ids  = batch["tgt_ids"].to(device)

        optimizer.zero_grad()

        # logits: (B, tgt_len-1, vocab_size)
        logits = model(src_ids, src_mask, tgt_ids, teacher_forcing)

        # Flatten for cross-entropy: ignore <BOS> in targets
        B, T, V = logits.shape
        loss = criterion(
            logits.reshape(B * T, V),
            tgt_ids[:, 1:].reshape(B * T),
        )

        loss.backward()
        nn.utils.clip_grad_norm_(model.parameters(), Config.CLIP_GRAD)
        optimizer.step()

        total_loss += loss.item()

    return total_loss / len(loader)


def evaluate_epoch(model, loader, criterion, device):
    model.eval()
    total_loss = 0.0

    with torch.no_grad():
        for batch in tqdm(loader, desc="Validation", leave=False):
            src_ids  = batch["src_ids"].to(device)
            src_mask = batch["src_mask"].to(device)
            tgt_ids  = batch["tgt_ids"].to(device)

            logits = model(src_ids, src_mask, tgt_ids, teacher_forcing_ratio=0.0)

            B, T, V = logits.shape
            loss = criterion(
                logits.reshape(B * T, V),
                tgt_ids[:, 1:].reshape(B * T),
            )
            total_loss += loss.item()

    return total_loss / len(loader)


def plot_training_curves(train_losses, val_losses, save_dir):
    """Save training/validation loss curve and per-epoch comparison bar chart."""
    try:
        import matplotlib
        matplotlib.use("Agg")  # non-interactive backend, safe for servers
        import matplotlib.pyplot as plt
        import numpy as np

        epochs = list(range(1, len(train_losses) + 1))
        os.makedirs(save_dir, exist_ok=True)

        # ── Plot 1: Loss curves ───────────────────────────────────────────────
        fig, ax = plt.subplots(figsize=(10, 5))
        ax.plot(epochs, train_losses, "b-o", linewidth=2, markersize=5, label="Train Loss")
        ax.plot(epochs, val_losses,   "r-o", linewidth=2, markersize=5, label="Validation Loss")
        ax.set_xlabel("Epoch", fontsize=13)
        ax.set_ylabel("Cross-Entropy Loss", fontsize=13)
        ax.set_title("Training vs Validation Loss", fontsize=15, fontweight="bold")
        ax.legend(fontsize=12)
        ax.grid(True, linestyle="--", alpha=0.6)
        ax.set_xticks(epochs)
        best_epoch = int(val_losses.index(min(val_losses))) + 1
        ax.axvline(x=best_epoch, color="green", linestyle="--", alpha=0.7,
                   label=f"Best epoch ({best_epoch})")
        ax.legend(fontsize=12)
        plt.tight_layout()
        path1 = os.path.join(save_dir, "loss_curves.png")
        fig.savefig(path1, dpi=150)
        plt.close(fig)
        print(f"  📊 Saved: {path1}")

        # ── Plot 2: Per-epoch loss comparison (grouped bar chart) ─────────────
        fig, ax = plt.subplots(figsize=(max(8, len(epochs) * 0.8), 5))
        x = np.arange(len(epochs))
        width = 0.35
        bars1 = ax.bar(x - width/2, train_losses, width, label="Train Loss",
                       color="steelblue", alpha=0.85)
        bars2 = ax.bar(x + width/2, val_losses,   width, label="Val Loss",
                       color="tomato",    alpha=0.85)
        ax.set_xlabel("Epoch", fontsize=13)
        ax.set_ylabel("Loss", fontsize=13)
        ax.set_title("Per-Epoch Loss Comparison", fontsize=15, fontweight="bold")
        ax.set_xticks(x)
        ax.set_xticklabels([str(e) for e in epochs])
        ax.legend(fontsize=12)
        ax.grid(True, axis="y", linestyle="--", alpha=0.5)
        # Annotate bars with values
        for bar in bars1:
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.005,
                    f"{bar.get_height():.3f}", ha="center", va="bottom", fontsize=7)
        for bar in bars2:
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.005,
                    f"{bar.get_height():.3f}", ha="center", va="bottom", fontsize=7)
        plt.tight_layout()
        path2 = os.path.join(save_dir, "loss_bar_chart.png")
        fig.savefig(path2, dpi=150)
        plt.close(fig)
        print(f"  📊 Saved: {path2}")

        # ── Plot 3: Loss gap (overfitting indicator) ──────────────────────────
        gaps = [v - t for t, v in zip(train_losses, val_losses)]
        fig, ax = plt.subplots(figsize=(10, 4))
        colors = ["green" if g <= 0 else "orange" if g < 0.1 else "red" for g in gaps]
        ax.bar(epochs, gaps, color=colors, alpha=0.8)
        ax.axhline(y=0, color="black", linewidth=0.8)
        ax.set_xlabel("Epoch", fontsize=13)
        ax.set_ylabel("Val Loss − Train Loss", fontsize=13)
        ax.set_title("Generalization Gap (Val − Train Loss)", fontsize=15, fontweight="bold")
        ax.set_xticks(epochs)
        ax.grid(True, axis="y", linestyle="--", alpha=0.5)
        # Legend
        from matplotlib.patches import Patch
        legend_elements = [
            Patch(facecolor="green",  label="Generalizing (gap ≤ 0)"),
            Patch(facecolor="orange", label="Slight overfit (0–0.1)"),
            Patch(facecolor="red",    label="Overfitting (gap > 0.1)"),
        ]
        ax.legend(handles=legend_elements, fontsize=10)
        plt.tight_layout()
        path3 = os.path.join(save_dir, "generalization_gap.png")
        fig.savefig(path3, dpi=150)
        plt.close(fig)
        print(f"  📊 Saved: {path3}")

    except ImportError:
        print("  ⚠ matplotlib not installed — skipping plots. Run: pip install matplotlib")


def save_training_log(train_losses, val_losses, save_dir):
    """Save loss history as JSON for later re-plotting."""
    os.makedirs(save_dir, exist_ok=True)
    log = {
        "epochs": list(range(1, len(train_losses) + 1)),
        "train_loss": train_losses,
        "val_loss": val_losses,
        "best_epoch": int(val_losses.index(min(val_losses))) + 1,
        "best_val_loss": min(val_losses),
    }
    path = os.path.join(save_dir, "training_log.json")
    with open(path, "w") as f:
        json.dump(log, f, indent=2)
    print(f"  📄 Saved training log: {path}")


def train():
    cfg    = Config()
    device = torch.device(cfg.DEVICE if torch.cuda.is_available() else "cpu")
    print(f"Using device: {device}")

    os.makedirs(cfg.MODEL_DIR, exist_ok=True)
    plots_dir = os.path.join(cfg.BASE_DIR, "plots")

    tokenizer    = get_tokenizer()
    train_loader = get_dataloader("train",      tokenizer, shuffle=True)
    val_loader   = get_dataloader("validation", tokenizer, shuffle=False)

    model = Seq2SeqSummarizer(cfg).to(device)
    print(f"Model parameters: {sum(p.numel() for p in model.parameters()):,}")

    criterion = nn.CrossEntropyLoss(ignore_index=0)
    optimizer = Adam(model.parameters(), lr=cfg.LEARNING_RATE)
    scheduler = ReduceLROnPlateau(optimizer, patience=2, factor=0.5, verbose=True)

    best_val_loss  = float("inf")
    train_losses   = []
    val_losses     = []

    for epoch in range(1, cfg.EPOCHS + 1):
        train_loss = train_epoch(
            model, train_loader, optimizer, criterion, device, cfg.TEACHER_FORCING
        )
        val_loss = evaluate_epoch(model, val_loader, criterion, device)
        scheduler.step(val_loss)

        train_losses.append(round(train_loss, 4))
        val_losses.append(round(val_loss, 4))

        print(f"Epoch {epoch:02d} | Train Loss: {train_loss:.4f} | Val Loss: {val_loss:.4f}")

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            ckpt_path = os.path.join(cfg.MODEL_DIR, "best_model.pt")
            torch.save(
                {
                    "epoch":       epoch,
                    "model_state": model.state_dict(),
                    "optim_state": optimizer.state_dict(),
                    "val_loss":    val_loss,
                },
                ckpt_path,
            )
            print(f"  ✓ Saved best model (val_loss={val_loss:.4f})")

        # Save plots after every epoch so you can monitor progress
        if epoch >= 2:
            plot_training_curves(train_losses, val_losses, plots_dir)

    # Final save
    save_training_log(train_losses, val_losses, plots_dir)
    plot_training_curves(train_losses, val_losses, plots_dir)
    print(f"\nTraining complete. Plots saved to: {plots_dir}/")


if __name__ == "__main__":
    train()
