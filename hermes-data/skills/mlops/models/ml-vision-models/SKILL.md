---
name: ml-vision-models
description: "ML vision model umbrella — covers image generation (Stable Diffusion), image segmentation (SAM), vision-language models (LLaVA, CLIP). Decision tree for selecting the right model, with links to specialized sub-skills."
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [Vision, Stable Diffusion, SAM, CLIP, LLaVA, Image Generation, Image Segmentation, Vision-Language, Multimodal]
---

# ML Vision Models — Umbrella

This umbrella covers four vision-related model families. Select the right model for your task.

## Decision Tree

```
What is your vision task?
├── Generate images from text
│   └── → Stable Diffusion (references/stable-diffusion.md)
│         Text-to-image, inpainting, image-to-image, LoRA fine-tuning.
├── Segment any object in an image (zero-shot)
│   └── → SAM — Segment Anything Model (references/sam.md)
│         Points, boxes, masks, automatic masks.
├── Connect images and text (classification/search)
│   └── → CLIP (references/clip.md)
│         Zero-shot image classification, image-text similarity.
└── Conversational image understanding
    └── → LLaVA (references/llava.md)
          Visual QA, multi-turn image chat, instruction following.
```

## Sub-Skill Reference

| Model | Task | Key Capability |
|-------|------|----------------|
| `references/stable-diffusion.md` | Image generation | Text-to-image, inpainting, LoRA, ControlNet |
| `references/sam.md` | Image segmentation | Zero-shot mask generation, point/box prompts |
| `references/clip.md` | Vision-language | Zero-shot classification, image-text retrieval |
| `references/llava.md` | Vision-language chat | Multi-turn VQA, instruction following |

## Absorbed Skills

The following skills have been absorbed into this umbrella (archived):
- `clip` → `references/clip.md`
- `segment-anything-model` → `references/sam.md`
- `stable-diffusion-image-generation` → `references/stable-diffusion.md`
- `llava` → `references/llava.md`

## When to Use Each

### Stable Diffusion
- Text-to-image generation
- Image-to-image translation
- Inpainting / outpainting
- LoRA fine-tuning for custom styles
- ControlNet-guided generation

### SAM (Segment Anything Model)
- Zero-shot object segmentation
- Interactive annotation (point/box prompts)
- Generating training data for detection models
- Medical/satellite image segmentation
- Automatic mask generation for all objects

### CLIP
- Zero-shot image classification (no training needed)
- Image-text similarity scoring
- Semantic image search
- Content moderation (NSFW detection)
- Cross-modal retrieval

### LLaVA
- Conversational image understanding
- Visual question answering
- Image description and captioning
- Multi-turn image dialogue
- Document understanding with images

## Common Patterns

### Zero-shot classification with CLIP
```python
from PIL import Image
import torch
from transformers import CLIPProcessor, CLIPModel

model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")

image = Image.open("photo.jpg")
text = ["a cat", "a dog", "a car"]
inputs = processor(text=text, images=image, return_tensors="pt", padding=True)
outputs = model(**inputs)
probs = outputs.logits_per_image.softmax(dim=1).T[0]
print(f"Best match: {text[probs.argmax()]}")
```

### Image generation with Stable Diffusion
```python
from diffusers import StableDiffusionPipeline
pipe = StableDiffusionPipeline.from_pretrained("runwayml/stable-diffusion-v1-5")
pipe.enable_model_cpu_offload()

image = pipe("a photo of a cat in a field", num_inference_steps=50).images[0]
```

### SAM automatic segmentation
```python
from segment_anything import sam_model_registry, SamAutomaticMaskGenerator
sam = sam_model_registry["vit_h"](checkpoint="sam_vit_h.pth").to("cuda")
mask_generator = SamAutomaticMaskGenerator(sam)
masks = mask_generator.generate(image)
```

### LLaVA image conversation
```python
from llava.model.builder import load_pretrained_model
tokenizer, model, image_processor, _ = load_pretrained_model("liuhaotian/llava-v1.5-7b", load_4bit=True)
# See references/llava.md for full multi-turn conversation pattern
```

## Resources

- **Stable Diffusion**: https://github.com/runwayml/stable-diffusion, https://huggingface.co/diffusers
- **SAM**: https://github.com/facebookresearch/segment-anything
- **CLIP**: https://github.com/openai/CLIP, https://laion-aai.github.io/2022/08/12/CLIP.html
- **LLaVA**: https://github.com/haotian-liu/LLaVA