# 🚀 Railway Production Environment Setup

## 📋 Required Environment Variables

Railway dashboard'da bu environment variable'ları ayarlamanız gerekiyor:

### 🤖 AI Features (OpenAI)
```
OPENAI_API_KEY=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
```

### 🗄️ Database
```
MONGO_URL=mongodb+srv://rotauser:Ccpp1144@rota-crm-cluster.6f2phik.mongodb.net/rotacrm?retryWrites=true&w=majority&appName=rota-crm-cluster
DB_NAME=rotacrm
```

### 🔐 Authentication
```
CLERK_SECRET_KEY=sk_test_9Waffz0EiZ21rH9N3qXwGKKSTgTWvmb0CQXllZ1tLg
CLERK_JWKS_URL=https://adapting-eft-6.clerk.accounts.dev/.well-known/jwks.json
```

### 📧 Email Service
```
GMAIL_USER=rotadanismanlikbildirimsistemi@gmail.com
GMAIL_PASSWORD=czdm oixx uwyp kvns
```

### 📁 File Storage
```
SUPABASE_URL=https://umqfbkbwdaltduwsbsjt.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVtcWZia2J3ZGFsdGR1d3Nic2p0Iiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTEwMDkyMDUsImV4cCI6MjA2NjU4NTIwNX0.gvUjswTi2GrfG2sjPckLMNLYeMNbM89b9eHrENoEIEg
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InVtcWZia2J3ZGFsdGR1d3Nic2p0Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc1MTAwOTIwNSwiZXhwIjoyMDY2NTg1MjA1fQ.yu-knALlj1ejSknW3KKVIPkPjzU-SMhFzqVV7t-G4vg
SUPABASE_BUCKET=documents
```

## 🔧 Railway Deployment Steps

1. **Railway Dashboard'a gidin**: https://railway.app
2. **Project'i seçin**: Rota-CRM project
3. **Settings > Variables** seçin
4. **Yukarıdaki tüm variable'ları ekleyin**
5. **Deploy** butonuna basın

## ✅ Verification

Deployment sonrası test edin:
- `/api/ai/test` endpoint'i çalışmalı
- AI önerileri aktif olmalı
- Sürdürülebilirlik raporu AI metinleri üretebi

## 🚨 Güvenlik Notları

- API key'leri asla public repo'ya commit etmeyin
- Railway environment variables güvenli şekilde saklanır
- Bu dosyayı da public repo'ya eklemeyin