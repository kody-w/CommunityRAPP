#!/bin/bash
#
# SharePoint Agent - Azure AD App Registration Script
# Registers an app with full SharePoint and Microsoft Graph permissions
#
# Prerequisites:
# - Azure CLI installed and logged in (az login)
# - Global Admin or Application Administrator role in the tenant
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  SharePoint Agent - Azure AD Registration  ${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""

# Check if logged in to Azure
echo -e "${YELLOW}Checking Azure CLI login status...${NC}"
if ! az account show > /dev/null 2>&1; then
    echo -e "${RED}Not logged in to Azure. Please run 'az login' first.${NC}"
    exit 1
fi

# Get current tenant info
TENANT_ID=$(az account show --query tenantId -o tsv)
ACCOUNT_NAME=$(az account show --query user.name -o tsv)
echo -e "${GREEN}✓ Logged in as: ${ACCOUNT_NAME}${NC}"
echo -e "${GREEN}✓ Tenant ID: ${TENANT_ID}${NC}"
echo ""

# App name
APP_NAME="${1:-SharePointCopilotAgent}"
echo -e "${YELLOW}Creating app registration: ${APP_NAME}${NC}"

# Create the app registration
echo -e "${YELLOW}Step 1: Creating Azure AD application...${NC}"
APP_RESULT=$(az ad app create \
    --display-name "$APP_NAME" \
    --sign-in-audience "AzureADMyOrg" \
    --output json)

APP_ID=$(echo $APP_RESULT | jq -r '.appId')
OBJECT_ID=$(echo $APP_RESULT | jq -r '.id')

echo -e "${GREEN}✓ App created with Client ID: ${APP_ID}${NC}"
echo ""

# Create a service principal for the app
echo -e "${YELLOW}Step 2: Creating service principal...${NC}"
SP_RESULT=$(az ad sp create --id $APP_ID --output json 2>/dev/null || echo '{}')
echo -e "${GREEN}✓ Service principal created${NC}"
echo ""

# Create a client secret
echo -e "${YELLOW}Step 3: Creating client secret...${NC}"
SECRET_RESULT=$(az ad app credential reset \
    --id $APP_ID \
    --append \
    --display-name "SharePointAgentSecret" \
    --years 2 \
    --output json)

CLIENT_SECRET=$(echo $SECRET_RESULT | jq -r '.password')
echo -e "${GREEN}✓ Client secret created${NC}"
echo ""

# Define required permissions
# Microsoft Graph API ID: 00000003-0000-0000-c000-000000000000
# SharePoint Online API ID: 00000003-0000-0ff1-ce00-000000000000

echo -e "${YELLOW}Step 4: Adding API permissions...${NC}"

# Microsoft Graph permissions (Application permissions for daemon/service apps)
GRAPH_API_ID="00000003-0000-0000-c000-000000000000"

# Permission IDs for Microsoft Graph (Application permissions)
# Sites.FullControl.All - 5a54b8b3-347c-476d-8f8e-42d5c7424d29
# Sites.ReadWrite.All - 9492366f-7969-46a4-8d15-ed1a20078fff
# Files.ReadWrite.All - 75359482-378d-4052-8f01-80520e7db3cd
# Directory.Read.All - 7ab1d382-f21e-4acd-a863-ba3e13f7da61
# Group.ReadWrite.All - 62a82d76-70ea-41e2-9197-370581804d09
# User.Read.All - df021288-bdef-4463-88db-98f22de89214

echo "Adding Microsoft Graph permissions..."

az ad app permission add \
    --id $APP_ID \
    --api $GRAPH_API_ID \
    --api-permissions \
        5a54b8b3-347c-476d-8f8e-42d5c7424d29=Role \
        9492366f-7969-46a4-8d15-ed1a20078fff=Role \
        75359482-378d-4052-8f01-80520e7db3cd=Role \
        7ab1d382-f21e-4acd-a863-ba3e13f7da61=Role \
        62a82d76-70ea-41e2-9197-370581804d09=Role \
        df021288-bdef-4463-88db-98f22de89214=Role

# SharePoint permissions
SHAREPOINT_API_ID="00000003-0000-0ff1-ce00-000000000000"

# Sites.FullControl.All - 678536fe-1083-478a-9c59-b99265e6b0d3
# Sites.Manage.All - 0c0bf378-bf22-4481-8f81-9e89a9b4960a
# User.Read.All - 741f803b-c850-494e-b5df-cde7c675a1ca
# TermStore.ReadWrite.All - d83cf9c6-da16-4a2f-a0a0-1b4daca2b9d8

echo "Adding SharePoint permissions..."

az ad app permission add \
    --id $APP_ID \
    --api $SHAREPOINT_API_ID \
    --api-permissions \
        678536fe-1083-478a-9c59-b99265e6b0d3=Role \
        0c0bf378-bf22-4481-8f81-9e89a9b4960a=Role \
        741f803b-c850-494e-b5df-cde7c675a1ca=Role \
        d83cf9c6-da16-4a2f-a0a0-1b4daca2b9d8=Role

echo -e "${GREEN}✓ API permissions added${NC}"
echo ""

# Grant admin consent
echo -e "${YELLOW}Step 5: Granting admin consent...${NC}"
echo -e "${YELLOW}Note: This requires Global Administrator or Privileged Role Administrator${NC}"

# Wait a moment for permissions to propagate
sleep 5

az ad app permission admin-consent --id $APP_ID 2>/dev/null || {
    echo -e "${YELLOW}⚠ Could not auto-grant admin consent. Please grant manually in Azure Portal.${NC}"
}

echo -e "${GREEN}✓ Admin consent granted (or needs manual approval)${NC}"
echo ""

# Output configuration
echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  Registration Complete!  ${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""
echo -e "${GREEN}App Registration Details:${NC}"
echo ""
echo -e "  Tenant ID:     ${TENANT_ID}"
echo -e "  Client ID:     ${APP_ID}"
echo -e "  Client Secret: ${CLIENT_SECRET}"
echo -e "  Object ID:     ${OBJECT_ID}"
echo ""
echo -e "${YELLOW}Add these to your local.settings.json:${NC}"
echo ""
echo '{
  "Values": {
    "SHAREPOINT_TENANT_ID": "'$TENANT_ID'",
    "SHAREPOINT_CLIENT_ID": "'$APP_ID'",
    "SHAREPOINT_CLIENT_SECRET": "'$CLIENT_SECRET'"
  }
}'
echo ""
echo -e "${YELLOW}Or for Azure Function App settings:${NC}"
echo ""
echo "az functionapp config appsettings set --name YOUR_FUNCTION_APP --resource-group YOUR_RG \\"
echo "  --settings SHAREPOINT_TENANT_ID=$TENANT_ID \\"
echo "  SHAREPOINT_CLIENT_ID=$APP_ID \\"
echo "  SHAREPOINT_CLIENT_SECRET='$CLIENT_SECRET'"
echo ""

# Save to file
CONFIG_FILE="sharepoint_agent_config.json"
cat > $CONFIG_FILE << EOF
{
  "tenantId": "$TENANT_ID",
  "clientId": "$APP_ID",
  "clientSecret": "$CLIENT_SECRET",
  "objectId": "$OBJECT_ID",
  "appName": "$APP_NAME",
  "createdAt": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "permissions": {
    "microsoftGraph": [
      "Sites.FullControl.All",
      "Sites.ReadWrite.All",
      "Files.ReadWrite.All",
      "Directory.Read.All",
      "Group.ReadWrite.All",
      "User.Read.All"
    ],
    "sharePoint": [
      "Sites.FullControl.All",
      "Sites.Manage.All",
      "User.Read.All",
      "TermStore.ReadWrite.All"
    ]
  }
}
EOF

echo -e "${GREEN}✓ Configuration saved to: ${CONFIG_FILE}${NC}"
echo ""
echo -e "${YELLOW}Important: Store the client secret securely - it won't be shown again!${NC}"
echo ""

# Verification steps
echo -e "${BLUE}============================================${NC}"
echo -e "${BLUE}  Verification Steps  ${NC}"
echo -e "${BLUE}============================================${NC}"
echo ""
echo "1. Verify in Azure Portal:"
echo "   https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationMenuBlade/~/Overview/appId/$APP_ID"
echo ""
echo "2. Check API permissions:"
echo "   https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationMenuBlade/~/CallAnAPI/appId/$APP_ID"
echo ""
echo "3. Test the SharePoint agent:"
echo '   curl -X POST http://localhost:7071/api/businessinsightbot_function \'
echo '     -H "Content-Type: application/json" \'
echo '     -d '\''{"user_input": "list all SharePoint sites", "conversation_history": []}'\'
echo ""
