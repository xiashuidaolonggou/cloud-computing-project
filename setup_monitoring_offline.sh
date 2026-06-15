#!/bin/bash
# 监控系统部署 - 从 GitHub 下载 chart 离线安装
set -e

echo "=========================================="
echo "  ☁️ 监控系统部署（离线安装）"
echo "=========================================="

echo ""
echo "[1/4] 下载 kube-prometheus-stack chart..."
curl -sL "https://raw.githubusercontent.com/xiashuidaolonggou/cloud-computing-project/main/kube-prometheus-stack-83.7.0.tgz" -o /tmp/kube-prometheus-stack-83.7.0.tgz
ls -lh /tmp/kube-prometheus-stack-83.7.0.tgz
echo "✅ 下载完成！"

echo ""
echo "[2/4] 安装 kube-prometheus-stack..."
helm install monitoring /tmp/kube-prometheus-stack-83.7.0.tgz \
  --namespace monitoring \
  --set grafana.adminPassword="admin123" \
  --set prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues=false \
  --set prometheus.service.type=NodePort \
  --set grafana.service.type=NodePort

echo ""
echo "[3/4] 等待 Pod 启动..."
kubectl get pods -n monitoring

echo ""
echo "[4/4] 部署完成！"
echo "=========================================="
echo "查看状态: kubectl get pods -n monitoring -w"
echo ""
echo "Grafana: 用户名 admin / 密码 admin123"
echo "端口转发 Prometheus: kubectl port-forward -n monitoring svc/monitoring-kube-prometheus-prometheus 9090:9090"
echo "端口转发 Grafana:    kubectl port-forward -n monitoring svc/monitoring-grafana 3000:80"
echo "=========================================="
