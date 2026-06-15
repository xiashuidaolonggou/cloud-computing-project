#!/bin/bash
# 监控系统部署 - 使用公共镜像源
set -e

echo "=========================================="
echo "  ☁️ 监控系统部署（公共镜像源）"
echo "=========================================="

echo ""
echo "[1/4] 删除旧的 release（如果有）..."
helm uninstall monitoring -n monitoring 2>/dev/null || true

echo ""
echo "[2/4] 下载 chart..."
curl -sL "https://raw.githubusercontent.com/xiashuidaolonggou/cloud-computing-project/main/kube-prometheus-stack-83.7.0.tgz" -o /tmp/kube-prometheus-stack-83.7.0.tgz
ls -lh /tmp/kube-prometheus-stack-83.7.0.tgz

echo ""
echo "[3/4] CRD 安装..."
tar xzf /tmp/kube-prometheus-stack-83.7.0.tgz -C /tmp/
kubectl apply -f /tmp/kube-prometheus-stack/charts/crds/crds/ 2>/dev/null || true

echo ""
echo "[4/4] 安装 kube-prometheus-stack（公共镜像，跳过 webhook）..."
helm install monitoring /tmp/kube-prometheus-stack-83.7.0.tgz \
  --namespace monitoring \
  --set global.imagePullSecrets[0].name=swr-secret \
  --set grafana.adminPassword="admin123" \
  --set grafana.image.registry=docker.io \
  --set grafana.image.repository=grafana/grafana \
  --set grafana.image.tag=11.5.2 \
  --set prometheusOperator.image.registry=quay.io \
  --set prometheusOperator.image.repository=prometheus-operator/prometheus-operator \
  --set prometheusOperator.image.tag=v0.76.0 \
  --set prometheusOperator.admissionWebhooks.enabled=false \
  --set prometheusOperator.admissionWebhooks.patch.enabled=false \
  --set prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues=false \
  --set prometheus.prometheusSpec.image.registry=docker.io \
  --set prometheus.prometheusSpec.image.repository=prom/prometheus \
  --set prometheus.prometheusSpec.image.tag=v2.55.0 \
  --set prometheus.service.type=NodePort \
  --set grafana.service.type=NodePort \
  --set kube-state-metrics.enabled=true \
  --set kube-state-metrics.image.registry=registry.k8s.io \
  --set kube-state-metrics.image.repository=kube-state-metrics/kube-state-metrics \
  --set kube-state-metrics.image.tag=v2.13.0 \
  --set prometheus-node-exporter.image.registry=docker.io \
  --set prometheus-node-exporter.image.repository=prom/node-exporter \
  --set prometheus-node-exporter.image.tag=v1.8.2 \
  --timeout 10m

echo ""
echo "✅ 安装完成！查看状态："
kubectl get pods -n monitoring

echo ""
echo "=========================================="
echo "Grafana: admin / admin123"
echo "端口转发: kubectl port-forward -n monitoring svc/monitoring-grafana 3000:80 &"
echo "=========================================="
