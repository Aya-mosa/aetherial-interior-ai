# ✦ Aetherial — Setup Guide (Windows)

## المتطلبات
- Python 3.10+ ✅ (عندك)
- Node.js 18+ → تحميل من https://nodejs.org
- Git (اختياري)

---

## Step 1 — الـ Backend

### 1.1 افتح `.env` وحط الـ API Key
```
backend\.env
```
غير السطر ده:
```
GEMINI_API_KEY=PASTE_YOUR_KEY_HERE
```
← الـ key بتاع Gemini من: https://aistudio.google.com/app/apikey

### 1.2 شغّل الـ Backend
افتح PowerShell في folder المشروع:
```powershell
cd aetherial-interior-ai\backend
uvicorn main:app --reload --port 8000
```

✅ هتشوف:
```
INFO: Uvicorn running on http://127.0.0.1:8000
```

API Docs متاحة على: http://localhost:8000/docs

---

## Step 2 — الـ Frontend

افتح **PowerShell تانية** (ابقى في نفس الـ folder الأصلي):
```powershell
cd aetherial-interior-ai\frontend
npm install
npm run dev
```

✅ هتشوف:
```
▲ Next.js 14.2.3
- Local: http://localhost:3000
```

---

## Step 3 — افتح المشروع

افتح: **http://localhost:3000** 🎉

---

## الـ HuggingFace Space (عشان الـ Rendering الحقيقي)

لو عايزة صور حقيقية بـ SDXL + ControlNet:

1. اعملي Space جديد على https://huggingface.co/spaces
2. استخدمي نموذج زي `lllyasviel/ControlNet-v1-1-nightly` أو `diffusers/controlnet-canny-sdxl-1.0`
3. حطي الـ Space URL في `.env`:
```
HF_SPACE_URL=https://your-username-space-name.hf.space
```

---

## مشاكل شائعة

### `GEMINI_API_KEY` error
← حطي الـ key الصح في `backend\.env`

### `npm: command not found`
← حملي Node.js من https://nodejs.org وأعيدي تشغيل PowerShell

### Port 8000 busy
```powershell
uvicorn main:app --reload --port 8001
```
وغيري في `frontend\.env.local`:
```
NEXT_PUBLIC_API_URL=http://localhost:8001
```

### CORS error في الـ browser
← تأكدي إن الـ backend شغال على port 8000 والـ frontend على 3000

---

## ملاحظة عن الـ Dependencies

الـ `pip install` هيشغل عادي رغم الـ warnings — دي مجرد conflict مع باكدجز تانية على جهازك (google-adk, streamlit) مش علاقتها بالمشروع.
