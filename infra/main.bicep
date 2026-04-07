// SNAC-v2 Infrastructure on Azure
// Azure Static Web Apps + Functions

@description('Environment name')
param environmentName string = 'snac'

@description('Azure location - must be one that supports Static Web Apps')
param location string = 'westus2'

@description('PostgreSQL admin password')
@secure()
param postgresPassword string = 'SnacPass123!'

@description('Redis password')
@secure()
param redisPassword string = 'RedisPass123!'

// Storage Account
resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: replace('${environmentName}storage', '-', '')
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
}

// Application Insights
resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: '${environmentName}-ai'
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    Request_Source: 'rest'
    RetentionInDays: 30
  }
}

// Log Analytics Workspace
resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2020-08-01' = {
  name: '${environmentName}-law'
  location: location
  sku: {
    name: 'PerGB2018'
  }
}

// Key Vault for secrets - using unique name to avoid soft-delete conflict
resource keyVault 'Microsoft.KeyVault/vaults@2023-02-01' = {
  name: '${environmentName}-kv-new'
  location: location
  properties: {
    sku: {
      family: 'A'
      name: 'standard'
    }
    tenantId: subscription().tenantId
    enableRbacAuthorization: true
    enableSoftDelete: true
    softDeleteRetentionInDays: 90
  }
}

// Static Web App - frontend
resource staticWebApp 'Microsoft.Web/staticSites@2022-09-01' = {
  name: '${environmentName}-frontend'
  location: location
  sku: {
    name: 'Free'
  }
  tags: {
    'azd-service-name': 'frontend'
  }
  properties: {}
}

// Function App - backend - using consumption plan
resource functionApp 'Microsoft.Web/sites@2022-09-01' = {
  name: '${environmentName}-backend'
  location: location
  kind: 'functionapp'
  tags: {
    'azd-service-name': 'backend'
  }
  properties: {
    clientAffinityEnabled: false
    reserved: true
  }
}

// Output connection strings
output storageAccountName string = storageAccount.name
output appInsightsInstrumentationKey string = appInsights.properties.InstrumentationKey
output keyVaultUri string = keyVault.properties.vaultUri
output backendAppUrl string = 'https://${functionApp.properties.defaultHostName}'