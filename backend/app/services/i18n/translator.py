import json
from pathlib import Path
class TranslationService:
    def __init__(self, default_lang="pt-BR"):
        self.default_lang = default_lang; self.translations = {}; self._load()
    def _load(self):
        d = Path(__file__).parent.parent.parent / "i18n"
        for f in ["en.json", "pt-BR.json"]:
            fp = d / f; lang = f.replace(".json", "")
            if fp.exists():
                with open(fp, 'r', encoding='utf-8') as fh: self.translations[lang] = json.load(fh)
    def translate(self, key, lang=None, **kw):
        lang = lang or self.default_lang
        for l in [lang, self.default_lang, "en"]:
            if l in self.translations:
                val = self.translations[l]
                for part in key.split("."):
                    if isinstance(val, dict) and part in val: val = val[part]
                    else: val = None; break
                if val is not None: return val.format(**kw) if kw else val
        return key
    def get_all_translations(self, lang):
        return self.translations.get(lang, self.translations.get(self.default_lang, {}))
    def translate_solver_output(self, text, target_lang="pt-BR"):
        if target_lang == "en": return text
        term_map = {"Converged": "Convergiu", "Simulation complete": "Simulacao concluida", "density": "densidade",
            "velocity": "velocidade", "pressure": "pressao", "temperature": "temperatura", "viscosity": "viscosidade"}
        result = text
        for en, pt in term_map.items(): result = result.replace(en, pt)
        return result
