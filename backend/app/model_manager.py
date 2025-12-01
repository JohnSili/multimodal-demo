"""
Менеджер для загрузки и работы с моделью SmolVLM2.
Реализует singleton паттерн для избежания множественных загрузок.
"""
import torch
from transformers import AutoProcessor, AutoModelForImageTextToText
from typing import Optional, Any
import os
from app.config import settings


class ModelManager:
    """Singleton менеджер модели SmolVLM2."""
    
    _instance: Optional['ModelManager'] = None
    _model: Optional[AutoModelForImageTextToText] = None
    _processor: Optional[AutoProcessor] = None
    _loaded: bool = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ModelManager, cls).__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._loaded:
            self._loaded = True
    
    def load_model(self) -> None:
        """Загружает модель и процессор из кэша или HuggingFace Hub."""
        if self._model is not None and self._processor is not None:
            return
        
        print(f"Загрузка модели {settings.MODEL_NAME}...")
        
        if settings.DEVICE == "cuda" and torch.cuda.is_available():
            if settings.TORCH_DTYPE == "float16":
                torch_dtype = torch.float16
            elif settings.TORCH_DTYPE == "bfloat16":
                torch_dtype = torch.bfloat16
            else:
                torch_dtype = torch.float32
            device = "cuda"
        else:
            torch_dtype = torch.float32
            device = "cpu"
            if settings.DEVICE == "cuda":
                print("Предупреждение: CUDA запрошена, но недоступна. Используется CPU.")
        
        print("Загрузка процессора...")
        self._processor = AutoProcessor.from_pretrained(
            settings.MODEL_NAME,
            cache_dir=settings.TRANSFORMERS_CACHE,
            trust_remote_code=True
        )
        
        print("Загрузка модели...")
        try:
            import flash_attn
            attn_implementation = "flash_attention_2" if device == "cuda" else "eager"
        except ImportError:
            attn_implementation = "eager"
            if device == "cuda":
                print("FlashAttention2 не установлен, используется eager attention")
        
        if device == "cuda":
            self._model = AutoModelForImageTextToText.from_pretrained(
                settings.MODEL_NAME,
                cache_dir=settings.TRANSFORMERS_CACHE,
                torch_dtype=torch_dtype,
                _attn_implementation=attn_implementation,
                trust_remote_code=True,
                device_map="auto"
            )
        else:
            self._model = AutoModelForImageTextToText.from_pretrained(
                settings.MODEL_NAME,
                cache_dir=settings.TRANSFORMERS_CACHE,
                torch_dtype=torch_dtype,
                _attn_implementation=attn_implementation,
                trust_remote_code=True
            )
            self._model = self._model.to(device)
        
        self._model.eval()
        print(f"Модель загружена на {device} с dtype {torch_dtype}")
    
    def get_model(self) -> AutoModelForImageTextToText:
        """Возвращает загруженную модель."""
        if self._model is None:
            self.load_model()
        return self._model
    
    def get_processor(self) -> AutoProcessor:
        """Возвращает загруженный процессор."""
        if self._processor is None:
            self.load_model()
        return self._processor
    
    def is_loaded(self) -> bool:
        """Проверяет, загружена ли модель."""
        return self._model is not None and self._processor is not None

    def vqa_inference(self, image, question: Optional[str] = None) -> str:
        if not self.is_loaded():
            self.load_model()

        model = self.get_model()
        processor = self.get_processor()

        if question is None or not question.strip():
            text_content = "Describe this image in detail."
        else:
            text_content = question

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image"},
                    {"type": "text", "text": text_content}
                ]
            }
        ]

        prompt = processor.apply_chat_template(messages, add_generation_prompt=True, tokenize=False)
        inputs = processor(text=prompt, images=[image], return_tensors="pt")

        device = next(model.parameters()).device
        dtype = next(model.parameters()).dtype
        inputs = {k: v.to(device).to(dtype) if v.dtype.is_floating_point else v.to(device) 
                  for k, v in inputs.items()}

        with torch.no_grad():
            generated_ids = model.generate(
                **inputs,
                max_new_tokens=512,
                do_sample=False,
                temperature=0.7,
                repetition_penalty=1.2,
                pad_token_id=processor.tokenizer.pad_token_id,
                eos_token_id=processor.tokenizer.eos_token_id
            )

        generated_texts = processor.batch_decode(
            generated_ids,
            skip_special_tokens=True
        )

        full_response = generated_texts[0]
        prompt_text = processor.apply_chat_template(messages, add_generation_prompt=True, tokenize=False)
        
        if prompt_text in full_response:
            answer = full_response.split(prompt_text, 1)[-1].strip()
        elif text_content in full_response:
            answer = full_response.split(text_content, 1)[-1].strip()
        else:
            answer = full_response
        
        answer = answer.replace("Assistant:", "").replace("assistant:", "").strip()
        answer = answer.replace("<text>", "").replace("</text>", "").strip()
        answer = answer.replace("<|im_start|>", "").replace("<|im_end|>", "").strip()
        answer = answer.replace("<end_of_utterance>", "").strip()
        
        words = answer.split()
        if len(words) > 3:
            last_words = words[-3:]
            if len(set(last_words)) == 1 and len(words) > 10:
                for i in range(len(words) - 3, 0, -1):
                    if words[i:i+3] == last_words:
                        answer = " ".join(words[:i])
                        break
        
        answer = " ".join(answer.split())
        
        return answer

    
    def ocr_inference(self, image) -> str:
        if not self.is_loaded():
            self.load_model()

        model = self.get_model()
        processor = self.get_processor()

        text_content = "Extract all text from this image. Return only the text, no additional description."

        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "image"},
                    {"type": "text", "text": text_content}
                ]
            }
        ]

        prompt = processor.apply_chat_template(messages, add_generation_prompt=True, tokenize=False)
        inputs = processor(text=prompt, images=[image], return_tensors="pt")

        device = next(model.parameters()).device
        dtype = next(model.parameters()).dtype
        inputs = {k: v.to(device).to(dtype) if v.dtype.is_floating_point else v.to(device) 
                  for k, v in inputs.items()}

        with torch.no_grad():
            generated_ids = model.generate(
                **inputs,
                max_new_tokens=512,
                do_sample=False,
                temperature=0.7,
                repetition_penalty=1.2,
                pad_token_id=processor.tokenizer.pad_token_id,
                eos_token_id=processor.tokenizer.eos_token_id
            )

        generated_texts = processor.batch_decode(
            generated_ids,
            skip_special_tokens=True
        )

        full_response = generated_texts[0]
        prompt_text = processor.apply_chat_template(messages, add_generation_prompt=True, tokenize=False)
        
        if prompt_text in full_response:
            text = full_response.split(prompt_text, 1)[-1].strip()
        elif text_content in full_response:
            text = full_response.split(text_content, 1)[-1].strip()
        else:
            text = full_response
        
        text = text.replace("Assistant:", "").replace("assistant:", "").strip()
        text = text.replace("<text>", "").replace("</text>", "").strip()
        text = text.replace("<|im_start|>", "").replace("<|im_end|>", "").strip()
        text = text.replace("<end_of_utterance>", "").strip()
        
        words = text.split()
        if len(words) > 3:
            last_words = words[-3:]
            if len(set(last_words)) == 1 and len(words) > 10:
                for i in range(len(words) - 3, 0, -1):
                    if words[i:i+3] == last_words:
                        text = " ".join(words[:i])
                        break
        
        lines = [line.strip() for line in text.split('\n') if line.strip()]
        text = '\n'.join(lines)
        
        return text
