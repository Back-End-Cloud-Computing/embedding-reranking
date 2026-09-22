# embedding-reranking no Kubernetes

Sobe três réplicas do embedding-reranking, com Service Discovery para
`vector-db` e `authorization`.

```
Service embedding-reranking :8003
          |
   Service Discovery
          |
   +------+------+------+
   |             |      |
  Pod           Pod    Pod
   |             |      |
   +------+------+------+
          |
          | vector-db:8002, authorization:8081
          v
   Services correspondentes
```

## Subir

Depende de `vector-db` e `authorization` já estarem no cluster (repositórios
próprios):

```bash
kubectl apply -f k8s/embedding-reranking.yaml
```

```bash
kubectl wait --for=condition=ready pod -l app=embedding-reranking --timeout=180s
kubectl get pods
```

## Testar a comunicação interna

```bash
kubectl run teste --image=curlimages/curl:latest -it --rm -- sh
```

```sh
T=$(curl -s -X POST http://authorization:8081/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@ganjj.com","password":"adminSegura123"}' \
  | sed 's/.*"accessToken":"\([^"]*\)".*/\1/')

# /embed não depende do vector-db, mas já exige o token
curl -s -X POST http://embedding-reranking:8003/embed \
  -H "Authorization: Bearer $T" -H "Content-Type: application/json" \
  -d '{"texts":["produto teste"]}'

# /index fala com o vector-db pelo nome do Service
curl -s -X POST http://embedding-reranking:8003/index \
  -H "Authorization: Bearer $T" -H "Content-Type: application/json" \
  -d '{"collection_name":"products","id":"teste-1","text":"produto teste","metadata":{}}'
```

## Autorrecuperação

```bash
kubectl get pods -l app=embedding-reranking
kubectl delete pod <nome-de-um-pod>
kubectl get pods -l app=embedding-reranking
```

O manifesto declara `replicas: 3`. Ao perder um Pod, o Deployment cria outro
para voltar ao estado declarado, e o Service atualiza os endpoints sozinho.

## Escalar

```bash
kubectl apply -f k8s/embedding-reranking.yaml
```

## Acessar do host

```bash
kubectl port-forward service/embedding-reranking 8003:8003
```

## Acessar via Ingress (sem port-forward por serviço)

```bash
minikube addons enable ingress
kubectl apply -f k8s/ingress.yaml
kubectl wait --namespace ingress-nginx --for=condition=ready pod \
  --selector=app.kubernetes.io/component=controller --timeout=120s
```

```bash
IP=$(minikube ip)
PORT=$(kubectl get svc -n ingress-nginx ingress-nginx-controller -o jsonpath='{.spec.ports[?(@.port==80)].nodePort}')
curl -H "Host: embedding-reranking.ganjj.local" http://$IP:$PORT/docs
```

**No WSL2**: encaminhe uma porta só, para o Ingress Controller (não para o
`embedding-reranking` diretamente):

```bash
kubectl port-forward -n ingress-nginx service/ingress-nginx-controller 8080:80
```

Hosts do Windows: `127.0.0.1  embedding-reranking.ganjj.local`. Navegador:
http://embedding-reranking.ganjj.local:8080/docs

## Sobre a imagem

Publicada em
[joao2006/embedding-reranking](https://hub.docker.com/r/joao2006/embedding-reranking).
Para publicar uma versão nova:

```bash
docker build -t joao2006/embedding-reranking:1.0.1 .
docker push joao2006/embedding-reranking:1.0.1
```

E atualize a tag em `image:` no `embedding-reranking.yaml`.
