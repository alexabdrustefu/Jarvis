"""OpenAPI 3.0 contract served to Swagger UI at runtime."""

OPENAPI = {
    "openapi": "3.0.3",
    "info": {
        "title": "J.A.R.V.I.S. Local API",
        "version": "1.0.0",
        "description": "API locale per chat, menu, promemoria, routine e statistiche.",
    },
    "servers": [{"url": "http://127.0.0.1:8765", "description": "Listener locale"}],
    "tags": [
        {"name": "System", "description": "Stato, documentazione e menu."},
        {"name": "Chat", "description": "Conversazione con il core JARVIS."},
        {"name": "Productivity", "description": "Promemoria e routine locali."},
        {"name": "Statistics", "description": "Metriche aggregate locali."},
    ],
    "paths": {
        "/api/v1/health": {
            "get": {
                "tags": ["System"],
                "summary": "Stato API e provider",
                "responses": {"200": {
                    "description": "Stato del servizio",
                    "content": {"application/json": {"schema": {"$ref": "#/components/schemas/HealthResponse"}}},
                }},
            },
        },
        "/api/v1/menu": {
            "get": {
                "tags": ["System"],
                "summary": "Menu delle funzionalità e link API",
                "responses": {"200": {
                    "description": "Catalogo navigabile",
                    "content": {"application/json": {"schema": {"$ref": "#/components/schemas/MenuResponse"}}},
                }},
            },
        },
        "/api/v1/stats": {
            "get": {
                "tags": ["Statistics"],
                "summary": "Statistiche aggregate locali",
                "responses": {"200": {
                    "description": "Conteggi conversazioni, memoria e attività",
                    "content": {"application/json": {"schema": {"$ref": "#/components/schemas/StatisticsResponse"}}},
                }},
            },
        },
        "/api/v1/chat": {
            "post": {
                "tags": ["Chat"],
                "summary": "Invia un messaggio a JARVIS",
                "requestBody": {"required": True, "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ChatRequest"}}}},
                "responses": {
                    "200": {"description": "Risposta dell'assistente", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ChatResponse"}}}},
                    "400": {"$ref": "#/components/responses/ApiError"},
                    "413": {"$ref": "#/components/responses/ApiError"},
                },
            },
        },
        "/api/v1/reminders": {
            "get": {
                "tags": ["Productivity"],
                "summary": "Elenca promemoria",
                "parameters": [{"name": "include_done", "in": "query", "schema": {"type": "boolean", "default": False}}],
                "responses": {"200": {"description": "Lista promemoria", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ReminderList"}}}}},
            },
            "post": {
                "tags": ["Productivity"],
                "summary": "Crea un promemoria",
                "requestBody": {"required": True, "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ReminderRequest"}}}},
                "responses": {
                    "201": {"description": "Promemoria creato", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/Reminder"}}}},
                    "400": {"$ref": "#/components/responses/ApiError"},
                },
            },
        },
        "/api/v1/reminders/{reminder_id}": {
            "patch": {
                "tags": ["Productivity"],
                "summary": "Completa un promemoria",
                "parameters": [{"$ref": "#/components/parameters/ReminderId"}],
                "requestBody": {"required": True, "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ReminderStatus"}}}},
                "responses": {
                    "200": {"description": "Promemoria completato", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ReminderStatus"}}}},
                    "404": {"$ref": "#/components/responses/ApiError"},
                },
            },
            "delete": {
                "tags": ["Productivity"],
                "summary": "Elimina un promemoria",
                "parameters": [{"$ref": "#/components/parameters/ReminderId"}],
                "responses": {
                    "200": {"description": "Promemoria eliminato", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ReminderDeleted"}}}},
                    "404": {"$ref": "#/components/responses/ApiError"},
                },
            },
        },
        "/api/v1/routines": {
            "get": {
                "tags": ["Productivity"],
                "summary": "Elenca routine configurate",
                "responses": {"200": {"description": "Lista routine", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/RoutineList"}}}}},
            },
        },
    },
    "components": {
        "schemas": {
            "ChatRequest": {"type": "object", "required": ["message"], "properties": {"message": {"type": "string", "minLength": 1, "maxLength": 12000}}},
            "ChatResponse": {"type": "object", "required": ["reply"], "properties": {"reply": {"type": "string"}}},
            "HealthResponse": {"type": "object", "properties": {"status": {"type": "string"}, "service": {"type": "string"}, "version": {"type": "string"}, "providers": {"type": "object", "additionalProperties": True}}},
            "MenuItem": {"type": "object", "required": ["id", "label", "description", "href", "methods"], "properties": {"id": {"type": "string"}, "label": {"type": "string"}, "description": {"type": "string"}, "href": {"type": "string"}, "methods": {"type": "array", "items": {"type": "string"}}}},
            "MenuResponse": {"type": "object", "properties": {"items": {"type": "array", "items": {"$ref": "#/components/schemas/MenuItem"}}}},
            "StatisticsResponse": {"type": "object", "properties": {"conversations": {"type": "object", "properties": {"messages_total": {"type": "integer"}, "messages_today": {"type": "integer"}}}, "facts": {"type": "object", "properties": {"saved": {"type": "integer"}}}, "productivity": {"type": "object", "additionalProperties": {"type": "integer"}}, "api": {"type": "object", "properties": {"requests_total": {"type": "integer"}, "requests_today": {"type": "integer"}, "errors_total": {"type": "integer"}, "average_duration_ms": {"type": "number"}, "by_route": {"type": "array", "items": {"$ref": "#/components/schemas/ApiRouteStatistic"}}}}, "provider": {"type": "string", "nullable": True}}},
            "ApiRouteStatistic": {"type": "object", "properties": {"method": {"type": "string"}, "route": {"type": "string"}, "requests": {"type": "integer"}, "errors": {"type": "integer"}, "average_duration_ms": {"type": "number"}}},
            "ReminderRequest": {"type": "object", "required": ["title"], "properties": {"title": {"type": "string", "minLength": 1, "maxLength": 500}, "due_at": {"type": "string", "format": "date-time", "nullable": True}}},
            "Reminder": {"type": "object", "required": ["id", "title", "due_at", "status"], "properties": {"id": {"type": "integer"}, "title": {"type": "string"}, "due_at": {"type": "string", "format": "date-time", "nullable": True}, "status": {"type": "string", "enum": ["pending", "done"]}}},
            "ReminderList": {"type": "object", "properties": {"items": {"type": "array", "items": {"$ref": "#/components/schemas/Reminder"}}}},
            "ReminderStatus": {"type": "object", "required": ["status"], "properties": {"status": {"type": "string", "enum": ["done"]}}},
            "ReminderDeleted": {"type": "object", "properties": {"id": {"type": "integer"}, "deleted": {"type": "boolean"}}},
            "Routine": {"type": "object", "properties": {"name": {"type": "string"}, "steps": {"type": "array", "items": {"type": "string"}}}},
            "RoutineList": {"type": "object", "properties": {"items": {"type": "array", "items": {"$ref": "#/components/schemas/Routine"}}}},
            "ApiError": {"type": "object", "properties": {"error": {"type": "object", "properties": {"code": {"type": "string"}, "message": {"type": "string"}}}}},
        },
        "parameters": {"ReminderId": {"name": "reminder_id", "in": "path", "required": True, "schema": {"type": "integer", "minimum": 1}}},
        "responses": {"ApiError": {"description": "Errore di richiesta", "content": {"application/json": {"schema": {"$ref": "#/components/schemas/ApiError"}}}}},
    },
}

SWAGGER_HTML = """<!doctype html>
<html lang="it"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>J.A.R.V.I.S. API · Swagger UI</title>
<link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css">
<style>body{margin:0;background:#080b12} .swagger-ui .topbar{background:#111722}</style>
</head><body><div id="swagger-ui"></div>
<script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
<script>window.onload=()=>SwaggerUIBundle({url:'/openapi.json',dom_id:'#swagger-ui',deepLinking:true});</script>
</body></html>"""
