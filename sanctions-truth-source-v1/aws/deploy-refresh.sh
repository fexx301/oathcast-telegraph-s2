#!/bin/sh
# Create or update the daily refresher Lambda and its EventBridge schedule. Usage: sh aws/deploy-refresh.sh
# Creates: IAM role telegraph-sanctions-refresh-lambda (logs + lambda:UpdateFunctionCode on the screen function only),
# Lambda telegraph-sanctions-refresh (900 s, 1024 MB), EventBridge rule telegraph-sanctions-daily (06:15 UTC).
set -eu
cd "$(dirname "$0")/.."
R=eu-north-1; F=telegraph-sanctions-refresh; ROLE=telegraph-sanctions-refresh-lambda; TARGET=telegraph-sanctions-screen
ACCT=$(aws sts get-caller-identity --query Account --output text)
rm -rf aws/rbuild aws/refresh.zip && mkdir aws/rbuild
cp aws/refresh_function.py aws/lambda_function.py api/_screen.py build_index.py aws/rbuild/
(cd aws/rbuild && zip -q -r ../refresh.zip .)
if ! aws iam get-role --role-name $ROLE >/dev/null 2>&1; then
  aws iam create-role --role-name $ROLE --assume-role-policy-document \
    '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"lambda.amazonaws.com"},"Action":"sts:AssumeRole"}]}' >/dev/null
  aws iam attach-role-policy --role-name $ROLE --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
  sleep 12  # IAM propagation
fi
# Only permission beyond logs: replace the code of the one screen function.
aws iam put-role-policy --role-name $ROLE --policy-name update-screen-code --policy-document \
  "{\"Version\":\"2012-10-17\",\"Statement\":[{\"Effect\":\"Allow\",\"Action\":\"lambda:UpdateFunctionCode\",\"Resource\":\"arn:aws:lambda:$R:$ACCT:function:$TARGET\"}]}"
ARN=$(aws iam get-role --role-name $ROLE --query Role.Arn --output text)
if aws lambda get-function --region $R --function-name $F >/dev/null 2>&1; then
  aws lambda update-function-code --region $R --function-name $F --zip-file fileb://aws/refresh.zip >/dev/null
else
  aws lambda create-function --region $R --function-name $F --runtime python3.12 --architectures arm64 \
    --handler refresh_function.handler --role "$ARN" --memory-size 1024 --timeout 900 \
    --environment "Variables={SCREEN_FUNCTION=$TARGET}" --zip-file fileb://aws/refresh.zip >/dev/null
  aws lambda wait function-active-v2 --region $R --function-name $F
fi
aws lambda wait function-updated-v2 --region $R --function-name $F
RULE_ARN=$(aws events put-rule --region $R --name telegraph-sanctions-daily --schedule-expression "cron(15 6 * * ? *)" --query RuleArn --output text)
aws lambda add-permission --region $R --function-name $F --statement-id daily-schedule --action lambda:InvokeFunction \
  --principal events.amazonaws.com --source-arn "$RULE_ARN" >/dev/null 2>&1 || true
aws events put-targets --region $R --rule telegraph-sanctions-daily \
  --targets "Id=refresh,Arn=arn:aws:lambda:$R:$ACCT:function:$F" >/dev/null
echo "refresher $F scheduled daily 06:15 UTC"
