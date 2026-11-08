#!/bin/sh
# Build the zip and create or update the Lambda + public Function URL. Usage: sh aws/deploy.sh
set -eu
cd "$(dirname "$0")/.."
R=eu-north-1; F=telegraph-sanctions-screen; ROLE=telegraph-sanctions-screen-lambda
rm -rf aws/build aws/fn.zip && mkdir aws/build
cp aws/lambda_function.py api/_screen.py api/index.json.gz aws/build/
(cd aws/build && zip -q -r ../fn.zip .)
if ! aws iam get-role --role-name $ROLE >/dev/null 2>&1; then
  aws iam create-role --role-name $ROLE --assume-role-policy-document \
    '{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"lambda.amazonaws.com"},"Action":"sts:AssumeRole"}]}' >/dev/null
  aws iam attach-role-policy --role-name $ROLE --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
  sleep 12  # IAM propagation
fi
ARN=$(aws iam get-role --role-name $ROLE --query Role.Arn --output text)
if aws lambda get-function --region $R --function-name $F >/dev/null 2>&1; then
  aws lambda update-function-code --region $R --function-name $F --zip-file fileb://aws/fn.zip >/dev/null
else
  aws lambda create-function --region $R --function-name $F --runtime python3.12 --architectures arm64 \
    --handler lambda_function.handler --role "$ARN" --memory-size 512 --timeout 15 --zip-file fileb://aws/fn.zip >/dev/null
  aws lambda wait function-active-v2 --region $R --function-name $F
  aws lambda create-function-url-config --region $R --function-name $F --auth-type NONE >/dev/null
  aws lambda add-permission --region $R --function-name $F --statement-id public-url \
    --action lambda:InvokeFunctionUrl --principal '*' --function-url-auth-type NONE >/dev/null
  aws lambda add-permission --region $R --function-name $F --statement-id public-invoke \
    --action lambda:InvokeFunction --principal '*' --invoked-via-function-url >/dev/null 2>&1 || true
fi
aws lambda wait function-updated-v2 --region $R --function-name $F
aws lambda get-function-url-config --region $R --function-name $F --query FunctionUrl --output text
