# Dev Teardown and Redeploy Instructions

This document summarizes the previous responses on how to teardown runtime and DB resources, and how to redeploy and restore the original functionality of the DB and runtime (including restoring the server container image in Fargate).

---

## Teardown Instructions

### 1. Teardown Runtime (ECS/Fargate, Web, and Workers)
- **Stop ECS/Fargate Services:**
  - In AWS Console or via CLI, scale down or delete the ECS service for the kinnoo server.
  - Example (CLI):
    ```sh
    aws ecs update-service --cluster <cluster-name> --service <service-name> --desired-count 0
    # Or to delete:
    aws ecs delete-service --cluster <cluster-name> --service <service-name>
    ```
- **Remove Cloudflare Worker (Web):**
  - Use Wrangler CLI or Cloudflare dashboard to remove the deployed worker.
    ```sh
    npx wrangler deployments list
    npx wrangler deployments delete <deployment-id>
    ```
- **Tear Down Other Runtime Resources:**
  - Remove any running containers, Lambda functions, or other compute resources as needed.

### 2. Teardown Database (Postgres, S3, etc.)
- **Drop Postgres Database:**
  - Use the RDS/Aurora console or psql CLI to drop the database.
    ```sh
    psql -h <host> -U <user> -c 'DROP DATABASE kinnoo_prod;'
    ```
- **Delete S3 Buckets:**
  - Use AWS Console or CLI to delete S3 buckets (e.g., kinnoo-terraform-state-prod, kinnoo-registry-prod).
    ```sh
    aws s3 rb s3://kinnoo-terraform-state-prod --force
    aws s3 rb s3://kinnoo-registry-prod --force
    ```
- **Remove Other State:**
  - Delete any Redis, DynamoDB, or other stateful resources as needed.

### 3. Remove IaC-managed Resources
- **Terraform Destroy:**
  - From the iac/ directory, run:
    ```sh
    terraform destroy
    ```
  - Confirm all resources are deleted.

---

## Redeploy and Restore Instructions

### 1. Restore Database
- **Provision Postgres:**
  - Use Terraform or AWS Console to create a new Postgres instance.
  - Apply migrations:
    ```sh
    alembic upgrade head
    # Or use your migration tool as documented
    ```
- **Restore Data (if backup exists):**
  - Use pg_restore or psql to restore from a backup dump.
    ```sh
    pg_restore -h <host> -U <user> -d kinnoo_prod < backup.dump
    ```
- **Recreate S3 Buckets:**
  - Use AWS Console or CLI to create buckets:
    ```sh
    aws s3 mb s3://kinnoo-terraform-state-prod
    aws s3 mb s3://kinnoo-registry-prod
    ```

### 2. Redeploy Runtime (ECS/Fargate, Web, Workers)
- **Rebuild and Push Server Container:**
  - Build the Docker image:
    ```sh
    docker build -t kinnoo-server:latest .
    docker tag kinnoo-server:latest <aws_account_id>.dkr.ecr.<region>.amazonaws.com/kinnoo-server:latest
    docker push <aws_account_id>.dkr.ecr.<region>.amazonaws.com/kinnoo-server:latest
    ```
- **Update ECS Service:**
  - In AWS Console or via CLI, update the ECS service to use the latest image.
    ```sh
    aws ecs update-service --cluster <cluster-name> --service <service-name> --force-new-deployment
    ```
- **Redeploy Cloudflare Worker:**
  - From web/ directory:
    ```sh
    npx wrangler deploy
    ```
- **Redeploy Other Runtimes:**
  - Recreate any Lambda functions, containers, or other compute resources as needed.

### 3. Restore Configuration and Secrets
- **Environment Variables:**
  - Ensure all required secrets (DB credentials, API tokens, etc.) are set in AWS Secrets Manager, SSM Parameter Store, or GitHub Actions Environments as appropriate.
- **Cloudflare Secrets:**
  - Add `CLOUDFLARE_API_TOKEN` and `CLOUDFLARE_ACCOUNT_ID` to the correct GitHub Environment or repository secrets.

### 4. Validate and Smoke Test
- **Run CI/CD:**
  - Trigger a deployment via GitHub Actions to verify all steps succeed.
- **Smoke Test:**
  - Run basic CLI and web flows to confirm registry, login, publish, and search all work as expected.

---

## Notes
- Always backup data before teardown if you intend to restore.
- For Fargate, restoring the server means pushing the correct container image and updating the service/task definition.
- For IaC, always run `terraform plan` before `apply` or `destroy` to confirm changes.
- For Cloudflare, ensure the correct environment is selected for secrets.
- For any issues, check logs in AWS CloudWatch, ECS task logs, and GitHub Actions output.

---

_Last updated: 2026-04-29_
