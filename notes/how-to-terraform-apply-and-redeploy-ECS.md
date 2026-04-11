# How to Run `terraform apply` and Redeploy ECS Server

This guide provides the exact, up-to-date commands for applying Terraform changes and redeploying the ECS server image for the kinnoo project. All steps are sourced from project documentation and validated against the current infrastructure setup.

---

## 1. Set Required Environment Variables

Before running any commands, ensure the following environment variables are set:

```sh
export AWS_PROFILE=jerry
export AWS_REGION=<your-aws-region>
export TF_VAR_zone_id=<your-route53-zone-id>
export CLOUDFLARE_API_TOKEN=<your-api-token>
```
- Replace `<your-aws-profile>`, `<your-aws-region>`, and `<your-route53-zone-id>` with your actual values.
- These are required for both Terraform and AWS CLI commands.

---

## 2. Run Terraform Apply

Navigate to the `iac/` directory and apply the infrastructure changes: (on plan, -detailed-exitcode is optional)

```sh
cd iac
terraform init
terraform plan -var-file=environments/dev/terraform.tfvars -out tfplan
terraform apply "tfplan"
```
- This will create/update all AWS resources, including Lambda, ECS, ECR, IAM, and networking.
- Confirm that the apply completes successfully and note any outputs (such as ECR repository URI, ECS cluster/service names, Lambda function name).

---

## 3. Build and Push the Docker Image to ECR

Return to the project root and build the Docker image for the server:

```sh
cd ..  # if still in iac/
# Get the ECR repository URI from Terraform outputs or AWS Console
export ECR_REPO_URI=$(terraform -chdir=iac output -raw ecr_repo_uri)
# Build the Docker image
DOCKER_BUILDKIT=1 docker build -t $ECR_REPO_URI:latest .
# Authenticate Docker to ECR
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_REPO_URI
# Push the image
docker push $ECR_REPO_URI:latest
```
- Ensure you have Docker and AWS CLI installed and configured.
- The image tag `latest` is used for ECS deployment.

---

## 4. Redeploy the ECS Service to Use the New Image

Update the ECS service to use the new image:

```sh
# Get ECS cluster and service names from Terraform outputs
export ECS_CLUSTER=$(terraform -chdir=iac output -raw ecs_cluster_name) should be "kinnoo-dev-cluster"
export ECS_SERVICE=$(terraform -chdir=iac output -raw ecs_service_name) should be "kinnoo-dev-service"
# Force a new deployment
aws ecs update-service --cluster $ECS_CLUSTER --service $ECS_SERVICE --force-new-deployment
```
- This will trigger ECS to pull the new image and restart the service tasks.
- Monitor the deployment in the AWS Console or with:

```sh
aws ecs describe-services --cluster $ECS_CLUSTER --services $ECS_SERVICE
```

---

## 5. (Optional) Validate Lambda Security Check Deployment

If you have published a new agent or made changes to the Lambda security check, you can validate its deployment:

- Publish a test agent using the kinnoo CLI.
- Check Lambda logs in CloudWatch for successful invocation after publish.

---

## References
- See `notes/tasks/task452-notes.md` and `notes/tasks/task448-human-handoff.md` for additional context and troubleshooting.
- Terraform outputs in `iac/outputs.tf` provide all required resource names and URIs.

---

**Last updated:** April 11, 2026
