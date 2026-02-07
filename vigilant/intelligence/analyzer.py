from __future__ import annotations

from vigilant.core.runtime import require_cli
require_cli()

import json
import math
import re
from pathlib import Path
from typing import Any, Optional

import requests

from vigilant.core.config import config
from vigilant.core.logger import logger, short_path

class AIAnalyzer:
    def __init__(self):
        self.base_url = config.OLLAMA_URL
        self.filter_model = config.AI_FILTER_MODEL
        self.analysis_model = config.AI_ANALYSIS_MODEL
        self.report_model = config.AI_REPORT_MODEL
        self.embed_model = config.AI_EMBED_MODEL
        self._session = requests.Session()
        self._prompt_embedding_cache: dict[str, list[float]] = {}
        self._yolo_model = None
        self._yolo_ready: Optional[bool] = None

        self._default_filter_prompt = (
            "Analiza la imagen y decide si cumple el criterio.\n"
            "Criterio: {prompt}\n"
            "Responde SOLO en JSON con: match (yes/no), confidence (0-100), detail (<=8 palabras)."
        )
        self._default_analysis_prompt = (
            "Analiza la imagen con criterio forense.\n"
            "Objetivo: {prompt}\n"
            "Describe lo relevante y por qué coincide. Usa 2-4 oraciones en español."
        )
        self._default_report_prompt = (
            "Redacta un informe profesional en español con estilo juridico.\n"
            "\n"
            "FORMATO OBLIGATORIO (Markdown):\n"
            "Hechos Observables:\n"
            "- ...\n"
            "\n"
            "Coincidencias relevantes:\n"
            "- ...\n"
            "\n"
            "Observaciones:\n"
            "- ...\n"
            "\n"
            "Limitaciones:\n"
            "- ...\n"
            "\n"
            "Reglas:\n"
            "- Usa SOLO esas 4 secciones (exactas).\n"
            "- Bajo cada seccion, usa SOLO bullets que comiencen con \"- \" (no parrafos).\n"
            "- No inventes datos. No asumas direcciones, marcas, matriculas, etc.\n"
            "- No incluyas duraciones ni tiempos exactos (HH:MM:SS); si es necesario, indica \"timestamp aproximado\".\n"
            "- Manten cada bullet breve (1-2 oraciones).\n"
            "\n"
            "Objeto de busqueda: {prompt}\n"
            "\n"
            "Base tu redaccion solo en estos registros (pueden contener timestamps aproximados):\n"
            "{items}\n"
        )
        self._default_report_system = "Eres un redactor juridico especializado en evidencia audiovisual."

    def _render_prompt(self, template: str, **kwargs: Any) -> str:
        class SafeDict(dict):
            def __missing__(self, key: str) -> str:
                return "{" + key + "}"
        return template.format_map(SafeDict(**kwargs))

    def _init_yolo(self) -> bool:
        if self._yolo_ready is not None:
            return self._yolo_ready
        try:
            from ultralytics import YOLO
        except Exception:
            logger.error("yolo no disponible (ultralytics no instalado)")
            self._yolo_ready = False
            return False

        if not config.YOLO_MODEL:
            logger.error("yolo no configurado (VIGILANT_YOLO_MODEL vacio)")
            self._yolo_ready = False
            return False

        model_path = Path(config.YOLO_MODEL)
        if not model_path.exists():
            logger.error(f"yolo modelo no encontrado path={short_path(model_path)}")
            self._yolo_ready = False
            return False

        try:
            self._yolo_model = YOLO(str(model_path))
            self._yolo_ready = True
            return True
        except Exception as e:
            logger.error(f"yolo init fallo err={e}")
            self._yolo_ready = False
            return False

    def check_yolo(self) -> bool:
        return self._init_yolo()
        
    def check_connection(self) -> bool:
        try:
            resp = self._session.get(f"{self.base_url}/api/tags", timeout=3)
            return resp.status_code == 200
        except requests.exceptions.RequestException:
            return False
    
    def check_models(self) -> tuple[bool, str]:
        """
        Verifica que todos los modelos necesarios estén disponibles en Ollama.
        
        Returns:
            tuple[bool, str]: (success, detail_message)
        """
        try:
            resp = self._session.get(f"{self.base_url}/api/tags", timeout=5)
            resp.raise_for_status()
            data = resp.json()
            
            # Extract model names from response
            available_models = []
            for model in data.get("models", []):
                name = model.get("name", "")
                if name:
                    available_models.append(name)
            
            # Check required models
            required = [self.filter_model, self.analysis_model, self.report_model]
            if config.AI_USE_EMBEDDINGS:
                required.append(self.embed_model)
            
            missing = []
            for model in required:
                if model not in available_models:
                    missing.append(model)
            
            if missing:
                models_str = ", ".join(missing)
                return False, f"faltantes: {models_str}"
            
            return True, "ok"
            
        except Exception as e:
            return False, f"error: {e}"

    def _generate(
        self,
        prompt: str,
        model: str,
        images: Optional[list[str]] = None,
        system: Optional[str] = None,
        options: Optional[dict[str, Any]] = None,
        timeout: int = 180,
    ) -> str:
        url = f"{self.base_url}/api/generate"
        payload: dict[str, Any] = {
            "model": model,
            "prompt": prompt,
            "stream": False,
        }
        if images:
            payload["images"] = images
        if system:
            payload["system"] = system
        if options:
            payload["options"] = options

        resp = self._session.post(url, json=payload, timeout=timeout)
        resp.raise_for_status()
        result = resp.json()
        return result.get("response", "").strip()

    def _embeddings(self, text: str, timeout: int = 60) -> Optional[list[float]]:
        if not text:
            return None
        url = f"{self.base_url}/api/embeddings"
        payload = {"model": self.embed_model, "prompt": text}
        try:
            resp = self._session.post(url, json=payload, timeout=timeout)
            resp.raise_for_status()
            result = resp.json()
            embedding = result.get("embedding")
            if isinstance(embedding, list):
                return [float(x) for x in embedding]
            return None
        except Exception as e:
            logger.error(f"embeddings fallo err={e}")
            return None

    def _cosine_similarity(self, a: list[float], b: list[float]) -> float:
        if not a or not b or len(a) != len(b):
            return 0.0
        dot = sum(x * y for x, y in zip(a, b))
        norm_a = math.sqrt(sum(x * x for x in a))
        norm_b = math.sqrt(sum(x * x for x in b))
        if norm_a == 0.0 or norm_b == 0.0:
            return 0.0
        return dot / (norm_a * norm_b)

    def _extract_json(self, text: str) -> Optional[dict[str, Any]]:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return None
        try:
            return json.loads(text[start : end + 1])
        except json.JSONDecodeError:
            return None

    def _parse_yes_no(self, text: str) -> bool:
        if not text:
            return False
        upper = text.strip().upper()
        if upper.startswith("YES"):
            return True
        if upper.startswith("NO"):
            return False
        return "YES" in upper and "NO" not in upper

    def _yolo_class_indices_from_prompt(self, prompt: str) -> Optional[list[int]]:
        if not self._yolo_model:
            return None

        names = self._yolo_model.names
        if isinstance(names, dict):
            name_to_id = {str(v).lower(): int(k) for k, v in names.items()}
        else:
            name_to_id = {str(v).lower(): int(k) for k, v in enumerate(names)}

        prompt_lower = prompt.lower()
        synonyms = {
            "car": ["car", "auto", "automovil", "vehiculo", "vehicle"],
            "person": ["person", "persona", "hombre", "mujer"],
            "truck": ["truck", "camion"],
            "bus": ["bus", "colectivo", "omnibus"],
            "motorcycle": ["motorcycle", "moto", "motocicleta"],
            "bicycle": ["bicycle", "bicicleta", "bike"],
            "dog": ["dog", "perro"],
            "cat": ["cat", "gato"],
        }
        class_names = []
        for key, terms in synonyms.items():
            if any(term in prompt_lower for term in terms):
                class_names.append(key)

        if not class_names and config.YOLO_CLASSES:
            if isinstance(config.YOLO_CLASSES, list):
                class_names = [str(c).strip().lower() for c in config.YOLO_CLASSES if str(c).strip()]
            else:
                class_names = [c.strip().lower() for c in str(config.YOLO_CLASSES).split(",") if c.strip()]

        if not class_names:
            return None

        indices = []
        for name in class_names:
            if name.isdigit():
                indices.append(int(name))
                continue
            idx = name_to_id.get(name)
            if idx is not None:
                indices.append(idx)
        return indices or None

    def yolo_match(self, image_path: Path, prompt: str) -> dict:
        if not self._init_yolo() or self._yolo_model is None:
            return {
                "match": False,
                "confidence": 0.0,
                "detail": "YOLO no disponible",
                "raw": "",
                "image_path": str(image_path),
            }

        class_indices = self._yolo_class_indices_from_prompt(prompt)
        try:
            results = self._yolo_model.predict(
                source=str(image_path),
                conf=config.YOLO_CONFIDENCE,
                iou=config.YOLO_IOU,
                imgsz=config.YOLO_IMG_SIZE,
                device=config.YOLO_DEVICE,
                classes=class_indices,
                verbose=False,
            )
            if not results:
                return {
                    "match": False,
                    "confidence": 0.0,
                    "detail": "sin detecciones",
                    "raw": "",
                    "image_path": str(image_path),
                }

            result = results[0]
            boxes = getattr(result, "boxes", None)
            if boxes is None or len(boxes) == 0:
                return {
                    "match": False,
                    "confidence": 0.0,
                    "detail": "sin detecciones",
                    "raw": "",
                    "image_path": str(image_path),
                }

            detections = []
            max_conf = 0.0
            cls_list = []
            try:
                for i in range(len(boxes)):
                    conf = float(boxes.conf[i])
                    max_conf = max(max_conf, conf)
                    cls_id = int(boxes.cls[i])
                    cls_list.append(cls_id)
                    xyxy = [float(v) for v in boxes.xyxy[i].tolist()]
                    detections.append({"cls_id": cls_id, "conf": conf, "xyxy": xyxy})
            except Exception:
                detections = []

            counts: dict[str, int] = {}
            names = self._yolo_model.names
            for cls_id in cls_list:
                if isinstance(names, dict):
                    name = str(names.get(cls_id, cls_id))
                else:
                    name = str(names[cls_id]) if cls_id < len(names) else str(cls_id)
                counts[name] = counts.get(name, 0) + 1
            detail = ", ".join(f"{name}({count})" for name, count in counts.items()) or "detecciones"

            return {
                "match": True,
                "confidence": max_conf,
                "detail": detail,
                "detections": detections,
                "raw": "",
                "image_path": str(image_path),
            }
        except Exception as e:
            logger.error(f"yolo fallo path={short_path(image_path)} err={e}")
            return {
                "match": False,
                "confidence": 0.0,
                "detail": "Error",
                "raw": "",
                "image_path": str(image_path),
            }

    def quick_match(self, image_path: Path, prompt: str) -> dict:
        """
        Fast filter pass. Returns match flag, confidence (0-1), and short detail.
        """
        import base64

        template = config.AI_PROMPT_FILTER.strip() or self._default_filter_prompt
        full_prompt = self._render_prompt(template, prompt=prompt)

        with open(image_path, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode("utf-8")

        try:
            response_text = self._generate(
                prompt=full_prompt,
                model=self.filter_model,
                images=[img_b64],
                options={
                    "num_predict": config.AI_FILTER_MAX_TOKENS,
                    "temperature": 0.0,
                },
            )

            parsed = self._extract_json(response_text) or {}
            match_raw = str(parsed.get("match", "")).strip().lower()
            match = match_raw in ("yes", "true", "si", "sí")
            if not match_raw:
                match = self._parse_yes_no(response_text)

            confidence_found = False
            confidence_val = parsed.get("confidence")
            if isinstance(confidence_val, (int, float)):
                confidence = max(0.0, min(1.0, float(confidence_val) / 100.0))
                confidence_found = True
            else:
                match_conf = re.search(r"confidence\s*[:=]\s*(\d{1,3})", response_text, re.I)
                if match_conf:
                    confidence = max(0.0, min(1.0, int(match_conf.group(1)) / 100.0))
                    confidence_found = True
                else:
                    confidence = 0.0

            if match and not confidence_found:
                confidence = 1.0

            detail = str(parsed.get("detail", "")).strip()
            if not detail:
                detail = response_text[:120]

            return {
                "match": match,
                "confidence": confidence,
                "detail": detail,
                "raw": response_text,
                "image_path": str(image_path),
            }
        except Exception as e:
            logger.error(f"prefiltro fallo path={short_path(image_path)} err={e}")
            return {
                "match": False,
                "confidence": 0.0,
                "detail": "Error",
                "raw": "",
                "image_path": str(image_path),
            }

    def deep_analyze(self, image_path: Path, prompt: str) -> dict:
        """
        Detailed analysis for matched frames.
        """
        import base64

        template = config.AI_PROMPT_ANALYSIS.strip() or self._default_analysis_prompt
        full_prompt = self._render_prompt(template, prompt=prompt)

        with open(image_path, "rb") as f:
            img_b64 = base64.b64encode(f.read()).decode("utf-8")

        try:
            response_text = self._generate(
                prompt=full_prompt,
                model=self.analysis_model,
                images=[img_b64],
                options={
                    "num_predict": config.AI_ANALYSIS_MAX_TOKENS,
                    "temperature": 0.2,
                },
                timeout=240,
            )
            return {
                "text": response_text,
                "image_path": str(image_path),
            }
        except Exception as e:
            logger.error(f"analisis profundo fallo path={short_path(image_path)} err={e}")
            return {"text": "Error", "image_path": str(image_path)}

    def prompt_similarity(self, prompt: str, text: str) -> Optional[float]:
        if not config.AI_USE_EMBEDDINGS:
            return None
        if prompt not in self._prompt_embedding_cache:
            prompt_emb = self._embeddings(prompt)
            if prompt_emb is None:
                return None
            self._prompt_embedding_cache[prompt] = prompt_emb
        prompt_emb = self._prompt_embedding_cache[prompt]
        text_emb = self._embeddings(text)
        if text_emb is None:
            return None
        return self._cosine_similarity(prompt_emb, text_emb)

    def generate_report(self, prompt: str, items: list[dict[str, Any]]) -> str:
        if not items:
            return "No se detectaron coincidencias suficientes para elaborar un informe."

        # Limit prompt size for report model
        items_sorted = sorted(
            items,
            key=lambda x: (x.get("confidence", 0.0), x.get("similarity", 0.0)),
            reverse=True,
        )
        items_sorted = items_sorted[: config.AI_REPORT_MAX_ITEMS]

        lines = []
        for item in items_sorted:
            video = item.get("video", "desconocido")
            timestamp = item.get("timestamp", "s/d")
            detail = item.get("detail", "")
            analysis = item.get("analysis", "")
            lines.append(f"- Video: {video} | Tiempo: {timestamp} | Detalle: {detail} | Analisis: {analysis}")

        items_text = "\n".join(lines)
        report_template = config.AI_PROMPT_REPORT.strip() or self._default_report_prompt
        report_prompt = self._render_prompt(report_template, prompt=prompt, items=items_text)

        system = config.AI_PROMPT_REPORT_SYSTEM.strip() or self._default_report_system

        try:
            return self._generate(
                prompt=report_prompt,
                model=self.report_model,
                system=system,
                options={"num_predict": config.AI_REPORT_MAX_TOKENS, "temperature": 0.2},
                timeout=240,
            )
        except Exception as e:
            logger.error(f"reporte fallo err={e}")
            return "No se pudo generar el informe."
