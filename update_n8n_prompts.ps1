# THROWAWAY - Update n8n workflow prompts via direct PostgreSQL update
# Usage: pwsh -File update_n8n_prompts.ps1

$VPS = "root@178.105.35.94"
$COMPOSE = "docker compose -f /opt/hermes/docker-compose.yml"

# Template for the SQL file we'll write on the VPS
$SqlContent = @'
-- Verify current structure
SELECT id, name,
       nodes::json->0->>'name' AS tc_n0_name,
       nodes::json->0->'parameters'->>'promptType' AS tc_promptType,
       CASE WHEN nodes::json->0->'parameters'->'messages' IS NOT NULL THEN 'HAS messages' ELSE 'NO messages' END AS tc_has_messages,
       substring(nodes::json->0->'parameters'->'messages'->'messageValues'->0->>'message' from 1 for 100) AS tc_msg_preview,
       nodes::json->1->>'name' AS tw_n1_name,
       CASE WHEN nodes::json->1->'parameters'->>'text' IS NOT NULL THEN 'HAS text' ELSE 'NO text' END AS tw_has_text,
       substring(nodes::json->1->'parameters'->>'text' from 1 for 100) AS tw_text_preview
FROM workflow_entity
WHERE id IN ('ekkM6AJIW4H3GJ4x', 'mUZWMuPy9phZby5H');
'@

# Write SQL file to VPS
Write-Host "=== Step 1: Verifying current DB structure ==="
$tempFile = "/tmp/verify_workflows.sql"
ssh -o StrictHostKeyChecking=no $VPS "cat > $tempFile << 'EOF'
$SqlContent
EOF
cat $tempFile | $COMPOSE exec -T postgres psql -U n8n -d n8n"
