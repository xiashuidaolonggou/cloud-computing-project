#!/bin/bash
# 监控系统安装 - 离线方式（从 GitHub 下载 chart）
set -e

echo "=========================================="
echo "  ☁️ 监控系统部署（离线安装）"
echo "=========================================="

echo ""
echo "[1/4] 下载 kube-prometheus-stack chart..."
curl -sL "https://github.com/prometheus-community/helm-charts/releases/download/kube-prometheus-stack-83.7.0/kube-prometheus-stack-83.7.0.tgz" -o /tmp/kube-prometheus-stack-83.7.0.tgz

echo "[2/4] 安装 kube-prometheus-stack..."
helm install monitoring /tmp/kube-prometheus-stack-83.7.0.tgz \
  --namespace monitoring \
  --set grafana.adminPassword="admin123" \
  --set prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues=false \
  --set prometheus.service.type=NodePort \
  --set grafana.service.type=NodePort

echo "[3/4] 等待 Pod 启动（约 2 分钟）..."
echo "   运行 kubectl get pods -n monitoring -w 查看状态"

echo ""
echo "[4/4] 部署完成！"
echo "=========================================="
echo ""
echo "Kubectl 查看状态: kubectl get pods -n monitoring"
echo ""
echo "Grafana: 用户名 admin / 密码 admin123"
echo "Prometheus 端口转发: kubectl port-forward -n monitoring service/monitoring-kube-prometheus-prometheus 9090:9090"
echo "Grafana 端口转发: kubectl port-forward -n monitoring service/monitoring-grafana 3000:80"
echo "=========================================="
