# Kalkulator API - DevOps LAB-03

Prosta aplikacja webowa zbudowana w FastAPI, służąca jako demonstracja podstawowego pipeline CI/CD z użyciem GitHub Actions i Azure Kubernetes Service.

## Funkcjonalność

Aplikacja udostępnia REST API kalkulatora z czterema operacjami matematycznymi:

| Endpoint | Metoda | Opis |
|---|---|---|
| `/health` | GET | Sprawdzenie stanu aplikacji |
| `/dodaj` | POST | Dodawanie dwóch liczb |
| `/odejmij` | POST | Odejmowanie dwóch liczb |
| `/mnoz` | POST | Mnożenie dwóch liczb |
| `/dziel` | POST | Dzielenie dwóch liczb (obsługa dzielenia przez zero) |

### Przykłady użycia

```bash
# Sprawdzenie stanu aplikacji
curl http://<EXTERNAL-IP>/health

# Dodawanie
curl -X POST http://<EXTERNAL-IP>/dodaj \
  -H "Content-Type: application/json" \
  -d '{"a": 10, "b": 5}'
# {"wynik": 15.0}

# Dzielenie przez zero
curl -X POST http://<EXTERNAL-IP>/dziel \
  -H "Content-Type: application/json" \
  -d '{"a": 10, "b": 0}'
# {"detail": "Dzielenie przez zero"}
```

Interaktywna dokumentacja API dostępna pod adresem: `http://<EXTERNAL-IP>/docs`

## Architektura

```
GitHub Repo
    │
    │  (Build + Test + Push)
    ▼
Azure Container Registry ──── (kubectl set image — ręcznie) ────▶ Azure Kubernetes Service
```

Pipeline GitHub Actions automatycznie:
1. Uruchamia testy jednostkowe
2. Buduje obraz Docker
3. Publikuje obraz do ACR z tagiem odpowiadającym SHA commita

Aktualizacja obrazu w klastrze AKS wykonywana jest ręcznie.

## Struktura projektu

```
.
├── app/
│   ├── main.py          # Kod aplikacji FastAPI
│   └── test_main.py     # Testy jednostkowe
├── k8s/
│   └── deployment.yaml  # Manifest Kubernetes (Deployment + Service)
├── .github/
│   └── workflows/
│       └── ci.yml       # Pipeline GitHub Actions
├── Dockerfile
├── requirements.txt
└── README.md
```

## Uruchomienie lokalne

### Wymagania
- Docker
- Python 3.12+

### Docker

```bash
docker build -t kalkulator .
docker run -p 8080:8080 kalkulator
```

Aplikacja dostępna pod adresem `http://localhost:8080`

### Bez Dockera

```bash
pip install -r requirements.txt
cd app
uvicorn main:app --host 0.0.0.0 --port 8080
```

### Testy

```bash
pip install -r requirements.txt
cd app && pytest
```

## Infrastruktura Azure

### Wymagania wstępne
- Azure CLI (`az`)
- kubectl
- Aktywna subskrypcja Azure

### Utworzenie infrastruktury

```bash
# Zmienne
ACR_NAME="<nazwa-acr>"
RG="rg-lab03"
AKS_NAME="aks-lab03"
LOCATION="polandcentral"

# Resource Group
az group create --name $RG --location $LOCATION

# Azure Container Registry
az acr create \
  --resource-group $RG \
  --name $ACR_NAME \
  --sku Basic

# Azure Kubernetes Service
az aks create \
  --resource-group $RG \
  --name $AKS_NAME \
  --node-count 1 \
  --generate-ssh-keys \
  --attach-acr $ACR_NAME

# Pobranie credentials do kubectl
az aks get-credentials \
  --resource-group $RG \
  --name $AKS_NAME
```

### Sekrety GitHub Actions

W ustawieniach repozytorium (`Settings → Secrets and variables → Actions`) należy dodać:

| Nazwa sekretu | Wartość |
|---|---|
| `AZURE_CLIENT_ID` | Username z ACR Admin Account |
| `AZURE_CLIENT_SECRET` | Password z ACR Admin Account |
| `AZURE_TENANT_ID` | ID tenanta Azure |
| `AZURE_SUBSCRIPTION_ID` | ID subskrypcji Azure |
| `ACR_LOGIN_SERVER` | `<nazwa-acr>.azurecr.io` |

Aby uzyskać credentials ACR:

```bash
az acr update --name $ACR_NAME --admin-enabled true
az acr credential show --name $ACR_NAME
```

## Deployment do AKS

### Pierwsze wdrożenie

```bash
kubectl apply -f k8s/deployment.yaml
kubectl get pods
kubectl get svc app-svc   # poczekaj na External IP (2-3 min)
```

### Aktualizacja obrazu po nowym buildzie

Po zakończeniu pipeline skopiuj SHA commita z zakładki Actions, następnie:

```bash
kubectl set image deployment/app \
  app=<nazwa-acr>.azurecr.io/app:<git-sha>

kubectl rollout status deployment/app
```

## Zarządzanie klastrem

### Zatrzymanie (oszczędność kosztów)

```bash
az aks stop --resource-group rg-lab03 --name aks-lab03
```

### Ponowne uruchomienie

```bash
az aks start --resource-group rg-lab03 --name aks-lab03

az aks get-credentials \
  --resource-group rg-lab03 \
  --name aks-lab03 \
  --overwrite-existing
```

### Sprawdzenie
```bash
kubectl get pods
kubectl get svc app-svc   # External IP
```

> ⚠️ Start klastra trwa ok. 3–5 minut.

## CI/CD Pipeline

Pipeline uruchamia się automatycznie przy każdym push na branch `main` i wykonuje:

1. **Checkout** — pobranie kodu
2. **Testy** — uruchomienie pytest
3. **Login do ACR** — uwierzytelnienie przez ACR Admin Account
4. **Build i Push** — zbudowanie obrazu Docker i wypchnięcie do ACR z tagiem `<sha-commita>`

> Stosowanie tagu `:latest` jest antywzorcem — tag SHA pozwala jednoznacznie powiązać obraz z konkretnym commitem.
