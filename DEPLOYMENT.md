# دليل الديبلوي — Aetherial (مجاني بالكامل)

الخطة: **Backend على Render (بـ Docker)** + **Frontend على Vercel (بدون Docker)**.

---

## 0. قبل ما تبدئي

- ارفعي المشروع على GitHub (repo واحد فيه فولدر `backend` و `frontend`)، لو لسه مش مرفوع.
- تأكدي إن `.env` الحقيقي (فيه الـ API keys بتاعتك) **مش متضاف** على GitHub — هو أصلاً متجاهل في `.gitignore`. متنسيش تحطي المفاتيح يدوي في Render بعدين.

---

## 1. Backend على Render

1. ادخلي https://render.com واعملي حساب (فيه Free tier كفاية للعرض).
2. من الـ Dashboard: **New → Web Service**.
3. اختاري الـ GitHub repo بتاعك.
4. الإعدادات:
   - **Root Directory:** `backend`
   - **Runtime:** Docker (هيكتشف الـ `Dockerfile` اللي عملناه تلقائي)
   - **Instance Type:** Free
5. من تبويب **Environment**، ضيفي المتغيرات دي (زي اللي في `.env.example`):
   ```
   GEMINI_API_KEY=...
   OPENROUTER_API_KEY=...
   HUGGINGFACE_API_KEY=...
   GEMINI_MODEL=gemini-2.0-flash
   APP_ENV=production
   SECRET_KEY=... (أي نص عشوائي طويل)
   ```
   FRONTEND_URL هتضيفيها بعد ما تاخدي رابط Vercel في الخطوة الجاية (سيبيها فاضية دلوقتي أو ارجعيلها بعدين).
6. دوسي **Create Web Service**. أول build هياخد كذا دقيقة.
7. بعد ما يخلص، هتاخدي رابط زي: `https://aetherial-backend.onrender.com`
   - جربيه: `https://aetherial-backend.onrender.com/api/health` المفروض يرجع استجابة.

**ملحوظة:** الخطة المجانية بتنام بعد 15 دقيقة من غير استخدام، وأول طلب بعدها بياخد ٣٠-٦٠ ثانية عشان يصحى. لو هتعرضي المشروع قدام الدكاترة، افتحي الرابط قبل العرض بشوية عشان "يصحى" الأول.

---

## 2. Frontend على Vercel

1. https://vercel.com → اعملي حساب واربطي GitHub.
2. **Add New → Project** → اختاري نفس الـ repo.
3. الإعدادات:
   - **Root Directory:** `frontend`
   - Framework: Next.js (هيتكتشف تلقائي، مش محتاجة Docker خالص هنا)
4. من **Environment Variables** ضيفي:
   ```
   NEXT_PUBLIC_API_URL=https://aetherial-backend.onrender.com
   ```
   (نفس رابط الـ backend من الخطوة اللي فاتت)
5. **Deploy**. هتاخدي رابط زي: `https://aetherial-xxxx.vercel.app`

---

## 3. اربطي الاتجاهين ببعض

ارجعي لـ Render → Environment → ضيفي:
```
FRONTEND_URL=https://aetherial-xxxx.vercel.app
```
واعملي **Manual Deploy → Redeploy** عشان الـ backend يقبل طلبات من رابط Vercel (CORS).

---

## 4. جربي كل حاجة

افتحي رابط الـ Vercel، وجربي إنك ترفعي صورة/تعملي تصميم، وشوفي إن الـ history والصور بترجع صح.

---

## ملحوظات مهمة للعرض قدام الدكاترة

- **البيانات مش دايمة**: أي إعادة نشر (redeploy) أو إعادة تشغيل للـ backend على Render المجاني ممكن تمسح `history.db` والصور القديمة (لأن التخزين مؤقت/ephemeral). ده مقبول تماماً لعرض تجريبي.
- **Cold start**: زي ما قلنا، افتحي رابط الـ backend شوية قبل العرض عشان يصحى.
- **للتجربة محلياً قبل الرفع** (اختياري، لو عندك Docker على جهازك):
  ```bash
  docker compose up --build
  ```
  ده هيشغل الـ backend على `localhost:8000` والـ frontend على `localhost:3000` مع بعض، عشان تتأكدي إن كل حاجة شغالة قبل ما تعملي deploy فعلي.

---

## لو حبيتي تخليها production أكتر بعدين

لو قررتي إن المشروع مش هيفضل بس للعرض وعاوزة البيانات تفضل محفوظة دايماً، وقتها هنحتاج:
- قاعدة بيانات خارجية مجانية (Supabase / Neon - Postgres) بدل SQLite المحلي
- تخزين خارجي للصور (Cloudflare R2 مجاني حتى 10GB)

ده تعديل إضافي في الكود، قوليلي لو وصلتي للمرحلة دي وهنعمله.
