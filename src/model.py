
import torch
import torch.nn as nn
import torch.nn.functional as F
import random
from src.config import Config


class Encoder(nn.Module):

    def __init__(self, vocab_size: int, embed_dim: int, hidden_dim: int, num_layers: int, dropout: float):
        super().__init__()
        self.embedding = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
        self.rnn = nn.GRU(
            embed_dim,
            hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            bidirectional=True,
            dropout=dropout if num_layers > 1 else 0.0,
        )
        self.dropout = nn.Dropout(dropout)
        # Project bidirectional hidden to decoder hidden size
        self.fc = nn.Linear(hidden_dim * 2, hidden_dim)

    def forward(self, src_ids, src_mask):
        embedded = self.dropout(self.embedding(src_ids))          # (B, src_len, E)
        outputs, hidden = self.rnn(embedded)                       # outputs: (B, src_len, H*2)

        # hidden: (num_layers*2, B, H) → merge directions
        # Take the last layer's forward & backward hidden states
        hidden = hidden.view(self.rnn.num_layers, 2, hidden.size(1), -1)
        # Concatenate forward and backward for each layer
        hidden = torch.cat([hidden[:, 0, :, :], hidden[:, 1, :, :]], dim=2)  # (layers, B, H*2)
        hidden = torch.tanh(self.fc(hidden))                       # (layers, B, H)

        return outputs, hidden


class BahdanauAttention(nn.Module):

    def __init__(self, hidden_dim: int):
        super().__init__()
        self.W_enc = nn.Linear(hidden_dim * 2, hidden_dim, bias=False)
        self.W_dec = nn.Linear(hidden_dim,     hidden_dim, bias=False)
        self.v     = nn.Linear(hidden_dim, 1,  bias=False)

    def forward(self, decoder_hidden, encoder_outputs, src_mask):
        src_len = encoder_outputs.size(1)

        dec_hidden_exp = decoder_hidden.unsqueeze(1).repeat(1, src_len, 1)  # (B, src_len, H)
        energy = torch.tanh(
            self.W_enc(encoder_outputs) + self.W_dec(dec_hidden_exp)
        )                                                                    # (B, src_len, H)
        scores = self.v(energy).squeeze(2)                                   # (B, src_len)

        # Mask padding positions
        scores = scores.masked_fill(src_mask == 0, float("-inf"))
        attn_weights = F.softmax(scores, dim=1)                              # (B, src_len)

        context = torch.bmm(attn_weights.unsqueeze(1), encoder_outputs)     # (B, 1, H*2)
        context = context.squeeze(1)                                         # (B, H*2)

        return context, attn_weights


class Decoder(nn.Module):

    def __init__(self, vocab_size: int, embed_dim: int, hidden_dim: int, num_layers: int, dropout: float):
        super().__init__()
        self.embedding  = nn.Embedding(vocab_size, embed_dim, padding_idx=0)
        self.attention  = BahdanauAttention(hidden_dim)
        self.rnn        = nn.GRU(
            embed_dim + hidden_dim * 2,   # input = embedding + context
            hidden_dim,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0,
        )
        self.fc_out     = nn.Linear(hidden_dim * 3 + embed_dim, vocab_size)
        self.dropout    = nn.Dropout(dropout)

    def forward_step(self, tgt_token, hidden, encoder_outputs, src_mask):
     
        embedded = self.dropout(self.embedding(tgt_token.unsqueeze(1)))  # (B, 1, E)

        # Use top layer hidden for attention query
        query = hidden[-1]                                                # (B, H)
        context, attn_w = self.attention(query, encoder_outputs, src_mask)

        rnn_input = torch.cat([embedded, context.unsqueeze(1)], dim=2)  # (B, 1, E+H*2)
        output, hidden = self.rnn(rnn_input, hidden)                     # output: (B, 1, H)

        output   = output.squeeze(1)                                     # (B, H)
        embedded = embedded.squeeze(1)                                   # (B, E)

        logits = self.fc_out(
            torch.cat([output, context, embedded], dim=1)
        )                                                                 # (B, vocab_size)

        return logits, hidden, attn_w

    def forward(self, tgt_ids, hidden, encoder_outputs, src_mask, teacher_forcing_ratio=0.5):
      
        batch_size = tgt_ids.size(0)
        tgt_len    = tgt_ids.size(1)
        vocab_size = self.fc_out.out_features

        outputs = torch.zeros(batch_size, tgt_len - 1, vocab_size).to(tgt_ids.device)
        token   = tgt_ids[:, 0]   # <BOS> token

        for t in range(1, tgt_len):
            logits, hidden, _ = self.forward_step(token, hidden, encoder_outputs, src_mask)
            outputs[:, t - 1, :] = logits

            use_teacher = random.random() < teacher_forcing_ratio
            top1  = logits.argmax(dim=1)
            token = tgt_ids[:, t] if use_teacher else top1

        return outputs


class Seq2SeqSummarizer(nn.Module):

    def __init__(self, config: Config):
        super().__init__()
        self.encoder = Encoder(
            vocab_size=config.VOCAB_SIZE,
            embed_dim=config.EMBED_DIM,
            hidden_dim=config.HIDDEN_DIM,
            num_layers=config.NUM_LAYERS,
            dropout=config.DROPOUT,
        )
        self.decoder = Decoder(
            vocab_size=config.VOCAB_SIZE,
            embed_dim=config.EMBED_DIM,
            hidden_dim=config.HIDDEN_DIM,
            num_layers=config.NUM_LAYERS,
            dropout=config.DROPOUT,
        )

    def forward(self, src_ids, src_mask, tgt_ids, teacher_forcing_ratio=0.5):
        encoder_outputs, hidden = self.encoder(src_ids, src_mask)
        logits = self.decoder(
            tgt_ids, hidden, encoder_outputs, src_mask, teacher_forcing_ratio
        )
        return logits   # (B, tgt_len-1, vocab_size)

