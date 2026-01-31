# SharePoint Agent Setup Guide

This guide walks you through registering an Azure AD application for the SharePoint Agent with full Microsoft Graph and SharePoint permissions.

## Option 1: Azure Portal Registration (Recommended)

### Step 1: Create App Registration

1. Go to [Azure Portal - App Registrations](https://portal.azure.com/#view/Microsoft_AAD_RegisteredApps/ApplicationsListBlade)
2. Click **+ New registration**
3. Fill in:
   - **Name**: `SharePointCopilotAgent`
   - **Supported account types**: Accounts in this organizational directory only
   - **Redirect URI**: Leave blank (not needed for daemon apps)
4. Click **Register**

### Step 2: Note Your App IDs

After registration, copy these values from the **Overview** page:
- **Application (client) ID**: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`
- **Directory (tenant) ID**: `xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx`

### Step 3: Create Client Secret

1. Go to **Certificates & secrets**
2. Click **+ New client secret**
3. Add description: `SharePointAgentSecret`
4. Set expiration: 24 months (recommended)
5. Click **Add**
6. **⚠️ COPY THE VALUE IMMEDIATELY** - it won't be shown again!

### Step 4: Add API Permissions

1. Go to **API permissions**
2. Click **+ Add a permission**

#### Microsoft Graph Permissions (Application)

Click **Microsoft Graph** → **Application permissions** → Add these:

| Permission | Description |
|------------|-------------|
| `Sites.FullControl.All` | Full control of all site collections |
| `Sites.ReadWrite.All` | Read and write items in all site collections |
| `Files.ReadWrite.All` | Read and write all files |
| `Directory.Read.All` | Read directory data |
| `Group.ReadWrite.All` | Read and write all groups |
| `User.Read.All` | Read all users' full profiles |

#### SharePoint Permissions (Application)

Click **Add a permission** → **SharePoint** → **Application permissions** → Add these:

| Permission | Description |
|------------|-------------|
| `Sites.FullControl.All` | Have full control of all site collections |
| `Sites.Manage.All` | Create, edit, and delete items and lists |
| `User.Read.All` | Read user profiles |
| `TermStore.ReadWrite.All` | Read and write managed metadata |

### Step 5: Grant Admin Consent

1. Still on **API permissions** page
2. Click **Grant admin consent for [Your Organization]**
3. Confirm by clicking **Yes**
4. All permissions should show ✅ green checkmarks

## Option 2: PowerShell Registration

If you have Azure AD PowerShell module installed:

```powershell
# Connect to Azure AD
Connect-AzureAD

# Create the app
$app = New-AzureADApplication -DisplayName "SharePointCopilotAgent"

# Create service principal
$sp = New-AzureADServicePrincipal -AppId $app.AppId

# Create client secret
$secret = New-AzureADApplicationPasswordCredential -ObjectId $app.ObjectId -CustomKeyIdentifier "SharePointAgentSecret" -EndDate (Get-Date).AddYears(2)

# Output credentials
Write-Host "Tenant ID: $((Get-AzureADTenantDetail).ObjectId)"
Write-Host "Client ID: $($app.AppId)"
Write-Host "Client Secret: $($secret.Value)"
```

Then add permissions via Azure Portal (Step 4 above).

## Option 3: Microsoft Graph PowerShell

```powershell
# Install module if needed
Install-Module Microsoft.Graph -Scope CurrentUser

# Connect with admin scope
Connect-MgGraph -Scopes "Application.ReadWrite.All", "AppRoleAssignment.ReadWrite.All"

# Create app
$app = New-MgApplication -DisplayName "SharePointCopilotAgent"

# Create secret
$passwordCred = @{
    displayName = 'SharePointAgentSecret'
    endDateTime = (Get-Date).AddYears(2)
}
$secret = Add-MgApplicationPassword -ApplicationId $app.Id -PasswordCredential $passwordCred

# Output
Write-Host "Client ID: $($app.AppId)"
Write-Host "Client Secret: $($secret.SecretText)"
```

---

## Configuration

### Local Development (local.settings.json)

Add these to your `local.settings.json`:

```json
{
  "IsEncrypted": false,
  "Values": {
    "SHAREPOINT_TENANT_ID": "your-tenant-id",
    "SHAREPOINT_CLIENT_ID": "your-client-id",
    "SHAREPOINT_CLIENT_SECRET": "your-client-secret"
  }
}
```

### Azure Function App Settings

```bash
az functionapp config appsettings set \
  --name YOUR_FUNCTION_APP \
  --resource-group YOUR_RESOURCE_GROUP \
  --settings \
    SHAREPOINT_TENANT_ID="your-tenant-id" \
    SHAREPOINT_CLIENT_ID="your-client-id" \
    SHAREPOINT_CLIENT_SECRET="your-client-secret"
```

---

## Testing the Agent

### List Sites
```bash
curl -X POST http://localhost:7071/api/businessinsightbot_function \
  -H "Content-Type: application/json" \
  -d '{
    "user_input": "List all SharePoint sites",
    "conversation_history": []
  }'
```

### Example Prompts

| Action | Example Prompt |
|--------|----------------|
| List sites | "Show me all SharePoint sites" |
| Search sites | "Find SharePoint sites about marketing" |
| List documents | "List files in the Documents library on [site]" |
| Upload file | "Upload this report to the Marketing site" |
| Create folder | "Create a folder called Q1-Reports in the Finance library" |
| Search content | "Search for budget documents in SharePoint" |
| Create list | "Create a new Tasks list on the Project site" |
| Share file | "Share the quarterly report with the sales team" |

---

## Permissions Reference

### Microsoft Graph API Permissions

| Permission | Type | Description |
|------------|------|-------------|
| Sites.FullControl.All | Application | Full control of all site collections |
| Sites.ReadWrite.All | Application | Read/write items in all site collections |
| Files.ReadWrite.All | Application | Read/write files in all site collections |
| Directory.Read.All | Application | Read directory data |
| Group.ReadWrite.All | Application | Read/write all groups (for team sites) |
| User.Read.All | Application | Read all users' profiles |

### SharePoint API Permissions

| Permission | Type | Description |
|------------|------|-------------|
| Sites.FullControl.All | Application | Full control of all site collections |
| Sites.Manage.All | Application | Create, edit, delete items and lists |
| User.Read.All | Application | Read user profiles |
| TermStore.ReadWrite.All | Application | Read/write managed metadata |

---

## Troubleshooting

### "Insufficient privileges" Error
- Ensure you're logged into the correct tenant
- Verify you have Global Admin or Application Administrator role
- Try using Azure Portal instead of CLI

### "AADSTS700016: Application not found"
- Wait 1-2 minutes after app creation for propagation
- Verify tenant ID matches where app was created

### "Access denied" on SharePoint operations
- Verify admin consent was granted for all permissions
- Check that app has Sites.FullControl.All permission
- Ensure the service principal exists

### Token errors
- Verify client secret hasn't expired
- Check that SHAREPOINT_CLIENT_SECRET is correct
- Ensure environment variables are loaded

---

## Security Notes

1. **Client Secret Rotation**: Rotate secrets every 6-12 months
2. **Principle of Least Privilege**: Only grant permissions actually needed
3. **Audit Logging**: Enable Azure AD sign-in logs for the app
4. **Conditional Access**: Consider applying policies to the service principal
5. **Never commit secrets**: Use Azure Key Vault or environment variables
