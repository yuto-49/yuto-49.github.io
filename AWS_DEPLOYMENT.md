# AWS Deployment Guide for RAG-Enabled Backend

## Recommended: AWS Elastic Beanstalk

### Why Elastic Beanstalk?
- ✅ Easy migration from Render
- ✅ Managed deployment and scaling
- ✅ Can choose instance types with 4GB+ RAM
- ✅ Persistent storage for ChromaDB
- ✅ Cost-effective (~$30-100/month)

### Setup Steps

#### 1. Install AWS CLI and EB CLI
```bash
# Install AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Install EB CLI
pip install awsebcli
```

#### 2. Create Elastic Beanstalk Application
```bash
# Initialize EB
cd /path/to/yuto_portfolio
eb init -p python-3.12 yuto-portfolio-backend --region us-east-1

# Create environment (choose instance type with more memory)
eb create yuto-portfolio-prod \
  --instance-type t3.medium \
  --envvars ANTHROPIC_API_KEY=your_key_here,DISABLE_RAG=false
```

#### 3. Create `.ebextensions` Configuration

Create `.ebextensions/01_python.config`:
```yaml
option_settings:
  aws:elasticbeanstalk:container:python:
    WSGIPath: backend:app
  aws:elasticbeanstalk:application:environment:
    PYTHONPATH: "/var/app/current:$PYTHONPATH"
```

Create `.ebextensions/02_requirements.config`:
```yaml
files:
  "/opt/elasticbeanstalk/hooks/appdeploy/pre/01_install_dependencies.sh":
    mode: "000755"
    owner: root
    group: root
    content: |
      #!/bin/bash
      cd /var/app/ondeck
      source /var/app/venv/*/bin/activate
      pip install -r requirements.txt
```

#### 4. Create `Procfile` for Elastic Beanstalk
```bash
web: cd backend && uvicorn app:app --host 0.0.0.0 --port 8000
```

#### 5. Deploy
```bash
eb deploy
```

### Instance Type Recommendations

| Instance Type | Memory | vCPU | Cost/month | Best For |
|--------------|--------|------|------------|----------|
| **t3.medium** | 4 GB | 2 | ~$30 | Development/Testing |
| **t3.large** | 8 GB | 2 | ~$60 | Production (recommended) |
| **t3.xlarge** | 16 GB | 4 | ~$120 | High traffic |
| **m5.large** | 8 GB | 2 | ~$70 | Production (better performance) |

**Recommendation**: Start with **t3.large** (8GB RAM) for RAG features.

---

## Alternative: AWS ECS/Fargate (Container-Based)

### Why ECS/Fargate?
- ✅ Container-based (Docker)
- ✅ Specify exact memory requirements
- ✅ Auto-scaling
- ✅ No server management

### Setup Steps

#### 1. Create Dockerfile
```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Expose port
EXPOSE 8000

# Run application
WORKDIR /app/backend
CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 2. Create ECS Task Definition
```json
{
  "family": "yuto-portfolio-backend",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "1024",
  "memory": "4096",
  "containerDefinitions": [{
    "name": "backend",
    "image": "your-ecr-repo/yuto-portfolio:latest",
    "portMappings": [{
      "containerPort": 8000,
      "protocol": "tcp"
    }],
    "environment": [
      {"name": "ANTHROPIC_API_KEY", "value": "your-key"},
      {"name": "DISABLE_RAG", "value": "false"}
    ],
    "logConfiguration": {
      "logDriver": "awslogs",
      "options": {
        "awslogs-group": "/ecs/yuto-portfolio",
        "awslogs-region": "us-east-1",
        "awslogs-stream-prefix": "ecs"
      }
    }
  }]
}
```

#### 3. Deploy to ECS
```bash
# Build and push to ECR
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com
docker build -t yuto-portfolio-backend .
docker tag yuto-portfolio-backend:latest YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/yuto-portfolio:latest
docker push YOUR_ACCOUNT.dkr.ecr.us-east-1.amazonaws.com/yuto-portfolio:latest

# Create ECS service
aws ecs create-service \
  --cluster yuto-portfolio-cluster \
  --service-name yuto-portfolio-backend \
  --task-definition yuto-portfolio-backend \
  --desired-count 1 \
  --launch-type FARGATE \
  --network-configuration "awsvpcConfiguration={subnets=[subnet-xxx],securityGroups=[sg-xxx],assignPublicIp=ENABLED}"
```

**Memory Options for Fargate**:
- 512 MB - 4 GB (0.25 vCPU)
- 1 GB - 8 GB (0.5 vCPU)
- 2 GB - 16 GB (1 vCPU) ← **Recommended for RAG**
- 4 GB - 30 GB (2 vCPU)
- 8 GB - 60 GB (4 vCPU)

---

## Alternative: AWS EC2 (Full Control)

### Why EC2?
- ✅ Full control over instance
- ✅ Choose any instance type
- ✅ Persistent storage (EBS)
- ✅ Cost-effective for steady workloads

### Setup Steps

#### 1. Launch EC2 Instance
- **Instance Type**: t3.large or m5.large (8GB+ RAM)
- **AMI**: Amazon Linux 2023 or Ubuntu 22.04
- **Storage**: 20GB+ EBS volume (for ChromaDB)

#### 2. Install Dependencies
```bash
# Update system
sudo yum update -y  # Amazon Linux
# or
sudo apt update && sudo apt upgrade -y  # Ubuntu

# Install Python 3.12
sudo yum install -y python3.12 python3.12-pip python3.12-venv

# Install Git
sudo yum install -y git

# Clone repository
git clone https://github.com/yourusername/yuto_portfolio.git
cd yuto_portfolio

# Create virtual environment
python3.12 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

#### 3. Setup Systemd Service
Create `/etc/systemd/system/yuto-portfolio.service`:
```ini
[Unit]
Description=Yuto Portfolio Backend
After=network.target

[Service]
Type=simple
User=ec2-user
WorkingDirectory=/home/ec2-user/yuto_portfolio/backend
Environment="PATH=/home/ec2-user/yuto_portfolio/venv/bin"
Environment="ANTHROPIC_API_KEY=your_key_here"
Environment="DISABLE_RAG=false"
ExecStart=/home/ec2-user/yuto_portfolio/venv/bin/uvicorn app:app --host 0.0.0.0 --port 8000
Restart=always

[Install]
WantedBy=multi-user.target
```

#### 4. Start Service
```bash
sudo systemctl daemon-reload
sudo systemctl enable yuto-portfolio
sudo systemctl start yuto-portfolio
sudo systemctl status yuto-portfolio
```

#### 5. Setup Nginx Reverse Proxy (Optional)
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

---

## Cost Comparison

| Service | Instance/Config | Monthly Cost | Memory | Best For |
|---------|----------------|--------------|--------|----------|
| **Render** | Free tier | $0 (limited) | 512MB | Development |
| **Render** | Standard | $7-25 | 512MB-2GB | Small apps |
| **Elastic Beanstalk** | t3.large | ~$60 | 8GB | **Recommended** |
| **ECS Fargate** | 2GB/1vCPU | ~$50 | 2GB | Container apps |
| **ECS Fargate** | 4GB/2vCPU | ~$100 | 4GB | Production RAG |
| **EC2** | t3.large | ~$60 | 8GB | Full control |

---

## Memory Requirements for RAG

- **Sentence Transformers Model**: ~400-500MB
- **ChromaDB**: ~100-500MB (depends on data)
- **FastAPI/Uvicorn**: ~100-200MB
- **Python/CrewAI**: ~200-300MB
- **Buffer**: ~500MB

**Total**: ~1.5-2GB minimum, **4GB+ recommended** for production

---

## Recommendation

**Start with AWS Elastic Beanstalk (t3.large instance)**:
1. ✅ Easiest migration from Render
2. ✅ 8GB RAM is sufficient for RAG
3. ✅ Managed service (less maintenance)
4. ✅ Cost-effective (~$60/month)
5. ✅ Can scale up/down easily

**If you need more control or have Docker setup**: Use **ECS Fargate** with 4GB memory.

**If you want full control**: Use **EC2 t3.large** or **m5.large**.

---

## Next Steps

1. Choose your AWS service (recommend Elastic Beanstalk)
2. Set up AWS account and configure credentials
3. Follow the setup steps above
4. Update your frontend to point to new AWS endpoint
5. Monitor memory usage and scale as needed

