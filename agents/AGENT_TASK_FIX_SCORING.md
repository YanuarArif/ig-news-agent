# Agent Task: Fix LLM Scoring Pipeline

## Objective
Implement 3 fixes to resolve JSON parse errors, reduce API calls, and add heuristic fallback:

1. **JSON Mode** - Enforce `response_format: {"type": "json_object"}` for all LLM calls
2. **Batch Scoring** - Process 5 items per LLM call (configurable via `SCORING_BATCH_SIZE`)
3. **Heuristic Fallback** - Keyword-based scoring when LLM fails completely

---

## Files to Modify

| File | Priority | Changes |
|------|----------|---------|
| `src/scoring/llm_client.py` | HIGH | Add `response_format` param, batch method |
| `src/scoring/news_scorer.py` | HIGH | Batch scoring, heuristic fallback, retry logic |
| `src/scoring/heuristic_scorer.py` | NEW | New file: keyword-based scoring |
| `src/scoring/__init__.py` | LOW | Export new classes |
| `.env` | LOW | Add `SCORING_BATCH_SIZE=5` |

---

## 1. LLM Client - Add JSON Mode & Batch Support

**File:** `src/scoring/llm_client.py`

```python
# ADD to imports
from typing import Optional, List, Dict, Any

# MODIFY complete() method signature
def complete(
    self, 
    system_prompt: str, 
    user_prompt: str, 
    max_tokens: int = 1024,
    response_format: Optional[Dict[str, str]] = None,  # NEW
    temperature: float = 0.3
) -> str:

# Inside complete(), ADD to create() call:
response = self.client.chat.completions.create(
    model=self.model,
    max_tokens=max_tokens,
    temperature=temperature,
    messages=[
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ],
    response_format=response_format or {"type": "text"},  # DEFAULT text, JSON when requested
)

# ADD NEW METHOD for batch scoring
def complete_batch(
    self,
    system_prompt: str,
    user_prompt: str,
    max_tokens: int = 1500,
    response_format: Optional[Dict[str, str]] = None,
) -> str:
    """Batch version with higher token limit."""
    return self.complete(system_prompt, user_prompt, max_tokens, response_format, temperature=0.2)
```

**Key:** Default `response_format={"type": "text"}` for backward compat. Pass `{"type": "json_object"}` explicitly where needed.

---

## 2. Heuristic Scorer - New File

**File:** `src/scoring/heuristic_scorer.py` (CREATE NEW)

```python
"""Keyword-based heuristic scoring - zero API calls, fast fallback."""

import re
import logging
from dataclasses import dataclass
from typing import List, Dict
from src.scoring.news_scorer import ScoreResult

logger = logging.getLogger(__name__)

# Source credibility tiers (1-10)
SOURCE_CREDIBILITY = {
    # Tier 1: Major national (9-10)
    "cnn indonesia": 9, "tempo": 9, "kompas": 9, "detik": 8, "liputan6": 8,
    "antara": 9, " republika": 7, "suara": 7, "okezone": 6,
    # Tier 2: Regional/tech (6-8)
    "teknologi": 7, "tekno": 7, "gadget": 6,
    # Default
    "default": 5
}

# Viral trigger keywords (weight 0.5-2.0)
VIRAL_KEYWORDS = {
    "breaking": 2.0, "viral": 1.8, "shocking": 1.5, "exclusive": 1.5,
    "bocor": 1.8, "terungkap": 1.5, "rahasia": 1.3, "heboh": 1.5,
    "trending": 1.3, "wow": 1.0, "gempar": 1.5, "kaget": 1.0,
    "gratis": 1.2, "gratis!": 1.5, "cuma": 0.8, "gratisnya": 1.0,
    "dapat": 0.5, "menang": 0.8, "hadiah": 0.8, "bonus": 0.8,
    "anjur": 0.5, "waspada": 1.0, "bahaya": 1.2, "awas": 1.0,
}

# Clickbait / sensationalism patterns
CLICKBAIT_PATTERNS = [
    r"kamu tidak akan percaya", r"nggak akan nyangka", r"bikin ngakak",
    r"bikin terharu", r"bikin ketar-ketir", r"hanya \d+ orang",
    r"rahasia .*? diungkap", r"fakta mengejutkan", r"!!!+",
]

SENSITIVE_KEYWORDS = {
    "sara": 10, "teror": 9, "bom": 9, "pembunuhan": 8, "bunuh diri": 9,
    "pelecehan": 8, "ksdr": 8, "radikal": 7, "ekstremis": 7,
    "bumil": 3, "bayi": 3, "anak": 2, "kematian": 5,
}

@dataclass
class HeuristicScorer:
    def score_batch(self, items: List[Dict]) -> List[ScoreResult]:
        """Score multiple items without LLM."""
        return [self.score_item(item) for item in items]

    def score_item(self, item: Dict) -> ScoreResult:
        title = item.get("title", "").lower()
        summary = item.get("summary", "").lower()
        source = item.get("source_name", "").lower()
        text = f"{title} {summary}"
        
        # 1. VIRAL POTENTIAL (1-10)
        viral = self._score_viral(title, text)
        
        # 2. CREDIBILITY (1-10)
        cred = self._score_credibility(source, text)
        
        # 3. SENSITIVITY (1-10)
        sens, is_sensitive = self._score_sensitivity(text)
        
        # 4. CROSS VERIFICATION - use existing (skip heuristic)
        cross_score = 0
        is_verified = False
        
        # 5. OVERALL
        overall = (
            viral * 0.35 +
            cred * 0.25 +
            (10 - sens) * 0.20 +
            cross_score * 0.20
        )
        
        return ScoreResult(
            viral_potential=viral,
            credibility_score=cred,
            sensitivity_score=sens,
            is_sensitive=is_sensitive,
            is_verified_multi_source=is_verified,
            cross_verification_score=cross_score,
            reasoning=f"Heuristic: viral={viral}, cred={cred}, sens={sens}",
            overall_score=round(overall, 2)
        )

    def _score_viral(self, title: str, text: str) -> int:
        score = 5  # base
        
        # Keyword boost
        for kw, weight in VIRAL_KEYWORDS.items():
            if kw in text:
                score += weight
        
        # Title length sweet spot (60-100 chars)
        if 60 <= len(title) <= 100:
            score += 1
        elif len(title) < 30:
            score -= 1
        
        # Numbers in title (listicles)
        if re.search(r"\b\d+\b", title):
            score += 0.5
        
        # Question mark = curiosity
        if "?" in title:
            score += 0.5
        
        return max(1, min(10, int(round(score))))

    def _score_credibility(self, source: str, text: str) -> int:
        # Source tier
        cred = SOURCE_CREDIBILITY.get(source, SOURCE_CREDIBILITY["default"])
        
        # Factual indicators
        factual_boost = 0
        if any(w in text for w in ["menurut", "data", "survei", "riset", "studi", "laporan", "resmi", "pemerintah", "kementerian", "polisi", "mabes"]):
            factual_boost += 1
        if re.search(r"\b\d{1,3}(?:[.,]\d{3})*(?:[.,]\d+)?\b", text):  # numbers with separators
            factual_boost += 0.5
        
        # Clickbait penalty
        clickbait_penalty = 0
        for pat in CLICKBAIT_PATTERNS:
            if re.search(pat, text):
                clickbait_penalty += 1.5
        
        final = cred + factual_boost - clickbait_penalty
        return max(1, min(10, int(round(final))))

    def _score_sensitivity(self, text: str) -> tuple[int, bool]:
        max_sens = 0
        for kw, weight in SENSITIVE_KEYWORDS.items():
            if kw in text:
                max_sens = max(max_sens, weight)
        
        is_sensitive = max_sens >= 7
        return max(1, min(10, max_sens)), is_sensitive


# Singleton
_heuristic_scorer = None

def get_heuristic_scorer() -> HeuristicScorer:
    global _heuristic_scorer
    if _heuristic_scorer is None:
        _heuristic_scorer = HeuristicScorer()
    return _heuristic_scorer
```

---

## 3. News Scorer - Batch + Fallback + Retry

**File:** `src/scoring/news_scorer.py` (REPLACE entire file)

```python
"""News scoring using LLM evaluation with batch + heuristic fallback."""

import json
import logging
import asyncio
import os
from dataclasses import dataclass
from typing import Optional, List, Dict, Any

from src.scoring.llm_client import LLMClient
from src.scoring.sensitivity_guard import check_sensitivity
from src.scoring.cross_verification import check_cross_verification
from src.scoring.heuristic_scorer import get_heuristic_scorer, HeuristicScorer

logger = logging.getLogger(__name__)

# Config
BATCH_SIZE = int(os.getenv("SCORING_BATCH_SIZE", "5"))
MAX_RETRIES = 2
BATCH_DELAY_SECONDS = 2


@dataclass
class ScoreResult:
    """Structured scoring result for a news item."""
    viral_potential: int          # 1-10
    credibility_score: int        # 1-10
    sensitivity_score: int        # 1-10
    is_sensitive: bool
    is_verified_multi_source: bool
    cross_verification_score: int # 1-10
    reasoning: str
    overall_score: float

    def passes_threshold(self, viral_thresh: int = 7, cred_thresh: int = 6) -> bool:
        return (
            self.viral_potential >= viral_thresh and
            self.credibility_score >= cred_thresh and
            not self.is_sensitive
        )

    def to_dict(self) -> dict:
        return {
            "viral_potential": self.viral_potential,
            "credibility_score": self.credibility_score,
            "sensitivity_score": self.sensitivity_score,
            "is_sensitive": self.is_sensitive,
            "is_verified_multi_source": self.is_verified_multi_source,
            "cross_verification_score": self.cross_verification_score,
            "reasoning": self.reasoning,
            "overall_score": self.overall_score,
        }


class NewsScorer:
    """Score news items using LLM with batch + heuristic fallback."""

    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.llm_client = llm_client or LLMClient()
        self.heuristic = get_heuristic_scorer()

    def score_batch(self, items: List[Dict]) -> List[ScoreResult]:
        """Score multiple items in batches of BATCH_SIZE."""
        results = []
        
        for i in range(0, len(items), BATCH_SIZE):
            batch = items[i:i + BATCH_SIZE]
            logger.info(f"Scoring batch {i//BATCH_SIZE + 1}: {len(batch)} items")
            
            batch_results = self._score_batch_with_retry(batch)
            results.extend(batch_results)
            
            # Delay between batches to avoid rate limit
            if i + BATCH_SIZE < len(items):
                asyncio.run(asyncio.sleep(BATCH_DELAY_SECONDS))
        
        return results

    def _score_batch_with_retry(self, batch: List[Dict]) -> List[ScoreResult]:
        """Try LLM batch scoring with retries, fallback to heuristic."""
        last_error = None
        
        for attempt in range(MAX_RETRIES + 1):
            try:
                return self._llm_batch_score(batch)
            except (json.JSONDecodeError, ValueError, KeyError) as e:
                last_error = e
                logger.warning(f"LLM batch attempt {attempt + 1} failed: {e}")
                if attempt < MAX_RETRIES:
                    asyncio.run(asyncio.sleep(2 ** attempt))  # exponential backoff
            except Exception as e:
                last_error = e
                logger.error(f"LLM batch unexpected error: {e}")
                break
        
        # All retries failed -> heuristic fallback
        logger.warning(f"LLM batch failed after {MAX_RETRIES + 1} attempts, using heuristic fallback: {last_error}")
        return self._heuristic_fallback(batch)

    def _llm_batch_score(self, batch: List[Dict]) -> List[ScoreResult]:
        """Single LLM call for multiple items with JSON mode."""
        prompt = self._build_batch_prompt(batch)
        system_prompt = (
            "You are an expert social media editor scoring news for Instagram. "
            "Be objective and strict. Output ONLY valid JSON."
        )
        
        # JSON MODE - forces valid JSON output
        response = self.llm_client.complete(
            system_prompt=system_prompt,
            user_prompt=prompt,
            max_tokens=1500,
            response_format={"type": "json_object"},  # KEY FIX
            temperature=0.2,
        )
        
        # Parse JSON response
        data = json.loads(response)
        scores = data.get("scores", [])
        
        if len(scores) != len(batch):
            raise ValueError(f"LLM returned {len(scores)} scores for {len(batch)} items")
        
        results = []
        for item, score_data in zip(batch, scores):
            # Cross-verification (existing, non-LLM)
            cross_verif = check_cross_verification(
                item.get("title", ""),
                item.get("source_name", "")
            )
            sensitivity = check_sensitivity(
                item.get("title", "") + " " + item.get("summary", "")
            )
            
            viral = int(score_data.get("viral_potential", 5))
            cred = int(score_data.get("credibility_score", 5))
            
            overall = (
                viral * 0.35 +
                cred * 0.25 +
                (10 - sensitivity.sensitivity_score) * 0.20 +
                cross_verif.cross_verification_score * 0.20
            )
            
            results.append(ScoreResult(
                viral_potential=viral,
                credibility_score=cred,
                sensitivity_score=sensitivity.sensitivity_score,
                is_sensitive=sensitivity.is_sensitive,
                is_verified_multi_source=cross_verif.is_verified,
                cross_verification_score=cross_verif.cross_verification_score,
                reasoning=score_data.get("reasoning", "LLM batch scoring"),
                overall_score=round(overall, 2)
            ))
            
            logger.info(
                f"✓ Batch scored '{item.get('title', '')[:50]}': "
                f"viral={viral} cred={cred} sens={sensitivity.sensitivity_score} "
                f"overall={overall:.1f}"
            )
        
        return results

    def _heuristic_fallback(self, batch: List[Dict]) -> List[ScoreResult]:
        """Fallback to keyword-based scoring."""
        results = []
        for item in batch:
            # Get heuristic base scores
            h_result = self.heuristic.score_item(item)
            
            # Still run cross-verification & sensitivity (fast, no LLM)
            cross_verif = check_cross_verification(
                item.get("title", ""),
                item.get("source_name", "")
            )
            sensitivity = check_sensitivity(
                item.get("title", "") + " " + item.get("summary", "")
            )
            
            # Override with actual cross-verif & sensitivity
            overall = (
                h_result.viral_potential * 0.35 +
                h_result.credibility_score * 0.25 +
                (10 - sensitivity.sensitivity_score) * 0.20 +
                cross_verif.cross_verification_score * 0.20
            )
            
            results.append(ScoreResult(
                viral_potential=h_result.viral_potential,
                credibility_score=h_result.credibility_score,
                sensitivity_score=sensitivity.sensitivity_score,
                is_sensitive=sensitivity.is_sensitive,
                is_verified_multi_source=cross_verif.is_verified,
                cross_verification_score=cross_verif.cross_verification_score,
                reasoning=f"Heuristic fallback: {h_result.reasoning}",
                overall_score=round(overall, 2)
            ))
            
            logger.info(
                f"⚠ Heuristic '{item.get('title', '')[:50]}': "
                f"viral={h_result.viral_potential} cred={h_result.credibility_score} "
                f"sens={sensitivity.sensitivity_score} overall={overall:.1f}"
            )
        
        return results

    def _build_batch_prompt(self, batch: List[Dict]) -> str:
        """Build prompt for batch scoring."""
        items_json = []
        for idx, item in enumerate(batch):
            items_json.append({
                "id": idx + 1,
                "title": item.get("title", ""),
                "summary": item.get("summary", "")[:300],
                "source": item.get("source_name", "Unknown"),
                "category": item.get("category", "general"),
            })
        
        return f"""
Analyze these {len(batch)} news items for Instagram publishing potential.

Items:
{json.dumps(items_json, ensure_ascii=False, indent=2)}

Score each item 1-10 for:
1. VIRAL_POTENTIAL: Visual appeal, emotional hook, shareability on Instagram
2. CREDIBILITY: Source reputation, factual accuracy, journalistic quality

Output ONLY valid JSON:
{{
  "scores": [
    {{"id": 1, "viral_potential": N, "credibility_score": N, "reasoning": "..."}},
    {{"id": 2, "viral_potential": N, "credibility_score": N, "reasoning": "..."}}
  ]
}}
"""


# Convenience functions (backward compat)
_scorer_instance = None

def score_news(item: Dict) -> ScoreResult:
    """Score single item (uses batch internally)."""
    global _scorer_instance
    if _scorer_instance is None:
        _scorer_instance = NewsScorer()
    return _scorer_instance.score_batch([item])[0]

def score_batch(items: List[Dict]) -> List[ScoreResult]:
    """Score multiple items."""
    global _scorer_instance
    if _scorer_instance is None:
        _scorer_instance = NewsScorer()
    return _scorer_instance.score_batch(items)
```

---

## 4. Update .env

**File:** `.env` (ADD at end)

```env
# Scoring batch size (5 items per LLM call)
SCORING_BATCH_SIZE=5
```

---

## 5. Test & Verify

```bash
# 1. Type check
npx tsc --noEmit  # or: python -m py_compile src/scoring/news_scorer.py

# 2. Run pipeline once
cd C:\Users\yanua\Documents\Project_Serius\10-ig-news-agent\ig-news-agent
.venv\Scripts\activate
python -m scripts.run_pipeline_once
```

### Expected Log Output (SUCCESS)

```
16:27:23 | INFO | __main__ | [4/8] Scoring news items...
16:27:23 | INFO | __main__ | Converted 18 items to dicts for scoring
16:27:23 | INFO | src.scoring.news_scorer | Scoring batch 1: 5 items
16:27:28 | INFO | src.scoring.news_scorer | ✓ Batch scored 'Platform Mengalami...': viral=6 cred=7 sens=2 overall=6.1
16:27:28 | INFO | src.scoring.news_scorer | ✓ Batch scored 'Dunia Makin...': viral=5 cred=6 sens=1 overall=5.3
...
16:27:33 | INFO | src.scoring.news_scorer | Scoring batch 2: 5 items
...
16:27:38 | INFO | src.scoring.news_scorer | Scoring batch 3: 5 items
...
16:27:43 | INFO | src.scoring.news_scorer | Scoring batch 4: 3 items
...
16:27:48 | INFO | __main__ |   3 items passed scoring threshold  ← Should vary, not all 5/5
```

### Verification Checklist

- [ ] **Zero** `Unterminated string` / `Expecting value` errors
- [ ] **4 batches** for 18 items (not 18 individual calls)
- [ ] Scores **vary** (not all viral=5, cred=5)
- [ ] Viral scores ≥7 for genuinely viral topics
- [ ] Credibility ≥7 for Tempo/CNN/Detik sources
- [ ] Pipeline completes in **<30s** (was ~90s)
- [ ] `npx tsc --noEmit` passes

---

## Rollback Plan

If issues:
1. Revert `news_scorer.py` to original
2. Remove `heuristic_scorer.py`
3. Remove `response_format` from `llm_client.py`
4. Set `SCORING_BATCH_SIZE=1` in `.env`

---

## Notes for Agent

- **DO NOT** modify `summarizer.py` or `caption_writer.py` - they have same JSON issues but separate task
- **DO NOT** run `prisma generate` or `prisma db push` - database safety rule
- Use `asyncio.sleep()` not `time.sleep()` for async compatibility
- Keep `temperature=0.2` for scoring (more deterministic)
- Heuristic scorer is **intentionally simple** - keyword based, no external deps