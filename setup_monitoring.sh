#!/bin/bash
# 云计算课设 - 附加题1：监控系统自动部署脚本
set -e

echo "=========================================="
echo "  ☁️ 监控系统自动部署"
echo "  Prometheus + Grafana + Node Exporter"
echo "=========================================="

# 1. 添加 Helm 仓库
echo ""
echo "[1/4] 添加 Prometheus Helm 仓库..."
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts 2>/dev/null
helm repo update

# 2. 安装 kube-prometheus-stack
echo ""
echo "[2/4] 安装 kube-prometheus-stack..."
helm install monitoring prometheus-community/kube-prometheus-stack \
  --namespace monitoring \
  --set grafana.adminPassword="admin123" \
  --set prometheus.prometheusSpec.serviceMonitorSelectorNilUsesHelmValues=false \
  --set prometheus.service.type=NodePort \
  --set grafana.service.type=NodePort

# 3. 等待 Pod 启动
echo ""
echo "[3/4] 等待 Pod 全部启动（约 2-3 分钟）..."
kubectl wait --for=condition=Ready pod -l app.kubernetes.io/instance=monitoring -n monitoring --timeout=180s 2>/dev/null || true

# 4. 查看状态
echo ""
echo "[4/4] 部署完成！查看状态："
echo "=========================================="
kubectl get pods -n monitoring
echo ""

# 获取访问信息
echo "=========================================="
echo "  📊 访问信息"
echo "=========================================="
GRAFANA_POD=$(kubectl get pod -n monitoring -l app.kubernetes.io/name=grafana -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)
PROMETHEUS_POD=$(kubectl get pod -n monitoring -l app.kubernetes.io/name=prometheus -o jsonpath='{.items[0].metadata.name}' 2>/dev/null)

echo ""
echo "Grafana: 用户名 admin / 密码 admin123"
echo "运行 kubectl port-forward -n monitoring $GRAFANA_POD 3000:3000 然后本地浏览器访问"
echo ""
echo "Prometheus:"
echo "运行 kubectl port-forward -n monitoring $PROMETHEUS_POD 9090:9090 然后本地浏览器访问"
echo ""
echo "=========================================="
echo "  ✅ 监控系统部署完成！"
echo "=========================================="
