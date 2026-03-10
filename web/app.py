from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.base import BaseHTTPMiddleware

from core.plugin_loader import load_plugins
from web.config import load_config


root_path = Path(__file__).resolve().parent.parent
templates = Jinja2Templates(directory=str(root_path / "web" / "templates"))

config = load_config()
app = FastAPI(title="Radiologists Agent (LAN)")


class ApiLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if not config.enable_request_logging or not request.url.path.startswith("/api/"):
            return await call_next(request)

        method = request.method
        path = request.url.path
        response = await call_next(request)
        status = response.status_code

        # Без логирования тел запросов/ответов, только метаданные.
        print(f"[API] {method} {path} -> {status}")
        return response


app.add_middleware(ApiLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


_plugins = load_plugins()
_plugins_by_id: Dict[str, Any] = {}
for p in _plugins:
    pid = getattr(p, "plugin_id", p.get_name())
    _plugins_by_id[str(pid)] = p


def _serialize_plugin(p) -> dict:
    return {
        "id": getattr(p, "plugin_id", p.get_name()),
        "name": p.get_name(),
        "description": p.get_description(),
    }


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    plugins = [_serialize_plugin(p) for p in _plugins]
    return templates.TemplateResponse(
        "index.html",
        {"request": request, "plugins": plugins},
    )


@app.get("/plugins/{plugin_id}", response_class=HTMLResponse)
async def plugin_page(plugin_id: str, request: Request):
    plugin = _plugins_by_id.get(plugin_id)
    if not plugin:
        raise HTTPException(status_code=404, detail="Плагин не найден")

    schema = getattr(plugin, "get_form_schema", None)
    schema_data = schema() if callable(schema) else None

    return templates.TemplateResponse(
        "plugin.html",
        {
            "request": request,
            "plugin": _serialize_plugin(plugin),
            "schema": schema_data,
        },
    )


@app.get("/api/plugins")
async def api_plugins():
    return [_serialize_plugin(p) for p in _plugins]


@app.get("/api/plugins/{plugin_id}/schema")
async def api_plugin_schema(plugin_id: str):
    plugin = _plugins_by_id.get(plugin_id)
    if not plugin:
        raise HTTPException(status_code=404, detail="Плагин не найден")
    schema_fn = getattr(plugin, "get_form_schema", None)
    if not callable(schema_fn):
        return {}
    return schema_fn()


@app.post("/api/plugins/{plugin_id}/description")
async def api_plugin_description(plugin_id: str, payload: Dict[str, Any]):
    plugin = _plugins_by_id.get(plugin_id)
    if not plugin:
        raise HTTPException(status_code=404, detail="Плагин не найден")

    generate_fn = getattr(plugin, "generate_spine_from_dict", None) or getattr(
        plugin,
        "generate_description_from_dict",
        None,
    )
    if not callable(generate_fn):
        raise HTTPException(status_code=400, detail="Плагин не поддерживает генерацию описания через API")

    try:
        result = generate_fn(payload)
    except ValueError as exc:
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    description = result.get("description") if isinstance(result, dict) else str(result)
    return {"description": description}


@app.post("/api/plugins/{plugin_id}/conclusion")
async def api_plugin_conclusion(plugin_id: str, payload: Dict[str, Any]):
    plugin = _plugins_by_id.get(plugin_id)
    if not plugin:
        raise HTTPException(status_code=404, detail="Плагин не найден")

    generate_fn = getattr(plugin, "generate_femur_from_dict", None) or getattr(
        plugin,
        "generate_conclusion_from_dict",
        None,
    )
    if not callable(generate_fn):
        raise HTTPException(status_code=400, detail="Плагин не поддерживает генерацию заключения через API")

    try:
        result = generate_fn(payload)
    except ValueError as exc:
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    conclusion = result.get("conclusion") if isinstance(result, dict) else str(result)
    return {"conclusion": conclusion}


@app.post("/api/plugins/{plugin_id}/report")
async def api_plugin_report(plugin_id: str, payload: Dict[str, Any]):
    plugin = _plugins_by_id.get(plugin_id)
    if not plugin:
        raise HTTPException(status_code=404, detail="Плагин не найден")

    generate_fn = getattr(plugin, "generate_all_from_dict", None) or getattr(
        plugin,
        "generate_report_from_dict",
        None,
    )
    if not callable(generate_fn):
        raise HTTPException(status_code=400, detail="Плагин не поддерживает комбинированный отчёт через API")

    try:
        result = generate_fn(payload)
    except ValueError as exc:
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    if isinstance(result, dict):
        return {
            "description": result.get("description", ""),
            "conclusion": result.get("conclusion", ""),
        }
    return {"text": str(result)}


