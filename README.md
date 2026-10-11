# ShopFlow: Local Kubernetes DevOps Portfolio

A production-style lab with two FastAPI services, PostgreSQL, Docker, kind, Kubernetes probes/resources, Jenkins CI, Prometheus metrics, and failure drills. It is a portfolio lab, not a production deployment.

## Prerequisites
Install Docker Engine, kubectl, kind, Git, and Python 3 on Linux. Verify:
```bash
docker --version
kubectl version --client
kind version
```
Docker group membership is effectively root-level access.

## 1. Test
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
pip install -r services/catalog/requirements.txt
pip install -r services/orders/requirements.txt
pytest -q
```

## 2. Create cluster and build images
```bash
kind create cluster --name shopflow --config kind/cluster.yaml
docker build -t shopflow/catalog-api:0.1.0 services/catalog
docker build -t shopflow/orders-api:0.1.0 services/orders
kind load docker-image shopflow/catalog-api:0.1.0 --name shopflow
kind load docker-image shopflow/orders-api:0.1.0 --name shopflow
```

## 3. Deploy
```bash
kubectl apply -f k8s/00-namespace.yaml
kubectl apply -f k8s/10-postgres.yaml
kubectl apply -f k8s/20-catalog.yaml
kubectl apply -f k8s/30-orders.yaml
kubectl apply -f k8s/40-network-policy.yaml
kubectl -n shopflow get pods,svc
kubectl -n shopflow wait --for=condition=Ready pod -l app=postgres --timeout=120s
kubectl -n shopflow rollout status deployment/catalog-api
kubectl -n shopflow rollout status deployment/orders-api
```

## 4. Test APIs
Terminal 1:
```bash
kubectl -n shopflow port-forward svc/catalog-api 8001:8000
```
Terminal 2:
```bash
curl -fsS http://127.0.0.1:8001/healthz
curl -fsS http://127.0.0.1:8001/products
curl -fsS http://127.0.0.1:8001/metrics | head
```
Terminal 3:
```bash
kubectl -n shopflow port-forward svc/orders-api 8002:8000
```
Terminal 4:
```bash
curl -fsS http://127.0.0.1:8002/healthz
curl -fsS -X POST http://127.0.0.1:8002/orders -H 'Content-Type: application/json' -d '{"product_id":"sku-001","quantity":2}'
curl -fsS http://127.0.0.1:8002/orders
```

## Troubleshooting
```bash
kubectl -n shopflow get pods
kubectl -n shopflow describe pod <pod-name>
kubectl -n shopflow logs deployment/orders-api --tail=100
kubectl -n shopflow get events --sort-by=.lastTimestamp
kubectl -n shopflow rollout history deployment/catalog-api
```
Common cases:
- `ImagePullBackOff`: check image tag and `kind load docker-image`.
- `CrashLoopBackOff`: inspect logs; orders waits for PostgreSQL at startup.
- `Pending` PostgreSQL: inspect PVC and storage events.
- Service has no endpoints: compare Service selector with pod labels.
- NetworkPolicy: enforcement depends on CNI; default kind networking may not enforce policies.

## Failure drills
1. Delete a catalog pod and observe ReplicaSet replacement:
   `kubectl -n shopflow delete pod -l app=catalog-api`
2. Change image tag to a nonexistent tag, apply, inspect events, then restore and run:
   `kubectl -n shopflow rollout undo deployment/catalog-api`
3. Temporarily break `/readyz` probe path and observe readiness.
4. Scale orders down/up: `kubectl -n shopflow scale deployment/orders-api --replicas=0` then `--replicas=2`.
5. Write an incident report with hypothesis, evidence, root cause, fix, prevention.

## CI/CD and next stages
`Jenkinsfile` tests and builds images. Run it on a dedicated agent with Python and Docker access; avoid mounting the host Docker socket into a shared controller because it grants powerful host access. Add Argo CD after CI is stable, with manifests in Git and Argo CD reconciling desired state. Prometheus config is a starting point; run Prometheus inside the cluster or adapt targets for host-based Prometheus.

Security TODOs: replace the lab-only DB password, move secrets out of Git, add Trivy and dependency scanning, pin images by digest, add TLS/RBAC/backup restore tests, and use a CNI that enforces NetworkPolicies.

Cleanup:
```bash
kind delete cluster --name shopflow
```
