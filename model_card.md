# Model Card — FoodLog AI

## Overview

FoodLog AI is a personal food logging web app that uses AI vision to automatically analyze meal photos and extract structured nutrition data.

---

## Model Details

| Field | Value |
|---|---|
| **Model** | Gemini 1.5 Flash |
| **Provider** | Google Generative AI |
| **Modality** | Multimodal (image + text → structured JSON) |
| **Access** | Google AI Studio API (free tier) |

---

## Inputs

| Input | Required | Description |
|---|---|---|
| Food image | ✅ Yes | JPEG, PNG, or WebP photo of a meal |
| User note | ❌ Optional | Free-text note, may include dish name, calories, or portion size |
| Timestamp | Auto | Captured at upload time; used for meal time inference |

---

## Outputs

The model returns a structured JSON object:

```json
{
  "dish": "chicken caesar salad",
  "estimated_calories": 520,
  "portion": "medium",
  "meal_time_guess": "lunch",
  "confidence": "high",
  "note_calories_explicit": null,
  "note_portion_explicit": null,
  "note_dish_explicit": null
}
```

---

## Intended Use

- **Primary use**: Personal, non-clinical food journaling and calorie awareness
- **Target users**: Individuals tracking their daily food intake casually
- **Deployment**: Local Streamlit app, single-user

---

## Out-of-Scope Uses

- ❌ Medical nutrition advice or clinical dietary planning
- ❌ Eating disorder treatment or monitoring
- ❌ Any use requiring certified nutritional accuracy
- ❌ Multi-user or production deployment without further review

---

## Limitations

| Limitation | Notes |
|---|---|
| Calorie estimates are approximations | Accuracy varies by dish complexity, plating, and lighting |
| Mixed dishes are harder to estimate | E.g. stews, salads with many components |
| Meal time inference may be wrong | Based on timestamp hour; does not account for timezone shifts or unusual schedules |
| Note parsing is best-effort | Free-text parsing relies on model interpretation, not deterministic rules |
| No memory across sessions | Each analysis is stateless; prior logs are not fed back to the model |

---

## Evaluation

This is a prototype. No formal evaluation has been conducted.

Informal testing shows:
- Common dishes (pizza, salad, pasta) identified correctly ~90% of the time
- Calorie estimates within ±150 kcal for standard portions of well-known dishes
- Explicit note values (e.g. "600 cal") are extracted reliably

---

## Ethical Considerations

- All data is stored **locally** on the user's machine — no images or notes are sent to any server other than the Google Generative AI API for inference
- Users should not rely on this app for medical or clinical nutrition decisions
- Calorie estimates should be treated as rough guides, not ground truth

---

## Dependencies

- `google-generativeai` — Gemini API client
- `streamlit` — UI framework
- `plotly` — Dashboard charts
- `Pillow` — Image preprocessing

---

*Last updated: April 2026*