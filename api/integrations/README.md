# Integration Module Structure

This document outlines the refactored structure of the LumTrails integration system.

## Overview

The integration system has been refactored from a single monolithic file into modular components organized by platform. This improves maintainability, separation of concerns, and makes it easier to add new integrations.

## Directory Structure

```
api/integrations/
├── shared/
│   ├── __init__.py
│   ├── database.py      # Shared database utilities and clients
│   └── models.py        # Pydantic models used across integrations
├── github/
│   ├── __init__.py      # Exports github_router and functions
│   └── routes.py        # All GitHub-specific routes and logic
├── slack/
│   ├── __init__.py      # Exports slack_router
│   └── routes.py        # All Slack-specific routes and logic
├── notion/
│   ├── __init__.py      # Exports notion_router
│   └── routes.py        # All Notion-specific routes and logic
└── integration_routes.py # Main router that combines all sub-routers
```

## Module Responsibilities

### Shared Module (`shared/`)

**`database.py`**
- Firestore and Secret Manager client initialization
- Common database operations (`get_user_integrations_doc`, `get_secret`, `store_secret`)
- Datetime serialization utilities
- Project configuration

**`models.py`**
- Pydantic models for request/response validation
- Common models: `IntegrationConfig`, `OAuthCallback`
- Platform-specific models: `GitHubConfig`, `GitHubConfigUpdate`, `SlackWebhookConfig`, `NotionConfig`

### GitHub Module (`github/`)

**Features:**
- Full OAuth 2.0 flow implementation
- Repository selection and validation
- Issue creation from scan results
- Configuration management (severity filters, grouping options)
- Token management and error handling
- Statistics tracking

**Routes:**
- `PUT /integrations/github/config` - Update GitHub configuration
- `PUT /integrations/github/status` - Enable/disable GitHub integration
- `POST /integrations/github/disconnect` - Disconnect GitHub integration
- `GET /integrations/github/oauth/authorize` - Start OAuth flow
- `GET /integrations/github/oauth/callback` - Handle OAuth callback
- `GET /integrations/github/repositories` - List user repositories

**Important Functions:**
- `create_github_issues_for_scan()` - Creates GitHub issues from scan results
- `convert_scan_to_github_issues()` - Converts scan data to GitHub issue format
- `verify_github_repository()` - Validates repository access
- `clear_github_connection()` - Cleans up invalid connections

### Slack Module (`slack/`)

**Features:**
- Webhook URL validation and testing
- Message posting to Slack channels
- Configuration management for notifications

**Routes:**
- `POST /integrations/slack/webhook` - Connect Slack via webhook
- `POST /integrations/slack/disconnect` - Disconnect Slack integration

### Notion Module (`notion/`)

**Features:**
- Placeholder for future Notion integration development
- Basic disconnect functionality

**Routes:**
- `POST /integrations/notion/disconnect` - Disconnect Notion integration

### Main Integration Router (`integration_routes.py`)

**Features:**
- Combines all platform-specific routers
- Provides common integration endpoints
- Manages default integration structure

**Routes:**
- `GET /integrations` - Get all user integrations with default structure
- `PUT /integrations/{platform}/config` - Generic config update for Notion/Slack

## API Route Mapping

All existing routes remain **exactly the same** from the frontend perspective:

| Route | Handler | Module |
|-------|---------|--------|
| `GET /integrations` | Main router | `integration_routes.py` |
| `PUT /integrations/github/config` | GitHub-specific | `github/routes.py` |
| `PUT /integrations/github/status` | GitHub-specific | `github/routes.py` |
| `GET /integrations/github/oauth/authorize` | GitHub-specific | `github/routes.py` |
| `GET /integrations/github/oauth/callback` | GitHub-specific | `github/routes.py` |
| `GET /integrations/github/repositories` | GitHub-specific | `github/routes.py` |
| `POST /integrations/slack/webhook` | Slack-specific | `slack/routes.py` |
| `POST /integrations/{platform}/disconnect` | Platform-specific | Each module handles its own |
| `PUT /integrations/{platform}/config` | Generic (Notion/Slack) | Main router |

## Key Benefits

1. **Separation of Concerns**: Each integration has its own dedicated module
2. **Maintainability**: Easier to find and modify platform-specific code
3. **Scalability**: Simple to add new integration platforms
4. **Testing**: Each module can be tested independently
5. **Code Reuse**: Shared utilities avoid duplication
6. **Type Safety**: Pydantic models provide clear contracts

## GitHub Integration (Critical - Working)

⚠️ **IMPORTANT**: The GitHub integration is the only fully working integration and has been carefully preserved during refactoring. All existing functionality remains intact:

- OAuth flow with proper state management
- Repository validation and selection  
- Issue creation with multiple grouping options
- Severity filtering (High/Medium/Low)
- Token refresh and error handling
- Statistics tracking

## Development Guidelines

### Adding a New Integration

1. Create a new folder: `integrations/{platform}/`
2. Add `__init__.py` with router exports
3. Create `routes.py` with platform-specific logic
4. Add platform models to `shared/models.py` if needed
5. Update main `integration_routes.py` to include the new router
6. Update default integration structure in `get_user_integrations()`

### Modifying Existing Integrations

1. Platform-specific changes go in the respective `{platform}/routes.py`
2. Shared functionality goes in `shared/database.py`
3. Model changes go in `shared/models.py`
4. Always test GitHub integration after changes

## Migration Notes

- No breaking changes to existing API contracts
- All imports in `main.py` remain unchanged
- Environment variables and deployment configuration unchanged
- Integration worker service (`integrations/main.py`) is separate and unaffected

## Testing

After deployment, verify:
1. `GET /integrations` returns proper default structure
2. GitHub OAuth flow works end-to-end
3. Repository selection and configuration work
4. Slack webhook connection works
5. All disconnect operations work properly
