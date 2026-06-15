#!/bin/bash
# 监控系统部署 - 离线安装（跳过 webhook 避免镜像拉取问题）
set -e

echo "=========================================="
echo "  ☁️ 监控系统部署"
echo "=========================================="

echo ""
echo "[1/4] 下载 chart..."
curl -sL "https://raw.githubusercontent.com/xiashuidaolonggou/cloud-computing-project/main/kube-prometheus-stack-83.7.0.tgz" -o /tmp/kube-prometheus-stack-83.7.0.tgz
ls -lh /tmp/kube-prometheus-stack-83.7.0.tgz

echo ""
echo "[2/4] 安装（跳过 webhook，CRD 手动创建）..."
tar xzf /tmp/kube-prometheus-stack-83.7.0.tgz -C /tmp/
kubectl apply -f /tmp/kube-prometheus-stack/charts/crds/crds/ 2>/dev/null || true

helm install monitoring /tmp/kube-prometheus-stack-83.7.0.tgz \
  --namespace monitoring \
  --set grafana.adminPassword="admin123" \
  --set prometheusOperator.admissionWebhooks.enabled=false \
  --set prometheusOperator.admissionWebhooks.patch.enabled=false \
  --set prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues=false \
  --set prometheus.service.type=NodePort \
  --set grafana.service.type=NodePort \
  --set kube-state-metrics.enabled=false \
  --timeout 10m

echo ""
echo "[3/4] 查看状态..."
kubectl get pods -n monitoring

echo ""
echo "[4/4] 完成！"
echo "=========================================="
echo "查看 Pod 启动: kubectl get pods -n monitoring -w"
echo "Grafana 账号: admin / admin123"
echo ""
echo "端口转发 Prometheus: kubectl port-forward -n monitoring svc/monitoring-kube-prometheus-prometheus 9090:9090 &"
echo "端口转发 Grafana:    kubectl port-forward -n monitoring svc/monitoring-grafana 3000:80 &"
echo "=========================================="
