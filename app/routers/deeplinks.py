import json
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse

from app.config import settings

router = APIRouter(tags=["DeepLinks"], include_in_schema=False)

_REDIRECT_TEMPLATE = (Path(__file__).resolve().parent.parent / "assets" / "deeplink_redirect.html").read_text(encoding="utf-8")


@router.get("/.well-known/assetlinks.json")
async def assetlinks() -> JSONResponse:
    return JSONResponse([
        {
            "relation": ["delegate_permission/common.handle_all_urls"],
            "target": {
                "namespace": "android_app",
                "package_name": settings.ANDROID_PACKAGE_NAME,
                "sha256_cert_fingerprints": settings.android_fingerprints_list,
            },
        }
    ])


def _redirect_page(app_uri: str) -> HTMLResponse:
    html = (
        _REDIRECT_TEMPLATE
        .replace("__APP_URI__", json.dumps(app_uri))
        .replace("__DOWNLOAD_HREF__", settings.APP_DOWNLOAD_URL)
        .replace("__DOWNLOAD__", json.dumps(settings.APP_DOWNLOAD_URL))
    )
    return HTMLResponse(html)


@router.get("/dl/{path:path}")
async def deeplink_landing(path: str, request: Request) -> HTMLResponse:
    if not path:
        raise HTTPException(status_code=404)
    app_uri = f"{settings.APP_SCHEME}://{path}"
    if request.url.query:
        app_uri += f"?{request.url.query}"
    return _redirect_page(app_uri)