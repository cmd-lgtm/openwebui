#!/bin/bash
echo "Deploying Causal Organism to Kubernetes..."
kubectl apply -f k8s/deployment.yaml
echo "Deployment triggered. Run 'kubectl get pods' to verify."
