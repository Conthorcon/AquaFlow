from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel
import torch
import os

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# =======================
# LOAD TOKENIZER
# =======================
def load_tokenizer(base_model_id, lora_path):
    tokenizer = AutoTokenizer.from_pretrained(
        base_model_id,
        trust_remote_code=True
    )

    # load chat template từ adapter
    # template_path = os.path.join(lora_path, "chat_template.jinja")
    # if os.path.exists(template_path):
    #     with open(template_path, "r", encoding="utf-8") as f:
    #         tokenizer.chat_template = f.read()

    return tokenizer


# =======================
# LOAD MODEL + LORA
# =======================
def load_model(base_model_id, lora_path):
    base_model = AutoModelForCausalLM.from_pretrained(
        base_model_id,
        torch_dtype=torch.bfloat16,
        trust_remote_code=True
    ).to(DEVICE)

    model = PeftModel.from_pretrained(base_model, lora_path)

    # merge LoRA → tránh lỗi runtime attach
    model = model.merge_and_unload()
    model.eval()

    return model


def inference_text(messages, tokenizer, model, device=DEVICE, max_new_tokens=128):
    prompt = tokenizer.apply_chat_template(
        messages,
        tokenize=False,
        add_generation_prompt=True
    )

    inputs = tokenizer(
        prompt,
        return_tensors="pt",
        truncation=True,
        max_length=max_new_tokens*2
    ).to(device)

    with torch.no_grad():
        outputs = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            do_sample=False,
            temperature=None,
            top_p=None,
            pad_token_id=tokenizer.eos_token_id
        )

    input_len = inputs["input_ids"].shape[1]

    result = tokenizer.decode(
        outputs[0][input_len:],
        skip_special_tokens=True
    )
    return result.strip()
    