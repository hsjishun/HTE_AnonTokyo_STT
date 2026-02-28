#!/usr/bin/env bash
set -euo pipefail

# ── Configuration ─────────────────────────────────────────────────────────────
REGION="us-east-1"
ACCOUNT_ID="675177356722"
APP_NAME="hte-anontokyo"
ECR_REPO="hte-anontokyo"
CLUSTER_NAME="hte-cluster"
SERVICE_NAME="hte-service"
TASK_FAMILY="hte-anontokyo"
LOG_GROUP="/ecs/hte-anontokyo"

echo "=== HTE AnonTokyo AWS Infrastructure Setup ==="
echo "Region: $REGION | Account: $ACCOUNT_ID"
echo ""

# ── 1. Create ECR Repository ─────────────────────────────────────────────────
echo "1. Creating ECR repository..."
aws ecr describe-repositories --repository-names "$ECR_REPO" --region "$REGION" 2>/dev/null || \
  aws ecr create-repository \
    --repository-name "$ECR_REPO" \
    --region "$REGION" \
    --image-scanning-configuration scanOnPush=true \
    --encryption-configuration encryptionType=AES256
echo "   ECR: $ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$ECR_REPO"

# ── 2. Create CloudWatch Log Group ───────────────────────────────────────────
echo "2. Creating CloudWatch log group..."
aws logs describe-log-groups --log-group-name-prefix "$LOG_GROUP" --region "$REGION" \
  --query "logGroups[?logGroupName=='$LOG_GROUP']" --output text | grep -q "$LOG_GROUP" || \
  aws logs create-log-group --log-group-name "$LOG_GROUP" --region "$REGION"
echo "   Log Group: $LOG_GROUP"

# ── 3. Create ECS Task Execution Role ────────────────────────────────────────
echo "3. Creating ECS Task Execution Role..."
EXEC_ROLE="ecsTaskExecutionRole"
aws iam get-role --role-name "$EXEC_ROLE" 2>/dev/null || \
  aws iam create-role \
    --role-name "$EXEC_ROLE" \
    --assume-role-policy-document '{
      "Version": "2012-10-17",
      "Statement": [{
        "Effect": "Allow",
        "Principal": {"Service": "ecs-tasks.amazonaws.com"},
        "Action": "sts:AssumeRole"
      }]
    }'

aws iam attach-role-policy \
  --role-name "$EXEC_ROLE" \
  --policy-arn "arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy" 2>/dev/null || true

# Allow reading SSM parameters for secrets
aws iam put-role-policy \
  --role-name "$EXEC_ROLE" \
  --policy-name "SSMReadAccess" \
  --policy-document '{
    "Version": "2012-10-17",
    "Statement": [{
      "Effect": "Allow",
      "Action": [
        "ssm:GetParameters",
        "ssm:GetParameter"
      ],
      "Resource": "arn:aws:ssm:'"$REGION"':'"$ACCOUNT_ID"':parameter/hte/*"
    }]
  }'
echo "   Execution Role: $EXEC_ROLE"

# ── 4. Create ECS Task Role ──────────────────────────────────────────────────
echo "4. Creating ECS Task Role..."
TASK_ROLE="ecsTaskRole"
aws iam get-role --role-name "$TASK_ROLE" 2>/dev/null || \
  aws iam create-role \
    --role-name "$TASK_ROLE" \
    --assume-role-policy-document '{
      "Version": "2012-10-17",
      "Statement": [{
        "Effect": "Allow",
        "Principal": {"Service": "ecs-tasks.amazonaws.com"},
        "Action": "sts:AssumeRole"
      }]
    }'
echo "   Task Role: $TASK_ROLE"

# ── 5. Create ECS Cluster ────────────────────────────────────────────────────
echo "5. Creating ECS Cluster..."
aws ecs describe-clusters --clusters "$CLUSTER_NAME" --region "$REGION" \
  --query "clusters[?status=='ACTIVE']" --output text | grep -q "$CLUSTER_NAME" || \
  aws ecs create-cluster --cluster-name "$CLUSTER_NAME" --region "$REGION"
echo "   Cluster: $CLUSTER_NAME"

# ── 6. Store secrets in SSM Parameter Store ──────────────────────────────────
echo ""
echo "6. SSM Parameters — store your API keys:"
echo "   Run these commands with your actual keys:"
echo ""
echo "   aws ssm put-parameter --name '/hte/OPENAI_API_KEY' --type SecureString --value 'YOUR_KEY' --region $REGION"
echo "   aws ssm put-parameter --name '/hte/GEMINI_API_KEY' --type SecureString --value 'YOUR_KEY' --region $REGION"

# ── 7. GitHub Secrets reminder ────────────────────────────────────────────────
echo ""
echo "7. GitHub Secrets — add these to your repository:"
echo "   AWS_ACCESS_KEY_ID     = (your deployer access key)"
echo "   AWS_SECRET_ACCESS_KEY = (your deployer secret key)"

# ── 8. VPC / Subnets / Security Groups ───────────────────────────────────────
echo ""
echo "8. After the first Docker push, create the ECS service:"
echo ""
echo "   # Get your default VPC subnets"
echo "   SUBNETS=\$(aws ec2 describe-subnets --filters 'Name=default-for-az,Values=true' --query 'Subnets[].SubnetId' --output text --region $REGION | tr '\t' ',')"
echo "   VPC_ID=\$(aws ec2 describe-vpcs --filters 'Name=isDefault,Values=true' --query 'Vpcs[0].VpcId' --output text --region $REGION)"
echo ""
echo "   # Create security group"
echo "   SG_ID=\$(aws ec2 create-security-group --group-name hte-ecs-sg --description 'HTE ECS' --vpc-id \$VPC_ID --region $REGION --query 'GroupId' --output text)"
echo "   aws ec2 authorize-security-group-ingress --group-id \$SG_ID --protocol tcp --port 8000 --cidr 0.0.0.0/0 --region $REGION"
echo ""
echo "   # Register task definition"
echo "   aws ecs register-task-definition --cli-input-json file://.aws/task-definition.json --region $REGION"
echo ""
echo "   # Create service"
echo "   aws ecs create-service \\"
echo "     --cluster $CLUSTER_NAME \\"
echo "     --service-name $SERVICE_NAME \\"
echo "     --task-definition $TASK_FAMILY \\"
echo "     --desired-count 1 \\"
echo "     --launch-type FARGATE \\"
echo "     --network-configuration \"awsvpcConfiguration={subnets=[\$SUBNETS],securityGroups=[\$SG_ID],assignPublicIp=ENABLED}\" \\"
echo "     --region $REGION"

echo ""
echo "=== Setup complete ==="
