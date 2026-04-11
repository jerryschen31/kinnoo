# task452 Notes

## Summary
- Bug fixed: remote publish path incorrectly rejected manifests missing top-level `framework` with HTTP 400 (`kinnoo.yaml missing required field(s): framework`).
- Server-side fix: publish validation now requires only `name` and `version`.
- CLI/template fix: JS/TS init manifests now emit `runtime.language` as `javascript` / `typescript` (instead of `nodejs`).
- Runtime compatibility fix: Node-compatible execution/install/pack/test/sandbox/runtime-monitor logic now accepts language aliases (`nodejs`, `javascript`, `typescript`, plus short aliases where applicable).

## Code Changes Implemented
- `server/routes/publish.py`
  - Removed `framework` from required-field validation in publish archive manifest checks.
- `server/tests/test_publish.py`
  - Added regression test: `test_publish_accepts_manifest_without_framework_field`.
- `src/kinnoo/init_command.py`
  - Updated node-manifest builder to write requested language value (`javascript`/`typescript`) for JS/TS scaffolds.
- `src/kinnoo/schema.py`
  - Expanded supported runtime languages to include `javascript` and `typescript`.
- `src/kinnoo/runtime_language.py` (new)
  - Added normalization + Node-compatible language helper.
- Updated Node-compatible checks in:
  - `src/kinnoo/pack_command.py`
  - `src/kinnoo/install_command.py`
  - `src/kinnoo/run_command.py`
  - `src/kinnoo/test_command.py`
  - `src/kinnoo/runtime_monitor.py`
  - `src/kinnoo/sandbox.py`
- Added init regression tests in `tests/test_init.py`:
  - `test_init_javascript_manifest_runtime_language`
  - `test_init_typescript_manifest_runtime_language`

## ECS Redeployment Back-Documentation

### 1) Rebuilt and pushed new server image
Command run:
```bash
cd /Users/jerry/gh/kinnoo && set -euo pipefail
ACCOUNT_ID=386775099533
REGION=us-west-2
REPO=kinnoo-dev-server
IMAGE_URI="$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com/$REPO"
TAG="phase13-uat-$(date +%Y%m%d-%H%M%S)"
aws --profile jerry --region "$REGION" ecr get-login-password | docker login --username AWS --password-stdin "$ACCOUNT_ID.dkr.ecr.$REGION.amazonaws.com"
docker buildx build --platform linux/amd64 -t "${IMAGE_URI}:${TAG}" -t "${IMAGE_URI}:latest" -f Dockerfile . --push
PUSHED_DIGEST=$(aws --profile jerry --region "$REGION" ecr describe-images --repository-name "$REPO" --image-ids imageTag="$TAG" --query 'imageDetails[0].imageDigest' --output text)
echo "IMAGE_URI=${IMAGE_URI}"
echo "TAG=${TAG}"
echo "PUSHED_DIGEST=${PUSHED_DIGEST}"
```
Result details:
- `IMAGE_URI=386775099533.dkr.ecr.us-west-2.amazonaws.com/kinnoo-dev-server`
- `TAG=phase13-uat-20260410-123644`
- `PUSHED_DIGEST=sha256:3e5b1602bad3f97d750f749bd5fb3ae637f2ec2cfb21b086d5c65a49bdee3456`

### 2) Forced ECS redeployment and waited for stability
Commands run:
```bash
cd /Users/jerry/gh/kinnoo && set -euo pipefail
REGION=us-west-2
CLUSTER=kinnoo-dev-cluster
SERVICE=kinnoo-dev-service
aws --profile jerry --region "$REGION" ecs update-service --cluster "$CLUSTER" --service "$SERVICE" --force-new-deployment --query 'service.{serviceName:serviceName,taskDefinition:taskDefinition,desired:desiredCount,running:runningCount,pending:pendingCount}' --output json
aws --profile jerry --region "$REGION" ecs wait services-stable --cluster "$CLUSTER" --services "$SERVICE"
aws --profile jerry --region "$REGION" ecs describe-services --cluster "$CLUSTER" --services "$SERVICE" --query 'services[0].{serviceName:serviceName,taskDefinition:taskDefinition,desired:desiredCount,running:runningCount,pending:pendingCount,status:status}' --output json
```
Stability verification details:
- Service reached stable state.
- Final deployment status showed single `PRIMARY` deployment.
- Final counts: `running=1`, `pending=0`, `desired=1`.

### 3) Verified running task digest matches pushed image digest
Command run:
```bash
cd /Users/jerry/gh/kinnoo && REGION=us-west-2 && CLUSTER=kinnoo-dev-cluster && SERVICE=kinnoo-dev-service && EXPECTED_DIGEST='sha256:3e5b1602bad3f97d750f749bd5fb3ae637f2ec2cfb21b086d5c65a49bdee3456' && TASK_ARN=$(aws --profile jerry --region "$REGION" ecs list-tasks --cluster "$CLUSTER" --service-name "$SERVICE" --desired-status RUNNING --query 'taskArns[0]' --output text) && aws --profile jerry --region "$REGION" ecs describe-tasks --cluster "$CLUSTER" --tasks "$TASK_ARN" --query 'tasks[0].containers[].{name:name,image:image,imageDigest:imageDigest,lastStatus:lastStatus}' --output json && ACTUAL_DIGEST=$(aws --profile jerry --region "$REGION" ecs describe-tasks --cluster "$CLUSTER" --tasks "$TASK_ARN" --query 'tasks[0].containers[0].imageDigest' --output text) && echo "EXPECTED_DIGEST=$EXPECTED_DIGEST" && echo "ACTUAL_DIGEST=$ACTUAL_DIGEST" && if [ "$ACTUAL_DIGEST" = "$EXPECTED_DIGEST" ]; then echo "DIGEST_MATCH=YES"; else echo "DIGEST_MATCH=NO"; fi
```
Verification details:
- Running container image digest:
  - `sha256:3e5b1602bad3f97d750f749bd5fb3ae637f2ec2cfb21b086d5c65a49bdee3456`
- Expected pushed digest:
  - `sha256:3e5b1602bad3f97d750f749bd5fb3ae637f2ec2cfb21b086d5c65a49bdee3456`
- Result:
  - `DIGEST_MATCH=YES`

## Important Note
- Repository remote branch naming note observed during rollout:
  - `origin` does not expose `main` (`origin/HEAD -> origin/master`).
  - Image was built from current checked-out branch state: `phase13/uat`.
