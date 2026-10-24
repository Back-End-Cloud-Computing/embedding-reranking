# Chart Helm — `embedding-reranking`

Mesmo desenho do [`k8s/`](../../k8s/README.md): Deployment `embedding-reranking` (3 réplicas, anotações do
Prometheus), Service `embedding-reranking:8003` e ConfigMap. Os valores que mudam entre ambientes estão em
[`values.yaml`](values.yaml).

Diferenças em relação aos charts com entrada pública:

- **Sem Ingress e sem `host`**: o serviço é interno, só o `product` o chama pelo Service.
- **Sem `existingSecret`**: não há segredo próprio; o JWT é validado com a chave pública do `authorization`, que
  precisa estar instalado antes. O `/index` grava no `vector-db` (chart [`helm/vector-db`](https://github.com/Back-End-Cloud-Computing/vector-db/tree/main/helm/vector-db)).

O modelo (`EMBEDDING_MODEL_NAME`) é baixado do Hugging Face na primeira requisição de cada réplica.

```bash
helm lint helm/embedding-reranking
helm upgrade --install embedding-reranking helm/embedding-reranking
kubectl get pods -w
helm uninstall embedding-reranking
```

| Quero | Faço |
|---|---|
| Outra versão da imagem | `--set image.tag=1.1.1` |
| Mais réplicas | `--set replicaCount=5` |
| Outro modelo | `--set config.EMBEDDING_MODEL_NAME=<modelo>` |
| Mais memória por réplica | `--set resources.limits.memory=2Gi` |

Testado em 24/10/2026 num cluster `kind` limpo (Kubernetes 1.37, Helm 4.3), junto com o chart do `vector-db`:
`helm lint` limpo, `helm install` com o `values.yaml` padrão sobe 3 pods `1/1`; pelo Service, `/metrics` responde 200
e `/index` com token gera o embedding e grava no `vector-db` (a primeira chamada de cada réplica leva ~25 s por causa
do download do modelo).
