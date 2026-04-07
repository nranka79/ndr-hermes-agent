#!/bin/bash
# Fix for Railway build issue
# Updates build command via Railway API to use simpler approach

RAILWAY_TOKEN=${RAILWAY_TOKEN:-""}
if [ -z "$RAILWAY_TOKEN" ]; then
    echo "Error: RAILWAY_TOKEN environment variable not set"
    echo "Get your token from: https://railway.app/account/tokens"
    exit 1
fi

# Railway service details
SERVICE_ID="42cde9f1-5f74-4f01-b236-f78f3479abcd"
ENVIRONMENT_ID="91a2dcb8-6ed4-4009-9bed-19a979ced590"

# New build command - simpler, doesn't require env vars at build time
NEW_BUILD_CMD="pip install -e '.[messaging]' requests && npm install -g @googleworkspace/cli"

# Alternative simpler build command if above fails:
# NEW_BUILD_CMD="pip install -e . requests && npm install -g @googleworkspace/cli"

echo "Updating Railway build command..."
echo "New command: $NEW_BUILD_CMD"

# GraphQL mutation to update build command
QUERY='
mutation updateService($input: ServiceInstanceUpdateInput!) {
  serviceInstanceUpdate(input: $input) {
    id
    buildCommand
  }
}
'

VARIABLES="{
  \"input\": {
    \"serviceId\": \"'$SERVICE_ID'\",
    \"buildCommand\": \"'$NEW_BUILD_CMD'\"
  }
}"

curl -X POST https://backboard.railway.app/graphql/v2 \
  -H "Authorization: Bearer $RAILWAY_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"$QUERY\", \"variables\": $VARIABLES}"

echo ""
echo "Done! Now click Deploy in Railway Dashboard"
