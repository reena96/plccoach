# What You Need to Do - Simple Checklist

I've automated everything I can. Here's what's left for you to do:

---

## ✅ One-Time Setup (30 minutes)

### 1. Install Tools

**macOS:**
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
brew install awscli terraform
```

**Windows:** [Download AWS CLI](https://aws.amazon.com/cli/) and [Terraform](https://www.terraform.io/downloads)

**Linux:**
```bash
# AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Terraform
sudo snap install terraform --classic
```

### 2. Configure AWS

Get your AWS Access Key from [AWS IAM Console](https://console.aws.amazon.com/iam/):
1. IAM → Users → Your Username → Security credentials
2. Create access key → CLI → Create
3. Copy the Access Key ID and Secret Key

Then run:
```bash
aws configure
# Paste your Access Key ID
# Paste your Secret Access Key
# Region: us-east-1
# Format: json
```

### 3. Deploy Infrastructure

**Super Easy - Just run this:**
```bash
cd plccoach
./scripts/deploy-infrastructure.sh
```

That's it! It will:
- Check everything is installed
- Show you what it will create
- Ask for confirmation
- Deploy everything (takes 15-20 minutes)
- Give you all the URLs and values you need

### 4. Subscribe to Alerts

After deployment, run this (with your email):
```bash
aws sns subscribe \
  --topic-arn $(cd infrastructure && terraform output -raw sns_alarms_topic_arn) \
  --protocol email \
  --notification-endpoint your-email@example.com
```

Check your email and click the confirmation link.

### 5. Set Up GitHub Actions

1. Go to your GitHub repo → Settings → Secrets → Actions
2. Click "New repository secret"
3. Add these two secrets:

```
Name: AWS_ROLE_TO_ASSUME
Value: (get from infrastructure-outputs.txt file)

Name: API_URL
Value: (get alb_dns_name from infrastructure-outputs.txt)
```

---

## 🎉 Done!

Your infrastructure is now deployed and ready. The automated CI/CD pipeline will deploy your application code when you push to `main` branch.

---

## 📊 Cost

- **Production:** ~$325/month
- **Development:** ~$100/month (see DEPLOYMENT_GUIDE.md for how to reduce costs)

---

## 🆘 If Something Goes Wrong

### Error: "AWS credentials not configured"
```bash
aws configure
# Re-enter your credentials
```

### Error: "Terraform not found"
Make sure you installed it correctly. Try:
```bash
terraform --version
```

### Deployment is stuck
This is normal - RDS takes 15-20 minutes to create. Just wait.

### Something else
1. Check `DEPLOYMENT_GUIDE.md` for detailed troubleshooting
2. Check `docs/infrastructure.md` for full documentation
3. Or just ask me!

---

## 🔄 What Happens Automatically (No Action Needed)

When you push code to `main` branch:
- ✅ Tests run automatically
- ✅ Docker images build automatically
- ✅ Backend deploys to ECS automatically
- ✅ Frontend deploys to S3/CloudFront automatically
- ✅ You get notified if anything fails

---

## 📱 Monitoring

After deployment:
- Go to [AWS CloudWatch Console](https://console.aws.amazon.com/cloudwatch/)
- You'll see a dashboard with all metrics
- You'll get email alerts if anything goes wrong

---

## Summary: Your 3 Commands

```bash
# 1. Configure AWS
aws configure

# 2. Deploy infrastructure
./scripts/deploy-infrastructure.sh

# 3. Subscribe to alerts
aws sns subscribe --topic-arn <from-output> --protocol email --notification-endpoint your@email.com
```

**That's literally all you have to do manually!**

Everything else is automated code that I've created for you.
